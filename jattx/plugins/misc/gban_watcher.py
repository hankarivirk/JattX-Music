"""
jattx/plugins/misc/gban_watcher.py
Silently reject gbanned users from using the bot.
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, db
from config import config


@app.on_message(group=1)
async def gban_check(client: Client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    if uid == config.OWNER_ID:
        return
    if await db.is_gbanned(uid):
        # Silently ignore — don't tip off the user
        raise filters.StopPropagation()
