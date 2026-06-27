"""
jattx/core/userbot.py
Multi-session userbot (up to 3 assistants) with round-robin load balancing.
Auto-detects assistant name/username just like the bot.
"""

import asyncio
from pyrogram import Client
from pytgcalls import PyTgCalls
from config import config


class _Assistant:
    def __init__(self, session: str, index: int):
        self.client = Client(
            name=f"JattXAssistant{index}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=session,
        )
        self.pytgcalls = PyTgCalls(self.client, cache_duration=0)
        self.name: str = ""
        self.username: str = ""
        self.id: int = 0

    async def start(self):
        await self.client.start()
        me = await self.client.get_me()
        self.id       = me.id
        self.name     = (me.first_name or "") + (" " + me.last_name if me.last_name else "")
        self.username = me.username or ""
        await self.pytgcalls.start()

    async def stop(self):
        try:
            await self.pytgcalls.stop()
            await self.client.stop()
        except Exception:
            pass


class Userbot:
    def __init__(self):
        self.assistants: list[_Assistant] = []
        self._rr = 0                          # round-robin index

    async def start(self):
        sessions = [s for s in [config.SESSION1, config.SESSION2, config.SESSION3] if s]
        if not sessions:
            raise SystemExit("❌ At least one SESSION string is required.")

        for i, sess in enumerate(sessions, 1):
            ass = _Assistant(sess, i)
            await ass.start()
            self.assistants.append(ass)

        from jattx import logger
        for a in self.assistants:
            logger.info(f"  Assistant #{self.assistants.index(a)+1}: {a.name} (@{a.username})")

    def get_client(self, chat_id: int | None = None) -> _Assistant:
        """Return an assistant using round-robin (ignores chat_id for now)."""
        if not self.assistants:
            raise RuntimeError("No assistants started yet.")
        self._rr = (self._rr + 1) % len(self.assistants)
        return self.assistants[self._rr]

    async def exit(self):
        for a in self.assistants:
            await a.stop()
