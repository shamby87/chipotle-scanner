"""One-shot scan: refresh token -> fetch -> detect -> notify -> save."""

from __future__ import annotations

import traceback

from chipotle_scanner.config import Settings, load_settings
from chipotle_scanner.detector import detect_promo
from chipotle_scanner.instagram import ensure_fresh_token, fetch_latest_media
from chipotle_scanner.notify import Notifier
from chipotle_scanner.store import load_seen_ids, save_seen_ids


def run() -> int:
    try:
        cfg = load_settings()
    except Exception as exc:
        print(f"Config error: {exc}")
        traceback.print_exc()
        return 1

    notifier = Notifier(cfg)

    try:
        access_token = ensure_fresh_token(cfg, notifier)
        media = fetch_latest_media(cfg, access_token)
        seen_ids = load_seen_ids(cfg.seen_posts_path)

        new_count = 0
        promo_count = 0
        for item in media:
            if item.id in seen_ids:
                continue

            new_count += 1
            hit = detect_promo(
                media_id=item.id,
                caption=item.caption,
                timestamp=item.timestamp,
            )
            if hit is not None:
                notifier.notify_promo(hit)
                promo_count += 1

            seen_ids = {*seen_ids, item.id}

        save_seen_ids(cfg.seen_posts_path, seen_ids)

        return 0
    except Exception as exc:
        notifier.log(f"Error in scan: {exc}")
        traceback.print_exc()
        return 1
