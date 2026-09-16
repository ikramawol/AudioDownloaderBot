import asyncio
import os
import re

# Python 3.14 removed the implicit loop creation in asyncio.get_event_loop(),
# which pyrogram's sync wrapper relies on at import time. Set one up first.
asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR, DB_PATH
from db import AudioCache
from downloader import download_audio, normalize_url

app = Client("audio_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
cache = AudioCache(DB_PATH)

URL_RE = re.compile(r"https?://\S+")


@app.on_message(filters.regex(URL_RE) & filters.private)
async def handle_url(client, message):
    url = normalize_url(message.text)
    status = await message.reply("Looking that up...")

    # 1. Cache check FIRST. If someone already asked for this link, we already
    #    have a file_id sitting on Telegram's servers -- send that straight back.
    cached = await cache.get(url)
    if cached:
        file_id, title = cached
        await client.send_audio(message.chat.id, audio=file_id, title=title)
        await status.delete()
        return

    # 2. Not cached -- do the real download. yt-dlp is blocking, so it runs on
    #    a worker thread via run_in_executor instead of on the bot's event loop.
    loop = asyncio.get_event_loop()
    try:
        await status.edit("Downloading audio...")
        result = await loop.run_in_executor(None, download_audio, url, DOWNLOAD_DIR)
    except Exception as e:
        msg = str(e)
        if "Unsupported URL" in msg:
            await status.edit(
                "That link isn't a single downloadable post (e.g. an Instagram "
                "'audio' browse page lists many reels, not one). Send the actual "
                "video/reel/post link instead."
            )
        elif "Failed to resolve" in msg or "getaddrinfo failed" in msg or "WinError 1231" in msg:
            await status.edit("Network error reaching that site. Check your internet connection and try again.")
        else:
            await status.edit(f"Couldn't download that: {e}")
        return

    # 3. Upload whatever codec yt-dlp gave us (Opus/M4A) as-is -- Telegram's
    #    audio player handles these natively, so there's no need to spend time
    #    converting to mp3 first.
    sent = await client.send_audio(
        message.chat.id,
        audio=result["path"],
        title=result["title"],
        performer=result["artist"],
        duration=result["duration"],
    )

    # 4. Remember the file_id so the NEXT request for this URL is instant.
    await cache.set(url, sent.audio.file_id, result["title"])

    # 5. Clean up the local copy -- Telegram now holds the only copy we need.
    if os.path.exists(result["path"]):
        os.remove(result["path"])

    await status.delete()


if __name__ == "__main__":
    print("Bot starting...")
    app.run()
    