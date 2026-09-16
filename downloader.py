"""
This function is 100% synchronous and can block for seconds on a slow source --
never call it directly from an async handler. bot.py always runs it through
loop.run_in_executor so it happens on a background thread instead of freezing
every other user's request.
"""
import os
import yt_dlp


def normalize_url(url: str) -> str:
    """Strip tracking query params so the same video isn't cached twice
    under two slightly different URLs (?si=..., ?igshid=..., etc.)."""
    return url.split("?")[0].strip()


def download_audio(url: str, download_dir: str) -> dict:
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        # "bestaudio" asks the site for its best STANDALONE audio track instead
        # of a full video file. On YouTube this exists natively, so yt-dlp
        # downloads only the audio bytes -- nothing to strip out afterwards.
        # Prefer m4a specifically (YouTube also offers Opus/webm at similar
        # quality) so downloads come out in a consistent container.
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Ride out transient network blips (DNS hiccups, timeouts) instead of
        # failing on the first one.
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        # Instagram doesn't publish separate audio-only streams for reels/posts
        # the way YouTube does, so yt-dlp has to pull the full clip and demux
        # (not re-encode) the audio track out of it -- still fast, since
        # stripping a container is just a copy, not a compression pass.
        #
        # Instagram also rate-limits anonymous requests aggressively. If you
        # start getting blocked, export cookies from a logged-in browser
        # session and point yt-dlp at them:
        # "cookiefile": "instagram_cookies.txt",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        return {
            "path": filepath,
            "title": info.get("title") or "Audio",
            "artist": info.get("uploader") or "Unknown",
            "duration": int(info.get("duration") or 0),
        }