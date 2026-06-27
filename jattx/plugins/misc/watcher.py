"""jattx/plugins/misc/watcher.py — Stream end & group events."""
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pytgcalls import filters as ptg_filters
from pytgcalls.types import GroupCallParticipant

from jattx import app, call, config, db, queue, userbot
from jattx import logger


# ── Stream ended ──────────────────────────────────────────────────────────────
for assistant in []:  # populated in __main__.py after userbot starts
    pass

def register_handlers():
    """Called after assistants are ready to wire up pytgcalls callbacks."""
    for a in userbot.assistants:

        @a.pytgcalls.on_stream_end()
        async def on_end(_, update):
            chat_id = update.chat_id
            logger.info(f"Stream ended in {chat_id}")
            await call.play_next(chat_id)

        @a.pytgcalls.on_closed_voice_chat()
        async def on_closed(_, update):
            chat_id = update.chat_id
            queue.clear(chat_id)
            await db.remove_call(chat_id)
            logger.info(f"VC closed in {chat_id}")

        @a.pytgcalls.on_kicked()
        async def on_kicked(_, update):
            chat_id = update.chat_id
            queue.clear(chat_id)
            await db.remove_call(chat_id)


# ── Bot added to group ────────────────────────────────────────────────────────
@app.on_message(filters.new_chat_members)
async def new_member(client: Client, message: Message):
    me = await client.get_me()
    for member in message.new_chat_members:
        if member.id == me.id:
            if await db.is_blacklisted(message.chat.id):
                await message.reply_text("❌ This group is blacklisted. Leaving.")
                await client.leave_chat(message.chat.id)
                return
            await db.set_group(message.chat.id, title=message.chat.title or "")
            await message.reply_text(
                f"👋 Hey! I'm **{config.BOT_NAME}** (`@{config.BOT_USERNAME}`).\n\n"
                f"Use `/play <song>` in a voice chat to start the music 🎵\n"
                f"Type `/help` for all commands.\n\n"
                f"🔗 Support: {config.SUPPORT_CHAT}"
            )
            logger.info(f"Added to group: {message.chat.title} ({message.chat.id})")


# ── Auto-leave empty VC ───────────────────────────────────────────────────────
# Handled by pytgcalls on_closed_voice_chat above
