"""
Caching layer. The whole trick here: once you've uploaded a file to Telegram once,
Telegram gives you back a `file_id`. Sending that same file_id again -- to the same
chat or a different one -- makes Telegram re-send the copy it already has on its own
servers. No download, no re-upload, no yt-dlp call. That's the single biggest lever
for making a bot "feel" instant on repeat requests.

sqlite3 itself is blocking, so every call is pushed through run_in_executor just like
the yt-dlp call in downloader.py -- otherwise a slow disk read would freeze the whole
bot for every user, not just the one asking.
"""
import asyncio
import sqlite3


def _init_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_cache (
            url TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def _get_cached(path: str, url: str):
    conn = sqlite3.connect(path)
    row = conn.execute(
        "SELECT file_id, title FROM audio_cache WHERE url = ?", (url,)
    ).fetchone()
    conn.close()
    return row


def _set_cached(path: str, url: str, file_id: str, title: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO audio_cache (url, file_id, title) VALUES (?, ?, ?)",
        (url, file_id, title),
    )
    conn.commit()
    conn.close()


class AudioCache:
    def __init__(self, path: str):
        self.path = path
        _init_db(path)

    async def get(self, url: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_cached, self.path, url)

    async def set(self, url: str, file_id: str, title: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _set_cached, self.path, url, file_id, title)