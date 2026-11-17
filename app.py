"""
Clip Studio — local server
Paste a YouTube (or other supported) link, pick start/end, and the server
downloads ONLY that section as MP4. The editor (ratio + captions + export)
then opens it in your browser.

Run:  python app.py   then open http://localhost:8000
"""
import io
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

import yt_dlp
from yt_dlp.utils import download_range_func

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
WORK = Path(tempfile.gettempdir()) / "clipstudio"
WORK.mkdir(exist_ok=True)


def find_ffmpeg():
    """System ffmpeg if present; else the imageio-ffmpeg binary, exposed under the name
    'ffmpeg' (yt-dlp does not recognise its 'ffmpeg-macos-…' file name)."""
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    try:
        import imageio_ffmpeg
        src = Path(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None
    bindir = WORK / "bin"
    bindir.mkdir(exist_ok=True)
    dst = bindir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not dst.exists():
        try:
            dst.symlink_to(src)
        except OSError:
            shutil.copy2(src, dst)
    return str(dst)


def find_deno():
    """yt-dlp needs a JavaScript runtime for YouTube (deno, from the 'deno' pip package)."""
    try:
        import deno
        return deno.find_deno_bin()
    except Exception:
        return shutil.which("deno")


FFMPEG = find_ffmpeg()
DENO = find_deno()
# yt-dlp's partial-download check looks for ffmpeg on PATH, not only ffmpeg_location
for _exe in (FFMPEG, DENO):
    if _exe:
        os.environ["PATH"] = str(Path(_exe).parent) + os.pathsep + os.environ.get("PATH", "")

MAX_CLIP_SECONDS = 10 * 60   # safety cap per clip
MAX_HEIGHT = 1080            # download quality cap

# Allowed origins for a separately hosted frontend (Vercel / Hostinger), comma separated.
# Example: ALLOWED_ORIGINS=https://clipstudio.vercel.app,https://mydomain.com   ("*" = any)
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
# Optional YouTube cookies (Netscape cookies.txt) — needed on cloud servers when YouTube says
# "Sign in to confirm you're not a bot". Give a file path, or paste the file content in YTDLP_COOKIES.
COOKIE_FILE = os.environ.get("YTDLP_COOKIES_FILE")
if not COOKIE_FILE and os.environ.get("YTDLP_COOKIES"):
    COOKIE_FILE = str(WORK / "cookies.txt")
    Path(COOKIE_FILE).write_text(os.environ["YTDLP_COOKIES"])
PROXY = os.environ.get("YTDLP_PROXY")  # optional, e.g. a residential proxy URL

app = Flask(__name__, static_folder=None)


def ydl_base():
    o = {"quiet": True, "noplaylist": True}
    if DENO:
        o["js_runtimes"] = {"deno": {"path": DENO}}
    if COOKIE_FILE and Path(COOKIE_FILE).exists():
        o["cookiefile"] = COOKIE_FILE
    if PROXY:
        o["proxy"] = PROXY
    return o


@app.after_request
def cors(resp):
    origin = (request.headers.get("Origin") or "").rstrip("/")
    if origin and ("*" in ALLOWED_ORIGINS or origin in ALLOWED_ORIGINS):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.route("/api/<path:_p>", methods=["OPTIONS"])
def preflight(_p):
    return ("", 204)


def parse_time(v):
    """Accepts 83, '83.5', '1:23', '01:02:03'."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    if not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts) or len(parts) > 3:
        raise ValueError(f"Bad time: {v}")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    return total


def valid_url(u):
    return isinstance(u, str) and re.match(r"^https?://", u.strip())


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/<path:name>")
def static_files(name):
    return send_from_directory(STATIC, name)


@app.get("/api/health")
def health():
    return jsonify(ok=True, ffmpeg=bool(FFMPEG), js_runtime=bool(DENO), cookies=bool(COOKIE_FILE), ytdlp=yt_dlp.version.__version__)


@app.post("/api/info")
def info():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not valid_url(url):
        return jsonify(error="Please paste a valid http(s) link."), 400
    try:
        with yt_dlp.YoutubeDL({**ydl_base(), "skip_download": True}) as ydl:
            meta = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify(error=f"Could not read this link: {short(e)}"), 400
    if meta.get("is_live"):
        return jsonify(error="This stream is live right now. Clip it after the stream ends (when the replay/VOD is available)."), 400
    return jsonify(
        title=meta.get("title"),
        duration=meta.get("duration"),
        thumbnail=meta.get("thumbnail"),
        uploader=meta.get("uploader") or meta.get("channel"),
    )


@app.post("/api/clip")
def clip():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not valid_url(url):
        return jsonify(error="Please paste a valid http(s) link."), 400
    if not FFMPEG:
        return jsonify(error="ffmpeg not found. Run: pip install imageio-ffmpeg"), 500
    try:
        start = parse_time(data.get("start")) or 0.0
        end = parse_time(data.get("end"))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    if end is None or end <= start:
        return jsonify(error="End time must be after start time."), 400
    if end - start > MAX_CLIP_SECONDS:
        return jsonify(error=f"Max {MAX_CLIP_SECONDS // 60} minutes per clip in this pilot."), 400

    job = WORK / uuid.uuid4().hex
    job.mkdir()
    opts = {
        **ydl_base(),
        "outtmpl": str(job / "clip.%(ext)s"),
        # H.264 + AAC so every browser can play and re-record it
        "format": (
            f"bv*[vcodec^=avc1][height<={MAX_HEIGHT}]+ba[ext=m4a]/"
            f"b[ext=mp4][height<={MAX_HEIGHT}]/"
            f"bv*[height<={MAX_HEIGHT}]+ba/b"
        ),
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG,
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,  # frame-accurate cut
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        files = sorted(job.glob("clip.*"))
        if not files:
            raise RuntimeError("No file produced")
        out = files[0]
        buf = io.BytesIO(out.read_bytes())
    except Exception as e:
        shutil.rmtree(job, ignore_errors=True)
        return jsonify(error=f"Download failed: {short(e)}"), 500
    shutil.rmtree(job, ignore_errors=True)
    buf.seek(0)
    return send_file(buf, mimetype="video/mp4", download_name="source_clip.mp4")


def short(e):
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e))
    return msg.replace("ERROR: ", "")[:300]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"\n  Clip Studio running →  http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
