# ⚡ JattX Music Bot

> The **fastest** Telegram voice chat music bot — YouTube, Spotify, audio effects, saved playlists, multi-assistant load balancing, and a stunning Now Playing card.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎵 YouTube | Play by URL, search query, or YouTube Music |
| 🎬 Video | Full HD video streaming in voice chat |
| 🎚 Audio Effects | Bass Boost, Nightcore, Slow Mode, Reverb, 3D, Karaoke, Loud |
| 📋 Queue | Full queue management, shuffle, remove, clear |
| 💾 Playlists | Save & load personal playlists via MongoDB |
| 🔗 Spotify | Spotify track / album / playlist → YouTube |
| 📻 Live Radio | Stream any live URL (IPTV / radio) |
| 📁 Telegram Files | Play audio/video files sent in chat |
| 🤖 Auto Mix | Auto-generate mix from current track |
| 🔁 Loop | Loop current track 1–10× or infinitely |
| 🔀 Shuffle | Shuffle queue |
| 📣 Inline Search | Search YouTube from any chat with @bot |
| 🌍 Multi-language | 10+ languages, per-group setting |
| 🎙 Multi-assistant | Up to 3 simultaneous assistants (load balancing) |
| 🛡 Security | Global ban, group blacklist, sudo system, auth users |
| 🖼 Now Playing Card | Pillow-generated thumbnail card with gradient + album art |
| ⚙️ Settings Panel | Inline settings per group (play mode, lang, clean mode, auto-end) |
| 📢 Broadcast | Owner broadcast to all groups |
| 🔧 Eval / Shell | Live Python/shell execution for owner |
| 🚀 Auto-detect | Bot name & username auto-detected at startup — no hardcoding |

---

## 🚀 Deployment

### Railway (recommended)
1. Fork this repo
2. Create a new Railway project → Deploy from GitHub
3. Add all vars from `app.json` in the Variables tab
4. Deploy — Railway uses the `Procfile` automatically

### Heroku
```bash
heroku create your-app-name
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... # etc.
git push heroku main
heroku ps:scale worker=1
```

### VPS / Local
```bash
git clone https://github.com/youruser/JattX-Music
cd JattX-Music
cp .env.example .env
nano .env          # fill in your values
pip install -r requirements.txt
python -m jattx
```

### Docker
```bash
docker build -t jattx-music .
docker run --env-file .env jattx-music
```

---

## 📋 Environment Variables

See `.env.example` for full documentation of every variable.

**Required:**
- `API_ID`, `API_HASH` — from [my.telegram.org](https://my.telegram.org)
- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `MONGO_URL` — MongoDB Atlas free tier works great
- `OWNER_ID` — your Telegram user ID
- `LOGGER_ID` — a channel/group where the bot logs startup messages
- `SESSION` — Pyrogram session string for the assistant userbot

Generate a session string: `python -c "from pyrogram import Client; Client('x',API_ID,API_HASH).run()"`

---

## 🎮 Commands

### Play
| Command | Description |
|---|---|
| `/play <query/URL>` | Play audio |
| `/vplay <query/URL>` | Play video |
| `/yplay <query>` | YouTube Music search |
| `/splay <Spotify URL>` | Play Spotify track |
| `/salbum <Spotify URL>` | Play Spotify album |
| `/splaylist <Spotify URL>` | Play Spotify playlist |
| `/playlist <YT URL>` | Load YouTube playlist |
| `/tplay` | Play replied Telegram audio/video |
| `/live <URL>` | Stream live radio/IPTV |
| `/mix` | Auto-mix from current track |

### Controls (Admin)
`/pause`, `/resume`, `/skip`, `/stop`, `/mute`, `/unmute`, `/seek <s>`, `/loop <n>`, `/shuffle`, `/effect <name>`

### Queue
`/queue`, `/remove <pos>`, `/clearqueue`, `/saveplaylist <name>`, `/myplaylists`, `/loadplaylist <name>`

### Tools
`/ping`, `/uptime`, `/activevc`, `/lyrics <song>`, `/lang <code>`, `/settings`

### Owner
`/botinfo`, `/stats`, `/broadcast`, `/sudo`, `/unsudo`, `/gban`, `/ungban`, `/blacklist`, `/maintenance on/off`, `/restart`, `/eval`, `/shell`, `/leaveall`

---

## 🤖 Auto Name & Username Detection

JattX Music automatically reads the bot's **name** and **username** from Telegram at startup.
You **never** need to hardcode them. Change your bot's name in BotFather anytime — the bot adapts on next restart.

The deploy info message sent to your logger channel always contains the live `/add to group` link with the correct username.

---

## 📄 License
MIT © JattX Music
