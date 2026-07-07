from pathlib import Path
import subprocess
import time
import logging
from utils.paths import YTDLP_EXE

logger = logging.getLogger("YTMusicDownloader")

def read_archive(path: Path) -> set[str]:
    """Returns set of video IDs marked done in the archive file."""
    if not path.exists():
        return set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        ids = set()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2:
                ids.add(parts[1])  # yt-dlp archive format: "youtube <video_id>"
        return ids
    except Exception as e:
        logger.error(f"Error reading archive {path}: {e}")
        return set()

def remove_from_archive(path: Path, video_id: str) -> None:
    """Remove a single video_id line from the archive file."""
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = [l for l in lines if video_id not in l]
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as e:
        logger.error(f"Error removing {video_id} from archive {path}: {e}")

def reconcile_archive(archive_path: Path, download_folder: Path, pattern: str) -> None:
    """
    For each video_id in the archive, check if the expected output file
    exists on disk. If the file is missing, remove the video_id from the
    archive so yt-dlp will re-download it.
    """
    if not archive_path.exists():
        return

    video_ids = read_archive(archive_path)
    if not video_ids:
        return

    # For large playlists, skip reconciliation if archive was modified within the last 24 hours
    if len(video_ids) > 50:
        try:
            mtime = archive_path.stat().st_mtime
            age_hours = (time.time() - mtime) / 3600
            if age_hours < 24:
                logger.info(f"Archive is only {age_hours:.1f} hours old and contains {len(video_ids)} entries. Skipping reconciliation.")
                return
        except Exception as e:
            logger.error(f"Error checking archive age: {e}")

    logger.info(f"Reconciling archive {archive_path} with {len(video_ids)} videos...")

    missing_ids = []
    for vid in video_ids:
        try:
            url = f"https://www.youtube.com/watch?v={vid}"
            output_template = str(download_folder / f"{pattern}.%(ext)s")
            args = [
                str(YTDLP_EXE),
                "--get-filename",
                "-x",
                "--audio-format", "mp3",
                "-o", output_template,
                url
            ]
            r = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            if r.returncode == 0:
                expected_file = Path(r.stdout.strip())
                if not expected_file.exists():
                    logger.info(f"File missing for {vid}: {expected_file}. Removing from archive.")
                    missing_ids.append(vid)
            else:
                logger.warning(f"Failed to get filename for {vid}: {r.stderr.strip()}")
        except Exception as e:
            logger.error(f"Error checking status for video {vid}: {e}")

    if missing_ids:
        try:
            lines = archive_path.read_text(encoding="utf-8").splitlines()
            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] in missing_ids:
                    continue
                new_lines.append(line)
            archive_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            logger.info(f"Removed {len(missing_ids)} missing tracks from archive.")
        except Exception as e:
            logger.error(f"Error re-writing archive {archive_path}: {e}")
