"""
jattx/plugins/play/play.py
Fixed: Missing async on command handlers
"""

import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, call, config, db, queue, yt
from jattx.helpers._dataclass import Track, Media
from jattx.helpers._utilities import seconds_to_str


async def _resolve_and_play(
    client: Client,
    message: Message,
    query: str,
    video: bool = False,
    ytmusic: bool = False,
):
    chat_id = message.chat.id
    user = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )

    if config.MAINTENANCE and (
        message.from_user.id != config.OWNER_ID
    ):
        return await message.reply_text(
            "🛠 Bot is under maintenance. Please try again later."
        )

    if await db.is_blacklisted(chat_id):
        return await message.reply_text(
            "❌ This group is blacklisted."
        )

    waiting = await message.reply_text("🔍 Searching…")

    track: Track | None = None

    if yt.invalid(query):
        return await waiting.edit_text(
            "❌ Invalid YouTube URL. "
            "Use a watch/shorts/playlist link."
        )

    if yt.valid(query):
        if yt.is_playlist(query):
            await waiting.delete()
            return await _handle_playlist(
                client, message, query, video, user
            )
        info = await asyncio.to_thread(_info_from_url, query)
        if info:
            dur = int(info.get("duration") or 0)
            track = Track(
                id=info["id"],
                title=(info.get("title") or "Unknown")[:55],
                channel_name=(
                    info.get("uploader")
                    or info.get("channel")
                    or ""
                ),
                duration=seconds_to_str(dur),
                duration_sec=dur,
                thumbnail=info.get("thumbnail") or "",
                url=query,
                message_id=message.id,
                user=user,
                video=video,
            )
    elif ytmusic:
        track = await yt.ytmusic_search(
            query, message.id, video
        )
    else:
        track = await yt.search(query, message.id, video)

    if not track:
        return await waiting.edit_text(
            "❌ No results found. Try a different query."
        )

    await waiting.edit_text(
        f"⬇️ Downloading **{track.title}**…"
    )
    track.user = user
    track.file_path = await yt.download(track.id, video=video)

    if not track.file_path:
        return await waiting.edit_text(
            f"❌ Download failed.\n"
            f"💡 Try setting a cookie or PO token.\n"
            f"Support: {config.SUPPORT_CHAT}"
        )

    await waiting.delete()

    if not queue.is_empty(chat_id) or _is_active(chat_id):
        queue.add(chat_id, track)
        pos = queue.size(chat_id)
        return await message.reply_text(
            f"📋 **Added to Queue** — Position #{pos}\n"
            f"🎵 **{track.title}**\n"
            f"⏱ {track.duration} | 👤 {user}"
        )

    await call.play_media(chat_id, message, track)


def _is_active(chat_id: int) -> bool:
    from jattx import queue as q
    return q.current(chat_id) is not None


def _info_from_url(url: str) -> dict | None:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "nocheckcertificate": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except Exception:
            return None


async def _handle_playlist(
    client: Client,
    message: Message,
    url: str,
    video: bool,
    user: str,
):
    chat_id = message.chat.id
    msg = await message.reply_text("📋 Fetching playlist…")

    async def _prog(done: int, total: int):
        try:
            await msg.edit_text(
                f"📋 Fetching playlist… {done}/{total}"
            )
        except Exception:
            pass

    tracks = await yt.playlist(
        config.PLAYLIST_LIMIT, user, url, video, _prog
    )
    if not tracks:
        return await msg.edit_text(
            "❌ Empty or invalid playlist."
        )

    first = tracks[0]
    first.file_path = await yt.download(first.id, video=video)
    if not first.file_path:
        return await msg.edit_text(
            "❌ Failed to download first track."
        )

    for t in tracks[1:]:
        queue.add(chat_id, t)

    await msg.delete()
    await call.play_media(chat_id, message, first)
    await message.reply_text(
        f"✅ **Playlist loaded** — {len(tracks)} tracks\n"
        f"🎵 Playing: **{first.title}**\n"
        f"📋 {len(tracks) - 1} tracks in queue"
    )


# ── Fixed: Added missing async keyword ──────────────────────
@app.on_message(
    filters.command(["play", "p"]) & filters.group
)
async def play_cmd(client: Client, message: Message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text(
            "❓ Usage: /play <song name or URL>"
        )
    await _resolve_and_play(
        client, message, query, video=False
    )


@app.on_message(
    filters.command(["vplay", "vp"]) & filters.group
)
async def vplay_cmd(client: Client, message: Message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text(
            "❓ Usage: /vplay <song name or URL>"
        )
    await _resolve_and_play(
        client, message, query, video=True
    )


@app.on_message(
    filters.command(["yplay", "yp"]) & filters.group
)
async def yplay_cmd(client: Client, message: Message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text(
            "❓ Usage: /yplay <song name>"
        )
    await _resolve_and_play(
        client, message, query, video=False, ytmusic=True
    )


@app.on_message(
    filters.command(["playlist", "pl"]) & filters.group
)
async def playlist_cmd(client: Client, message: Message):
    url = " ".join(message.command[1:]).strip()
    if not url:
        return await message.reply_text(
            "❓ Usage: /playlist <YouTube playlist URL>"
        )
    user = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )
    await _handle_playlist(
        client, message, url, False, user
    )


@app.on_message(
    filters.command(["vplaylist", "vpl"]) & filters.group
)
async def vplaylist_cmd(client: Client, message: Message):
    url = " ".join(message.command[1:]).strip()
    if not url:
        return await message.reply_text(
            "❓ Usage: /vplaylist <YouTube playlist URL>"
        )
    user = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )
    await _handle_playlist(
        client, message, url, True, user
    )


@app.on_message(
    filters.command(["tplay", "tp"]) & filters.group
)
async def tplay_cmd(client: Client, message: Message):
    reply    = message.reply_to_message
    media_msg = reply or message

    file = (
        media_msg.audio
        or media_msg.video
        or media_msg.document
        or media_msg.voice
        or media_msg.video_note
    )
    if not file:
        return await message.reply_text(
            "❓ Reply to an audio or video file to play it."
        )

    wait = await message.reply_text("⬇️ Downloading file…")
    path = await media_msg.download()
    if not path:
        return await wait.edit_text("❌ Failed to download.")

    is_video = bool(
        media_msg.video or media_msg.video_note
    )
    title = (
        getattr(file, "title", None)
        or getattr(file, "file_name", None)
        or "Telegram File"
    )[:55]
    dur = getattr(file, "duration", 0) or 0

    media = Media(
        file_path=path,
        title=title,
        duration=seconds_to_str(dur),
        duration_sec=dur,
        video=is_video,
        user=(
            message.from_user.mention
            if message.from_user
            else "Unknown"
        ),
    )

    await wait.delete()
    chat_id = message.chat.id

    if not queue.is_empty(chat_id) or _is_active(chat_id):
        queue.add(chat_id, media)
        return await message.reply_text(
            f"📋 Added to queue: **{title}**"
        )

    await call.play_media(chat_id, message, media)


@app.on_message(filters.command(["live"]) & filters.group)
async def live_cmd(client: Client, message: Message):
    url = " ".join(message.command[1:]).strip()
    if not url:
        return await message.reply_text(
            "❓ Usage: /live <stream URL>"
        )
    user = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )
    media = Media(
        file_path=url,
        title="Live Stream",
        duration="∞",
        duration_sec=0,
        video=False,
        user=user,
    )
    await call.play_media(message.chat.id, message, media)


@app.on_message(filters.command(["mix"]) & filters.group)
async def mix_cmd(client: Client, message: Message):
    query   = " ".join(message.command[1:]).strip()
    current = queue.current(message.chat.id)

    if not query and not current:
        return await message.reply_text(
            "❓ Usage: `/mix <YouTube video URL or ID>`\n"
            "Or use while a track is playing."
        )

    wait     = await message.reply_text("🎲 Building mix…")
    video_id = query or current.id
    user     = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )
    tracks = await yt.mix(video_id, user, video=False)

    if not tracks:
        return await wait.edit_text(
            "❌ Couldn't build a mix for that track."
        )

    for t in tracks:
        queue.add(message.chat.id, t)

    await wait.edit_text(
        f"🎲 Mix added — **{len(tracks)} tracks** queued!"
    )
