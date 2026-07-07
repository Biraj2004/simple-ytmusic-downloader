# Dependency download URLs
YTDLP_DOWNLOAD_URL  = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_RELEASES_API  = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Developer links
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
