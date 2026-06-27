"""
jattx/plugins/misc/cleanmode.py
If clean_mode is ON for a group, auto-deletes /play commands after 30s.
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, db

_PLAY_CMDS = ["play", "vplay", "yplay", "splay", "tplay", "playlist",
              "vplaylist", "live", "mix", "skip", "stop", "pause", "resume"]


@app.on_message(filters.command(_PLAY_CMDS) & filters.group, group=99)
async def clean_mode_watcher(client: Client, message: Message):
    doc = await db.get_group(message.chat.id)
    if not doc.get("clean_mode"):
        return
    await asyncio.sleep(30)
    try:
        await message.delete()
    except Exception:
        pass
