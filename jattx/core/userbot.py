"""
jattx/core/userbot.py
Multi-session userbot with round-robin load balancing.
Fixed: cache_duration removed, compatible with py-tgcalls 2.0.0
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
        # Fixed: removed cache_duration=0
        self.pytgcalls = PyTgCalls(self.client)
        self.name: str = ""
        self.username: str = ""
        self.id: int = 0

    async def start(self):
        await self.client.start()
        me = await self.client.get_me()
        self.id = me.id
        self.name = (
            (me.first_name or "")
            + (" " + me.last_name if me.last_name else "")
        )
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
        self._rr = 0

    async def start(self):
        sessions = [
            s for s in [
                config.SESSION1,
                config.SESSION2,
                config.SESSION3
            ] if s
        ]
        if not sessions:
            raise SystemExit(
                "❌ At least one SESSION string is required."
            )

        for i, sess in enumerate(sessions, 1):
            try:
                ass = _Assistant(sess, i)
                await ass.start()
                self.assistants.append(ass)
                from jattx import logger
                logger.info(
                    f"  Assistant #{i}: "
                    f"{ass.name} (@{ass.username})"
                )
            except Exception as e:
                from jattx import logger
                logger.error(
                    f"  Assistant #{i} failed to start: {e}"
                )

        if not self.assistants:
            raise SystemExit(
                "❌ No assistants could start. "
                "Check your SESSION string."
            )

    def get_client(
        self, chat_id: int | None = None
    ) -> _Assistant:
        if not self.assistants:
            raise RuntimeError("No assistants started yet.")
        self._rr = (self._rr + 1) % len(self.assistants)
        return self.assistants[self._rr]

    async def exit(self):
        for a in self.assistants:
            await a.stop()
