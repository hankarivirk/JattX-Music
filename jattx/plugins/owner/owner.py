"""
jattx/plugins/owner/owner.py
Owner-only commands:
  /botinfo   — Full deployment info (name, username, IDs, sessions)
  /broadcast — Message all groups
  /eval      — Run Python code
  /shell     — Run shell command
  /stats     — Bot statistics
  /sudo      — Add sudo user
  /unsudo    — Remove sudo user
  /gban      — Global ban
  /ungban    — Remove global ban
  /blacklist — Blacklist group
  /maintenance on/off
  /restart
"""

import asyncio
import traceback
import time
from io import StringIO
from contextlib import redirect_stdout

from pyrogram import Client, filters
from pyrogram.types import Message

from jattx import app, boot_time, call, config, db, queue, userbot
from jattx.helpers._admins import owner_only, sudo_only
from jattx.helpers._utilities import human_size, seconds_to_str


# ── /botinfo ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command(["botinfo", "info"]) & filters.private)
@owner_only
async def botinfo_cmd(client: Client, message: Message):
    assistants = "\n".join(
        f"  #{i+1}: {a.name} (@{a.username}) | ID: {a.id}"
        for i, a in enumerate(userbot.assistants)
    ) or "  None"

    uptime_sec = int(time.time() - boot_time)
    uptime_str = seconds_to_str(uptime_sec)

    text = (
        f"╔══════════════════════════════════╗\n"
        f"║    ⚡ {config.BOT_NAME} — Deploy Info\n"
        f"╠══════════════════════════════════╣\n"
        f"║  🤖 Username : @{config.BOT_USERNAME}\n"
        f"║  🆔 Bot ID   : `{config.BOT_ID}`\n"
        f"║  👑 Owner    : `{config.OWNER_ID}`\n"
        f"║  📋 Logger   : `{config.LOGGER_ID}`\n"
        f"╠══════════════════════════════════╣\n"
        f"║  🕒 Uptime   : {uptime_str}\n"
        f"║  🎙 Assistants:\n"
        f"{assistants}\n"
        f"╠══════════════════════════════════╣\n"
        f"║  🔗 Support  : {config.SUPPORT_CHAT}\n"
        f"║  📢 Channel  : {config.SUPPORT_CHANNEL}\n"
        f"╚══════════════════════════════════╝\n\n"
        f"**Add bot to group:**\n"
        f"`https://t.me/{config.BOT_USERNAME}?startgroup=true"
        f"&admin=manage_voice_chats+invite_users`"
    )
    await message.reply_text(text)


# ── /stats ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("stats"))
@sudo_only
async def stats_cmd(client: Client, message: Message):
    groups  = await db.total_groups()
    active  = await db.total_active()
    sudoers = await db.get_sudoers()
    uptime  = seconds_to_str(int(time.time() - boot_time))

    text = (
        f"📊 **{config.BOT_NAME} Statistics**\n\n"
        f"🏠 Total Groups : **{groups}**\n"
        f"🎙 Active VCs   : **{active}**\n"
        f"👥 Sudoers      : **{len(sudoers)}**\n"
        f"🕒 Uptime       : **{uptime}**\n"
        f"🤖 Assistants   : **{len(userbot.assistants)}**"
    )
    await message.reply_text(text)


# ── /broadcast ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("broadcast"))
@owner_only
async def broadcast_cmd(client: Client, message: Message):
    text = " ".join(message.command[1:]).strip()
    reply = message.reply_to_message
    if not text and not reply:
        return await message.reply_text("❓ Usage: `/broadcast <message>` or reply to a message.")

    chats = [d["_id"] async for d in db.groups.find({})]
    sent = failed = 0

    wait = await message.reply_text(f"📢 Broadcasting to {len(chats)} groups…")

    for chat_id in chats:
        try:
            if reply:
                await reply.copy(chat_id)
            else:
                await client.send_message(chat_id, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await wait.edit_text(f"✅ Broadcast done.\n✔ Sent: {sent}\n✖ Failed: {failed}")


# ── /maintenance ──────────────────────────────────────────────────────────────
@app.on_message(filters.command("maintenance"))
@owner_only
async def maintenance_cmd(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        state = "ON" if config.MAINTENANCE else "OFF"
        return await message.reply_text(f"🛠 Maintenance is currently **{state}**.")
    if args[0].lower() == "on":
        config.MAINTENANCE = True
        await message.reply_text("🛠 Maintenance mode **ON** — bot will reject non-owner commands.")
    elif args[0].lower() == "off":
        config.MAINTENANCE = False
        await message.reply_text("✅ Maintenance mode **OFF** — bot is back to normal.")
    else:
        await message.reply_text("❓ Usage: `/maintenance on/off`")


# ── /sudo / /unsudo ───────────────────────────────────────────────────────────
@app.on_message(filters.command("sudo"))
@owner_only
async def sudo_cmd(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(message.command[1])
        except Exception: pass
    if not target:
        return await message.reply_text("❓ Reply to a user or provide username.")
    await db.add_sudo(target.id)
    await message.reply_text(f"✅ {target.mention} added to sudoers.")


@app.on_message(filters.command("unsudo"))
@owner_only
async def unsudo_cmd(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(message.command[1])
        except Exception: pass
    if not target:
        return await message.reply_text("❓ Reply to a user or provide username.")
    await db.remove_sudo(target.id)
    await message.reply_text(f"✅ {target.mention} removed from sudoers.")


# ── /gban / /ungban ───────────────────────────────────────────────────────────
@app.on_message(filters.command("gban"))
@sudo_only
async def gban_cmd(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else ""
    if not target and len(message.command) > 1:
        try: target = await client.get_users(message.command[1])
        except Exception: pass
    if not target:
        return await message.reply_text("❓ Reply or provide username.")
    await db.gban(target.id, reason)
    await message.reply_text(f"🚫 **{target.mention}** globally banned.\nReason: {reason or 'None'}")


@app.on_message(filters.command("ungban"))
@sudo_only
async def ungban_cmd(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(message.command[1])
        except Exception: pass
    if not target:
        return await message.reply_text("❓ Reply or provide username.")
    await db.ungban(target.id)
    await message.reply_text(f"✅ {target.mention} un-globally-banned.")


# ── /blacklist / /unblacklist ─────────────────────────────────────────────────
@app.on_message(filters.command("blacklist"))
@sudo_only
async def blacklist_cmd(client: Client, message: Message):
    args = message.command[1:]
    chat_id = int(args[0]) if args else message.chat.id
    await db.blacklist_chat(chat_id)
    await message.reply_text(f"🚫 Chat `{chat_id}` blacklisted.")


@app.on_message(filters.command("unblacklist"))
@sudo_only
async def unblacklist_cmd(client: Client, message: Message):
    args = message.command[1:]
    chat_id = int(args[0]) if args else message.chat.id
    await db.unblacklist_chat(chat_id)
    await message.reply_text(f"✅ Chat `{chat_id}` un-blacklisted.")


# ── /restart ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("restart"))
@owner_only
async def restart_cmd(client: Client, message: Message):
    await message.reply_text("🔄 Restarting…")
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ── /eval ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command(["eval", "ev"]))
@owner_only
async def eval_cmd(client: Client, message: Message):
    code = " ".join(message.command[1:]).strip()
    if not code and message.reply_to_message:
        code = message.reply_to_message.text or ""
    if not code:
        return await message.reply_text("❓ Provide code to evaluate.")

    buf = StringIO()
    try:
        with redirect_stdout(buf):
            exec(  # noqa: S102
                f"async def _jattx_eval():\n"
                + "\n".join(f"    {l}" for l in code.splitlines()),
                {"client": client, "message": message, "app": client,
                 "db": db, "config": config, "call": call, "queue": queue}
            )
            import sys
            result = await eval("_jattx_eval()", sys._getframe(0).f_locals)
    except Exception:
        result = traceback.format_exc()

    output = buf.getvalue() or str(result) or "Done (no output)"
    await message.reply_text(f"```\n{output[:3500]}\n```")


# ── /shell ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command(["shell", "sh"]))
@owner_only
async def shell_cmd(client: Client, message: Message):
    cmd = " ".join(message.command[1:]).strip()
    if not cmd:
        return await message.reply_text("❓ Provide a shell command.")
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = (stdout or b"(no output)").decode(errors="replace")
    except asyncio.TimeoutError:
        proc.kill()
        output = "⏰ Command timed out after 30 seconds."
    await message.reply_text(f"```\n{output[:3500]}\n```")
