"""jattx/helpers/_dataclass.py"""
from dataclasses import dataclass, field


@dataclass
class Track:
    id: str
    title: str           = "Unknown"
    channel_name: str    = ""
    duration: str        = "0:00"
    duration_sec: int    = 0
    thumbnail: str       = ""
    url: str             = ""
    view_count: str      = ""
    message_id: int      = 0
    video: bool          = False
    user: str            = ""
    file_path: str       = ""
    live: bool           = False


@dataclass
class Media:
    file_path: str
    title: str           = "Telegram Audio"
    duration: str        = "∞"
    duration_sec: int    = 0
    video: bool          = False
    user: str            = ""
    thumbnail: str       = ""
