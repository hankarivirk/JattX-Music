"""
jattx/plugins/bot/inline.py
Inline query handler — Fixed to use yt-dlp instead of py_yt.
"""

import asyncio
from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from jattx import app, yt
from config import config


@app.on_inline_query()
async def inline_query(client: Client, query: InlineQuery):
    q = query.query.strip()
    if not q:
        await query.answer(
            results=[],
            cache_time=5,
            switch_pm_text=f"🔍 Search {config.BOT_NAME}",
            switch_pm_parameter="search",
        )
        return

    results = []
    try:
        import yt_dlp
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "noplaylist": True,
            "nocheckcertificate": True,
        }
        cookie = yt.get_cookie()
        if cookie:
            opts["cookiefile"] = cookie

        def _search():
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(
                        f"ytsearch5:{q}", download=False
                    )
                    return (info or {}).get("entries", [])
                except Exception:
                    return []

        items = await asyncio.to_thread(_search)
    except Exception:
        items = []

    for item in items[:5]:
        if not item:
            continue
        vid_id   = item.get("id", "")
        title    = (item.get("title") or "Unknown")[:60]
        duration = item.get("duration_string") or "?"
        channel  = item.get("uploader") or item.get("channel") or ""
        thumb    = item.get("thumbnail") or config.DEFAULT_THUMB
        url      = (
            item.get("url")
            or f"https://youtube.com/watch?v={vid_id}"
        )

        results.append(
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputTextMessageContent(
                    f"🎵 **{title}**\n"
                    f"🎤 {channel}\n"
                    f"⏱ {duration}\n"
                    f"🔗 {url}"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "▶️ Play in Group",
                        switch_inline_query_current_chat=(
                            f"/play {url}"
                        )
                    ),
                    InlineKeyboardButton(
                        "🎬 Video",
                        switch_inline_query_current_chat=(
                            f"/vplay {url}"
                        )
                    ),
                ]]),
                description=f"🎤 {channel}  ⏱ {duration}",
                thumb_url=thumb,
            )
        )

    await query.answer(
        results=results,
        cache_time=10,
        switch_pm_text=f"⚡ {config.BOT_NAME}",
        switch_pm_parameter="inline_help",
    )
