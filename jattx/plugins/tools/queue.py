"""jattx/plugins/tools/queue.py — Queue commands."""
from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, queue
from jattx.helpers._admins import admin_only


@app.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    current = queue.current(chat_id)
    tracks  = queue.get_queue(chat_id)

    if not current and not tracks:
        return await message.reply_text("📋 Queue is empty.")

    lines = []
    if current:
        lines.append(f"🎵 **Now Playing:**\n   {current.title} — {current.duration}\n")

    if tracks:
        lines.append(f"📋 **Up Next ({len(tracks)} tracks):**")
        for i, t in enumerate(tracks[:15], 1):
            lines.append(f"   `{i}.` {t.title} — {t.duration}")
        if len(tracks) > 15:
            lines.append(f"\n   … and **{len(tracks) - 15}** more tracks.")

    await message.reply_text("\n".join(lines))


@app.on_message(filters.command(["remove", "rm"]) & filters.group)
@admin_only
async def remove_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args or not args[0].isdigit():
        return await message.reply_text("❓ Usage: `/remove <position>`")
    pos = int(args[0])
    if queue.remove(message.chat.id, pos):
        await message.reply_text(f"🗑 Removed track at position **{pos}**.")
    else:
        await message.reply_text("❌ Invalid position.")


@app.on_message(filters.command("clearqueue") & filters.group)
@admin_only
async def clearqueue_cmd(client: Client, message: Message):
    queue.clear(message.chat.id)
    await message.reply_text("🗑 Queue cleared.")


@app.on_message(filters.command(["saveplaylist", "savep"]) & filters.group)
async def saveplaylist_cmd(client: Client, message: Message):
    from jattx import db
    args = " ".join(message.command[1:]).strip()
    if not args:
        return await message.reply_text("❓ Usage: `/saveplaylist <name>`")
    tracks = queue.get_queue(message.chat.id)
    cur    = queue.current(message.chat.id)
    all_t  = ([cur] if cur else []) + tracks
    if not all_t:
        return await message.reply_text("❌ Nothing in queue to save.")
    serialised = [
        {"id": t.id, "title": t.title, "duration": t.duration,
         "thumbnail": getattr(t, "thumbnail", ""), "url": getattr(t, "url", "")}
        for t in all_t
    ]
    await db.save_playlist(message.from_user.id, args, serialised)
    await message.reply_text(f"💾 Playlist **{args}** saved with **{len(serialised)}** tracks.")


@app.on_message(filters.command("myplaylists") & filters.group)
async def myplaylists_cmd(client: Client, message: Message):
    from jattx import db
    names = await db.list_playlists(message.from_user.id)
    if not names:
        return await message.reply_text("📂 You have no saved playlists.")
    text = "💾 **Your Saved Playlists:**\n\n"
    for i, n in enumerate(names, 1):
        text += f"{i}. {n}\n"
    text += "\nUse `/loadplaylist <name>` to load."
    await message.reply_text(text)


@app.on_message(filters.command("loadplaylist") & filters.group)
async def loadplaylist_cmd(client: Client, message: Message):
    from jattx import db, yt, call
    from jattx.helpers._dataclass import Track
    args = " ".join(message.command[1:]).strip()
    if not args:
        return await message.reply_text("❓ Usage: `/loadplaylist <name>`")
    tracks_data = await db.get_playlist(message.from_user.id, args)
    if not tracks_data:
        return await message.reply_text(f"❌ Playlist **{args}** not found.")

    user = message.from_user.mention
    chat_id = message.chat.id

    for t in tracks_data:
        queue.add(chat_id, Track(
            id=t["id"], title=t["title"], duration=t["duration"],
            thumbnail=t.get("thumbnail", ""), url=t.get("url", ""),
            user=user, video=False,
        ))

    await message.reply_text(
        f"✅ Loaded playlist **{args}** — **{len(tracks_data)}** tracks added to queue!"
    )
