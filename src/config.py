from dataclasses import dataclass, asdict, field
import json
from utils.paths import CONF_PATH, EXE_DIR

@dataclass
class Config:
    download_folder: str = ""        # set to str(EXE_DIR/"downloads") on init if empty
    filename_pattern: str = "%(title)s"
    audio_quality: str = "0"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    max_retries_video_error: int = 3
    max_retries_network_error: int = 5
    window_x: int = -1              # -1 means "centre on first launch"
    window_y: int = -1
    window_w: int = -1              # -1 means calculate 60% of screen size
    window_h: int = -1

    def __post_init__(self):
        if not self.download_folder:
            self.download_folder = str(EXE_DIR / "downloads")

def load_config() -> Config:
    try:
        if CONF_PATH.exists():
            data = json.loads(CONF_PATH.read_text(encoding="utf-8"))
            # Filter keys to match Config fields
            valid_data = {k: v for k, v in data.items() if k in Config.__dataclass_fields__}
            cfg = Config(**valid_data)
            return cfg
    except Exception:
        pass
    return Config()             # silently reset on any parse failure

def save_config(cfg: Config) -> None:
    try:
        CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONF_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    except Exception:
        pass
