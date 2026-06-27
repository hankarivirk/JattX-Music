"""
jattx/plugins/owner/activevc.py
/activevc — list all active voice chats
/leaveall — leave all voice chats (emergency)
/leavevc  — leave specific VC
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, call, db, queue, userbot
from jattx.helpers._admins import sudo_only


@app.on_message(filters.command("activevc"))
@sudo_only
async def activevc_cmd(client: Client, message: Message):
    ids = await db.get_all_active()
    if not ids:
        return await message.reply_text("😴 No active voice chats right now.")
    lines = [f"🎙 **Active Voice Chats ({len(ids)})**\n"]
    for cid in ids[:25]:
        try:
            chat = await client.get_chat(cid)
            cur  = queue.current(cid)
            song = cur.title if cur else "—"
            lines.append(f"• **{chat.title}** — {song}")
        except Exception:
            lines.append(f"• `{cid}`")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command("leaveall"))
async def leaveall_cmd(client: Client, message: Message):
    from config import config
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("❌ Owner only.")
    ids = await db.get_all_active()
    if not ids:
        return await message.reply_text("😴 No active voice chats.")
    wait = await message.reply_text(f"🚪 Leaving {len(ids)} voice chats…")
    left = 0
    for cid in ids:
        try:
            await call.stop(cid)
            left += 1
        except Exception:
            pass
    await wait.edit_text(f"✅ Left **{left}** voice chat(s).")


@app.on_message(filters.command("leavevc") & filters.group)
async def leavevc_cmd(client: Client, message: Message):
    from jattx.helpers._admins import is_auth
    if not await is_auth(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admins only.")
    await call.stop(message.chat.id)
    await message.reply_text("👋 Left the voice chat.")
