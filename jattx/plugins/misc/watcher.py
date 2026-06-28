"""jattx/plugins/misc/watcher.py — Stream end & group events."""
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls.types import Update

from jattx import app, call, config, db, queue, userbot
from jattx import logger


def register_handlers():
    """Called after assistants are ready to wire up pytgcalls callbacks."""
    for a in userbot.assistants:

        # ── Fixed: on_stream_end → on_update ──────────────────────────
        @a.pytgcalls.on_update()
        async def on_update(_, update: Update):
            try:
                chat_id = update.chat_id
            except AttributeError:
                return

            # Stream ended
            if hasattr(update, 'status'):
                status = str(update.status).lower()

                if 'ended' in status or 'finished' in status:
                    logger.info(f"Stream ended in {chat_id}")
                    await call.play_next(chat_id)

                elif 'closed' in status or 'kicked' in status:
                    queue.clear(chat_id)
                    await db.remove_call(chat_id)
                    logger.info(f"VC closed/kicked in {chat_id}")


# ── Bot added to group ─────────────────────────────────────────────────────
@app.on_message(filters.new_chat_members)
async def new_member(client: Client, message: Message):
    me = await client.get_me()
    for member in message.new_chat_members:
        if member.id == me.id:
            if await db.is_blacklisted(message.chat.id):
                await message.reply_text(
                    "❌ This group is blacklisted. Leaving."
                )
                await client.leave_chat(message.chat.id)
                return
            await db.set_group(
                message.chat.id,
                title=message.chat.title or ""
            )
            await message.reply_text(
                f"👋 Hey! I'm {config.BOT_NAME} "
                f"(@{config.BOT_USERNAME}).\n"
                f"Use /play <song> in a voice chat "
                f"to start the music 🎵\n"
                f"Type /help for all commands.\n"
                f"🔗 Support: {config.SUPPORT_CHAT}"
            )
            logger.info(
                f"Added to group: "
                f"{message.chat.title} ({message.chat.id})"
            )
