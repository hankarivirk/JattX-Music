"""jattx/core/bot.py"""
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from config import config


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="JattXMusicBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            sleep_threshold=60,
            max_concurrent_transmissions=10,
            plugins={"root": "jattx/plugins"},
        )

    async def start(self):
        while True:
            try:
                await super().start()
                break
            except FloodWait as e:
                wait = e.value
                from jattx import logger
                logger.warning(
                    f"⚠️ FloodWait: Waiting {wait}s..."
                )
                await asyncio.sleep(wait + 5)

        me = await self.get_me()

        config.BOT_ID       = me.id
        config.BOT_NAME     = me.first_name or "JattX Music"
        config.BOT_USERNAME = me.username or "JattXMusicBot"
        config.BOT_MENTION  = f"@{config.BOT_USERNAME}"

        config.resolve_support_links()

        from jattx import logger
        logger.info(
            f"\n╔══════════════════════════════════╗\n"
            f"║  ✅  {config.BOT_NAME:<28}║\n"
            f"║  🤖  @{config.BOT_USERNAME:<27}║\n"
            f"║  🆔  {config.BOT_ID:<28}║\n"
            f"╚══════════════════════════════════╝"
        )

    async def exit(self):
        try:
            await self.stop()
        except Exception:
            pass
