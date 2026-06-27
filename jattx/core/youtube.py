"""
jattx/core/youtube.py
Full YouTube engine: search, YT Music search, download (audio+video),
playlist fetch, auto-mix, PO token support, cookie rotation, cache cleanup.
"""

import os
import re
import glob
import shlex
import asyncio
import random
import aiohttp
import yt_dlp
from pathlib import Path
from typing import Callable

from py_yt import VideosSearch
from jattx import logger
from jattx.helpers._dataclass import Track
from jattx.helpers._utilities import to_seconds, seconds_to_str

MAX_DOWNLOADS   = 20
MAX_CACHE_MB    = 300
_AUDIO_EXTS     = ("webm", "opus", "m4a", "mp3")
_YT_ID_RE       = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _parse_extra_args(raw: str) -> dict:
    opts, tokens, i = {}, shlex.split(raw) if raw else [], 0
    while i < len(tokens):
        t = tokens[i]
        if t == "--impersonate"     and i + 1 < len(tokens): opts["impersonate"]      = tokens[i + 1]; i += 2
        elif t == "--check-formats":  opts["check_formats"]  = "selected"; i += 1
        elif t == "-4":               opts["source_address"] = "0.0.0.0";  i += 1
        elif t == "-6":               opts["source_address"] = "::";       i += 1
        else: i += 1
    return opts


class YouTube:
    def __init__(self):
        self.base       = "https://www.youtube.com/watch?v="
        self.cookies: list[str] = []
        self.checked    = False
        self.warned     = False
        self.sem        = asyncio.Semaphore(6)
        self.cookie_dir = "jattx/cookies"

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|(?:PL|RD|RDCLAK|UU|FL|OL)[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=|[A-Za-z0-9_-]{11}))\S*"
        )
        self._playlist_re = re.compile(r"(?:list=)((?:PL|RD|RDCLAK|UU|FL|OL)[A-Za-z0-9_-]+)")

    # ── Cookie helpers ────────────────────────────────────────────────
    def get_cookie(self) -> str | None:
        if not self.checked:
            os.makedirs(self.cookie_dir, exist_ok=True)
            for f in os.listdir(self.cookie_dir):
                if f.endswith(".txt"):
                    path = f"{self.cookie_dir}/{f}"
                    try:
                        line = open(path, errors="ignore").readline().strip()
                        if "Netscape" in line or line.startswith("#"):
                            self.cookies.append(path)
                    except Exception:
                        pass
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("No cookies found; YouTube downloads may fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]):
        os.makedirs(self.cookie_dir, exist_ok=True)
        async with aiohttp.ClientSession() as s:
            for url in urls:
                name = url.split("/")[-1]
                async with s.get(f"https://batbin.me/raw/{name}") as r:
                    r.raise_for_status()
                    text = await r.text()
                    if "Netscape HTTP Cookie File" not in text:
                        text = "# Netscape HTTP Cookie File\n" + text
                    with open(f"{self.cookie_dir}/{name}.txt", "w") as fw:
                        fw.write(text)
        self.checked = False  # force re-scan

    # ── URL validators ────────────────────────────────────────────────
    def valid(self, url: str)        -> bool: return bool(self.regex.match(url))
    def invalid(self, url: str)      -> bool: return bool(self.iregex.match(url))
    def is_playlist(self, url: str)  -> bool: return bool(self._playlist_re.search(url))
    def is_yt_id(self, vid: str)     -> bool: return bool(_YT_ID_RE.match(vid))

    # ── Base yt-dlp opts ─────────────────────────────────────────────
    def _base_opts(self) -> dict:
        from config import config
        cookie = self.get_cookie()
        extra  = _parse_extra_args(config.YT_DLP_EXTRA_ARGS)
        opts = {
            "outtmpl":                    "downloads/%(id)s.%(ext)s",
            "quiet":                      True,
            "noplaylist":                 True,
            "geo_bypass":                 True,
            "no_warnings":                True,
            "overwrites":                 False,
            "nocheckcertificate":         True,
            "cookiefile":                 cookie,
            "concurrent_fragment_downloads": 5,
            "buffersize":                 32768,
            "http_chunk_size":            10_485_760,
            "socket_timeout":             15,
            "retries":                    5,
            "fragment_retries":           5,
            "noresizebuffer":             True,
            "file_access_retries":        3,
            **extra,
        }
        if config.YT_PO_TOKEN and config.YT_VISITOR_DATA:
            opts["extractor_args"] = {
                "youtube": {
                    "po_token":     [f"web+{config.YT_PO_TOKEN}"],
                    "visitor_data": [config.YT_VISITOR_DATA],
                }
            }
        return opts

    # ── Cache cleanup ─────────────────────────────────────────────────
    def _cleanup(self):
        files = sorted(glob.glob("downloads/*"), key=os.path.getctime)
        if len(files) > MAX_DOWNLOADS:
            for f in files[:len(files) - MAX_DOWNLOADS]:
                try: os.remove(f)
                except Exception: pass
            files = sorted(glob.glob("downloads/*"), key=os.path.getctime)
        total_mb = sum(os.path.getsize(f) for f in files if os.path.isfile(f)) / 1_048_576
        while total_mb > MAX_CACHE_MB and files:
            try:
                total_mb -= os.path.getsize(files[0]) / 1_048_576
                os.remove(files[0])
            except Exception:
                pass
            files.pop(0)

    # ── Search ────────────────────────────────────────────────────────
    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            results = await VideosSearch(query, limit=1, with_live=False).next()
        except Exception:
            return None
        if results and results.get("result"):
            d = results["result"][0]
            return Track(
                id=d.get("id", ""),
                title=(d.get("title") or "Unknown")[:55],
                channel_name=d.get("channel", {}).get("name", ""),
                duration=d.get("duration", "0:00"),
                duration_sec=to_seconds(d.get("duration")),
                thumbnail=(d.get("thumbnails") or [{}])[-1].get("url", "").split("?")[0],
                url=d.get("link", ""),
                view_count=d.get("viewCount", {}).get("short", ""),
                message_id=m_id,
                video=video,
            )
        return None

    async def ytmusic_search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        """Prefer YouTube Music results over regular YouTube."""
        opts = {**self._base_opts(), "extract_flat": True, "skip_download": True,
                "default_search": "https://music.youtube.com/search?q="}

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    entries = (info or {}).get("entries", [])
                    return entries[0] if entries else None
                except Exception:
                    return None

        data = await asyncio.to_thread(_run)
        if not data or not data.get("id"):
            return await self.search(query, m_id, video)
        dur = int(data.get("duration") or 0)
        return Track(
            id=data["id"],
            title=(data.get("title") or "Unknown")[:55],
            channel_name=data.get("uploader") or data.get("channel") or "",
            duration=seconds_to_str(dur),
            duration_sec=dur,
            thumbnail=data.get("thumbnail") or "",
            url=f"https://music.youtube.com/watch?v={data['id']}",
            view_count=str(data.get("view_count") or ""),
            message_id=m_id,
            video=video,
        )

    # ── Playlist fetch ────────────────────────────────────────────────
    async def playlist(
        self, limit: int, user: str, url: str, video: bool,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> list[Track]:
        opts = {**self._base_opts(), "extract_flat": "in_playlist",
                "skip_download": True, "ignoreerrors": True,
                "playlistend": limit if limit > 0 else None}

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    return (info or {}).get("entries", [])
                except Exception:
                    return []

        entries = await asyncio.to_thread(_run)
        total   = len([e for e in entries if e])
        tracks  = []

        for i, e in enumerate(entries):
            if not e or not e.get("id"):
                continue
            dur = int(e.get("duration") or 0)
            tracks.append(Track(
                id=e["id"],
                title=(e.get("title") or "Unknown")[:55],
                channel_name=e.get("uploader") or e.get("channel") or "",
                duration=seconds_to_str(dur),
                duration_sec=dur,
                thumbnail=e.get("thumbnail") or "",
                url=f"https://www.youtube.com/watch?v={e['id']}",
                user=user, video=video,
            ))
            if progress_cb and (i + 1) % 10 == 0:
                try: await progress_cb(len(tracks), total)
                except Exception: pass

        return tracks

    # ── Auto-mix ──────────────────────────────────────────────────────
    async def mix(self, video_id: str, user: str, video: bool, limit: int = 25) -> list[Track]:
        if not self.is_yt_id(video_id):
            return []
        tracks = await self.playlist(
            limit, user,
            f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}",
            video,
        )
        if not tracks:
            t = await self.search(video_id, 0, video=video)
            return [t] if t else []
        return tracks

    # ── Download ──────────────────────────────────────────────────────
    async def download(self, video_id: str, video: bool = False) -> str | None:
        os.makedirs("downloads", exist_ok=True)
        url = self.base + video_id

        # Cache hit?
        if video:
            c = f"downloads/{video_id}.mp4"
            if Path(c).exists(): return c
        else:
            for ext in _AUDIO_EXTS:
                c = f"downloads/{video_id}.{ext}"
                if Path(c).exists(): return c

        opts = self._base_opts()
        if video:
            opts["format"] = (
                "(bestvideo[height<=?720][width<=?1280][ext=mp4]"
                "/bestvideo[height<=?720])"
                "+(bestaudio[ext=m4a]/bestaudio)/best"
            )
            opts["merge_output_format"] = "mp4"
        else:
            opts["format"] = "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio"

        def _run() -> str | None:
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info) if info else None
                except Exception as e:
                    logger.warning(f"Download failed [{video_id}]: {e}")
                    return None

        async with self.sem:
            result = await asyncio.to_thread(_run)

        self._cleanup()
        return result
