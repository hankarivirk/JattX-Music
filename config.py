from os import getenv
from dotenv import load_dotenv

load_dotenv()


class config:
    # Bot Configuration
    API_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH", None)
    BOT_TOKEN = getenv("BOT_TOKEN", None)

    # Owner & Logger
    OWNER_ID = int(getenv("OWNER_ID", 0))
    LOGGER_ID = int(getenv("LOGGER_ID", 0))

    # MongoDB
    MONGO_DB_URI = getenv("MONGO_DB_URI", None)

    # String Sessions
    STRING1 = getenv("STRING_SESSION", None)
    STRING2 = getenv("STRING_SESSION2", None)
    STRING3 = getenv("STRING_SESSION3", None)
    STRING4 = getenv("STRING_SESSION4", None)
    STRING5 = getenv("STRING_SESSION5", None)

    # Duration Limits
    DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 60))

    # Upstream Repo
    UPSTREAM_REPO = getenv(
        "UPSTREAM_REPO",
        "https://github.com/hankarivirk/JattX-Music"
    )
    UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "master")

    # Support & Channels
    SUPPORT_CHANNEL = getenv(
        "SUPPORT_CHANNEL",
        "https://t.me/JattXMusic"
    )
    SUPPORT_CHAT = getenv(
        "SUPPORT_CHAT",
        "https://t.me/JattXSupport"
    )

    # Image URLs
    START_IMAGE_URL = getenv(
        "START_IMAGE_URL",
        "https://te.legra.ph/file/your-image.jpg"
    )

    # Auto-Leaving Assistant
    AUTO_LEAVING_ASSISTANT = bool(
        getenv("AUTO_LEAVING_ASSISTANT", True)
    )

    # Spotify Optional
    SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", None)
    SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", None)

    # Heroku
    HEROKU_APP_NAME = getenv("HEROKU_APP_NAME", None)
    HEROKU_API_KEY = getenv("HEROKU_API_KEY", None)

    @classmethod
    def check(cls):
        required = {
            "API_ID": cls.API_ID,
            "API_HASH": cls.API_HASH,
            "BOT_TOKEN": cls.BOT_TOKEN,
            "MONGO_DB_URI": cls.MONGO_DB_URI,
            "OWNER_ID": cls.OWNER_ID,
            "STRING_SESSION": cls.STRING1,
        }
        missing = []
        for key, value in required.items():
            if not value:
                missing.append(key)
        if missing:
            print(f"❌ Missing Variables: {', '.join(missing)}")
            print("Please add them in Railway Variables!")
            exit(1)
        print("✅ All required variables are set!")
