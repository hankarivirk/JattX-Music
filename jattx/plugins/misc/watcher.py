"""jattx/plugins/misc/watcher.py"""
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded
from pytgcalls.types.call_holder import CallHolderNotFound

from jattx import app, call, config, db, queue, userbot
from jattx import logger


def register_handlers():
    """Wire up pytgcalls v2.x callbacks."""
    for a in userbot.assistants:

        @a.pytgcalls.on_update()
        async def handle_update(client, update: Update):
            try:
                chat_id = update.chat_id
            except AttributeError:
                return

            update_type = type(update).__name__

            # Stream ended — play next
            if update_type in (
                "StreamAudioEnded",
                "StreamVideoEnded",
                "StreamDeleted",
                "MutedStream",
            ):
                logger.info(
                    f"Stream ended ({update_type}) in {chat_id}"
                )
                await call.play_next(chat_id)

            # VC closed or kicked
            elif update_type in (
                "ClosedVoiceChat",
                "KickedFromGroupCall",
                "LeftGroupCallParticipant",
            ):
                queue.clear(chat_id)
                await db.remove_call(chat_id)
                logger.info(
                    f"VC closed ({update_type}) in {chat_id}"
                )


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
