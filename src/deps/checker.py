import subprocess
from utils.paths import YTDLP_EXE, FFMPEG_EXE

def get_ytdlp_version() -> str | None:
    """Returns version string or None if not present / broken."""
    if not YTDLP_EXE.exists():
        return None
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
    """Returns version string or None if not present / broken."""
    if not FFMPEG_EXE.exists():
        return None
    try:
        r = subprocess.run(
            [str(FFMPEG_EXE), "-version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            if lines:
                return lines[0].strip()  # first line has version e.g. ffmpeg version 7.1.1
        return None
    except Exception:
        return None

def all_deps_present() -> bool:
    """Check if the physical files exist."""
    return YTDLP_EXE.exists() and FFMPEG_EXE.exists()

def deps_functional() -> tuple[bool, bool]:
    """Returns (ytdlp_ok, ffmpeg_ok)."""
    return (get_ytdlp_version() is not None, get_ffmpeg_version() is not None)
