FROM python:3.11-slim

# System deps for Pillow, numpy, yt-dlp, ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create runtime dirs
RUN mkdir -p downloads cache assets jattx/cookies

CMD ["python", "-m", "jattx"]
