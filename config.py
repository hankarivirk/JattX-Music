"""
╔══════════════════════════════════════╗
║       JattX Music Bot  v1.0.0        ║
║   The Fastest Telegram Music Bot     ║
╚══════════════════════════════════════╝

Auto-detects BOT_NAME and BOT_USERNAME at startup.
All fields below can be set via environment variables.
"""

from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Core Telegram credentials ──────────────────────────
    API_ID: int        = int(getenv("API_ID", 0))
    API_HASH: str      = getenv("API_HASH", "")
    BOT_TOKEN: str     = getenv("BOT_TOKEN", "")
    MONGO_URL: str     = getenv("MONGO_URL", "")

    # ── IDs ────────────────────────────────────────────────
    OWNER_ID: int      = int(getenv("OWNER_ID", 0))
    LOGGER_ID: int     = int(getenv("LOGGER_ID", 0))

    # ── Assistant userbots (up to 3 for load-balancing) ───
    SESSION1: str      = getenv("SESSION", "")
    SESSION2: str      = getenv("SESSION2", "")
    SESSION3: str      = getenv("SESSION3", "")

    # ── Auto-detected at startup (do NOT set manually) ────
    BOT_NAME: str      = "JattX Music"   # overwritten in __init__.py
    BOT_USERNAME: str  = "JattXMusicBot" # overwritten in __init__.py
    BOT_MENTION: str   = "@JattXMusicBot"
    BOT_ID: int        = 0

    # ── Limits ─────────────────────────────────────────────
    DURATION_LIMIT: int  = int(getenv("DURATION_LIMIT", 90)) * 60   # minutes → seconds
    QUEUE_LIMIT: int     = int(getenv("QUEUE_LIMIT", 30))
    PLAYLIST_LIMIT: int  = int(getenv("PLAYLIST_LIMIT", 25))

    # ── Support links (auto-filled from BOT_USERNAME if blank) ──
    SUPPORT_CHANNEL: str = getenv("SUPPORT_CHANNEL", "")
    SUPPORT_CHAT: str    = getenv("SUPPORT_CHAT", "")

    # ── Behaviour flags ────────────────────────────────────
    AUTO_LEAVE: bool   = getenv("AUTO_LEAVE",  "False").lower() == "true"
    AUTO_END: bool     = getenv("AUTO_END",    "False").lower() == "true"
    THUMB_GEN: bool    = getenv("THUMB_GEN",   "True").lower()  == "true"
    VIDEO_PLAY: bool   = getenv("VIDEO_PLAY",  "True").lower()  == "true"
    MAINTENANCE: bool  = False   # toggled at runtime by owner

    # ── Autoplay ───────────────────────────────────────────
    # When queue ends, auto-fetch related songs and keep playing
    AUTOPLAY: bool     = getenv("AUTOPLAY", "False").lower() == "true"
    AUTOPLAY_LIMIT: int = int(getenv("AUTOPLAY_LIMIT", 5))   # songs to add per refill

    # ── Localisation ───────────────────────────────────────
    LANG_CODE: str     = getenv("LANG_CODE", "en")

    # ── YouTube / yt-dlp ───────────────────────────────────
    COOKIES_URL: list  = [
        u for u in getenv("COOKIES_URL", "").split()
        if u and "batbin.me" in u
    ]
    YT_DLP_EXTRA_ARGS: str  = getenv("YT_DLP_EXTRA_ARGS", "")
    YT_PO_TOKEN: str        = getenv("YT_PO_TOKEN", "")
    YT_VISITOR_DATA: str    = getenv("YT_VISITOR_DATA", "")

    # ── Spotify (optional) ─────────────────────────────────
    SPOTIFY_CLIENT_ID: str     = getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = getenv("SPOTIFY_CLIENT_SECRET", "")

    # ── Appearance ─────────────────────────────────────────
    # ── Image URLs (always URLs — never local file paths) ──
    # These are shown as Telegram photo messages.
    # Replace with your own telegra.ph / imgur / catbox links.
    DEFAULT_THUMB: str = getenv(
        "DEFAULT_THUMB",
        "https://envs.sh/JattX-default.jpg"
    )
    PING_IMG: str = getenv(
        "PING_IMG",
        "https://envs.sh/JattX-ping.jpg"
    )
    START_IMG: str = getenv(
        "START_IMG",
        "https://envs.sh/JattX-start.jpg"
    )

    # ── Runtime autoplay state (per group, in-memory) ──────
    # {chat_id: True/False} — overrides global AUTOPLAY per group
    _autoplay_state: dict = {}

    @classmethod
    def is_autoplay(cls, chat_id: int) -> bool:
        return cls._autoplay_state.get(chat_id, cls.AUTOPLAY)

    @classmethod
    def set_autoplay(cls, chat_id: int, val: bool):
        cls._autoplay_state[chat_id] = val

    @classmethod
    def check(cls):
        required = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL",
                    "OWNER_ID", "LOGGER_ID", "SESSION1"]
        missing = [v for v in required if not getattr(cls, v)]
        if missing:
            raise SystemExit(
                f"❌ Missing required environment variables: {', '.join(missing)}\n"
                f"   Please set them in your .env file or deployment vars."
            )

    @classmethod
    def resolve_support_links(cls):
        """Fill support links from BOT_USERNAME if not explicitly set."""
        if not cls.SUPPORT_CHANNEL:
            cls.SUPPORT_CHANNEL = f"https://t.me/{cls.BOT_USERNAME}Channel"
        if not cls.SUPPORT_CHAT:
            cls.SUPPORT_CHAT = f"https://t.me/{cls.BOT_USERNAME}Support"


config = Config()
