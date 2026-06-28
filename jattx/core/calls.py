"""jattx/core/calls.py — Fixed for your exact __init__.py"""
import asyncio
from pyrogram.errors import ChatSendMediaForbidden, MessageIdInvalid
from pyrogram.types import Message
from pytgcalls.types import MediaStream
from pytgcalls.types.stream import AudioQuality, VideoQuality

from jattx.helpers._dataclass import Track, Media
from jattx.helpers._buttons import now_playing_buttons

EFFECT_FILTERS: dict[str, str] = {
    "bassboost": "bass=g=20,dynaudnorm=f=200",
    "nightcore": "atempo=1.25,asetrate=44100*1.25",
    "slowmode":  "atempo=0.85",
    "reverb":    "aecho=0.8:0.9:1000:0.3",
    "3d":        "apulsator=hz=0.125",
    "karaoke":   "pan=stereo|c0=c0-c1|c1=c1-c0",
    "loud":      "dynaudnorm=f=200",
    "clear":     "",
}


class JattXCall:
    def __init__(self):
        self._effect: dict[int, str] = {}
        self._active: dict[int, int] = {}

    def _get_assistant(self, chat_id: int):
        """Get assistant using round robin."""
        from jattx import userbot
        idx = self._active.get(chat_id, 0)
        if not userbot.assistants:
            raise RuntimeError("No assistants available!")
        idx = idx % len(userbot.assistants)
        return userbot.assistants[idx]

    def _mk_stream(
        self,
        media: "Track | Media",
        seek: int = 0,
        effect: str = "",
    ) -> MediaStream:
        filt    = EFFECT_FILTERS.get(effect, "")
        ff_pre  = f"-ss {seek}" if seek > 1 else ""
        ff_post = f'-af "{filt}"' if filt else ""
        ffmpeg  = " ".join(filter(None, [ff_pre, ff_post])) or None

        return MediaStream(
            media_path=media.file_path,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=ffmpeg,
        )

    # ── Playback controls ──────────────────────────────────
    async def pause(self, chat_id: int) -> bool:
        try:
            assistant = self._get_assistant(chat_id)
            await assistant.pytgcalls.pause(chat_id)
            return True
        except Exception as e:
            from jattx import logger
            logger.error(f"Pause error [{chat_id}]: {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            assistant = self._get_assistant(chat_id)
            await assistant.pytgcalls.resume(chat_id)
            return True
        except Exception as e:
            from jattx import logger
            logger.error(f"Resume error [{chat_id}]: {e}")
            return False

    async def stop(self, chat_id: int):
        from jattx import db, queue
        try:
            assistant = self._get_assistant(chat_id)
            await assistant.pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        queue.clear(chat_id)
        self._effect.pop(chat_id, None)
        self._active.pop(chat_id, None)
        try:
            await db.remove_call(chat_id)
            await db.set_loop(chat_id, 0)
        except Exception:
            pass

    async def mute(self, chat_id: int):
        try:
            assistant = self._get_assistant(chat_id)
            await assistant.pytgcalls.mute(chat_id)
        except Exception:
            pass

    async def unmute(self, chat_id: int):
        try:
            assistant = self._get_assistant(chat_id)
            await assistant.pytgcalls.unmute(chat_id)
        except Exception:
            pass

    async def seek(self, chat_id: int, seek_time: int):
        from jattx import queue
        track = queue.current(chat_id)
        if not track:
            return
        try:
            assistant = self._get_assistant(chat_id)
            stream = self._mk_stream(
                track,
                seek=seek_time,
                effect=self._effect.get(chat_id, "")
            )
            await assistant.pytgcalls.change_stream(
                chat_id, stream
            )
        except Exception as e:
            from jattx import logger
            logger.error(f"Seek error [{chat_id}]: {e}")

    async def set_effect(
        self, chat_id: int, effect: str
    ) -> bool:
        from jattx import queue
        if effect not in EFFECT_FILTERS:
            return False
        self._effect[chat_id] = effect
        track = queue.current(chat_id)
        if track:
            try:
                assistant = self._get_assistant(chat_id)
                stream = self._mk_stream(track, effect=effect)
                await assistant.pytgcalls.change_stream(
                    chat_id, stream
                )
            except Exception:
                pass
        return True

    # ── Main play ──────────────────────────────────────────
    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: "Track | Media",
        seek_time: int = 0,
    ):
        from jattx import config, logger, queue, thumb, userbot

        if not getattr(media, "file_path", None):
            await message.reply_text(
                f"❌ Failed to get file.\n"
                f"Support: {config.SUPPORT_CHAT}"
            )
            return await self.play_next(chat_id)

        # Get assistant round robin
        assistant = userbot.get_client(chat_id)
        self._active[chat_id] = (
            userbot.assistants.index(assistant)
        )

        effect = self._effect.get(chat_id, "")
        stream = self._mk_stream(
            media, seek=seek_time, effect=effect
        )

        # Generate thumbnail
        _thumb_url = None
        if config.THUMB_GEN and isinstance(media, Track):
            try:
                generated = await thumb.generate(media)
                _thumb_url = generated
            except Exception:
                pass

        if (
            not _thumb_url
            and isinstance(media, Track)
            and media.thumbnail
        ):
            _thumb_url = media.thumbnail

        # Join or change stream
        try:
            await assistant.pytgcalls.join_group_call(
                chat_id, stream
            )
        except Exception:
            try:
                await assistant.pytgcalls.change_stream(
                    chat_id, stream
                )
            except Exception as e:
                logger.error(
                    f"Play failed [{chat_id}]: {e}"
                )
                return

        # Build caption
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
            f"└ 🔄 AutoPlay: "
            f"{'✅ ON' if ap_on else '❌ OFF'}\n\n"
            f"⚡ **{config.BOT_NAME}**"
        )
        buttons = now_playing_buttons(chat_id, autoplay=ap_on)

        # Send now playing card
        try:
            if _thumb_url:
                await message.reply_photo(
                    photo=_thumb_url,
                    caption=caption,
                    reply_markup=buttons,
                )
            else:
                await message.reply_text(
                    caption,
                    reply_markup=buttons
                )
        except (ChatSendMediaForbidden, MessageIdInvalid):
            try:
                await message.reply_text(
                    caption, reply_markup=buttons
                )
            except Exception:
                pass

    # ── Play next ──────────────────────────────────────────
    async def play_next(self, chat_id: int):
        from jattx import app, config, db, logger, queue, yt

        # Loop handling
        try:
            loop = await db.get_loop(chat_id)
            if loop > 0:
                track = queue.current(chat_id)
                if track:
                    await db.set_loop(chat_id, loop - 1)
                    track.file_path = await yt.download(
                        track.id, video=track.video
                    )
                    return
        except Exception:
            pass

        nxt = queue.pop(chat_id)

        # Autoplay refill
        if not nxt and config.is_autoplay(chat_id):
            nxt = await self._autoplay_refill(chat_id)

        if not nxt:
            if config.AUTO_END:
                await self.stop(chat_id)
            return

        nxt.file_path = await yt.download(
            nxt.id, video=nxt.video
        )
        if not nxt.file_path:
            return await self.play_next(chat_id)

        try:
            msg = await app.send_message(
                config.LOGGER_ID,
                f"▶️ Auto-playing: **{nxt.title}**"
            )
            await self.play_media(chat_id, msg, nxt)
        except Exception as e:
            logger.warning(
                f"play_next failed [{chat_id}]: {e}"
            )

    # ── Autoplay refill ────────────────────────────────────
    async def _autoplay_refill(
        self, chat_id: int
    ) -> "Track | None":
        from jattx import config, logger, queue, yt

        last = queue.current(chat_id)
        if not last or not getattr(last, "id", None):
            return None

        try:
            related = await yt.mix(
                last.id,
                user="🔄 AutoPlay",
                video=getattr(last, "video", False),
                limit=config.AUTOPLAY_LIMIT + 1,
            )
        except Exception as e:
            logger.warning(f"AutoPlay mix failed: {e}")
            return None

        if not related:
            return None

        filtered = [
            t for t in related
            if t.id != last.id
        ][:config.AUTOPLAY_LIMIT]

        if not filtered:
            return None

        for t in filtered[1:]:
            queue.add(chat_id, t)

        return filtered[0]

    # ── Suggestions ────────────────────────────────────────
    async def get_suggestions(self, chat_id: int) -> list:
        from jattx import queue, yt

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

        return [
            t for t in related
            if t.id != current.id
        ][:5]
