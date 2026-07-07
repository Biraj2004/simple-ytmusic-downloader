import re
import subprocess
import threading
import time
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from config import Config
from engine.queue_item import QueueItem, Mode, Status
from engine.archive import reconcile_archive
from utils.paths import YTDLP_EXE, FFMPEG_EXE
from constants import CONTENT_ERROR_STRINGS, NETWORK_ERROR_STRINGS
import logging

logger = logging.getLogger("YTMusicDownloader")

PROGRESS_RE = re.compile(
    r"\[download\]\s+([\d.]+)%\s+of\s+~?[\d.]+\S+\s+at\s+(\S+)"
)

PLAYLIST_RE = re.compile(
    r"\[download\]\s+Downloading\s+item\s+(\d+)\s+of\s+(\d+)"
)

class DownloadWorker(QThread):
    progress_updated  = Signal(str, float, str)           # item_id, percent, speed
    playlist_item_changed = Signal(str, int, int)         # item_id, current_index, total_count
    status_changed    = Signal(str, object)               # item_id, Status enum
    log_line          = Signal(str, str)                  # item_id, line
    finished_item     = Signal(str)                       # item_id
    error_occurred    = Signal(str, str, str)             # item_id, error_type, message

    def __init__(self, item: QueueItem, config: Config):
        super().__init__()
        self.item   = item
        self.config = config
        self._cancel = threading.Event()
        self._process: subprocess.Popen | None = None
        self.track_status = {1: "success"}
        self.track_names = {1: item.title}
        self.current_track_index = 1

    def request_cancel(self):
        self._cancel.set()
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def run(self):
        try:
            self._run_download()
        except Exception as e:
            logger.error(f"Unexpected error in DownloadWorker: {e}", exc_info=True)
            self.error_occurred.emit(self.item.id, "unexpected", str(e))
            self.status_changed.emit(self.item.id, Status.ERROR)
            self.finished_item.emit(self.item.id)

    def _run_download(self):
        item = self.item
        cfg  = self.config

        # 0. Resolve Metadata
        self.status_changed.emit(item.id, Status.DOWNLOADING)
        self.log_line.emit(item.id, "Resolving metadata...")
        try:
            from engine.metadata import resolve_metadata
            meta = resolve_metadata(item.url)
            item.title = meta["title"]
            item.is_playlist = meta["is_playlist"]
            item.track_count = meta["track_count"]
            
            if item.mode == Mode.UPDATE_PLAYLIST and not item.archive_path:
                playlist_id = meta["playlist_id"] or "playlist"
                from utils.paths import ARCH_DIR
                item.archive_path = ARCH_DIR / f"{playlist_id}.txt"
                
            self.status_changed.emit(item.id, Status.DOWNLOADING)
        except Exception as e:
            logger.error(f"Error resolving metadata: {e}")
            self.error_occurred.emit(item.id, "metadata", f"Failed to resolve metadata: {str(e)}")
            self.status_changed.emit(item.id, Status.ERROR)
            self.finished_item.emit(item.id)
            return

        # 1. Pre-flight check: Single Video vs Playlist
        # Note: Resolve expected path for single videos. For playlists, we rely on archive reconciliation.
        if not item.is_playlist:
            try:
                output_template = str(Path(cfg.download_folder) / f"{cfg.filename_pattern}.%(ext)s")
                args = [
                    str(YTDLP_EXE),
                    "--get-filename",
                    "-x",
                    "--audio-format", "mp3",
                    "-o", output_template,
                    item.url
                ]
                r = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=15
                )
                if r.returncode == 0:
                    expected_file = Path(r.stdout.strip())
                    if expected_file.exists():
                        logger.info(f"File already exists on disk for single: {expected_file}. Skipping.")
                        item.tracks_downloaded = item.track_count or 1
                        item.tracks_error = 0
                        item.failed_tracks = []
                        self.status_changed.emit(item.id, Status.SKIPPED_DUPLICATE)
                        self.finished_item.emit(item.id)
                        return
            except Exception as e:
                logger.error(f"Error checking duplicate for {item.url}: {e}")

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
            self.status_changed.emit(item.id, Status.DOWNLOADING)
            returncode, stdout_buf = self._run_process(args)

            if self._cancel.is_set():
                self.status_changed.emit(item.id, Status.CANCELLED)
                self._cleanup_temp_files()
                self._reconcile_track_stats()
                self.finished_item.emit(item.id)
                return

            if returncode == 0:
                self.status_changed.emit(item.id, Status.DONE)
                self._reconcile_track_stats()
                self.finished_item.emit(item.id)
                return

            error_type = self._classify_error(stdout_buf)
            reason = self._extract_reason(stdout_buf)

            if error_type == "content":
                if attempt <= max_attempts_content:
                    wait = backoff_content[min(attempt - 1, len(backoff_content) - 1)]
                    logger.warning(f"Content error on attempt {attempt}. Retrying in {wait}s... Reason: {reason}")
                    self._sleep_cancelable(wait)
                    continue
                else:
                    logger.error(f"Content error on attempt {attempt}. Retries exhausted. Skipping. Reason: {reason}")
                    self.error_occurred.emit(item.id, "content", reason)
                    self.status_changed.emit(item.id, Status.SKIPPED)
                    self._reconcile_track_stats()
                    self.finished_item.emit(item.id)
                    return

            elif error_type == "network":
                if attempt <= max_attempts_network:
                    wait = backoff_network[min(attempt - 1, len(backoff_network) - 1)]
                    logger.warning(f"Network error on attempt {attempt}. Retrying in {wait}s... Reason: {reason}")
                    self._sleep_cancelable(wait)
                    continue
                else:
                    logger.error(f"Network error on attempt {attempt}. Retries exhausted. Pausing queue. Reason: {reason}")
                    self.error_occurred.emit(item.id, "network", reason)
                    self.status_changed.emit(item.id, Status.PAUSED_NETWORK)
                    self._reconcile_track_stats()
                    # Do NOT emit finished_item to pause the queue execution
                    return

            else:
                logger.error(f"Unexpected download error. Return code: {returncode}. Reason: {reason}")
                self.error_occurred.emit(item.id, "unexpected", reason)
                self.status_changed.emit(item.id, Status.ERROR)
                self._reconcile_track_stats()
                self.finished_item.emit(item.id)
                return

    def _sleep_cancelable(self, seconds: int):
        for _ in range(seconds):
            if self._cancel.is_set():
                break
            self.msleep(1000)

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
        
        dest_pattern = re.compile(r"\[download\]\s+Destination:\s+(?:.*[\\/])?([^\\/]+)\.[^.]+$")
        already_pattern = re.compile(r"\[download\]\s+(?:.*[\\/])?([^\\/]+)\.[^.]+\s+has\s+already\s+been\s+downloaded")
        
        for line in self._process.stdout:
            line = line.rstrip()
            buf.append(line)
            self.item.log_buffer.append(line)
            self.log_line.emit(self.item.id, line)
            
            m_prog = PROGRESS_RE.match(line)
            if m_prog:
                self.progress_updated.emit(self.item.id, float(m_prog.group(1)), m_prog.group(2))
                
            m_play = PLAYLIST_RE.match(line)
            if m_play:
                idx = int(m_play.group(1))
                tot = int(m_play.group(2))
                self.current_track_index = idx
                self.track_status[idx] = "success"
                if idx not in self.track_names:
                    self.track_names[idx] = f"Track {idx}"
                self.playlist_item_changed.emit(self.item.id, idx, tot)

            m_dest = dest_pattern.match(line)
            if m_dest:
                self.track_names[self.current_track_index] = m_dest.group(1)
            else:
                m_already = already_pattern.match(line)
                if m_already:
                    self.track_names[self.current_track_index] = m_already.group(1)

            if "error:" in line.lower() and "warning:" not in line.lower():
                self.track_status[self.current_track_index] = "error"
                
            if self._cancel.is_set():
                try:
                    self._process.terminate()
                except Exception:
                    pass
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
        for line in reversed(output.splitlines()):
            if "ERROR:" in line or "error:" in line.lower():
                return line.replace("ERROR:", "").strip()
        # Fallback to last few lines
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        if lines:
            return " | ".join(lines[-2:])
        return "Unknown yt-dlp error."

    def _cleanup_temp_files(self):
        """Scan download directory and clean up any .part files corresponding to this item."""
        try:
            dl_dir = Path(self.config.download_folder)
            if not dl_dir.exists():
                return
            # Delete any file ending with .part or .ytdl
            for p in dl_dir.glob("*.part"):
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            for p in dl_dir.glob("*.ytdl"):
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    def _build_args(self) -> list[str]:
        item = self.item
        cfg  = self.config
        if item.is_playlist and item.title:
            # Clean playlist title to make it a safe directory name on Windows
            safe_title = "".join(c for c in item.title if c not in '<>:"/\\|?*').strip()
            if not safe_title:
                safe_title = "Playlist"
            playlist_folder = Path(cfg.download_folder) / safe_title
            playlist_folder.mkdir(parents=True, exist_ok=True)
            output_template = str(playlist_folder / f"{cfg.filename_pattern}.%(ext)s")
        else:
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
            "--no-overwrites", # Skip downloading existing files
        ]
        if cfg.embed_metadata:
            args.append("--add-metadata")
        if cfg.embed_thumbnail:
            args += [
                "--embed-thumbnail",
                "--ppa",
                "EmbedThumbnail+ffmpeg_o:-c:v mjpeg -vf crop=ih:ih",
            ]
        if item.mode == Mode.UPDATE_PLAYLIST and item.archive_path:
            args += ["--download-archive", str(item.archive_path)]
        args.append(item.url)
        return args

    def _reconcile_track_stats(self):
        successes = 0
        failures = 0
        failed_list = []
        for idx in sorted(self.track_status.keys()):
            status = self.track_status[idx]
            name = self.track_names.get(idx, f"Track {idx}")
            if status == "success":
                successes += 1
            else:
                failures += 1
                failed_list.append(name)
        
        self.item.tracks_downloaded = successes
        self.item.tracks_error = failures
        self.item.failed_tracks = failed_list
