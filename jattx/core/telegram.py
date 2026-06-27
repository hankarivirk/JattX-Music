"""jattx/core/telegram.py — Telegram file-send helpers."""
from pyrogram.types import Message
from config import config


class Telegram:
    async def send_photo_safe(self, chat_id: int, photo: str, caption: str, reply_markup=None):
        from jattx import app
        try:
            return await app.send_photo(chat_id, photo, caption=caption, reply_markup=reply_markup)
        except Exception:
            return await app.send_message(chat_id, caption, reply_markup=reply_markup)
