DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

DEFAULT_CONFIG_PATHS = (
    "/media/VintagePiTV/config.toml",
    "/boot/firmware/vintage-pi-tv-config.toml",
    "./config.toml",
)

DEFAULT_RATINGS = [
    {"rating": "G", "description": "General"},
    {"rating": "PG", "description": "Parental Guidance"},
    {"rating": "R", "description": "Restricted"},
    {"rating": "X", "description": "Adult"},
]

DEFAULT_MPV_OPTIONS = {
    "ao": "pipewire",
    "fullscreen": True,
    "gpu-context": "drm",
    "hwdec": "auto-safe",
    "profile": "sw-fast",
    "vo": "gpu",
}

DEFAULT_AUDIO_FILE_EXTENSIONS = [
    "mp3",
    "wav",
    "aac",
    "flac",
    "ogg",
    "wma",
    "aiff",
    "m4a",
    "amr",
    "ac3",
    "mp2",
    "au",
    "ape",
    "opus",
    "dsf",
    "dff",
    "m4a",
    "mid",
    "ra",
    "wv",
    "mpc",
    "mpga",
    "spx",
    "mod",
    "awb",
    "mka",
]

DEFAULT_VIDEO_FILE_EXTENSIONS = [
    "mp4",
    "avi",
    "mkv",
    "mov",
    "wmv",
    "flv",
    "3gp",
    "mpeg",
    "webm",
    "ogg",
    "asf",
    "vob",
    "divx",
    "xvid",
    "h264",
    "h265",
    "vp9",
    "avchd",
    "swf",
    "theora",
    "realvideo",
    "mxf",
    "cineform",
    "heif",
    "prores",
]
