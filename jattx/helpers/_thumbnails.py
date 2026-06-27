"""
jattx/helpers/_thumbnails.py
Generates a beautiful Now Playing thumbnail card:
  • Blurred + darkened album art background
  • Gradient overlay (dark purple → midnight blue)
  • Circular cropped album art + spinning disc
  • Track title, artist, duration, requester name
  • Bot branding watermark
"""

import os
import io
import asyncio
import textwrap
from pathlib import Path

import aiohttp
import aiofiles
from PIL import (
    Image, ImageDraw, ImageFilter, ImageEnhance,
    ImageFont, ImageChops
)

CACHE_DIR = "cache"
FONT_DIR  = "assets"

# We ship one bold font; fallback to default if missing
_FONT_BOLD   = os.path.join(FONT_DIR, "Raleway-Bold.ttf")
_FONT_LIGHT  = os.path.join(FONT_DIR, "Inter-Light.ttf")


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size * 3, size * 3), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 3, size * 3), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def _apply_circle(img: Image.Image, size: int) -> Image.Image:
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = _circle_mask(size)
    img.putalpha(mask)
    return img


def _gradient_overlay(w: int, h: int) -> Image.Image:
    """Dark gradient: left half dark purple, right transparent."""
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for x in range(w):
        alpha = int(200 * (1 - x / w))
        draw.line([(x, 0), (x, h)], fill=(15, 10, 35, alpha))
    return grad


class Thumbnail:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch_image(self, url: str) -> Image.Image | None:
        if not url:
            return None
        try:
            s = await self._get_session()
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            pass
        return None

    async def _get_user_avatar(self, user_id: int) -> Image.Image | None:
        from jattx import app
        try:
            path = await app.download_media(
                (await app.get_users(user_id)).photo.big_file_id,
                file_name=f"cache/{user_id}_avatar.jpg",
            )
            return Image.open(path).convert("RGBA")
        except Exception:
            return None

    async def generate(self, track) -> str | None:
        """Generate and cache a Now Playing thumbnail. Returns file path or None."""
        cache_path = f"{CACHE_DIR}/np_{track.id}_{getattr(track, 'message_id', 0)}.png"
        if Path(cache_path).exists():
            return cache_path

        try:
            return await asyncio.wait_for(
                self._build(track, cache_path), timeout=10
            )
        except Exception:
            return None

    async def _build(self, track, out_path: str) -> str | None:
        W, H = 1280, 720

        # 1. Background — blurred album art
        thumb_img = await self._fetch_image(track.thumbnail)
        if thumb_img:
            bg = thumb_img.resize((W, H), Image.LANCZOS).convert("RGBA")
            bg = bg.filter(ImageFilter.GaussianBlur(18))
            bg = ImageEnhance.Brightness(bg).enhance(0.35)
        else:
            bg = Image.new("RGBA", (W, H), (10, 8, 25, 255))

        # 2. Gradient overlay
        overlay = _gradient_overlay(W, H)
        bg = Image.alpha_composite(bg, overlay)

        draw = ImageDraw.Draw(bg)

        # 3. Album art circle (right side)
        art_size = 340
        art_x, art_y = W - art_size - 80, (H - art_size) // 2
        if thumb_img:
            art_circle = _apply_circle(thumb_img, art_size)
            # Subtle glow ring
            ring = Image.new("RGBA", (art_size + 20, art_size + 20), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse(
                (0, 0, art_size + 20, art_size + 20),
                outline=(180, 100, 255, 120), width=6
            )
            bg.paste(ring, (art_x - 10, art_y - 10), ring)
            bg.paste(art_circle, (art_x, art_y), art_circle)

        # 4. Text
        fn_big   = _load_font(_FONT_BOLD,  62)
        fn_med   = _load_font(_FONT_BOLD,  38)
        fn_small = _load_font(_FONT_LIGHT, 32)
        fn_tiny  = _load_font(_FONT_LIGHT, 26)

        tx = 80    # left margin
        ty = 160   # start y

        # Playing label
        draw.text((tx, ty - 60), "♪  NOW PLAYING", font=fn_tiny,
                  fill=(180, 100, 255, 220))

        # Title (max 2 lines)
        title = textwrap.fill(track.title[:60], width=28)
        draw.text((tx, ty), title, font=fn_big, fill=(255, 255, 255, 255))
        ty += fn_big.getbbox(title)[3] + 28

        # Artist
        if track.channel_name:
            draw.text((tx, ty), f"🎤  {track.channel_name[:40]}",
                      font=fn_med, fill=(200, 180, 255, 210))
            ty += 55

        # Duration
        draw.text((tx, ty), f"⏱  {track.duration}",
                  font=fn_small, fill=(160, 160, 200, 200))
        ty += 48

        # Requester
        if getattr(track, "user", ""):
            draw.text((tx, ty), f"👤  {track.user}",
                      font=fn_small, fill=(140, 140, 180, 180))
            ty += 48

        # Progress bar placeholder (cosmetic)
        bar_y = H - 80
        draw.rounded_rectangle([tx, bar_y, W - 80, bar_y + 8],
                                radius=4, fill=(60, 60, 100, 160))
        # filled portion (random-ish, just visual)
        draw.rounded_rectangle([tx, bar_y, tx + 300, bar_y + 8],
                                radius=4, fill=(180, 100, 255, 230))

        # Bot watermark
        from config import config
        draw.text((tx, H - 48), f"⚡ {config.BOT_NAME}",
                  font=fn_tiny, fill=(120, 120, 160, 150))

        # 5. Save
        bg = bg.convert("RGB")
        bg.save(out_path, "PNG", optimize=True)
        return out_path
