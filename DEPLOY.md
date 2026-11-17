# Deploying Clip Studio

Clip Studio has two parts:

| Part | What it does | Where it can run |
|---|---|---|
| `static/` (HTML + JS) | Editor: ratio, captions, export (all in the browser) | Anywhere: Vercel, Hostinger shared, Netlify, or the Python server itself |
| `app.py` (Python) | Downloads the YouTube section with yt-dlp + ffmpeg | Only on a server that can run Python + ffmpeg for 1–3 minutes per request |

**A browser on its own cannot download from YouTube** (CORS, signed stream URLs, JS challenges).
So the HTML file needs the Python backend for "From a link".

## Why not Vercel or Hostinger shared for the backend
- **Vercel functions:** the response limit is 4.5 MB (a video clip is bigger), there is a time limit, and there's no ffmpeg. YouTube also blocks AWS/Vercel IPs ("Sign in to confirm you're not a bot").
- **Hostinger shared hosting:** PHP only, no long Python processes, no ffmpeg.

Both are fine for the **frontend** (`static/` folder).

---

## Option A — Backend on your own PC + free Cloudflare Tunnel (free, most reliable)
Your home internet IP is not blocked by YouTube.

1. Run the backend: `./run_mac_linux.sh` (or `run_windows.bat`)
2. Install cloudflared: `brew install cloudflared` (Windows: download from Cloudflare)
3. `cloudflared tunnel --url http://localhost:8000` → it prints a URL like `https://xyz.trycloudflare.com`
4. Open that URL directly, or put it in `static/config.js` for your Vercel/Hostinger frontend.

Drawback: your PC has to stay on. The quick-tunnel URL changes on every restart (a named tunnel with your own domain keeps it fixed, still free).

## Option B — Backend on Render (free, Docker)
1. Push this folder to GitHub.
2. Render → New → Blueprint (it reads `render.yaml`) or Web Service → Docker.
3. You get `https://clipstudio-api.onrender.com`. The full app also works at that URL.

Drawbacks: the free plan sleeps after 15 minutes (the first request takes about 50 seconds), and YouTube often blocks Render IPs. In that case, add cookies (see below).

Other Docker hosts that work the same way: Railway, Fly.io, Koyeb, or a **Hostinger VPS** (about $5/month, best paid option: `docker build -t clip . && docker run -d -p 80:8000 clip`).

## Frontend on Vercel
1. Edit `static/config.js` → `window.CLIPSTUDIO_API = 'https://your-backend-url';`
2. `npx vercel` in this folder (uses `vercel.json`, which serves `static/`). Or upload `static/` to Vercel through GitHub.
3. On the backend, set `ALLOWED_ORIGINS=https://your-app.vercel.app` (the default `*` allows all).

## Frontend on Hostinger shared hosting
Upload the **contents** of `static/` (`index.html`, `config.js`) to `public_html/` with File Manager. Set the backend URL in `config.js`.

Tip: `?api=https://backend-url` on the page URL also sets the backend and remembers it in that browser.

---

## YouTube "Sign in to confirm you're not a bot" on cloud servers
1. In Chrome, install the "Get cookies.txt LOCALLY" extension and export youtube.com cookies (use a spare Google account).
2. On the server, set the env var `YTDLP_COOKIES` to the file's full text (or `YTDLP_COOKIES_FILE` to a path).
3. Optional: set `YTDLP_PROXY` to a residential proxy URL.

`/api/health` shows `ffmpeg`, `js_runtime` and `cookies` status.

## Environment variables
| Var | Default | Meaning |
|---|---|---|
| `PORT` | 8000 | Port |
| `HOST` | 127.0.0.1 | Use `0.0.0.0` when running `python app.py` on a server (Docker uses gunicorn on 0.0.0.0) |
| `ALLOWED_ORIGINS` | `*` | Frontend domains allowed to call the API (comma separated) |
| `YTDLP_COOKIES` / `YTDLP_COOKIES_FILE` | – | YouTube cookies |
| `YTDLP_PROXY` | – | Proxy for yt-dlp |
