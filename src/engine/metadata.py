import subprocess
import json
from utils.paths import YTDLP_EXE

def resolve_metadata(url: str) -> dict:
    """
    Runs yt-dlp.exe --dump-json --flat-playlist --skip-download <url>
    and parses the output. Returns a dictionary with resolved metadata:
    {
        "title": str,
        "is_playlist": bool,
        "playlist_id": str | None,
        "playlist_title": str | None,
        "track_count": int,
        "artist": str | None
    }
    """
    if not YTDLP_EXE.exists():
        raise FileNotFoundError("yt-dlp.exe dependency is missing.")

    args = [
        str(YTDLP_EXE),
        "--dump-json",
        "--flat-playlist",
        "--skip-download",
        "--no-warnings",
        url
    ]

    r = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=30
    )

    if r.returncode != 0:
        error_msg = r.stderr.strip() or r.stdout.strip() or "Unknown error resolving metadata."
        raise Exception(error_msg)

    # Parse stdout.
    # Note: flat-playlist dump-json prints one line of JSON for the main playlist, 
    # or one line for the video.
    stdout_lines = [line.strip() for line in r.stdout.splitlines() if line.strip()]
    if not stdout_lines:
        raise Exception("No metadata returned by yt-dlp.")

    # Try parsing the first line as JSON
    data = json.loads(stdout_lines[0])
    
    is_playlist = data.get("_type") == "playlist" or "entries" in data or "playlist" in url.lower()
    
    title = data.get("title", "Unknown Title")
    playlist_id = data.get("id") if is_playlist else None
    playlist_title = title if is_playlist else None
    
    # If it is a playlist, the track count is the number of elements in entries, or playlist_count
    track_count = 0
    if is_playlist:
        entries = data.get("entries", [])
        track_count = len(entries) if entries else data.get("playlist_count", 0)
        # If there are multiple lines outputted by dump-json, count them
        if not track_count and len(stdout_lines) > 1:
            track_count = len(stdout_lines)
    else:
        track_count = 1

    artist = data.get("uploader") or data.get("artist") or data.get("creator")

    return {
        "title": title,
        "is_playlist": is_playlist,
        "playlist_id": playlist_id,
        "playlist_title": playlist_title,
        "track_count": track_count,
        "artist": artist
    }
