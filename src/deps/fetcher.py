import zipfile
import shutil
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from utils.paths import BIN_DIR, YTDLP_EXE, FFMPEG_EXE, FFPROBE_EXE
from constants import YTDLP_DOWNLOAD_URL, FFMPEG_DOWNLOAD_URL
from utils.net import get_request

class FetchWorker(QThread):
    progress = Signal(str, int)    # (item_name, percent)
    item_done = Signal(str)        # item_name
    item_failed = Signal(str, str) # (item_name, error_message)
    all_done = Signal()

    def __init__(self, fetch_ytdlp: bool = True, fetch_ffmpeg: bool = True, parent=None):
        super().__init__(parent)
        self.fetch_ytdlp_flag = fetch_ytdlp
        self.fetch_ffmpeg_flag = fetch_ffmpeg
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        if self.fetch_ytdlp_flag:
            self._fetch_ytdlp()
        else:
            self.item_done.emit("yt-dlp.exe")

        if self._cancel_requested:
            return

        if self.fetch_ffmpeg_flag:
            self._fetch_ffmpeg()
        else:
            self.item_done.emit("ffmpeg.exe")

        self.all_done.emit()

    def _fetch_ytdlp(self):
        name = "yt-dlp.exe"
        try:
            tmp = BIN_DIR / "yt-dlp.exe.tmp"
            self._download(YTDLP_DOWNLOAD_URL, tmp, name)
            if self._cancel_requested:
                tmp.unlink(missing_ok=True)
                return
            # Unlink YTDLP_EXE first to avoid FileExistsError on Windows rename
            YTDLP_EXE.unlink(missing_ok=True)
            tmp.rename(YTDLP_EXE)
            self.item_done.emit(name)
        except Exception as e:
            self.item_failed.emit(name, str(e))

    def _fetch_ffmpeg(self):
        name = "ffmpeg.exe"
        try:
            tmp_zip = BIN_DIR / "ffmpeg.zip.tmp"
            self._download(FFMPEG_DOWNLOAD_URL, tmp_zip, name)
            if self._cancel_requested:
                tmp_zip.unlink(missing_ok=True)
                return
            self._extract_ffmpeg(tmp_zip)
            tmp_zip.unlink(missing_ok=True)
            self.item_done.emit(name)
        except Exception as e:
            self.item_failed.emit(name, str(e))

    def _download(self, url: str, dest: Path, label: str):
        r = get_request(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if self._cancel_requested:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    self.progress.emit(label, int(done * 100 / total))
                else:
                    self.progress.emit(label, 0) # indeterminate if content-length is missing

    def _extract_ffmpeg(self, zip_path: Path):
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if self._cancel_requested:
                    break
                fname = Path(member).name
                if fname in ("ffmpeg.exe", "ffprobe.exe"):
                    target = BIN_DIR / fname
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
