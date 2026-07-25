"""Detect Chipotle SMS promo codes in Instagram captions."""

from __future__ import annotations

import re
from dataclasses import dataclass

PROMO_PATTERN = re.compile(
    r"(?:text|txt|send)\s+(\S+)\s+to\s+([\d-]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PromoHit:
    code: str
    phone: str
    media_id: str
    caption: str
    timestamp: str


def detect_promo(
    *,
    media_id: str,
    caption: str | None,
    timestamp: str = "",
) -> PromoHit | None:
    if not caption or "chipotle" not in caption.lower():
        return None

    match = PROMO_PATTERN.search(caption)
    if not match:
        return None

    return PromoHit(
        code=match.group(1),
        phone=match.group(2),
        media_id=media_id,
        caption=caption,
        timestamp=timestamp or "",
    )
