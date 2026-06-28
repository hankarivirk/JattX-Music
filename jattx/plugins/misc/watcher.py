"""jattx/plugins/misc/watcher.py"""
from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, call, config, db, queue, userbot
from jattx import logger


def register_handlers():
    """Wire up pytgcalls v2.x callbacks."""
    for a in userbot.assistants:

        @a.pytgcalls.on_update()
        async def handle_update(_, update):
            try:
                chat_id = update.chat_id
            except AttributeError:
                return

            update_type = type(update).__name__
            logger.info(
                f"PyTgCalls update: {update_type} "
                f"in {chat_id}"
            )

            if update_type in (
                "StreamAudioEnded",
                "StreamVideoEnded",
                "StreamDeleted",
            ):
                await call.play_next(chat_id)

            elif update_type in (
                "ClosedVoiceChat",
                "KickedFromGroupCall",
            ):
                queue.clear(chat_id)
                await db.remove_call(chat_id)


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
                f"Use /play <song> to start music 🎵\n"
                f"Type /help for commands.\n"
                f"🔗 Support: {config.SUPPORT_CHAT}"
            )
            logger.info(
                f"Added to group: "
                f"{message.chat.title} ({message.chat.id})"
            )
