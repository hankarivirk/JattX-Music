"""jattx/__main__.py"""
import asyncio
import sys

async def main():
    from jattx import app, userbot, logger
    from jattx.plugins.misc.watcher import register_handlers
    from pyrogram.errors import FloodWait

    logger.info("=" * 52)
    logger.info("  ⚡  JattX Music Bot  |  Starting up…")
    logger.info("=" * 52)

    # Start Bot
    while True:
        try:
            await app.start()
            break
        except FloodWait as e:
            wait = e.value
            logger.warning(
                f"⚠️ FloodWait: waiting {wait}s..."
            )
            await asyncio.sleep(wait + 5)
        except Exception as e:
            logger.error(f"Bot start failed: {e}")
            sys.exit(1)

    # Start Assistants
    await userbot.start()

    # Register handlers
    register_handlers()

    logger.info("✅ JattX Music Bot is LIVE!")

    # Keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import logging
        logging.getLogger("JattX").error(f"Fatal: {e}")
        sys.exit(1)
