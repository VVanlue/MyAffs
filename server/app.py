"""
MyAffs. — reference TTS server
================================

This is a minimal Flask server that implements the one endpoint the
frontend (index.html) expects:

    POST /api/tts
    body: {"text": "...", "speed": 1.5, "voice": "default"}
    -> 200, Content-Type: audio/wav, raw WAV bytes
    -> 4xx/5xx, JSON {"error": "..."} on failure

Out of the box this returns a short placeholder tone so you can wire
up the frontend and confirm the request/response flow works end to
end. Swap `synthesize_speech()` below for a call into your own
trained TTS model — that's the only function you need to change.

Run it:
    cd server
    pip install -r requirements.txt
    python app.py
    # server listens on http://localhost:5000

Then point the frontend at it. If you're serving index.html from this
same Flask app (see the bottom of this file), the default
TTS_ENDPOINT = "/api/tts" in index.html already works with no changes.
If you host the frontend somewhere else (GitHub Pages, Netlify, etc.),
change TTS_ENDPOINT in index.html to this server's full URL, e.g.
"https://your-tts-server.example.com/api/tts" — CORS is already
enabled below for that case.
"""

import io
import math
import struct
import wave

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="..", static_url_path="")
CORS(app)  # allow the frontend to call this API from a different origin

MAX_CHARS = 2000
SAMPLE_RATE = 22050


def synthesize_speech(text: str, speed: float, voice: str) -> bytes:
    """
    Replace this function with a call into your trained TTS model.

    It must return raw WAV audio bytes (mono or stereo, 16-bit PCM is
    simplest). `text` is already validated and trimmed to MAX_CHARS.
    `speed` is a float between 0.25 and 10 — you can bake it into the
    generated audio here (e.g. by adjusting your model's duration /
    speaking-rate parameter), or leave the audio at a natural pace and
    let the browser apply playbackRate on top; the frontend does both
    so either approach works.

    Common ways to plug in a real model:
      - Coqui TTS (`pip install TTS`):
            from TTS.api import TTS
            _tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            def synthesize_speech(text, speed, voice):
                buf = io.BytesIO()
                _tts.tts_to_file(text=text, file_path=buf, speed=speed)
                return buf.getvalue()
      - Your own trained model: load its checkpoint once at import time
        (module-level, outside this function, so it isn't reloaded per
        request) and run inference here, writing the result to WAV
        bytes with the `wave` module or your model's own exporter.

    For now, this placeholder renders `text` as a gentle series of
    tones (one per word) so the full pipeline — request, save, mix,
    export — can be tested without a trained model attached yet.
    """
    words = text.split() or ["hush"]
    duration_per_word = max(0.12, 0.32 / max(speed, 0.25))
    n_samples = int(SAMPLE_RATE * duration_per_word)

    frames = bytearray()
    base_freq = 220.0
    for i, _word in enumerate(words):
        freq = base_freq * (1.0 + 0.15 * math.sin(i))
        for n in range(n_samples):
            t = n / SAMPLE_RATE
            envelope = math.sin(math.pi * n / n_samples)  # fade in/out each "syllable"
            sample = 0.2 * envelope * math.sin(2 * math.pi * freq * t)
            frames += struct.pack("<h", int(sample * 32767))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(bytes(frames))
    return buf.getvalue()


@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json(silent=True) or {}

    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No text was provided."}), 400
    if len(text) > MAX_CHARS:
        return jsonify({"error": f"Text is too long (max {MAX_CHARS} characters)."}), 400

    try:
        speed = float(data.get("speed", 1))
    except (TypeError, ValueError):
        speed = 1.0
    speed = max(0.25, min(speed, 10.0))

    voice = str(data.get("voice", "default"))[:64]

    try:
        wav_bytes = synthesize_speech(text, speed, voice)
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the client
        app.logger.exception("TTS synthesis failed")
        return jsonify({"error": "Voice synthesis failed on the server."}), 500

    return send_file(io.BytesIO(wav_bytes), mimetype="audio/wav")


# Optional: serve index.html and friends from this same server, so the
# whole site (frontend + API) runs from one process during development.
@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
