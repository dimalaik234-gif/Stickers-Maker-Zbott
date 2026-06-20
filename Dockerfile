FROM python:3.11-slim

# Системные зависимости для Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    libpng-dev \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/temp data/stickers data/fonts

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
