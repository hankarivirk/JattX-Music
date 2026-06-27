"""
jattx/core/spotify.py
Converts Spotify track/album/playlist links → YouTube search queries.
Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in config.
"""

import re
import asyncio
import aiohttp
from jattx import logger
from config import config

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE  = "https://api.spotify.com/v1"

_TRACK_RE    = re.compile(r"spotify\.com/track/([A-Za-z0-9]+)")
_ALBUM_RE    = re.compile(r"spotify\.com/album/([A-Za-z0-9]+)")
_PLAYLIST_RE = re.compile(r"spotify\.com/playlist/([A-Za-z0-9]+)")


class Spotify:
    def __init__(self):
        self._token: str  = ""
        self._expires: float = 0.0
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _refresh_token(self):
        if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
            return
        import base64, time
        creds = base64.b64encode(
            f"{config.SPOTIFY_CLIENT_ID}:{config.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()
        s = await self._get_session()
        async with s.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {creds}"},
        ) as r:
            data = await r.json()
            self._token   = data.get("access_token", "")
            self._expires = time.time() + data.get("expires_in", 3600) - 60

    async def _headers(self) -> dict:
        import time
        if not self._token or time.time() > self._expires:
            await self._refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    async def _get(self, path: str) -> dict:
        s = await self._get_session()
        async with s.get(f"{_API_BASE}{path}", headers=await self._headers()) as r:
            return await r.json() if r.status == 200 else {}

    # ── Public helpers ────────────────────────────────────────────────────
    def is_spotify(self, url: str) -> bool:
        return "spotify.com" in url

    def link_type(self, url: str) -> str | None:
        if _TRACK_RE.search(url):    return "track"
        if _ALBUM_RE.search(url):    return "album"
        if _PLAYLIST_RE.search(url): return "playlist"
        return None

    async def track_query(self, url: str) -> str | None:
        """Return 'Artist - Title' search query for a Spotify track URL."""
        m = _TRACK_RE.search(url)
        if not m:
            return None
        data = await self._get(f"/tracks/{m.group(1)}")
        if not data:
            return None
        name    = data.get("name", "")
        artists = ", ".join(a["name"] for a in data.get("artists", []))
        return f"{artists} - {name}" if artists else name

    async def album_queries(self, url: str, limit: int = 25) -> list[str]:
        m = _ALBUM_RE.search(url)
        if not m:
            return []
        data = await self._get(f"/albums/{m.group(1)}/tracks?limit={limit}")
        items = data.get("items", [])
        return [
            f"{', '.join(a['name'] for a in t.get('artists', []))} - {t['name']}"
            for t in items if t.get("name")
        ]

    async def playlist_queries(self, url: str, limit: int = 25) -> list[str]:
        m = _PLAYLIST_RE.search(url)
        if not m:
            return []
        data  = await self._get(f"/playlists/{m.group(1)}/tracks?limit={limit}")
        items = data.get("items", [])
        out   = []
        for item in items:
            t = (item or {}).get("track")
            if not t or not t.get("name"):
                continue
            artists = ", ".join(a["name"] for a in t.get("artists", []))
            out.append(f"{artists} - {t['name']}")
        return out

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
