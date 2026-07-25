# chipotle-scanner

Cron job that polls the PGA Tour Instagram account (via Meta Business Discovery) for Chipotle SMS promo codes and alerts Discord.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# fill in IG_USER_ID, IG_ACCESS_TOKEN, META_APP_ID, META_APP_SECRET, DISCORD_WEBHOOK, USER_ID
```

## Run once

```bash
.venv/bin/python main.py
```

## Cron

Runs every 1 minute from 7:00 AM through 8:59 PM, Thursday through Sunday.

```bash
* 7-20 * * THU-SAT,SUN cd path/to/chipotle-scanner && .venv/bin/python main.py >> logs/$(date +\%Y-\%m-%d).log 2>&1
```

Create `logs/` before enabling cron. Seen media ids live in `data/seen_posts.json`; refreshed tokens in `data/token.json`.
