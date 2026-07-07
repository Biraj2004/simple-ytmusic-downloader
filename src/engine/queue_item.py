from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid

class Mode(Enum):
    NEW_DOWNLOAD = "New"
    UPDATE_PLAYLIST = "Update"

class Status(Enum):
    QUEUED = "Queued"
    DOWNLOADING = "Downloading"
    DONE = "Done"
    SKIPPED = "Skipped"
    SKIPPED_DUPLICATE = "Duplicate"
    PAUSED_NETWORK = "Paused (Network)"
    ERROR = "Error"
    CANCELLED = "Cancelled"

@dataclass
class QueueItem:
    url: str
    mode: Mode
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: Status = Status.QUEUED
    title: str = ""
    subtitle: str = "Pending metadata resolution..."
    is_playlist: bool = False
    archive_path: Path | None = None
    log_buffer: list[str] = field(default_factory=list)
    error_message: str = ""
    progress_pct: float = 0.0
    speed_str: str = ""
    track_count: int = 0
    skipped_count: int = 0
    tracks_downloaded: int = 0
    tracks_error: int = 0
    failed_tracks: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title:
            self.title = self.url
