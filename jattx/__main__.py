"""
JattX Music Bot — Main entry point
Run: python -m jattx
"""

import asyncio
import sys
import time

from jattx import app, boot_time, config, db, logger, stop, userbot, yt


async def main():
    logger.info("=" * 52)
    logger.info("  ⚡  JattX Music Bot  |  Starting up…")
    logger.info("=" * 52)

    # 1. Start Pyrogram bot (auto-detects name + username)
    await app.start()

    # 2. Start assistants
    await userbot.start()

    # 3. Register pytgcalls stream-end + VC-closed hooks
    from jattx.plugins.misc.watcher import register_handlers
    register_handlers()

    # 4. Download cookies from batbin.me if configured
    if config.COOKIES_URL:
        try:
            await yt.save_cookies(config.COOKIES_URL)
            logger.info(f"  Cookies loaded from {len(config.COOKIES_URL)} URL(s).")
        except Exception as e:
            logger.warning(f"  Cookie download failed: {e}")

    # 5. Send deploy message to logger channel
    uptime_start = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    deploy_msg = (
        f"✅ **{config.BOT_NAME}** is now **LIVE!**\n\n"
        f"🤖 Username  : @{config.BOT_USERNAME}\n"
        f"🆔 Bot ID    : `{config.BOT_ID}`\n"
        f"👑 Owner ID  : `{config.OWNER_ID}`\n"
        f"🎙 Assistants: {len(userbot.assistants)}\n"
        f"🕒 Started   : {uptime_start}\n\n"
        f"🔗 **Add to Group:**\n"
        f"`https://t.me/{config.BOT_USERNAME}?startgroup=true"
        f"&admin=manage_voice_chats+invite_users+change_info`\n\n"
        f"📢 Channel   : {config.SUPPORT_CHANNEL}\n"
        f"💬 Support   : {config.SUPPORT_CHAT}"
    )
    try:
        await app.send_message(config.LOGGER_ID, deploy_msg, disable_web_page_preview=True)
    except Exception as e:
        logger.warning(f"  Logger message failed: {e}")

    logger.info(
        f"\n  ✅  {config.BOT_NAME}\n"
        f"  🤖  @{config.BOT_USERNAME}  (ID: {config.BOT_ID})\n"
        f"  🎙  {len(userbot.assistants)} assistant(s) ready\n"
    )
    logger.info("=" * 52)

    # Block forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(stop())
        logger.info("Stopped. Goodbye!")
        sys.exit(0)
