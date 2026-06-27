"""jattx/helpers/_buttons.py — All inline keyboard layouts."""
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def now_playing_buttons(chat_id: int, autoplay: bool = False) -> InlineKeyboardMarkup:
    ap_icon = "🔄 AutoPlay ✅" if autoplay else "🔄 AutoPlay ❌"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏮ Skip",    callback_data=f"skip_{chat_id}"),
            InlineKeyboardButton("⏸ Pause",   callback_data=f"pause_{chat_id}"),
            InlineKeyboardButton("⏹ Stop",    callback_data=f"stop_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🔀 Shuffle", callback_data=f"shuffle_{chat_id}"),
            InlineKeyboardButton("🔁 Loop",    callback_data=f"loop_{chat_id}"),
            InlineKeyboardButton("📋 Queue",   callback_data=f"queue_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🎚 Effects", callback_data=f"effects_{chat_id}"),
            InlineKeyboardButton("🎵 Suggest", callback_data=f"suggest_{chat_id}"),
            InlineKeyboardButton(ap_icon,      callback_data=f"autoplay_{chat_id}"),
        ],
    ])


def suggest_buttons(chat_id: int, tracks: list) -> InlineKeyboardMarkup:
    """
    Inline buttons showing up to 5 suggested songs.
    Each button adds that song to queue when tapped.
    tracks = list of Track objects
    """
    rows = []
    for i, t in enumerate(tracks[:5]):
        label = f"➕ {t.title[:35]}" if len(t.title) > 35 else f"➕ {t.title}"
        rows.append([
            InlineKeyboardButton(label, callback_data=f"addsugg_{chat_id}_{t.id}")
        ])
    rows.append([
        InlineKeyboardButton("🔄 Refresh",  callback_data=f"suggest_{chat_id}"),
        InlineKeyboardButton("« Back",      callback_data=f"np_{chat_id}"),
    ])
    return InlineKeyboardMarkup(rows)


def audio_effects_buttons(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 Bass Boost", callback_data=f"fx_bassboost_{chat_id}"),
            InlineKeyboardButton("🌙 Nightcore",  callback_data=f"fx_nightcore_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🐢 Slow Mode",  callback_data=f"fx_slowmode_{chat_id}"),
            InlineKeyboardButton("🌊 Reverb",     callback_data=f"fx_reverb_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🎧 3D Audio",   callback_data=f"fx_3d_{chat_id}"),
            InlineKeyboardButton("🎤 Karaoke",    callback_data=f"fx_karaoke_{chat_id}"),
        ],
        [
            InlineKeyboardButton("🔈 Loud",       callback_data=f"fx_loud_{chat_id}"),
            InlineKeyboardButton("✅ Clear FX",   callback_data=f"fx_clear_{chat_id}"),
        ],
        [InlineKeyboardButton("« Back", callback_data=f"np_{chat_id}")],
    ])


def start_buttons(bot_username: str, support_channel: str, support_chat: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add Me to Group",
                url=(
                    f"https://t.me/{bot_username}?startgroup=true"
                    f"&admin=manage_voice_chats+invite_users"
                )
            ),
        ],
        [
            InlineKeyboardButton("📖 Help",     callback_data="help_main"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_self"),
        ],
        [
            InlineKeyboardButton("📢 Updates",  url=support_channel),
            InlineKeyboardButton("💬 Support",  url=support_chat),
        ],
    ])


def help_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Play",    callback_data="help_play"),
            InlineKeyboardButton("⚙️ Admin",   callback_data="help_admin"),
        ],
        [
            InlineKeyboardButton("🎚 Effects", callback_data="help_effects"),
            InlineKeyboardButton("📋 Queue",   callback_data="help_queue"),
        ],
        [
            InlineKeyboardButton("🔧 Owner",   callback_data="help_owner"),
            InlineKeyboardButton("📊 Stats",   callback_data="help_stats"),
        ],
        [InlineKeyboardButton("« Back", callback_data="help_main")],
    ])


def close_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✖ Close", callback_data="close")]])
