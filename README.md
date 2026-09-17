# MyAffs.

Build a custom subliminal / affirmation tape: write affirmations across
up to five layers, have each one voiced, tune its speed and volume,
layer in ambiance, solfeggio frequencies, isochronic tones and music,
then export it all as one audio file.

This repo has two parts:

```
index.html        the whole frontend — one self-contained file, no build step
server/app.py      a reference backend that turns text into speech (TTS)
server/requirements.txt
```

## Running it locally

1. **Start the voice server:**
   ```bash
   cd server
   pip install -r requirements.txt
   python app.py
   ```
   This serves both the API (`/api/tts`) and `index.html` itself at
   `http://localhost:5000`, so you can just open that URL in a
   browser and everything works together with no extra configuration.

2. **Or serve the frontend separately** (e.g. GitHub Pages, Netlify,
   any static host) and run `server/app.py` on your own server. In
   that case open `index.html` and change this one line near the top
   of the `<script>` block:
   ```js
   var TTS_ENDPOINT = "/api/tts";
   ```
   to your server's full URL, e.g.:
   ```js
   var TTS_ENDPOINT = "https://your-tts-server.example.com/api/tts";
   ```
   CORS is already enabled in `app.py` (via `flask-cors`) so this
   cross-origin setup works out of the box.

## Wiring in your own trained TTS model

Everything routes through one function in `server/app.py`:

```python
def synthesize_speech(text: str, speed: float, voice: str) -> bytes:
    ...
```

Out of the box it returns a placeholder tone sequence so you can test
the full pipeline (save a layer → request → decode → mix → download)
before your model is ready. Replace the body of that function with a
call into your model, returning WAV bytes. Load your model/checkpoint
once at module import time (outside the function) rather than per
request, so it isn't re-initialized on every call. The docstring in
that file has a worked example using Coqui TTS as a starting point if
that's useful, but any model that can produce a WAV/PCM buffer from
text will work — the frontend doesn't care how the audio was made.

**Request contract** the frontend sends:
```json
POST /api/tts
{ "text": "I am calm and confident.", "speed": 1.5, "voice": "default" }
```

**Response contract** the frontend expects:
- `200` with `Content-Type: audio/wav` (or `audio/mpeg`) and the raw audio bytes
- Any error status with JSON `{ "error": "message shown to the user" }`

If a layer is saved while no voice server is reachable, the frontend
doesn't break — it shows a "preview only" tag on that layer (browser
text-to-speech is used for on-screen previewing only) and simply
leaves that layer's spoken audio out of the final downloaded file
until a server is connected.

## What's client-side only

The ambiance, solfeggio frequency, isochronic tone, and music-preview
sounds are all synthesized live in the browser with the Web Audio API
— no audio files or server calls needed for those. The music tab
currently plays a simple placeholder arpeggio per genre; swap in real
licensed tracks whenever you have them by pointing `buildOverlayGraph`
(in `index.html`) at actual audio files instead of the generated tone,
or extending it to `fetch`+`decodeAudioData` a file per genre.

## Accounts & storage

Login/signup/guest accounts and saved tapes currently live in the
browser's `localStorage` (passwords are hashed with SHA-256 before
being stored, never in plain text). This is fine for a single-browser
demo but isn't a real user database — usernames/passwords won't carry
over between browsers or devices, and anyone with access to the same
browser profile can see the (hashed) account list. When you're ready
for real accounts, swap `loadUsers()` / `saveUsers()` in `index.html`
for calls to your own backend and auth system.

## Donations

The Ko-fi links in the page currently point to a placeholder
(`https://ko-fi.com/myaffs`) — update every occurrence to your real
Ko-fi URL once it's live (search the file for `ko-fi.com/myaffs`).
