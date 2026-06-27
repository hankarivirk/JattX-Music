"""
jattx/plugins/play/spotify.py
Spotify commands: /splay (track), /salbum, /splaylist
Converts Spotify URLs → YouTube searches → downloads → plays.
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, call, config, db, queue, yt
from jattx.core.spotify import Spotify

spotify = Spotify()


async def _search_and_queue(
    client: Client,
    message: Message,
    queries: list[str],
    video: bool,
    user: str,
    chat_id: int,
):
    """Search YouTube for each Spotify query and queue/play."""
    from jattx.helpers._dataclass import Track

    if not queries:
        return await message.reply_text("❌ No tracks found.")

    wait = await message.reply_text(
        f"🎵 Loading **{len(queries)}** track(s) from Spotify…"
    )

    loaded = 0
    first_played = False

    for i, q in enumerate(queries):
        track = await yt.ytmusic_search(q, message.id, video)
        if not track:
            track = await yt.search(q, message.id, video)
        if not track:
            continue

        track.user = user
        loaded += 1

        # Play first track immediately, queue rest
        if not first_played and queue.is_empty(chat_id):
            track.file_path = await yt.download(track.id, video=video)
            if track.file_path:
                first_played = True
                await wait.delete()
                await call.play_media(chat_id, message, track)
                if len(queries) > 1:
                    await message.reply_text(
                        f"🎵 Playing: **{track.title}**\n"
                        f"📋 Queuing remaining {len(queries)-1} tracks…"
                    )
                continue
        else:
            queue.add(chat_id, track)

        # Progress update every 10
        if loaded % 10 == 0:
            try:
                await wait.edit_text(
                    f"📋 Queuing Spotify tracks… {loaded}/{len(queries)}"
                )
            except Exception:
                pass

    try:
        await wait.delete()
    except Exception:
        pass

    if loaded:
        await message.reply_text(
            f"✅ Spotify: **{loaded}** track(s) loaded successfully!"
        )
    else:
        await message.reply_text("❌ Failed to find any tracks on YouTube.")


@app.on_message(filters.command(["splay", "sp"]) & filters.group)
async def splay_cmd(client: Client, message: Message):
    args = " ".join(message.command[1:]).strip()
    if not args:
        return await message.reply_text(
            "❓ Usage: `/splay <Spotify track URL or search query>`"
        )
    user    = message.from_user.mention if message.from_user else "Unknown"
    chat_id = message.chat.id

    if spotify.is_spotify(args):
        q = await spotify.track_query(args)
        if not q:
            return await message.reply_text("❌ Couldn't fetch track from Spotify.")
        await _search_and_queue(client, message, [q], False, user, chat_id)
    else:
        # Plain search on YouTube Music
        track = await yt.ytmusic_search(args, message.id, False)
        if not track:
            return await message.reply_text("❌ No results found.")
        track.user = user
        track.file_path = await yt.download(track.id, video=False)
        if not track.file_path:
            return await message.reply_text("❌ Download failed.")
        if not queue.is_empty(chat_id):
            queue.add(chat_id, track)
            return await message.reply_text(f"📋 Added: **{track.title}**")
        await call.play_media(chat_id, message, track)


@app.on_message(filters.command(["salbum"]) & filters.group)
async def salbum_cmd(client: Client, message: Message):
    url = " ".join(message.command[1:]).strip()
    if not url or not spotify.is_spotify(url):
        return await message.reply_text(
            "❓ Usage: `/salbum <Spotify album URL>`"
        )
    queries = await spotify.album_queries(url, limit=config.PLAYLIST_LIMIT)
    user    = message.from_user.mention if message.from_user else "Unknown"
    await _search_and_queue(client, message, queries, False, user, message.chat.id)


@app.on_message(filters.command(["splaylist"]) & filters.group)
async def splaylist_cmd(client: Client, message: Message):
    url = " ".join(message.command[1:]).strip()
    if not url or not spotify.is_spotify(url):
        return await message.reply_text(
            "❓ Usage: `/splaylist <Spotify playlist URL>`"
        )
    queries = await spotify.playlist_queries(url, limit=config.PLAYLIST_LIMIT)
    user    = message.from_user.mention if message.from_user else "Unknown"
    await _search_and_queue(client, message, queries, False, user, message.chat.id)
