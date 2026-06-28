"""
JattX Music Bot — core initialisation
Auto-detects BOT_NAME & BOT_USERNAME from Telegram at startup.
"""

import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("jattx.log", maxBytes=10_485_760, backupCount=3),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
for noisy in ("httpx", "ntgcalls", "pymongo", "pyrogram", "pytgcalls", "httpcore"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)

logger = logging.getLogger("JattX")

__version__ = "1.0.0"

# ── Config ────────────────────────────────────────────────────────────────────
from config import config
config.check()

boot_time = time.time()
tasks: list = []

# ── Core singletons ───────────────────────────────────────────────────────────
from jattx.core.bot      import Bot
from jattx.core.dir      import ensure_dirs
from jattx.core.userbot  import Userbot
from jattx.core.mongo    import MongoDB
from jattx.core.youtube  import YouTube
from jattx.core.telegram import Telegram
thumb   = Thumbnail()

from jattx.core.calls import JattXCall
call    = JattXCall()

from jattx.helpers       import Queue, Thumbnail

ensure_dirs()

app     = Bot()
userbot = Userbot()
db      = MongoDB()
yt      = YouTube()
tg      = Telegram()
queue   = Queue()
thumb   = Thumbnail()
call    = JattXCall()


async def stop() -> None:
    logger.info("Shutting down JattX Music…")
    for t in tasks:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
    await app.exit()
    await userbot.exit()
    await db.close()
    await thumb.close()
    logger.info("Goodbye! ✨")
