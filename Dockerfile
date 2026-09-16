FROM python:3.12-slim

# ffmpeg is used by yt-dlp for probing/demuxing audio streams.
# gcc is needed to compile tgcrypto's C extension (no prebuilt wheel for this image).
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
