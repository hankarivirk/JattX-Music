"""
jattx/plugins/play/autoplay.py

/autoplay on/off  — toggle autoplay for this group
🎵 Suggest button — show 5 related songs inline, tap to add any to queue
🔄 AutoPlay button on NP card — toggle autoplay inline

How autoplay works:
  When the queue empties, JattX automatically fetches related/mix tracks
  based on the LAST played song and keeps the music going.
  Users can also browse suggestions manually at any time via the Suggest button.
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from jattx import app, call, config, db, queue, yt
from jattx.helpers._admins import admin_only, is_auth
from jattx.helpers._buttons import now_playing_buttons, suggest_buttons
from jattx.helpers._dataclass import Track


# ── /autoplay command ─────────────────────────────────────────────────────────
@app.on_message(filters.command("autoplay") & filters.group)
@admin_only
async def autoplay_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    args    = message.command[1:]

    if not args:
        # Show current state
        state = "✅ ON" if config.is_autoplay(chat_id) else "❌ OFF"
        return await message.reply_text(
            f"🔄 **AutoPlay** is currently **{state}**\n\n"
            f"When ON, JattX automatically fetches related songs\n"
            f"when the queue empties — music never stops! 🎵\n\n"
            f"Toggle: `/autoplay on` or `/autoplay off`"
        )

    if args[0].lower() in ("on", "1", "true", "enable"):
        config.set_autoplay(chat_id, True)
        await message.reply_text(
            "🔄 **AutoPlay ON** ✅\n\n"
            "When the queue ends, I'll automatically fetch related songs\n"
            "based on what was playing. Music never stops! 🎵"
        )
    elif args[0].lower() in ("off", "0", "false", "disable"):
        config.set_autoplay(chat_id, False)
        await message.reply_text(
            "🔄 **AutoPlay OFF** ❌\n\n"
            "Queue will stop when all tracks finish."
        )
    else:
        await message.reply_text("❓ Usage: `/autoplay on` or `/autoplay off`")


# ── Autoplay toggle via NP card button ───────────────────────────────────────
@app.on_callback_query(filters.regex(r"^autoplay_(-?\d+)$"))
async def autoplay_toggle_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[1])

    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)

    # Toggle
    current = config.is_autoplay(chat_id)
    config.set_autoplay(chat_id, not current)
    new_state = config.is_autoplay(chat_id)

    await cb.answer(
        f"🔄 AutoPlay {'ON ✅' if new_state else 'OFF ❌'}",
        show_alert=True
    )

    # Refresh NP card buttons to reflect new state
    try:
        await cb.message.edit_reply_markup(
            now_playing_buttons(chat_id, autoplay=new_state)
        )
    except Exception:
        pass


# ── 🎵 Suggest button — show related song suggestions ────────────────────────
@app.on_callback_query(filters.regex(r"^suggest_(-?\d+)$"))
async def suggest_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[1])
    await cb.answer("🔍 Fetching suggestions…")

    current = queue.current(chat_id)
    if not current:
        return await cb.answer("❌ Nothing is playing.", show_alert=True)

    # Fetch related tracks
    suggestions = await call.get_suggestions(chat_id)

    if not suggestions:
        return await cb.answer(
            "❌ Couldn't find suggestions. Try again!", show_alert=True
        )

    # Store suggestions temporarily for add callbacks
    _store_suggestions(chat_id, suggestions)

    title = current.title[:40]
    text  = (
        f"🎵 **Song Suggestions**\n"
        f"Based on: **{title}**\n\n"
        f"Tap a song to add it to the queue:"
    )

    try:
        await cb.message.edit_caption(
            caption=text,
            reply_markup=suggest_buttons(chat_id, suggestions),
        )
    except Exception:
        try:
            await cb.message.edit_text(
                text,
                reply_markup=suggest_buttons(chat_id, suggestions),
            )
        except Exception:
            pass


# ── Add suggested song to queue ───────────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^addsugg_(-?\d+)_([A-Za-z0-9_-]{11})$"))
async def add_suggestion_cb(client: Client, cb: CallbackQuery):
    parts   = cb.data.split("_")
    chat_id = int(parts[1])
    vid_id  = parts[2]

    user = cb.from_user.mention

    # Try to get track from stored suggestions first
    track = _get_stored_suggestion(chat_id, vid_id)

    if not track:
        # Fallback: build a minimal Track from the YouTube ID
        track = Track(
            id=vid_id,
            title="Loading…",
            user=user,
            video=False,
        )

    track.user = user
    queue.add(chat_id, track)

    await cb.answer(f"✅ Added: {track.title[:40]}", show_alert=False)

    # Go back to NP card view
    current = queue.current(chat_id)
    if current:
        ap_on = config.is_autoplay(chat_id)
        caption = (
            f"🎵 **Now Playing**\n\n"
            f"**{current.title}**\n"
            f"┌ 🎤 {getattr(current, 'channel_name', '')}\n"
            f"├ ⏱ {current.duration}\n"
            f"├ 👤 {getattr(current, 'user', '')}\n"
            f"└ 🔄 AutoPlay: {'✅ ON' if ap_on else '❌ OFF'}\n\n"
            f"⚡ **{config.BOT_NAME}**\n\n"
            f"➕ **{track.title[:40]}** added to queue!"
        )
        try:
            await cb.message.edit_caption(
                caption=caption,
                reply_markup=now_playing_buttons(chat_id, autoplay=ap_on),
            )
        except Exception:
            try:
                await cb.message.edit_text(
                    caption,
                    reply_markup=now_playing_buttons(chat_id, autoplay=ap_on),
                )
            except Exception:
                pass


# ── Back to NP card from suggestions ─────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^np_(-?\d+)$"))
async def back_to_np_cb(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[1])
    current = queue.current(chat_id)
    ap_on   = config.is_autoplay(chat_id)

    if not current:
        return await cb.answer("❌ Nothing playing.", show_alert=True)

    caption = (
        f"🎵 **Now Playing**\n\n"
        f"**{current.title}**\n"
        f"┌ 🎤 {getattr(current, 'channel_name', '')}\n"
        f"├ ⏱ {current.duration}\n"
        f"├ 👤 {getattr(current, 'user', '')}\n"
        f"└ 🔄 AutoPlay: {'✅ ON' if ap_on else '❌ OFF'}\n\n"
        f"⚡ **{config.BOT_NAME}**"
    )
    try:
        await cb.message.edit_caption(
            caption=caption,
            reply_markup=now_playing_buttons(chat_id, autoplay=ap_on),
        )
    except Exception:
        try:
            await cb.message.edit_text(
                caption,
                reply_markup=now_playing_buttons(chat_id, autoplay=ap_on),
            )
        except Exception:
            pass
    await cb.answer()


# ── In-memory suggestion store (per group, short-lived) ──────────────────────
_suggestion_cache: dict[int, list] = {}


def _store_suggestions(chat_id: int, tracks: list):
    _suggestion_cache[chat_id] = tracks


def _get_stored_suggestion(chat_id: int, vid_id: str) -> "Track | None":
    for t in _suggestion_cache.get(chat_id, []):
        if t.id == vid_id:
            return t
    return None
