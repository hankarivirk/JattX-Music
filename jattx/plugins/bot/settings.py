"""
jattx/plugins/bot/settings.py
Fixed: _lang_buttons was called but defined as lang_buttons
"""

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from jattx import app, db
from jattx.helpers._admins import admin_only, is_auth
from config import config

_LANGS = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 Hindi",
    "pa": "🇮🇳 Punjabi",
    "ar": "🇸🇦 Arabic",
    "de": "🇩🇪 German",
    "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French",
    "ru": "🇷🇺 Russian",
    "tr": "🇹🇷 Turkish",
    "zh": "🇨🇳 Chinese",
}


async def _settings_text(chat_id: int) -> str:
    lang     = await db.get_lang(chat_id)
    playmode = await db.get_playmode(chat_id)
    doc      = await db.get_group(chat_id)
    return (
        f"⚙️ **Group Settings**\n\n"
        f"🌍 Language  : **{_LANGS.get(lang, lang)}**\n"
        f"▶️ Play Mode : **{playmode.title()}**\n"
        f"🧹 Clean Mode: **{'On' if doc.get('clean_mode') else 'Off'}**\n"
        f"⏹ Auto End  : **{'On' if doc.get('auto_end', config.AUTO_END) else 'Off'}**"
    )


def _settings_buttons(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌍 Language",
                callback_data=f"set_lang_{chat_id}"
            ),
            InlineKeyboardButton(
                "▶️ Play Mode",
                callback_data=f"set_mode_{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🧹 Clean Mode",
                callback_data=f"set_clean_{chat_id}"
            ),
            InlineKeyboardButton(
                "⏹ Auto End",
                callback_data=f"set_autoend_{chat_id}"
            ),
        ],
        [InlineKeyboardButton("✖ Close", callback_data="close")],
    ])


# ── Fixed: was lang_buttons, now _lang_buttons ──────────────
def _lang_buttons(chat_id: int) -> InlineKeyboardMarkup:
    rows, row = [], []
    for code, name in _LANGS.items():
        row.append(InlineKeyboardButton(
            name,
            callback_data=f"setlang_{code}_{chat_id}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(
        "« Back",
        callback_data=f"settings_{chat_id}"
    )])
    return InlineKeyboardMarkup(rows)


@app.on_message(filters.command("settings") & filters.group)
@admin_only
async def settings_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )


@app.on_callback_query(filters.regex(r"^settings_(-?\d+)$"))
async def settings_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[1])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    await cb.message.edit_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^set_lang_(-?\d+)$"))
async def set_lang_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[-1])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    await cb.message.edit_text(
        "🌍 Choose Language:",
        reply_markup=_lang_buttons(chat_id),
    )
    await cb.answer()


@app.on_callback_query(filters.regex(r"^setlang_([a-z]+)_(-?\d+)$"))
async def setlang_cb(client: Client, cb: CallbackQuery):
    parts   = cb.data.split("_")
    lang    = parts[1]
    chat_id = int(parts[2])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    await db.set_lang(chat_id, lang)
    await cb.answer(
        f"✅ Language set to {_LANGS.get(lang, lang)}",
        show_alert=True
    )
    await cb.message.edit_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )


@app.on_callback_query(filters.regex(r"^set_mode_(-?\d+)$"))
async def set_mode_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[-1])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    cur = await db.get_playmode(chat_id)
    nxt = "direct" if cur == "inline" else "inline"
    await db.set_playmode(chat_id, nxt)
    await cb.answer(f"▶️ Play mode: {nxt.title()}", show_alert=True)
    await cb.message.edit_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )


@app.on_callback_query(filters.regex(r"^set_clean_(-?\d+)$"))
async def set_clean_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[-1])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    doc = await db.get_group(chat_id)
    nxt = not doc.get("clean_mode", False)
    await db.set_group(chat_id, clean_mode=nxt)
    await cb.answer(
        f"🧹 Clean Mode: {'On' if nxt else 'Off'}",
        show_alert=True
    )
    await cb.message.edit_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )


@app.on_callback_query(filters.regex(r"^set_autoend_(-?\d+)$"))
async def set_autoend_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[-1])
    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)
    doc = await db.get_group(chat_id)
    nxt = not doc.get("auto_end", config.AUTO_END)
    await db.set_group(chat_id, auto_end=nxt)
    await cb.answer(
        f"⏹ Auto End: {'On' if nxt else 'Off'}",
        show_alert=True
    )
    await cb.message.edit_text(
        await _settings_text(chat_id),
        reply_markup=_settings_buttons(chat_id),
    )
