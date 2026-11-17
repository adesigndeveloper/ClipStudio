# 🎬 Clip Studio

Make short clips from YouTube videos and add captions, all on your own computer.

Paste a YouTube link, choose the **From** and **To** time, and only that part is downloaded. Then choose a ratio (**9:16** for Reels/Shorts, **16:9**, or **1:1**), add captions in one of 3 styles, and export an **MP4**.

Everything runs locally on your computer. There's no account, no upload, and no watermark.

---

## ✅ What you need

| | |
|---|---|
| **Python 3.9 or newer** | [Download Python](https://www.python.org/downloads/) |
| **Internet** | To download the video part |
| **Browser** | Chrome or Edge works best for exporting |

ffmpeg and everything else are installed automatically on the first run.

> **Windows users:** when you install Python, tick **"Add Python to PATH"** on the first screen of the installer.

To check that Python is installed, open a Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```bash
python --version     # Windows
python3 --version    # Mac / Linux
```
You should see something like `Python 3.12.x`.

---

## 📥 Step 1: Download the project

**Option A: Download ZIP (easiest)**
1. On this GitHub page, click the green **Code** button, then **Download ZIP**.
2. Unzip it. You'll get a folder named `ClipStudio` (or `ClipStudio-main`).

**Option B: With git**
```bash
git clone https://github.com/<your-username>/ClipStudio.git
cd ClipStudio
```

---

## ▶️ Step 2: Run it

### Windows
1. Open the `ClipStudio` folder.
2. Double-click **`run_windows.bat`**.
3. If Windows shows "Windows protected your PC", click **More info** and then **Run anyway**.

### Mac
1. Open **Terminal**.
2. Type `cd `, with a space after it, and drag the `ClipStudio` folder into the Terminal window. Press **Enter**.
3. Run:
   ```bash
   chmod +x run_mac_linux.sh
   ./run_mac_linux.sh
   ```

### Linux
```bash
cd ClipStudio
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```
If you get a `venv` error on Ubuntu or Debian, run `sudo apt install python3-venv` first.

**The first run takes 1–2 minutes** while it installs everything. After that, your browser opens at:

### 👉 http://localhost:8000

If the page doesn't open by itself, or shows an error, wait a few seconds and refresh.

**Keep the Terminal or Command Prompt window open** while you use the app. To stop the app, press **Ctrl + C** in that window or just close it.

**Next time**, run `run_windows.bat` or `./run_mac_linux.sh` again. Starting is fast after the first run.

---

## ✂️ How to use

1. **Paste the YouTube link** and click **Check link**. You'll see the title and duration.
2. Enter **From** and **To**, for example `1:20` and `2:05`, then click **Fetch this part**. This takes 10–60 seconds.
3. Fine-trim on the timeline if needed.
4. Choose the **ratio** (9:16 / 16:9 / 1:1) and the framing.
5. **Add captions** in any of these ways:
   - type one at the playhead,
   - paste a script, or
   - import an `.srt` file.
6. Click **Export clip**, then **Download**.

You can also skip the link and **upload your own video file**.

---

## 🛠️ Manual setup (if the scripts don't work)

```bash
cd ClipStudio
python3 -m venv .venv                 # Windows: python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Then open **http://localhost:8000**.

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| `python` / `python3` not found | Install Python. On Windows, reinstall it and tick **Add Python to PATH**. |
| `permission denied: ./run_mac_linux.sh` | Run `chmod +x run_mac_linux.sh` |
| Port 8000 already in use | Use another port. Mac/Linux: `PORT=8001 python app.py`. Windows: `set PORT=8001 && python app.py`. Then open `http://localhost:8001`. |
| YouTube download suddenly fails | YouTube changes often. Close the app and run the script again, because it updates yt-dlp automatically. Manual update: `pip install -U "yt-dlp[default]"` |
| "This stream is live right now" | You can't clip a stream that's still live. Wait for the replay (VOD) after it ends. |
| "Sign in to confirm you're not a bot" | This is rare on home internet. Try again later, turn off your VPN, or try another network. |
| Export doesn't work | Use Chrome or Edge. |

To check the app's status, open http://localhost:8000/api/health. It should show `"ok": true`.

---

## ⚙️ Limits

- Max clip length: **10 minutes**. Max quality: **1080p**. You can change these with `MAX_CLIP_SECONDS` and `MAX_HEIGHT` in `app.py`.
- Many other sites supported by [yt-dlp](https://github.com/yt-dlp/yt-dlp) also work, such as Vimeo and Twitch VODs.

---

## 📁 Project files

```
ClipStudio/
├── app.py              # Local server (downloads the clip with yt-dlp + ffmpeg)
├── static/
│   ├── index.html      # Editor (ratio, captions, export) that runs in your browser
│   └── config.js       # Optional backend URL (leave empty for local use)
├── requirements.txt    # Python packages
├── run_windows.bat     # One-click start on Windows
└── run_mac_linux.sh    # One-click start on Mac / Linux
```

---

## ⚠️ Disclaimer

Only use videos you **own** or have **permission** to use. Downloading other people's videos without permission can break YouTube's Terms of Service and copyright law. You are responsible for how you use this tool.

Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [Flask](https://flask.palletsprojects.com/) and [ffmpeg](https://ffmpeg.org/).
