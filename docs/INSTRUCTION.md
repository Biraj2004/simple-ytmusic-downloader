# INSTRUCTION.md
# YT Music Downloader — Build Instructions for the Coding Agent

Author : Biraj Sarkar  
Version: 1.0

Read ARCHITECTURE.md and DESIGN_GUIDE.md in full before writing any code.
This document tells you what to build, in what order, and what to verify at
each stage. Do not skip phases. Do not merge phases.

---

## Phase 0 — Environment

```
python --version          # must be 3.11 or higher
pip install PySide6 requests pyinstaller
```

Do NOT install `yt-dlp` as a pip package. The application uses the standalone
`yt-dlp.exe` binary, fetched at runtime, not a Python import.

Create the source tree per ARCHITECTURE.md Section 4. All source lives under
`src/`. All paths at runtime are resolved relative to `sys.executable`.

---

## Phase 1 — Foundation Modules (no GUI)

Build and test these before touching any GUI code.

### 1.1 `src/utils/paths.py`

```python
import sys
from pathlib import Path

def exe_dir() -> Path:
    # Works both in dev (script) and frozen (PyInstaller) modes
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent

EXE_DIR   = exe_dir()
BIN_DIR   = EXE_DIR / "bin"
DATA_DIR  = EXE_DIR / "data"
LOGS_DIR  = DATA_DIR / "logs"
ARCH_DIR  = DATA_DIR / "archives"
CONF_PATH = DATA_DIR / "config.json"
YTDLP_EXE = BIN_DIR / "yt-dlp.exe"
FFMPEG_EXE = BIN_DIR / "ffmpeg.exe"
FFPROBE_EXE = BIN_DIR / "ffprobe.exe"
```

Create all directories on import if they do not exist:
`BIN_DIR.mkdir(parents=True, exist_ok=True)` etc.

### 1.2 `src/constants.py`

Define all magic values here. Nothing else in the codebase should contain
bare strings for error patterns, URLs, or version strings.

```python
# Dependency download URLs
YTDLP_DOWNLOAD_URL  = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_RELEASES_API  = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Placeholder URLs — Biraj will replace these
TODO_GITHUB_URL = "https://github.com/Biraj2004"
TODO_REPO_URL   = "https://github.com/Biraj2004/yt-music-downloader"

# App info
APP_NAME    = "YT Music Downloader"
APP_VERSION = "1.0.0"

# yt-dlp error string classification
# Extend this list when new error variants are encountered in practice.
CONTENT_ERROR_STRINGS = [
    "Private video",
    "Video unavailable",
    "This video is not available",
    "This video has been removed",
    "This video is unavailable",
    "Sign in to confirm your age",
    "This live event will begin in",
    "members-only content",
    "This video is only available to",
    "Playback is not available",
    "has been terminated",
    "This account has been terminated",
    "No video formats found",
    "This content isn't available",
]

NETWORK_ERROR_STRINGS = [
    "Connection refused",
    "Failed to resolve",
    "Read timed out",
    "Network is unreachable",
    "urlopen error",
    "RemoteDisconnected",
    "ConnectionResetError",
    "TimeoutError",
    "socket.timeout",
    "Unable to connect",
    "getaddrinfo failed",
    "SSL: CERTIFICATE_VERIFY_FAILED",
    "Temporary failure in name resolution",
]

# URL validation
VALID_URL_PREFIXES = [
    "https://www.youtube.com/watch",
    "https://youtube.com/watch",
    "https://www.youtube.com/playlist",
    "https://youtube.com/playlist",
    "https://music.youtube.com/watch",
    "https://music.youtube.com/playlist",
    "https://youtu.be/",
    "http://www.youtube.com/watch",
    "http://youtube.com/watch",
    "http://youtu.be/",
]
```

### 1.3 `src/config.py`

Dataclass wrapping `config.json`. Read on launch; write on settings save
and window close.

```python
from dataclasses import dataclass, asdict, field
import json
from utils.paths import CONF_PATH

@dataclass
class Config:
    download_folder: str = ""        # set to str(EXE_DIR/"downloads") on init if empty
    filename_pattern: str = "%(title)s - %(artist)s"
    audio_quality: str = "0"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    max_retries_video_error: int = 3
    max_retries_network_error: int = 5
    window_x: int = -1              # -1 means "centre on first launch"
    window_y: int = -1
    window_w: int = 700
    window_h: int = 540

def load_config() -> Config:
    try:
        data = json.loads(CONF_PATH.read_text(encoding="utf-8"))
        return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
    except Exception:
        return Config()             # silently reset on any parse failure

def save_config(cfg: Config) -> None:
    CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONF_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
```

### 1.4 `src/deps/checker.py`

```python
import subprocess
from utils.paths import YTDLP_EXE, FFMPEG_EXE

def get_ytdlp_version() -> str | None:
    """Returns version string or None if not present / broken."""
    try:
        r = subprocess.run(
            [str(YTDLP_EXE), "--version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

def get_ffmpeg_version() -> str | None:
    try:
        r = subprocess.run(
            [str(FFMPEG_EXE), "-version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            return r.stdout.splitlines()[0]  # first line has version
        return None
    except Exception:
        return None

def all_deps_present() -> bool:
    return YTDLP_EXE.exists() and FFMPEG_EXE.exists()

def deps_functional() -> tuple[bool, bool]:
    """Returns (ytdlp_ok, ffmpeg_ok)."""
    return (get_ytdlp_version() is not None, get_ffmpeg_version() is not None)
```

### 1.5 `src/deps/fetcher.py`

Downloads missing binaries. Runs in a QThread (from SetupWindow).
Must emit progress signals so the setup UI can show a live progress bar.

```python
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from utils.paths import BIN_DIR, YTDLP_EXE, FFMPEG_EXE, FFPROBE_EXE
from constants import YTDLP_DOWNLOAD_URL, FFMPEG_DOWNLOAD_URL

class FetchWorker(QThread):
    progress = Signal(str, int)    # (item_name, percent)
    item_done = Signal(str)        # item_name
    item_failed = Signal(str, str) # (item_name, error_message)
    all_done = Signal()

    def run(self):
        if not YTDLP_EXE.exists():
            self._fetch_ytdlp()
        else:
            self.item_done.emit("yt-dlp.exe")

        if not FFMPEG_EXE.exists():
            self._fetch_ffmpeg()
        else:
            self.item_done.emit("ffmpeg.exe")

        self.all_done.emit()

    def _fetch_ytdlp(self):
        name = "yt-dlp.exe"
        try:
            tmp = BIN_DIR / "yt-dlp.exe.tmp"
            self._download(YTDLP_DOWNLOAD_URL, tmp, name)
            tmp.rename(YTDLP_EXE)
            self.item_done.emit(name)
        except Exception as e:
            self.item_failed.emit(name, str(e))

    def _fetch_ffmpeg(self):
        name = "ffmpeg.exe"
        try:
            tmp_zip = BIN_DIR / "ffmpeg.zip.tmp"
            self._download(FFMPEG_DOWNLOAD_URL, tmp_zip, name)
            self._extract_ffmpeg(tmp_zip)
            tmp_zip.unlink(missing_ok=True)
            self.item_done.emit(name)
        except Exception as e:
            self.item_failed.emit(name, str(e))

    def _download(self, url: str, dest: Path, label: str):
        # Stream download with progress emission
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                done += len(chunk)
                if total:
                    self.progress.emit(label, int(done * 100 / total))

    def _extract_ffmpeg(self, zip_path: Path):
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                fname = Path(member).name
                if fname in ("ffmpeg.exe", "ffprobe.exe"):
                    target = BIN_DIR / fname
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
```

**Test Phase 1 manually before proceeding:**
- Run checker with no `bin/` folder — both should report missing.
- Run fetcher — both should download and appear in `bin/`.
- Run checker again — both should report installed and functional.

---

### 1.6 `src/engine/archive.py`

The most critical module. Read ARCHITECTURE.md Section 7.3 carefully.

```python
from pathlib import Path

def read_archive(path: Path) -> set[str]:
    """Returns set of video IDs marked done in the archive file."""
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    ids = set()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
            ids.add(parts[1])  # yt-dlp archive format: "youtube <video_id>"
    return ids

def remove_from_archive(path: Path, video_id: str) -> None:
    """Remove a single video_id line from the archive file."""
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    new_lines = [l for l in lines if video_id not in l]
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

def reconcile_archive(archive_path: Path, download_folder: Path, pattern: str) -> None:
    """
    For each video_id in the archive, check if the expected output file
    exists on disk. If the file is missing, remove the video_id from the
    archive so yt-dlp will re-download it.

    This covers the case where the user deleted a downloaded file and
    wants to re-download it via Update playlist — yt-dlp's own archive
    check would skip it; this function corrects the archive first.

    NOTE: Full reconciliation requires resolving the expected filename for
    each archived video, which needs a metadata fetch per video. For large
    playlists this is expensive. A pragmatic alternative that satisfies the
    requirement: scan the download_folder for all .mp3 files, build a set
    of filenames, then for any archived video whose expected filename is NOT
    in that set, remove it from the archive. The expected filename must be
    computed using the same pattern the download uses.

    For v1, implement the lightweight version: scan archive video IDs,
    run --dump-json for each to get title/artist, compute expected path,
    check existence. If the playlist is large (>50 tracks), do this check
    only for IDs added more than 24 hours ago (check file mtime on archive)
    to avoid excessive API calls on large playlists.
    """
    pass  # implement per the logic above
```

**Test this module in isolation with a real scenario before wiring to GUI.**
The required test:
1. Download a playlist of 3–5 tracks using `yt-dlp.exe` directly (not via
   the app yet).
2. Delete one of the MP3 files.
3. Run `reconcile_archive(...)`.
4. Confirm the deleted file's video ID has been removed from the archive.
5. Run `yt-dlp.exe --download-archive <archive> ...` on the playlist.
6. Confirm only the deleted track is re-downloaded; others are skipped.

Do not proceed to Phase 2 until this test passes.

### 1.7 `src/engine/worker.py`

QThread that manages a single queue item end-to-end.

```python
import re
import subprocess
import threading
from PySide6.QtCore import QThread, Signal
from pathlib import Path
from config import Config
from engine.queue_item import QueueItem, Mode, Status
from engine.archive import reconcile_archive
from utils.paths import YTDLP_EXE, FFMPEG_EXE
from constants import CONTENT_ERROR_STRINGS, NETWORK_ERROR_STRINGS

PROGRESS_RE = re.compile(
    r"\[download\]\s+([\d.]+)%\s+of\s+[\d.]+\S+\s+at\s+([\d.]+\S+/s)"
)

class DownloadWorker(QThread):
    progress_updated  = Signal(str, float, str)  # item_id, percent, speed
    status_changed    = Signal(str, str)          # item_id, status_name
    log_line          = Signal(str, str)          # item_id, line
    finished_item     = Signal(str)               # item_id
    error_occurred    = Signal(str, str, str)     # item_id, error_type, message

    def __init__(self, item: QueueItem, config: Config):
        super().__init__()
        self.item   = item
        self.config = config
        self._cancel = threading.Event()
        self._process: subprocess.Popen | None = None

    def request_cancel(self):
        self._cancel.set()
        if self._process:
            self._process.terminate()

    def run(self):
        try:
            self._run_download()
        except Exception as e:
            self.error_occurred.emit(self.item.id, "unexpected", str(e))

    def _run_download(self):
        item = self.item
        cfg  = self.config

        # Reconcile archive before download (Update playlist mode only)
        if item.mode == Mode.UPDATE_PLAYLIST and item.archive_path:
            reconcile_archive(
                item.archive_path,
                Path(cfg.download_folder),
                cfg.filename_pattern,
            )

        args = self._build_args()
        attempt = 0
        max_attempts_content = cfg.max_retries_video_error
        max_attempts_network = cfg.max_retries_network_error
        backoff_content = [2, 5, 10]
        backoff_network = [3, 6, 12, 24, 48]

        while not self._cancel.is_set():
            attempt += 1
            returncode, stdout_buf = self._run_process(args)

            if returncode == 0:
                self.status_changed.emit(item.id, Status.DONE)
                self.finished_item.emit(item.id)
                return

            error_type = self._classify_error(stdout_buf)

            if error_type == "content":
                if attempt <= max_attempts_content:
                    wait = backoff_content[min(attempt - 1, len(backoff_content) - 1)]
                    self.msleep(wait * 1000)
                    continue
                else:
                    self.error_occurred.emit(item.id, "content", self._extract_reason(stdout_buf))
                    self.status_changed.emit(item.id, Status.SKIPPED)
                    self.finished_item.emit(item.id)  # continue queue
                    return

            elif error_type == "network":
                if attempt <= max_attempts_network:
                    wait = backoff_network[min(attempt - 1, len(backoff_network) - 1)]
                    self.msleep(wait * 1000)
                    continue
                else:
                    self.error_occurred.emit(item.id, "network", self._extract_reason(stdout_buf))
                    self.status_changed.emit(item.id, Status.PAUSED_NETWORK)
                    # Do NOT call finished_item — queue stops here until user retries
                    return

            else:
                # Unexpected / unknown error
                self.error_occurred.emit(item.id, "unexpected", stdout_buf[-500:])
                self.status_changed.emit(item.id, Status.ERROR)
                self.finished_item.emit(item.id)  # continue queue
                return

    def _run_process(self, args: list[str]) -> tuple[int, str]:
        buf = []
        self._process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in self._process.stdout:
            line = line.rstrip()
            buf.append(line)
            self.log_line.emit(self.item.id, line)
            m = PROGRESS_RE.match(line)
            if m:
                self.progress_updated.emit(self.item.id, float(m.group(1)), m.group(2))
            if self._cancel.is_set():
                self._process.terminate()
                break
        self._process.wait()
        return self._process.returncode, "\n".join(buf)

    def _classify_error(self, output: str) -> str:
        for s in CONTENT_ERROR_STRINGS:
            if s.lower() in output.lower():
                return "content"
        for s in NETWORK_ERROR_STRINGS:
            if s.lower() in output.lower():
                return "network"
        return "unknown"

    def _extract_reason(self, output: str) -> str:
        # Return the most relevant error line for display
        for line in reversed(output.splitlines()):
            if "ERROR" in line or "error" in line.lower():
                return line.strip()
        return output.strip()[-200:]

    def _build_args(self) -> list[str]:
        item = self.item
        cfg  = self.config
        output_template = str(
            Path(cfg.download_folder) / f"{cfg.filename_pattern}.%(ext)s"
        )
        args = [
            str(YTDLP_EXE),
            "--no-playlist" if not item.is_playlist else "--yes-playlist",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", cfg.audio_quality,
            "--ffmpeg-location", str(FFMPEG_EXE.parent),
            "--output", output_template,
            "--newline",
            "--progress",
            "--no-warnings",
        ]
        if cfg.embed_metadata:
            args.append("--add-metadata")
        if cfg.embed_thumbnail:
            args += [
                "--embed-thumbnail",
                "--ppa",
                "EmbedThumbnail+ffmpeg_o:-c:v mjpeg -vf crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
            ]
        if item.mode == Mode.UPDATE_PLAYLIST and item.archive_path:
            args += ["--download-archive", str(item.archive_path)]
        args.append(item.url)
        return args
```

---

## Phase 2 — GUI Shell

Build the window structure before adding any logic.

### 2.1 `src/gui/main_window.py`

`QMainWindow` with a custom title bar and a `QTabWidget`.
Tabs: Downloader, Settings, About.
Apply Fusion style: `QApplication.setStyle(QStyleFactory.create("Fusion"))`.
Load and save window geometry via `config.py`.

### 2.2 `src/gui/setup_window.py`

`QDialog`, modal. Shows two `FetchWorker` items with progress bars.
Connects to `FetchWorker` signals.
Closes and allows main window to open only when `all_done` signal received
and both deps verify as functional.
If either fails: show inline error per item + "Retry setup" button.
"Close app" button calls `sys.exit(1)`.

### 2.3 Tab scaffolds

Create `downloader.py`, `settings.py`, `about.py` as `QWidget` subclasses
with placeholder layouts. Get the tab structure rendering before wiring any
real logic.

---

## Phase 3 — Downloader Tab (full)

Build the complete Downloader tab. Wire all interactions per DESIGN_GUIDE.md
Section 5.

Checklist:
- [ ] Mode buttons (New download / Update playlist), mutually exclusive
- [ ] URL input, Enter key triggers add, validation on add
- [ ] Inline validation error label (hidden when no error, shown on error)
- [ ] Save-to row with folder picker
- [ ] Empty state widget
- [ ] Queue list (`QScrollArea` containing a `QVBoxLayout` of `QueueRow` widgets)
- [ ] Each `QueueRow` wired to its item's status: icon, title, subtitle, mode
  tag, mini progress bar, remove/cancel button
- [ ] Error panel (collapsible, copy button)
- [ ] Dependency status line
- [ ] Start queue / Pause / Cancel all buttons with correct enabled state
- [ ] Two labelled progress bars at bottom (hidden when idle)

---

## Phase 4 — Download Engine Integration

Wire the `DownloadWorker` to the Downloader tab.

- Main thread creates a `DownloadWorker` for the first QUEUED item and
  starts it.
- Worker signals connect to:
  - `progress_updated` → update the queue row's mini pbar and the bottom
    item progress bar
  - `status_changed` → update the queue row icon and subtitle
  - `log_line` → append to the item's log buffer (used by error panel)
  - `finished_item` → if more QUEUED items exist, start the next one;
    otherwise mark the session done
  - `error_occurred` → append to error panel; update row state
- Window title reflects download progress: set via `setWindowTitle`.
- Pause: set a flag; after current item finishes, do not start the next.
- Cancel: call `worker.request_cancel()` on the active worker; mark all
  QUEUED items as CANCELLED.

---

## Phase 5 — Settings Tab (full)

Checklist:
- [ ] Download folder row with file picker
- [ ] Filename pattern dropdown (one option)
- [ ] Audio quality dropdown (one option)
- [ ] Post-processing groupbox with two checkboxes
- [ ] Dependencies groupbox with two side-by-side dep cards
- [ ] Each dep card: name, pill, version text, action button or pbar
- [ ] "Check for update" runs `checker.get_ytdlp_version()` + GitHub API
  call in a `QThread`; updates pill and version text on return
- [ ] "Update now" runs `yt-dlp.exe -U` in a `QThread`; monitors stdout
  for progress; re-reads version on completion
- [ ] ffmpeg "Check for update" / "Update now" re-downloads from gyan.dev
- [ ] Save settings button writes config; shows toast "Settings saved"
- [ ] Reset to defaults restores `Config()` defaults; does NOT save
  automatically (user must click Save)

---

## Phase 6 — About Tab

Static layout per DESIGN_GUIDE.md Section 7.
Wire GitHub and Repository buttons to open URLs via `QDesktopServices.openUrl`.
`TODO_GITHUB_URL` and `TODO_REPO_URL` from `constants.py`.

---

## Phase 7 — Polish

Work through DESIGN_GUIDE.md Section 9 (interactions) and Section 10
(tooltips) methodically.

Checklist:
- [ ] All icon-only buttons have `setToolTip`
- [ ] Enter in URL field triggers add
- [ ] Escape clears URL field if not empty
- [ ] Window title updates during download
- [ ] Window position/size saved on close and restored on launch
- [ ] Off-screen position detection and reset
- [ ] Toast notifications (queue add, settings save, copy to clipboard)
- [ ] Disabled states on all relevant buttons
- [ ] Queue row × button correct behaviour per status
- [ ] Partial `.part` file cleanup on cancel (scan download folder for
  `*.part` files matching the current item's expected base name and delete)
- [ ] `config.json` missing or corrupt: silently recreate with defaults
- [ ] Download folder missing: create it before download; show error in
  Settings if creation fails

---

## Phase 8 — Packaging

```
pyinstaller \
  --onefile \
  --windowed \
  --name YTMusicDownloader \
  --hidden-import PySide6.QtSvg \
  --hidden-import PySide6.QtXml \
  src/main.py
```

After build:
1. Copy the `dist/YTMusicDownloader.exe` to a fresh folder.
2. Run it on a machine with no Python installed.
3. Verify `bin/`, `data/`, `downloads/` are created next to the exe on
   first run.
4. Verify the setup window appears and downloads both deps.
5. Verify a single song downloads correctly.
6. Verify a playlist downloads correctly.
7. Run all edge case tests in Phase 9.

---

## Phase 9 — Edge Case Test Checklist

Run every item manually. Report pass / fail / partial for each.

**Dependency setup:**
- [ ] First run with empty `bin/`: setup window appears, both tools download
- [ ] Delete `bin/yt-dlp.exe` after normal use, relaunch: setup window
  appears, only yt-dlp is re-downloaded (ffmpeg already present)
- [ ] Disconnect internet during ffmpeg download: error shown, Retry works

**URL validation:**
- [ ] Non-YouTube URL: inline error, not added to queue
- [ ] Single video URL with Update playlist mode: inline error, not added
- [ ] Playlist URL with New download mode: added normally
- [ ] Empty URL field, press Enter: no error, no action
- [ ] Paste URL with trailing whitespace: stripped and accepted if valid

**Duplicate handling (CRITICAL — must pass):**
- [ ] Add a song, download it, add the same URL again: second attempt shows
  "Already downloaded — file exists, skipped"
- [ ] Download a playlist. Delete one MP3 manually. Run Update playlist on
  the same URL. Confirm: the deleted song is re-downloaded; all others
  are skipped. Paste the actual log output to confirm.
- [ ] Download a playlist. Delete one MP3 and edit the archive file to
  remove its entry manually. Run Update playlist. Confirm: the deleted
  song is re-downloaded.

**Error handling:**
- [ ] Add a known private/deleted video URL to a playlist: after 3 retries,
  it is skipped; error appears in error panel; rest of playlist continues
- [ ] Disconnect internet mid-download: after 5 retries, item shows
  "Paused — network issue"; queue stops; Retry button is functional;
  reconnect and retry works
- [ ] Queue with 3 items; cancel mid-download of item 2: item 2 shows
  CANCELLED; item 3 is also marked CANCELLED (Cancel all); no `.part`
  files remain in download folder

**Settings:**
- [ ] Change download folder: new downloads go to the new folder
- [ ] Toggle off embed thumbnail: downloaded file has no thumbnail
  (verify in a tag editor)
- [ ] Click Check for update when already up to date: pill shows "up to date"
- [ ] Click Update now when update available: yt-dlp updates, version
  refreshes, pill returns to "up to date"
- [ ] Update fails (no internet): inline error on dep card; existing binary
  still works

**Window behaviour:**
- [ ] Resize window: queue list and error panel grow/shrink correctly
- [ ] Move window, close, reopen: restores to previous position
- [ ] Move window entirely off-screen (via config.json edit), relaunch:
  recentres on primary monitor

---

## Phase 10 — Verify Prompt

After packaging, run the following checks and report results plainly
(pass / fail / partial):

1. Does the exe run standalone on a machine with no Python installed?
2. Does first run fetch both `bin/yt-dlp.exe` and `bin/ffmpeg.exe`
   automatically?
3. Delete one downloaded MP3. Run Update playlist on the same playlist URL.
   Does the deleted song re-download? Paste the yt-dlp output log.
4. Does a private/deleted video in a playlist retry 3 times then skip,
   with the rest of the playlist continuing?
5. Does a network failure retry 5 times then pause that item with a Retry
   button, without skipping it?
6. Does "Update now" in Settings actually replace `bin/yt-dlp.exe` and
   show the new version?
7. Is the output filename pattern exactly `%(title)s - %(artist)s`, with
   thumbnail embedded (square-cropped) and metadata embedded?
8. Is there one archive file per playlist at `data/archives/<playlist_id>.txt`?
9. What is still incomplete or placeholder? List it.

---

## Notes for the Agent

- If you find a genuine ambiguity not covered by ARCHITECTURE.md,
  DESIGN_GUIDE.md, or this file: stop and ask Biraj. Do not guess.
- The duplicate/archive reconciliation logic (Phase 1.6 and edge case test
  "Duplicate handling") is the single most important correctness requirement.
  If it is wrong, it silently corrupts the user's library. Get it right
  before moving on.
- `CREATE_NO_WINDOW` on every subprocess call is mandatory. A console
  flashing open on every download is a visible, embarrassing bug.
- Do not add any feature not listed in these documents without flagging it.
  "Nice to have" additions are for v1.1.
- Test packaging (Phase 8) early — after Phase 2 at the latest. PySide6
  packaging issues are much cheaper to fix before features are built on top.
