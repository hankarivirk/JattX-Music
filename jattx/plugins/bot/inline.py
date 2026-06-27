"""
jattx/plugins/bot/inline.py
Inline query handler — search YouTube from any chat via @BotUsername query.
Returns up to 5 results as articles with a Play button.
"""

import asyncio
from pyrogram import Client
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
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

    # Quick search — up to 5 results
    results = []
    try:
        from py_yt import VideosSearch
        search = VideosSearch(q, limit=5, with_live=False)
        data   = await search.next()
        items  = (data or {}).get("result", [])
    except Exception:
        items = []

    for item in items[:5]:
        vid_id   = item.get("id", "")
        title    = (item.get("title") or "Unknown")[:60]
        duration = item.get("duration") or "?"
        channel  = (item.get("channel") or {}).get("name", "")
        thumb    = ((item.get("thumbnails") or [{}])[-1].get("url") or "").split("?")[0]
        url      = item.get("link") or f"https://youtube.com/watch?v={vid_id}"

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
                        switch_inline_query_current_chat=f"/play {url}"
                    ),
                    InlineKeyboardButton(
                        "🎬 Video",
                        switch_inline_query_current_chat=f"/vplay {url}"
                    ),
                ]]),
                description=f"🎤 {channel}  ⏱ {duration}",
                thumb_url=thumb or config.DEFAULT_THUMB,
            )
        )

    await query.answer(
        results=results,
        cache_time=10,
        switch_pm_text=f"⚡ {config.BOT_NAME}",
        switch_pm_parameter="inline_help",
    )
