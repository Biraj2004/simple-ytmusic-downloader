# ARCHITECTURE.md
# YT Music Downloader — System Architecture

Author : Biraj Sarkar  
Version: 1.0  
Target : Windows 10/11 x64, portable, no installer

---

## 1. Overview

A portable Windows desktop application that downloads audio from YouTube and
YouTube Music links as MP3 files, with embedded thumbnail and metadata.
It wraps two external binaries — `yt-dlp.exe` and `ffmpeg.exe` — both fetched
automatically on first launch and stored locally. The GUI is built in Python
with PySide6 (Qt). The final deliverable is a single `.exe` produced by
PyInstaller.

The application has no installer, writes nothing to the Windows registry, and
is fully self-contained within its own folder.

---

## 2. Design Principles

These are the non-negotiable constraints that shaped every decision below.

**Portable.** The entire app lives in one folder. Copy the folder to another
machine and it works. Nothing is installed system-wide.

**Small and fast.** The PyInstaller exe contains only the GUI and orchestration
code. The two large, frequently-updated binaries (`yt-dlp.exe`, `ffmpeg.exe`)
live outside the frozen bundle. This keeps the exe small and allows those
binaries to be updated independently without rebuilding the app.

**Genuinely self-updating.** `yt-dlp.exe` is the official standalone binary
release (not a PyPI package import). Only the standalone binary supports
`yt-dlp -U` for in-place self-update. A PyPI package frozen into a
PyInstaller bundle cannot update itself; this architecture choice was made
explicitly to make the in-app "Update yt-dlp" button work correctly.

**No silent failures.** Every error — missing dependency, broken video,
dropped network, duplicate file — has a defined, visible outcome. Nothing
is swallowed silently.

**No registry, no admin rights.** The app runs as a standard user. All
persistent state lives in `data/config.json` next to the exe.

---

## 3. Folder Layout (Runtime)

```
YTMusicDownloader/
├── YTMusicDownloader.exe       <- PyInstaller onefile build; the app itself
├── bin/
│   ├── yt-dlp.exe              <- fetched from github.com/yt-dlp/yt-dlp releases
│   ├── ffmpeg.exe              <- extracted from gyan.dev ffmpeg-release-essentials.zip
│   └── ffprobe.exe             <- same zip as ffmpeg
├── data/
│   ├── config.json             <- user settings and window state
│   ├── archives/
│   │   └── <playlist_id>.txt   <- one file per playlist; used by --download-archive
│   └── logs/
│       └── app.log             <- rolling log (max 2 MB, then rotated)
└── downloads/                  <- default output root; user-configurable
```

All paths are resolved relative to `sys.executable` (the exe location) at
runtime, never hardcoded. This ensures portability regardless of where the
user places the folder.

---

## 4. Module Structure (Source Code)

```
src/
├── main.py                 <- entry point; launches QApplication
├── constants.py            <- all magic values, error string tables, URLs
├── config.py               <- read/write config.json; dataclass for settings
├── deps/
│   ├── checker.py          <- detects presence and version of yt-dlp, ffmpeg
│   └── fetcher.py          <- downloads and installs yt-dlp.exe / ffmpeg zip
├── engine/
│   ├── queue_item.py       <- dataclass: url, mode, status, metadata, archive path
│   ├── metadata.py         <- runs yt-dlp --dump-json to resolve title/artist
│   ├── archive.py          <- read/write/reconcile per-playlist archive .txt files
│   └── worker.py           <- QThread; spawns yt-dlp.exe subprocess, parses stdout
├── gui/
│   ├── main_window.py      <- top-level QMainWindow; tab container
│   ├── tabs/
│   │   ├── downloader.py   <- Downloader tab: URL input, mode, queue list, progress
│   │   ├── settings.py     <- Settings tab: folder, pattern, toggles, dep cards
│   │   └── about.py        <- About tab: name, version, links
│   ├── widgets/
│   │   ├── queue_row.py    <- single queue item widget (icon, title, sub, pbar, x)
│   │   ├── dep_card.py     <- dependency version/status/update card widget
│   │   └── progress_bar.py <- Windows-style labelled progress bar widget
│   └── setup_window.py     <- first-run dependency setup window (shown before main)
└── utils/
    ├── paths.py            <- resolve all runtime paths from exe location
    ├── logger.py           <- rolling file logger + in-app log buffer
    └── net.py              <- requests wrapper with timeout and retry
```

---

## 5. Tech Stack

| Layer              | Choice                         | Reason                                                                                      |
|--------------------|--------------------------------|---------------------------------------------------------------------------------------------|
| Language           | Python 3.11+                   | Sufficient for all tasks; PySide6 and requests available                                    |
| GUI framework      | PySide6 (Qt 6)                 | Native Windows look via QStyle; proper threading with QThread and signals                   |
| Qt style           | `QStyleFactory.create("Fusion")` | Consistent cross-Windows-version appearance; light theme matches the approved mockup      |
| Downloader         | `yt-dlp.exe` subprocess        | Standalone binary supports `-U` self-update; no PyPI import needed in the bundle           |
| Audio processing   | `ffmpeg.exe` (gyan.dev static) | Required by yt-dlp for MP3 extraction, thumbnail embed, metadata embed                     |
| HTTP               | `requests` (bundled)           | Used only for dep fetching (yt-dlp.exe, ffmpeg zip) and version checks                     |
| Packaging          | PyInstaller `--onefile --windowed` | Single exe; `--windowed` suppresses the console on Windows                              |
| Config             | JSON (`data/config.json`)      | No registry; human-readable; easy to hand-edit if needed                                   |
| Logging            | Python `logging` + RotatingFileHandler | `data/logs/app.log`; max 2 MB, 1 backup                                          |

Do not substitute Tkinter (inadequate for this GUI), wxPython (heavier),
or any Electron/web-based approach (adds Node.js dependency, much larger
binary size).

---

## 6. Data Flow

### 6.1 Normal download

```
User pastes URL + clicks Add
    -> URL validation (regex; must match youtube.com or music.youtube.com)
    -> QueueItem created (status = QUEUED)
    -> Added to queue list widget

User clicks Start queue
    -> DownloadWorker(QThread) created for first QUEUED item
    -> worker.metadata_resolve():
         runs: yt-dlp.exe --dump-json --skip-download <url>
         parses: title, artist, playlist_id (if playlist)
         updates: QueueItem.title, QueueItem.archive_path
    -> worker.reconcile_archive():   [Update playlist mode only]
         reads archive file line by line
         for each video_id in archive:
             compute expected output filepath from title/artist template
             if file does NOT exist on disk -> remove that line from archive
         writes corrected archive back
    -> worker.run_download():
         builds subprocess args list (see Section 9)
         spawns: subprocess.Popen([yt-dlp.exe, ...], stdout=PIPE, stderr=STDOUT,
                                   creationflags=CREATE_NO_WINDOW)
         reads stdout line by line in loop:
             progress line  -> emit progress_updated signal -> GUI updates pbar
             postprocessor line -> append to item log buffer
             error line     -> classify (content vs network) -> trigger retry logic
    -> on clean exit (returncode 0):
         QueueItem.status = DONE
         start next QUEUED item
    -> on non-zero exit:
         classify error, apply retry or pause logic (see Section 7)
```

### 6.2 Dependency fetch (first run / missing bin/)

```
App launches
    -> SetupWindow shown (blocks main window)
    -> checker.py checks bin/yt-dlp.exe:
         runs: yt-dlp.exe --version
         if missing or fails: fetcher downloads from GitHub releases API
    -> checker.py checks bin/ffmpeg.exe:
         runs: ffmpeg.exe -version
         if missing or fails: fetcher downloads ffmpeg-release-essentials.zip
                               from gyan.dev, extracts ffmpeg.exe + ffprobe.exe
    -> both pass: SetupWindow closes, MainWindow shown
    -> either fails after retries: SetupWindow shows error + Retry button; app
       cannot proceed until both tools are present and working
```

### 6.3 yt-dlp self-update

```
User clicks Check for update (Settings tab)
    -> runs: yt-dlp.exe --version  -> installed_version
    -> hits: https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest
    -> compares tag_name to installed_version
    -> if newer: pill changes to "update available"; shows installed -> latest
    -> user clicks Update now:
         runs: yt-dlp.exe -U  (yt-dlp replaces its own binary in bin/)
         monitors stdout for progress percentage if present
         on completion: re-runs --version; updates displayed version + pill
```

---

## 7. Error Handling — All Cases

This section is the most important part of this document. Every case has an
explicit outcome; none are left to the implementer's judgement.

### 7.1 Content error (private / deleted / region-blocked video)

Identified by: yt-dlp exits non-zero AND stdout contains one of the strings
in `constants.CONTENT_ERROR_STRINGS` (e.g. "Private video", "Video unavailable",
"This video is not available", "Sign in to confirm your age",
"This video has been removed").

Action:
- Retry up to `config.max_retries_video_error` times (default 3).
- Backoff between retries: 2 s, 5 s, 10 s.
- After all retries exhausted: mark item as SKIPPED, append to error log
  (timestamp, title/URL, reason string), continue to next queue item.
- Do NOT pause the queue. Do NOT cancel other items.
- Show skipped count in queue row subtitle: "Playlist · 38 tracks · done · 2 skipped".

### 7.2 Network error (connection drop / timeout / DNS failure)

Identified by: yt-dlp exits non-zero AND stdout contains one of the strings
in `constants.NETWORK_ERROR_STRINGS` (e.g. "Connection refused",
"Failed to resolve", "Read timed out", "Network is unreachable",
"urlopen error", "RemoteDisconnected").

Action:
- Retry up to `config.max_retries_network_error` times (default 5).
- Exponential backoff: 3 s, 6 s, 12 s, 24 s, 48 s.
- After all retries exhausted: mark item as PAUSED_NETWORK (not SKIPPED).
  Show "Paused — network issue, check your connection" on that row.
  Show a Retry button on that specific row.
- Do NOT skip. Do NOT cancel. The queue stops at this item until user retries.
- This is deliberately different from 7.1 — a network drop is recoverable;
  a deleted video is not.

### 7.3 Duplicate / already-downloaded file

The source of truth is the filesystem, not the archive file.

Pre-flight check before every download:
1. Resolve expected output filepath: run `yt-dlp.exe --dump-json --skip-download`
   to get title and artist, then apply the filename pattern.
2. If the file exists on disk: mark row as SKIPPED_DUPLICATE.
   Show "Already downloaded — file exists, skipped" on the row.
   Do not re-download. Do not overwrite.
3. If the file does NOT exist on disk, but the video ID IS in the archive file:
   Remove that line from the archive file before invoking the download.
   Proceed with a fresh download. This covers the "user deleted the file, now
   wants it back" case — the archive must not block it.
4. If the file does not exist and the video ID is not in the archive: normal
   download. Append video ID to archive on success.

This logic MUST be implemented manually. Passing `--download-archive` to
yt-dlp unmodified does not satisfy step 3 — yt-dlp's own archive check is
file-blind and will skip a video regardless of whether the output file exists.

### 7.4 Invalid URL (not a YouTube / YT Music link)

Validate at add-time using a regex against the URL field.
Accepted patterns: `youtube.com/watch`, `youtube.com/playlist`,
`music.youtube.com/watch`, `music.youtube.com/playlist`, `youtu.be/`.
If the URL does not match: show inline error below the URL field.
Do not add the item to the queue. Do not show a dialog box.

### 7.5 Update playlist mode + single video URL

If mode is UPDATE_PLAYLIST and the URL resolves (via `--dump-json`) to a
single video (no `playlist_id` in the response): show inline validation
error "Update playlist mode requires a playlist link" below the URL field.
Do not add to queue.

### 7.6 Empty queue + Start pressed

The Start queue button must be visually disabled (greyed out, `setEnabled(False)`)
whenever the queue is empty. No click handler action needed.

### 7.7 Missing dependency detected on launch (not first run)

If `bin/yt-dlp.exe` or `bin/ffmpeg.exe` is missing on a non-first launch
(user deleted a file):
- Show the SetupWindow again, same as first run.
- Fetch only the missing file(s), not both if one is present.
- This check runs every launch; it is fast (just a file existence check
  followed by `--version`).

### 7.8 yt-dlp / ffmpeg update fails

If `yt-dlp.exe -U` exits non-zero, or the ffmpeg re-download fails:
- Show an inline error on the dependency card: "Update failed — check your
  internet connection."
- The existing installed version remains intact and usable.
- Do not leave `bin/` in a partially-replaced state — download to a temp file
  first, then rename atomically on success.

### 7.9 config.json corrupted or missing

On launch, if `data/config.json` is missing or cannot be parsed:
- Log the error.
- Silently recreate it with default values. Do not show an error dialog.
- Default `download_folder`: `<exe_dir>/downloads`.

### 7.10 Output folder does not exist

If the configured download folder does not exist at download time:
- Create it (including any missing parent directories) before starting.
- If creation fails (permissions, invalid path): show an inline error in the
  Settings tab and disable Start queue until a valid folder is selected.

### 7.11 Subprocess unexpectedly killed / crash

If the yt-dlp subprocess exits with a return code not matching any known
error pattern (e.g. killed by the OS, segfault):
- Mark the item as ERROR.
- Show "Unexpected error — see log" on the queue row.
- Log the full stdout/stderr buffer for that item.
- Continue with the next queue item.

### 7.12 Cancel mid-download

Per-row cancel or Cancel all:
- Call `process.terminate()` on the active subprocess.
- Wait up to 3 seconds for it to exit.
- If still running after 3 s: call `process.kill()`.
- After process exits: delete any `.part` temporary files in the download
  folder that were created by that yt-dlp invocation.
- Mark item as CANCELLED. Do not add it to the error log.

---

## 8. Threading Model

All download work runs on worker threads. The GUI thread (main thread) only
updates widgets.

```
Main thread (QApplication)
    |
    +-- SetupWindow (blocking; shown before MainWindow if deps missing)
    |
    +-- MainWindow
          |
          +-- DownloadWorker : QThread   (one at a time; sequential queue)
                |
                +-- metadata resolve   (subprocess: yt-dlp --dump-json)
                +-- archive reconcile  (filesystem read/write; fast)
                +-- download loop      (subprocess: yt-dlp [full args])
                      |
                      signals emitted to main thread:
                      +-- progress_updated(item_id, percent, speed_str)
                      +-- item_status_changed(item_id, status)
                      +-- item_log_line(item_id, line)
                      +-- queue_finished()
                      +-- error_occurred(item_id, error_type, message)
```

Rules:
- Never update a widget from a worker thread. Always use signals.
- Never block the main thread with a subprocess call.
- One active DownloadWorker at a time. When it finishes (DONE, SKIPPED,
  PAUSED_NETWORK, CANCELLED), the main thread starts the next QUEUED item.
- The worker checks a `_cancel_requested` flag (a threading.Event) at the
  start of each loop iteration so cancellation is prompt.

---

## 9. yt-dlp Subprocess Arguments

Built as a Python list. Never concatenated as a string. Passed to
`subprocess.Popen` with `shell=False`.

```python
args = [
    str(BIN_DIR / "yt-dlp.exe"),
    "--no-playlist" if item.is_single else "--yes-playlist",
    "-x",
    "--audio-format", "mp3",
    "--audio-quality", config.audio_quality,          # "0" = best VBR
    "--ffmpeg-location", str(BIN_DIR / "ffmpeg.exe"),
    "--output", str(output_template),                 # full path with pattern
    "--newline",
    "--progress",
    "--no-warnings",
]
if config.embed_metadata:
    args.append("--add-metadata")
if config.embed_thumbnail:
    args += [
        "--embed-thumbnail",
        "--ppa",
        "EmbedThumbnail+ffmpeg_o:-c:v mjpeg -vf crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
    ]
if item.mode == Mode.UPDATE_PLAYLIST:
    args += ["--download-archive", str(item.archive_path)]
args.append(item.url)
```

`output_template` = `config.download_folder / "%(title)s - %(artist)s.%(ext)s"`

`subprocess.Popen` flags on Windows:
```python
process = subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
    creationflags=subprocess.CREATE_NO_WINDOW,
)
```

`CREATE_NO_WINDOW` is mandatory. Without it, a console window flashes open
on every download invocation in a `--windowed` PyInstaller build.

---

## 10. Progress Line Parsing

yt-dlp emits (with `--newline --progress`):

```
[download]  42.3% of    5.20MiB at    1.10MiB/s ETA 00:03
```

Regex:

```python
PROGRESS_RE = re.compile(
    r"\[download\]\s+([\d.]+)%\s+of\s+[\d.]+\S+\s+at\s+([\d.]+\S+/s)"
)
```

Group 1: percentage (float). Group 2: speed string (display only).

Lines not matching this pattern: passed to the item log buffer.
Postprocessor lines (`[ExtractAudio]`, `[EmbedThumbnail]`, `[Metadata]`):
also passed to log buffer — useful for debugging.

---

## 11. Config Schema

File: `data/config.json`

```json
{
    "download_folder": "C:\\Users\\username\\Music\\YT-Music",
    "filename_pattern": "%(title)s - %(artist)s",
    "audio_quality": "0",
    "embed_thumbnail": true,
    "embed_metadata": true,
    "max_retries_video_error": 3,
    "max_retries_network_error": 5,
    "window_x": 100,
    "window_y": 100,
    "window_w": 700,
    "window_h": 540
}
```

`window_x/y/w/h`: saved on close, restored on launch. Validated on load —
if the saved position is off-screen (e.g. user changed monitor setup),
reset to centre of primary screen.

Default `download_folder`: `<exe_dir>/downloads` (created on first use).

---

## 12. Dependency Fetch Sources

| Binary         | Source                                                        | Method                                    |
|----------------|---------------------------------------------------------------|-------------------------------------------|
| `yt-dlp.exe`   | `https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe` | Direct download via `requests`  |
| `ffmpeg.exe`   | `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip`      | Download zip, extract, place in `bin/`   |
| `ffprobe.exe`  | Same zip as ffmpeg                                            | Extracted alongside ffmpeg                |

Version check for yt-dlp:
- Installed: `yt-dlp.exe --version` (stdout, strip whitespace)
- Latest: `https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest`
  → `json["tag_name"]`

Version check for ffmpeg:
- Installed: `ffmpeg.exe -version` → parse first line
  (`ffmpeg version N-XXXXX-gXXXXXXX`)
- Latest: re-download and compare (ffmpeg has no simple version API;
  update is triggered manually by the user from Settings, not auto-checked)

---

## 13. Packaging

```
pip install pyinstaller
pyinstaller --onefile --windowed --name YTMusicDownloader src/main.py
```

The `bin/`, `data/`, and `downloads/` folders are NOT bundled inside the exe.
They are created at runtime next to the exe. The exe contains only:
- Python interpreter (frozen)
- PySide6 Qt libraries
- `requests`
- Application source modules

PyInstaller hidden imports to add if needed:
```
--hidden-import PySide6.QtSvg
--hidden-import PySide6.QtXml
```

Test the build on a clean Windows VM (no Python installed) before shipping.

---

## 14. Non-Goals (v1)

These are explicitly out of scope. Do not implement them.

- Video download (MP4 or other formats)
- Login / cookies for private or age-restricted content
- Concurrent / parallel downloads
- Auto-detection of previously-downloaded playlists (mode is always manual)
- macOS or Linux builds
- System tray integration
- Dark mode toggle (light Fusion theme only for v1)
- Any form of telemetry or network call not initiated by the user
