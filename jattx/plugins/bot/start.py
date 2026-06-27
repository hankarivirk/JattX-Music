"""
jattx/plugins/bot/start.py
Start command — uses AUTO-DETECTED bot name & username.
Beautiful UI with animated-style text.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from jattx import app
from jattx.helpers._buttons import start_buttons, help_buttons, close_button
from config import config

_HELP: dict[str, str] = {
    "play": (
        "🎵 **Play Commands**\n\n"
        "`/play <song name or URL>` — Play audio\n"
        "`/vplay <song name or URL>` — Play video\n"
        "`/yplay <song>` — YouTube Music search\n"
        "`/cplay <URL>` — Play from channel\n"
        "`/playlist <URL>` — Add entire playlist\n"
        "`/live <URL>` — Stream live radio/video\n"
        "`/tplay` — Play Telegram audio/video file\n"
    ),
    "admin": (
        "⚙️ **Admin Commands**\n\n"
        "`/pause` — Pause playback\n"
        "`/resume` — Resume playback\n"
        "`/skip` — Skip current track\n"
        "`/stop` — Stop & clear queue\n"
        "`/mute` / `/unmute` — Mute / unmute\n"
        "`/seek <seconds>` — Jump to position\n"
        "`/loop <0-10>` — Set loop count\n"
        "`/shuffle` — Shuffle queue\n"
        "`/auth @user` — Authorise user\n"
        "`/unauth @user` — Remove authorisation\n"
    ),
    "effects": (
        "🎚 **Audio Effects**\n\n"
        "`/effect bassboost` — Deep bass boost\n"
        "`/effect nightcore` — Fast + high pitch\n"
        "`/effect slowmode` — Slow + deep\n"
        "`/effect reverb` — Echo reverb\n"
        "`/effect 3d` — 3D spatial audio\n"
        "`/effect karaoke` — Remove vocals\n"
        "`/effect loud` — Loudness normalise\n"
        "`/effect clear` — Remove all effects\n"
    ),
    "queue": (
        "📋 **Queue Commands**\n\n"
        "`/queue` — Show current queue\n"
        "`/remove <position>` — Remove a track\n"
        "`/shuffle` — Shuffle queue\n"
        "`/clearqueue` — Empty queue\n"
        "`/saveplaylist <name>` — Save queue as playlist\n"
        "`/myplaylists` — List saved playlists\n"
        "`/loadplaylist <name>` — Load saved playlist\n"
    ),
    "owner": (
        "🔧 **Owner Commands**\n\n"
        "`/broadcast <msg>` — Broadcast to all groups\n"
        "`/gban @user` — Global ban\n"
        "`/ungban @user` — Remove global ban\n"
        "`/sudo @user` — Add sudo user\n"
        "`/unsudo @user` — Remove sudo user\n"
        "`/blacklist <chat_id>` — Blacklist group\n"
        "`/maintenance on/off` — Toggle maintenance\n"
        "`/restart` — Restart bot\n"
        "`/eval <code>` — Run Python code\n"
        "`/shell <cmd>` — Run shell command\n"
        "`/stats` — Bot statistics\n"
        "`/botinfo` — Full deployment info\n"
    ),
    "stats": (
        "📊 **Stats & Tools**\n\n"
        "`/ping` — Bot latency\n"
        "`/stats` — Usage statistics\n"
        "`/uptime` — Bot uptime\n"
        "`/activevc` — Active voice chats\n"
        "`/lyrics <song>` — Fetch lyrics\n"
        "`/speed` — Speed test\n"
        "`/lang <code>` — Set group language\n"
    ),
}


@app.on_message(filters.command("start") & filters.private)
async def start_private(client: Client, message: Message):
    text = (
        f"╔══════════════════════════════╗\n"
        f"║  ⚡ **{config.BOT_NAME}**\n"
        f"║  `@{config.BOT_USERNAME}`\n"
        f"╚══════════════════════════════╝\n\n"
        f"The **fastest** Telegram music bot — "
        f"crystal-clear audio, video, effects, playlists & more.\n\n"
        f"**Add me to your group** and start the music! 🎶\n\n"
        f"┌ 🎵 YouTube / YT Music\n"
        f"├ 🎬 Video streaming\n"
        f"├ 🎚 Audio effects (bass, nightcore…)\n"
        f"├ 📋 Queue management\n"
        f"├ 💾 Saved playlists\n"
        f"└ 🌍 Multi-language support"
    )
    # START_IMG is always a URL (set in config/env) — never a local file
    await message.reply_photo(
        photo=config.START_IMG,
        caption=text,
        reply_markup=start_buttons(
            config.BOT_USERNAME,
            config.SUPPORT_CHANNEL,
            config.SUPPORT_CHAT,
        ),
    )


@app.on_message(filters.command("start") & filters.group)
async def start_group(client: Client, message: Message):
    await message.reply_text(
        f"👋 Hey! I'm **{config.BOT_NAME}** (`@{config.BOT_USERNAME}`).\n"
        f"Use `/play <song>` to start the music! 🎵\n"
        f"Type `/help` for all commands.",
        reply_markup=start_buttons(
            config.BOT_USERNAME,
            config.SUPPORT_CHANNEL,
            config.SUPPORT_CHAT,
        ),
    )


@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    text = (
        f"📖 **{config.BOT_NAME} Help Menu**\n\n"
        f"Choose a category below:"
    )
    await message.reply_text(text, reply_markup=help_buttons())


# ── Callback handlers ─────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^help_"))
async def help_cb(client: Client, cb: CallbackQuery):
    cat = cb.data.replace("help_", "")
    if cat == "main":
        text = (
            f"📖 **{config.BOT_NAME} Help Menu**\n\n"
            "Choose a category:"
        )
        await cb.message.edit_text(text, reply_markup=help_buttons())
    elif cat in _HELP:
        await cb.message.edit_text(
            _HELP[cat],
            reply_markup=help_buttons(),
        )
    await cb.answer()


@app.on_callback_query(filters.regex("^close$"))
async def close_cb(client: Client, cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()
