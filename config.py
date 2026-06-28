"""
╔══════════════════════════════════════╗
║       JattX Music Bot  v1.0.0        ║
║   The Fastest Telegram Music Bot     ║
╚══════════════════════════════════════╝
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

    # ── Assistant userbots (up to 3) ───────────────────────
    SESSION1: str      = getenv("SESSION", "")
    SESSION2: str      = getenv("SESSION2", "")
    SESSION3: str      = getenv("SESSION3", "")

    # ── Auto-detected at startup ───────────────────────────
    BOT_NAME: str      = "JattX Music"
    BOT_USERNAME: str  = "JattXMusicBot"
    BOT_MENTION: str   = "@JattXMusicBot"
    BOT_ID: int        = 0

    # ── Limits ─────────────────────────────────────────────
    DURATION_LIMIT: int  = int(getenv("DURATION_LIMIT", 90)) * 60
    QUEUE_LIMIT: int     = int(getenv("QUEUE_LIMIT", 30))
    PLAYLIST_LIMIT: int  = int(getenv("PLAYLIST_LIMIT", 25))

    # ── Support links ──────────────────────────────────────
    SUPPORT_CHANNEL: str = getenv("SUPPORT_CHANNEL", "")
    SUPPORT_CHAT: str    = getenv("SUPPORT_CHAT", "")

    # ── Behaviour flags ────────────────────────────────────
    AUTO_LEAVE: bool   = getenv("AUTO_LEAVE",  "False").lower() == "true"
    AUTO_END: bool     = getenv("AUTO_END",    "False").lower() == "true"
    THUMB_GEN: bool    = getenv("THUMB_GEN",   "True").lower()  == "true"
    VIDEO_PLAY: bool   = getenv("VIDEO_PLAY",  "True").lower()  == "true"
    MAINTENANCE: bool  = False

    # ── Autoplay ───────────────────────────────────────────
    AUTOPLAY: bool      = getenv("AUTOPLAY", "False").lower() == "true"
    AUTOPLAY_LIMIT: int = int(getenv("AUTOPLAY_LIMIT", 5))

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

    # ── Spotify ────────────────────────────────────────────
    SPOTIFY_CLIENT_ID: str     = getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = getenv("SPOTIFY_CLIENT_SECRET", "")

    # ── Appearance ─────────────────────────────────────────
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

    # ── Runtime autoplay state ─────────────────────────────
    _autoplay_state: dict = {}

    @classmethod
    def is_autoplay(cls, chat_id: int) -> bool:
        return cls._autoplay_state.get(chat_id, cls.AUTOPLAY)

    @classmethod
    def set_autoplay(cls, chat_id: int, val: bool):
        cls._autoplay_state[chat_id] = val

    @classmethod
    def check(cls):
        """Validate required environment variables."""
        required = {
            "API_ID": cls.API_ID,
            "API_HASH": cls.API_HASH,
            "BOT_TOKEN": cls.BOT_TOKEN,
            "MONGO_URL": cls.MONGO_URL,
            "OWNER_ID": cls.OWNER_ID,
            "LOGGER_ID": cls.LOGGER_ID,
            "SESSION": cls.SESSION1,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise SystemExit(
                f"❌ Missing required environment variables: "
                f"{', '.join(missing)}\n"
                f"   Please set them in Railway Variables!"
            )
        print("✅ All required config variables verified!")

    @classmethod
    def resolve_support_links(cls):
        if not cls.SUPPORT_CHANNEL:
            cls.SUPPORT_CHANNEL = (
                f"https://t.me/{cls.BOT_USERNAME}Channel"
            )
        if not cls.SUPPORT_CHAT:
            cls.SUPPORT_CHAT = (
                f"https://t.me/{cls.BOT_USERNAME}Support"
            )


config = Config()
