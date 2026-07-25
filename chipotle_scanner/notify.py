"""Discord notifications (SMS hook can land here later)."""

from __future__ import annotations

from datetime import datetime

from discordwebhook import Discord

from chipotle_scanner.config import Settings
from chipotle_scanner.detector import PromoHit


class Notifier:
    def __init__(self, settings: Settings) -> None:
        self._channel = Discord(url=settings.discord_webhook)
        self._user_id = settings.discord_user_id

    def log(self, text: str, *, tag: bool = False) -> None:
        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        msg = f"{now} - {text}"
        print(msg)
        prefix = f"<@{self._user_id}> " if tag else ""
        self._channel.post(content=f"{prefix}{msg}")

    def notify_promo(self, hit: PromoHit) -> None:
        self.log(
            f"Chipotle code {hit.code}, text to {hit.phone}.",
            tag=True,
        )
