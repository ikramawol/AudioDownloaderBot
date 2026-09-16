import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# /dev/shm is RAM-backed on Linux (tmpfs) -- writing here instead of a real disk
# removes most of the "disk I/O" cost without you having to build true zero-disk
# streaming. Falls back to a normal folder if /dev/shm doesn't exist (e.g. on Windows/Mac).
DOWNLOAD_DIR = os.environ.get(
    "DOWNLOAD_DIR",
    "/dev/shm/audio_bot" if os.path.exists("/dev/shm") else "downloads",
)

DB_PATH = os.environ.get("DB_PATH", "cache.db")