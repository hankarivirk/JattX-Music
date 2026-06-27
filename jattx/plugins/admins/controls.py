"""jattx/plugins/admins/controls.py — Playback control commands."""
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from jattx import app, call, db, queue
from jattx.helpers._admins import admin_only
from jattx.helpers._buttons import now_playing_buttons, audio_effects_buttons
from jattx.core.calls import EFFECT_FILTERS


@app.on_message(filters.command("pause") & filters.group)
@admin_only
async def pause_cmd(client: Client, message: Message):
    ok = await call.pause(message.chat.id)
    await message.reply_text("⏸ Paused." if ok else "❌ Nothing is playing.")


@app.on_message(filters.command("resume") & filters.group)
@admin_only
async def resume_cmd(client: Client, message: Message):
    ok = await call.resume(message.chat.id)
    await message.reply_text("▶️ Resumed." if ok else "❌ Nothing to resume.")


@app.on_message(filters.command(["skip", "s"]) & filters.group)
@admin_only
async def skip_cmd(client: Client, message: Message):
    await call.play_next(message.chat.id)
    await message.reply_text("⏭ Skipped!")


@app.on_message(filters.command(["stop", "end"]) & filters.group)
@admin_only
async def stop_cmd(client: Client, message: Message):
    await call.stop(message.chat.id)
    await message.reply_text("⏹ Stopped and cleared queue.")


@app.on_message(filters.command("mute") & filters.group)
@admin_only
async def mute_cmd(client: Client, message: Message):
    await call.mute(message.chat.id)
    await message.reply_text("🔇 Muted.")


@app.on_message(filters.command("unmute") & filters.group)
@admin_only
async def unmute_cmd(client: Client, message: Message):
    await call.unmute(message.chat.id)
    await message.reply_text("🔊 Unmuted.")


@app.on_message(filters.command("seek") & filters.group)
@admin_only
async def seek_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args or not args[0].isdigit():
        return await message.reply_text("❓ Usage: `/seek <seconds>`")
    await call.seek(message.chat.id, int(args[0]))
    await message.reply_text(f"⏩ Seeked to {args[0]}s.")


@app.on_message(filters.command("loop") & filters.group)
@admin_only
async def loop_cmd(client: Client, message: Message):
    args = message.command[1:]
    count = int(args[0]) if args and args[0].isdigit() else 0
    await db.set_loop(message.chat.id, count)
    await message.reply_text(
        f"🔁 Loop set to **{count}** times." if count else "🔁 Loop disabled."
    )


@app.on_message(filters.command("shuffle") & filters.group)
@admin_only
async def shuffle_cmd(client: Client, message: Message):
    queue.shuffle(message.chat.id)
    await message.reply_text("🔀 Queue shuffled!")


@app.on_message(filters.command("effect") & filters.group)
@admin_only
async def effect_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args or args[0] not in EFFECT_FILTERS:
        effects_list = ", ".join(f"`{e}`" for e in EFFECT_FILTERS)
        return await message.reply_text(
            f"❓ Usage: `/effect <name>`\n\nAvailable: {effects_list}"
        )
    ok = await call.set_effect(message.chat.id, args[0])
    if ok:
        await message.reply_text(f"🎚 Effect applied: **{args[0]}**")
    else:
        await message.reply_text("❌ Nothing is playing.")


# ── Auth commands ─────────────────────────────────────────────────────────────
@app.on_message(filters.command("auth") & filters.group)
@admin_only
async def auth_cmd(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❓ Reply to a user or use `/auth @username`.")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        try:
            target = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")
    await db.add_authuser(message.chat.id, target.id)
    await message.reply_text(f"✅ {target.mention} is now authorised to control music.")


@app.on_message(filters.command("unauth") & filters.group)
@admin_only
async def unauth_cmd(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❓ Reply to a user or use `/unauth @username`.")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        try:
            target = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found.")
    await db.remove_authuser(message.chat.id, target.id)
    await message.reply_text(f"✅ {target.mention} has been unauthorised.")


# ── Callback button handlers ──────────────────────────────────────────────────
@app.on_callback_query(filters.regex(r"^(pause|resume|stop|skip|shuffle|loop|queue|np)_(-?\d+)$"))
async def playback_cb(client: Client, cb: CallbackQuery):
    from jattx.helpers._admins import is_auth
    chat_id = int(cb.data.split("_")[-1])
    action  = cb.data.rsplit("_", 1)[0]

    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)

    if action == "pause":
        await call.pause(chat_id)
        await cb.answer("⏸ Paused")
    elif action == "resume":
        await call.resume(chat_id)
        await cb.answer("▶️ Resumed")
    elif action == "stop":
        await call.stop(chat_id)
        await cb.message.delete()
        return
    elif action == "skip":
        await call.play_next(chat_id)
        await cb.answer("⏭ Skipped")
    elif action == "shuffle":
        queue.shuffle(chat_id)
        await cb.answer("🔀 Shuffled!")
    elif action == "loop":
        cur = await db.get_loop(chat_id)
        nxt = (cur + 1) % 6
        await db.set_loop(chat_id, nxt)
        await cb.answer(f"🔁 Loop: {nxt}")
    elif action == "queue":
        tracks = queue.get_queue(chat_id)
        if not tracks:
            return await cb.answer("📋 Queue is empty.", show_alert=True)
        text = "📋 **Queue**\n\n"
        for i, t in enumerate(tracks[:10], 1):
            text += f"{i}. {t.title} — {t.duration}\n"
        if len(tracks) > 10:
            text += f"\n… and {len(tracks) - 10} more."
        await cb.answer(text[:200], show_alert=True)
    elif action == "effects":
        await cb.message.edit_reply_markup(audio_effects_buttons(chat_id))
        await cb.answer()
        return
    elif action == "np":
        await cb.message.edit_reply_markup(now_playing_buttons(chat_id))
        await cb.answer()
        return

    # Refresh buttons
    try:
        await cb.message.edit_reply_markup(now_playing_buttons(chat_id))
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^fx_(.+)_(-?\d+)$"))
async def effects_cb(client: Client, cb: CallbackQuery):
    from jattx.helpers._admins import is_auth
    parts   = cb.data.split("_")
    effect  = "_".join(parts[1:-1])
    chat_id = int(parts[-1])

    if not await is_auth(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admins only!", show_alert=True)

    ok = await call.set_effect(chat_id, effect)
    if ok:
        await cb.answer(f"🎚 Effect: {effect}", show_alert=False)
    else:
        await cb.answer("❌ Nothing playing", show_alert=True)
    try:
        await cb.message.edit_reply_markup(now_playing_buttons(chat_id))
    except Exception:
        pass
