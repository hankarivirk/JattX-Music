"""
jattx/core/bot.py
Pyrogram Bot client with AUTO NAME + USERNAME detection.
"""

from pyrogram import Client
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
        await super().start()
        me = await self.get_me()

        # ── Auto-detect and inject into config ────────────────
        config.BOT_ID       = me.id
        config.BOT_NAME     = me.first_name or "JattX Music"
        config.BOT_USERNAME = me.username or "JattXMusicBot"
        config.BOT_MENTION  = f"@{config.BOT_USERNAME}"

        # ── Resolve support links now that we know the username ─
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
