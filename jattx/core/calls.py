"""
jattx/core/calls.py
Voice chat engine — play, pause, resume, seek, skip, stop, loop,
audio effects, Now Playing card (thumbnail from song art, not a file),
autoplay (auto-fetch related tracks when queue empties).
"""

import asyncio
from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram.errors import ChatSendMediaForbidden, MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types

from jattx import app, config, db, logger, queue, thumb, userbot
from jattx.helpers._dataclass import Track, Media
from jattx.helpers._buttons import now_playing_buttons


# ── Audio effect FFmpeg filter chains ─────────────────────────────────────────
EFFECT_FILTERS: dict[str, str] = {
    "bassboost":  "bass=g=20,dynaudnorm=f=200",
    "nightcore":  "atempo=1.25,asetrate=44100*1.25",
    "slowmode":   "atempo=0.85",
    "reverb":     "aecho=0.8:0.9:1000:0.3",
    "3d":         "apulsator=hz=0.125",
    "karaoke":    "pan=stereo|c0=c0-c1|c1=c1-c0",
    "loud":       "dynaudnorm=f=200",
    "clear":      "",
}


class JattXCall:
    def __init__(self):
        self._effect: dict[int, str] = {}

    # ── Internal helpers ──────────────────────────────────────────────
    async def _client(self, chat_id: int):
        return await db.get_assistant(chat_id)

    def _mk_stream(
        self, media: "Track | Media", seek: int = 0, effect: str = ""
    ) -> types.MediaStream:
        filt    = EFFECT_FILTERS.get(effect, "")
        ff_pre  = f"-ss {seek}" if seek > 1 else ""
        ff_post = f'-af "{filt}"' if filt else ""
        ffmpeg  = " ".join(filter(None, [ff_pre, ff_post])) or None
        return types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if getattr(media, "video", False)
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=ffmpeg,
        )

    # ── Playback controls ─────────────────────────────────────────────
    async def pause(self, chat_id: int) -> bool:
        client = await self._client(chat_id)
        await db.playing(chat_id, paused=True)
        try:
            return await client.pytgcalls.pause(chat_id)
        except Exception:
            return False

    async def resume(self, chat_id: int) -> bool:
        client = await self._client(chat_id)
        await db.playing(chat_id, paused=False)
        try:
            return await client.pytgcalls.resume(chat_id)
        except Exception:
            return False

    async def stop(self, chat_id: int):
        client = await self._client(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)
        self._effect.pop(chat_id, None)
        try:
            await client.pytgcalls.leave_call(chat_id)
        except Exception:
            pass

    async def mute(self, chat_id: int):
        client = await self._client(chat_id)
        try:
            await client.pytgcalls.mute(chat_id)
        except Exception:
            pass

    async def unmute(self, chat_id: int):
        client = await self._client(chat_id)
        try:
            await client.pytgcalls.unmute(chat_id)
        except Exception:
            pass

    async def seek(self, chat_id: int, seek_time: int):
        track = queue.current(chat_id)
        if not track:
            return
        client = await self._client(chat_id)
        stream = self._mk_stream(
            track, seek=seek_time, effect=self._effect.get(chat_id, "")
        )
        await client.pytgcalls.change_stream(chat_id, stream)

    async def set_effect(self, chat_id: int, effect: str) -> bool:
        if effect not in EFFECT_FILTERS:
            return False
        self._effect[chat_id] = effect
        track = queue.current(chat_id)
        if track:
            client = await self._client(chat_id)
            stream = self._mk_stream(track, effect=effect)
            try:
                await client.pytgcalls.change_stream(chat_id, stream)
            except Exception:
                pass
        return True

    # ── Main play ─────────────────────────────────────────────────────
    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: "Track | Media",
        seek_time: int = 0,
    ):
        client = await self._client(chat_id)
        effect = self._effect.get(chat_id, "")

        if not getattr(media, "file_path", None):
            await message.reply_text(
                f"❌ Failed to get file.\nSupport: {config.SUPPORT_CHAT}"
            )
            return await self.play_next(chat_id)

        stream = self._mk_stream(media, seek=seek_time, effect=effect)

        # ── Generate thumbnail from song art (URL-based, not a local file) ──
        _thumb_url: str | None = None
        if config.THUMB_GEN and isinstance(media, Track):
            try:
                # thumb.generate returns a local path for the generated card
                generated = await thumb.generate(media)
                _thumb_url = generated  # local file path → send as photo
            except Exception:
                _thumb_url = None

        # If thumbnail generation failed, use the raw song thumbnail URL directly
        if not _thumb_url and isinstance(media, Track) and media.thumbnail:
            _thumb_url = media.thumbnail   # ← this is always a URL, never a .jpg file

        try:
            await client.pytgcalls.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
        except ConnectionNotFound:
            try:
                await client.pytgcalls.join_group_call(
                    chat_id=chat_id,
                    stream=stream,
                    config=types.GroupCallConfig(auto_start=False),
                )
            except Exception as e:
                logger.error(f"JoinGroupCall failed [{chat_id}]: {e}")
                return
        except Exception as e:
            logger.error(f"Play failed [{chat_id}]: {e}")
            return

        await db.set_active(chat_id, userbot.assistants.index(client))

        # ── Build Now Playing caption ─────────────────────────────────
        title     = getattr(media, "title", "Unknown")
        dur       = getattr(media, "duration", "∞")
        channel   = getattr(media, "channel_name", "")
        requester = getattr(media, "user", "")
        ap_on     = config.is_autoplay(chat_id)

        caption = (
            f"🎵 **Now Playing**\n\n"
            f"**{title}**\n"
            f"┌ 🎤 {channel}\n"
            f"├ ⏱ {dur}\n"
            f"├ 👤 {requester}\n"
            f"└ 🔄 AutoPlay: {'✅ ON' if ap_on else '❌ OFF'}\n\n"
            f"⚡ **{config.BOT_NAME}**"
        )
        buttons = now_playing_buttons(chat_id, autoplay=ap_on)

        # ── Send Now Playing — photo is always a URL, NEVER a .jpg attachment ─
        try:
            if _thumb_url:
                await message.reply_photo(
                    photo=_thumb_url,
                    caption=caption,
                    reply_markup=buttons,
                )
            else:
                # Fallback: text-only NP card
                await message.reply_text(caption, reply_markup=buttons)
        except (ChatSendMediaForbidden, MessageIdInvalid):
            try:
                await message.reply_text(caption, reply_markup=buttons)
            except Exception:
                pass

    # ── Play next / Autoplay refill ───────────────────────────────────
    async def play_next(self, chat_id: int):
        # Loop handling
        loop = await db.get_loop(chat_id)
        if loop > 0:
            track = queue.current(chat_id)
            if track:
                await db.set_loop(chat_id, loop - 1)
                from jattx import yt
                track.file_path = await yt.download(track.id, video=track.video)
                return

        nxt = queue.pop(chat_id)

        # ── Autoplay: refill queue from related tracks if empty ───────
        if not nxt and config.is_autoplay(chat_id):
            nxt = await self._autoplay_refill(chat_id)

        if not nxt:
            if config.AUTO_END:
                await self.stop(chat_id)
            return

        from jattx import yt
        nxt.file_path = await yt.download(nxt.id, video=nxt.video)
        if not nxt.file_path:
            return await self.play_next(chat_id)

        try:
            msg = await app.send_message(
                config.LOGGER_ID,
                f"▶️ Auto-playing: **{nxt.title}**"
            )
            await self.play_media(chat_id, msg, nxt)
        except Exception as e:
            logger.warning(f"play_next send failed [{chat_id}]: {e}")

    # ── Autoplay refill logic ─────────────────────────────────────────
    async def _autoplay_refill(self, chat_id: int) -> "Track | None":
        """
        Fetch related songs based on the last played track.
        Adds AUTOPLAY_LIMIT songs to queue, returns the first one.
        """
        from jattx import yt

        last = queue.current(chat_id)
        if not last or not getattr(last, "id", None):
            return None

        logger.info(f"[AutoPlay] Refilling queue for {chat_id} from: {last.title}")

        try:
            related = await yt.mix(
                last.id,
                user="🔄 AutoPlay",
                video=getattr(last, "video", False),
                limit=config.AUTOPLAY_LIMIT + 1,  # +1 because first = current
            )
        except Exception as e:
            logger.warning(f"[AutoPlay] mix fetch failed: {e}")
            return None

        if not related:
            return None

        # Skip the first result if it's the same as current track
        filtered = [t for t in related if t.id != last.id][:config.AUTOPLAY_LIMIT]
        if not filtered:
            return None

        # Queue all except the first (which we play now)
        for t in filtered[1:]:
            queue.add(chat_id, t)

        logger.info(
            f"[AutoPlay] Added {len(filtered)} related tracks for {chat_id}"
        )
        return filtered[0]

    # ── Fetch suggestions (for inline button) ─────────────────────────
    async def get_suggestions(self, chat_id: int) -> list:
        """
        Return up to 5 related Track objects based on currently playing song.
        Used by the 🎵 Suggest button.
        """
        from jattx import yt

        current = queue.current(chat_id)
        if not current or not getattr(current, "id", None):
            return []

        try:
            related = await yt.mix(
                current.id,
                user="Suggestion",
                video=False,
                limit=6,
            )
        except Exception:
            return []

        # Exclude current track
        return [t for t in related if t.id != current.id][:5]
