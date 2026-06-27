"""jattx/plugins/tools/misc.py — Ping, uptime, active VC, lyrics, speedtest."""
import asyncio
import time

from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, boot_time, call, config, db
from jattx.helpers._utilities import seconds_to_str


@app.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    t1  = time.monotonic()
    msg = await message.reply_text("🏓 Pong!")
    ms  = round((time.monotonic() - t1) * 1000, 2)
    caption = (
        f"🏓 **Pong!**\n"
        f"📡 Latency : **{ms} ms**\n"
        f"⚡ Bot     : **{config.BOT_NAME}**"
    )
    await msg.delete()
    # PING_IMG is always a URL from config/env — never a local .jpg path
    try:
        await message.reply_photo(photo=config.PING_IMG, caption=caption)
    except Exception:
        await message.reply_text(caption)


@app.on_message(filters.command("uptime"))
async def uptime_cmd(client: Client, message: Message):
    uptime = seconds_to_str(int(time.time() - boot_time))
    await message.reply_text(
        f"⏱ **Uptime:** `{uptime}`\n"
        f"⚡ Bot: **{config.BOT_NAME}**"
    )


@app.on_message(filters.command("activevc"))
async def activevc_cmd(client: Client, message: Message):
    active_ids = await db.get_all_active()
    if not active_ids:
        return await message.reply_text("😴 No active voice chats.")
    lines = [f"🎙 **Active Voice Chats ({len(active_ids)})**\n"]
    for cid in active_ids[:20]:
        try:
            chat = await client.get_chat(cid)
            lines.append(f"• {chat.title} (`{cid}`)")
        except Exception:
            lines.append(f"• `{cid}`")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command("lyrics"))
async def lyrics_cmd(client: Client, message: Message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text("❓ Usage: `/lyrics <song name>`")
    wait = await message.reply_text("🔍 Searching lyrics…")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://api.lyrics.ovh/v1/{query.replace(' ', '/')}",
                timeout=aiohttp.ClientTimeout(total=8)
            ) as r:
                data = await r.json()
        lyrics = data.get("lyrics", "")
        if not lyrics:
            return await wait.edit_text("❌ Lyrics not found.")
        # Trim to Telegram limit
        if len(lyrics) > 3800:
            lyrics = lyrics[:3800] + "\n\n… (truncated)"
        await wait.edit_text(f"🎵 **Lyrics**\n\n{lyrics}")
    except Exception:
        await wait.edit_text("❌ Failed to fetch lyrics.")


@app.on_message(filters.command(["speed", "speedtest"]))
async def speedtest_cmd(client: Client, message: Message):
    from jattx.helpers._admins import sudo_only as _check
    if message.from_user.id not in [config.OWNER_ID, *(await db.get_sudoers())]:
        return await message.reply_text("❌ Sudo access required.")
    wait = await message.reply_text("⚡ Running speed test…")
    try:
        proc = await asyncio.create_subprocess_shell(
            "python3 -c \"import speedtest; s=speedtest.Speedtest(); s.download(); s.upload(); r=s.results.dict(); print(f'⬇️ {r[\\\"download\\\"]/1e6:.2f} Mbps  ⬆️ {r[\\\"upload\\\"]/1e6:.2f} Mbps  📍 {r[\\\"server\\\"][\\\"country\\\"]}'  )\"",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        await wait.edit_text(f"🌐 **Speed Test**\n\n{out.decode(errors='replace').strip()}")
    except Exception as e:
        await wait.edit_text(f"❌ Speed test failed: {e}")


@app.on_message(filters.command("lang") & filters.group)
async def lang_cmd(client: Client, message: Message):
    from jattx.helpers._admins import is_auth
    if not await is_auth(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admins only.")
    args = message.command[1:]
    if not args:
        cur = await db.get_lang(message.chat.id)
        return await message.reply_text(f"🌍 Current language: `{cur}`")
    await db.set_lang(message.chat.id, args[0].lower())
    await message.reply_text(f"✅ Language set to `{args[0].lower()}`.")
