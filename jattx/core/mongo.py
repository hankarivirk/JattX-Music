"""
jattx/core/mongo.py
MongoDB wrapper — groups, playlists, sudoers, blacklist, settings, active calls.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import config


class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(config.MONGO_URL)
        db = self.client["JattXMusic"]

        self.groups     = db["groups"]
        self.playlists  = db["playlists"]
        self.sudoers    = db["sudoers"]
        self.blacklist  = db["blacklist"]
        self.active     = db["active_calls"]
        self.settings   = db["settings"]
        self.authusers  = db["authusers"]
        self.gbans      = db["gbans"]

    async def close(self):
        self.client.close()

    # ── Group settings ────────────────────────────────────────────────
    async def get_group(self, chat_id: int) -> dict:
        doc = await self.groups.find_one({"_id": chat_id})
        return doc or {}

    async def set_group(self, chat_id: int, **kwargs):
        await self.groups.update_one({"_id": chat_id}, {"$set": kwargs}, upsert=True)

    async def get_lang(self, chat_id: int) -> str:
        doc = await self.get_group(chat_id)
        return doc.get("lang", config.LANG_CODE)

    async def set_lang(self, chat_id: int, lang: str):
        await self.set_group(chat_id, lang=lang)

    # ── Active voice chat tracking ────────────────────────────────────
    async def get_assistant(self, chat_id: int):
        from jattx import userbot
        doc = await self.active.find_one({"_id": chat_id})
        if doc and "assistant_idx" in doc:
            idx = doc["assistant_idx"]
            if idx < len(userbot.assistants):
                return userbot.assistants[idx]
        return userbot.get_client(chat_id)

    async def set_active(self, chat_id: int, assistant_idx: int):
        await self.active.update_one(
            {"_id": chat_id},
            {"$set": {"active": True, "paused": False, "loop": 0,
                      "assistant_idx": assistant_idx}},
            upsert=True,
        )

    async def remove_call(self, chat_id: int):
        await self.active.delete_one({"_id": chat_id})

    async def playing(self, chat_id: int, paused: bool):
        await self.active.update_one({"_id": chat_id}, {"$set": {"paused": paused}})

    async def is_paused(self, chat_id: int) -> bool:
        doc = await self.active.find_one({"_id": chat_id})
        return (doc or {}).get("paused", False)

    async def get_loop(self, chat_id: int) -> int:
        doc = await self.active.find_one({"_id": chat_id})
        return (doc or {}).get("loop", 0)

    async def set_loop(self, chat_id: int, count: int):
        await self.active.update_one({"_id": chat_id}, {"$set": {"loop": count}}, upsert=True)

    async def get_all_active(self) -> list[int]:
        return [d["_id"] async for d in self.active.find({"active": True})]

    # ── Authorized users per group ────────────────────────────────────
    async def get_authusers(self, chat_id: int) -> list[int]:
        doc = await self.authusers.find_one({"_id": chat_id})
        return (doc or {}).get("users", [])

    async def add_authuser(self, chat_id: int, user_id: int):
        await self.authusers.update_one(
            {"_id": chat_id}, {"$addToSet": {"users": user_id}}, upsert=True
        )

    async def remove_authuser(self, chat_id: int, user_id: int):
        await self.authusers.update_one(
            {"_id": chat_id}, {"$pull": {"users": user_id}}
        )

    # ── Sudoers ───────────────────────────────────────────────────────
    async def get_sudoers(self) -> list[int]:
        doc = await self.sudoers.find_one({"_id": "sudoers"})
        return (doc or {}).get("users", [])

    async def add_sudo(self, user_id: int):
        await self.sudoers.update_one(
            {"_id": "sudoers"}, {"$addToSet": {"users": user_id}}, upsert=True
        )

    async def remove_sudo(self, user_id: int):
        await self.sudoers.update_one(
            {"_id": "sudoers"}, {"$pull": {"users": user_id}}
        )

    # ── Global bans ───────────────────────────────────────────────────
    async def gban(self, user_id: int, reason: str = ""):
        await self.gbans.update_one(
            {"_id": user_id}, {"$set": {"reason": reason}}, upsert=True
        )

    async def ungban(self, user_id: int):
        await self.gbans.delete_one({"_id": user_id})

    async def is_gbanned(self, user_id: int) -> bool:
        return bool(await self.gbans.find_one({"_id": user_id}))

    # ── Blacklist chats ───────────────────────────────────────────────
    async def blacklist_chat(self, chat_id: int):
        await self.blacklist.update_one({"_id": chat_id}, {"$set": {}}, upsert=True)

    async def unblacklist_chat(self, chat_id: int):
        await self.blacklist.delete_one({"_id": chat_id})

    async def is_blacklisted(self, chat_id: int) -> bool:
        return bool(await self.blacklist.find_one({"_id": chat_id}))

    # ── Play mode (inline / direct) ───────────────────────────────────
    async def get_playmode(self, chat_id: int) -> str:
        doc = await self.get_group(chat_id)
        return doc.get("playmode", "inline")

    async def set_playmode(self, chat_id: int, mode: str):
        await self.set_group(chat_id, playmode=mode)

    # ── Saved playlists ───────────────────────────────────────────────
    async def save_playlist(self, user_id: int, name: str, tracks: list):
        await self.playlists.update_one(
            {"_id": user_id, "name": name},
            {"$set": {"tracks": tracks}},
            upsert=True,
        )

    async def get_playlist(self, user_id: int, name: str) -> list:
        doc = await self.playlists.find_one({"_id": user_id, "name": name})
        return (doc or {}).get("tracks", [])

    async def list_playlists(self, user_id: int) -> list[str]:
        return [d["name"] async for d in self.playlists.find({"_id": user_id})]

    async def delete_playlist(self, user_id: int, name: str):
        await self.playlists.delete_one({"_id": user_id, "name": name})

    # ── Stats ─────────────────────────────────────────────────────────
    async def total_groups(self) -> int:
        return await self.groups.count_documents({})

    async def total_active(self) -> int:
        return await self.active.count_documents({"active": True})
