# AZRxGUARD Bot

Telegram ve Discord grupları için moderasyon, yardımcı araçlar, AI özellikleri ve bağlantı takip hizmetleri sunan bot projesi.

## Çalıştırma

- **Web servisi**: `gunicorn --bind 0.0.0.0:5000 main:app`
- **Telegram botu**: `python3 bot.py` — `TELEGRAM_BOT_TOKEN` gerektirir
- **Discord botu**: `python3 discord_bot.py` — Discord token yapılandırması gerektirir

## Yapı

- `bot.py` — Telegram botu
- `discord_bot.py` — Discord botu
- `main.py` — Flask keep-alive ve bağlantı takip endpoint'leri
- `tracking_store.py` — SQLite tabanlı takip kayıtları
- `attached_assets/` — bot medya varlıkları

## Gerekli yapılandırma

Telegram botunu çalıştırmak için `TELEGRAM_BOT_TOKEN`; sahip düzeyi komutlar için isteğe bağlı `BOT_OWNER_ID` gerekir. Bu değerler gizli ortam değişkenleri olarak eklenmelidir.
