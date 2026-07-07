import sys
from pathlib import Path

def exe_dir() -> Path:
    # Works both in dev (script) and frozen (PyInstaller) modes
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

EXE_DIR   = exe_dir()
BIN_DIR   = EXE_DIR / "bin"
DATA_DIR  = EXE_DIR / "data"
LOGS_DIR  = DATA_DIR / "logs"
ARCH_DIR  = DATA_DIR / "archives"
CONF_PATH = DATA_DIR / "config.json"
YTDLP_EXE = BIN_DIR / "yt-dlp.exe"
FFMPEG_EXE = BIN_DIR / "ffmpeg.exe"
FFPROBE_EXE = BIN_DIR / "ffprobe.exe"

# Create directories on import if they do not exist
BIN_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ARCH_DIR.mkdir(parents=True, exist_ok=True)

def resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent.parent.parent
    return base_path / relative_path
