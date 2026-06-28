"""jattx/plugins/misc/watcher.py"""
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls.types import Update
from pytgcalls import filters as ptg_filters

from jattx import app, call, config, db, queue, userbot
from jattx import logger


def register_handlers():
    """Wire up pytgcalls callbacks after assistants start."""
    for a in userbot.assistants:

        @a.pytgcalls.on_stream_end()
        async def on_end(client, update: Update):
            try:
                chat_id = update.chat_id
                logger.info(f"Stream ended in {chat_id}")
                await call.play_next(chat_id)
            except Exception as e:
                logger.error(f"on_end error: {e}")

        @a.pytgcalls.on_closed_voice_chat()
        async def on_closed(client, update: Update):
            try:
                chat_id = update.chat_id
                queue.clear(chat_id)
                await db.remove_call(chat_id)
                logger.info(f"VC closed in {chat_id}")
            except Exception as e:
                logger.error(f"on_closed error: {e}")

        @a.pytgcalls.on_kicked()
        async def on_kicked(client, update: Update):
            try:
                chat_id = update.chat_id
                queue.clear(chat_id)
                await db.remove_call(chat_id)
            except Exception as e:
                logger.error(f"on_kicked error: {e}")


# ── Bot added to group ─────────────────────────────────────
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
