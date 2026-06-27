"""jattx/helpers/_admins.py — Permission decorators and helpers."""
from functools import wraps
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from config import config


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    from jattx import db
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status.value in ("administrator", "owner", "creator")
    except Exception:
        return False


async def is_auth(client: Client, chat_id: int, user_id: int) -> bool:
    from jattx import db
    if user_id == config.OWNER_ID:
        return True
    sudoers = await db.get_sudoers()
    if user_id in sudoers:
        return True
    auth = await db.get_authusers(chat_id)
    if user_id in auth:
        return True
    return await is_admin(client, chat_id, user_id)


def admin_only(func):
    """Decorator: only group admins / auth users can use this command."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        from jattx import db
        if not await is_auth(client, message.chat.id, message.from_user.id):
            await message.reply_text(
                "❌ Only admins and authorised users can use this command."
            )
            return
        return await func(client, message)
    return wrapper


def owner_only(func):
    """Decorator: only the bot owner can use this command."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        if message.from_user.id != config.OWNER_ID:
            await message.reply_text("❌ This command is reserved for the bot owner.")
            return
        return await func(client, message)
    return wrapper


def sudo_only(func):
    """Decorator: owner + sudo users."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        from jattx import db
        sudoers = await db.get_sudoers()
        if message.from_user.id not in [config.OWNER_ID, *sudoers]:
            await message.reply_text("❌ Sudo access required.")
            return
        return await func(client, message)
    return wrapper
