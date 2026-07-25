"""Instagram Business Discovery fetch and long-lived token refresh."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from chipotle_scanner.config import TOKEN_REFRESH_WITHIN_SECONDS, Settings
from chipotle_scanner.notify import Notifier


@dataclass(frozen=True)
class MediaItem:
    id: str
    caption: str
    timestamp: str


@dataclass(frozen=True)
class TokenState:
    access_token: str
    expires_at: int | None


def _graph_base(settings: Settings) -> str:
    return f"https://graph.facebook.com/{settings.graph_version}"


def load_token_state(path: Path, fallback_token: str) -> TokenState:
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and data.get("access_token"):
            expires_at = data.get("expires_at")
            return TokenState(
                access_token=str(data["access_token"]),
                expires_at=int(expires_at) if expires_at is not None else None,
            )
    return TokenState(access_token=fallback_token, expires_at=None)


def save_token_state(path: Path, state: TokenState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"access_token": state.access_token}
    if state.expires_at is not None:
        payload["expires_at"] = state.expires_at
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def needs_refresh(state: TokenState, now: int | None = None) -> bool:
    current = now if now is not None else int(time.time())
    # An unknown expiry means we can't trust how long this token is good for,
    # so lean toward refreshing to re-establish a token with a known expiry.
    if state.expires_at is None:
        return True
    return state.expires_at - current <= TOKEN_REFRESH_WITHIN_SECONDS


def refresh_long_lived_token(settings: Settings, current_token: str) -> TokenState:
    url = f"{_graph_base(settings)}/oauth/access_token"
    response = requests.get(
        url,
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "fb_exchange_token": current_token,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Token refresh failed (HTTP {response.status_code})")
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise RuntimeError("Token refresh response missing access_token")

    expires_in = data.get("expires_in")
    expires_at = int(time.time()) + int(expires_in) if expires_in is not None else None
    return TokenState(access_token=str(access_token), expires_at=expires_at)


def ensure_fresh_token(settings: Settings, notifier: Notifier) -> str:
    state = load_token_state(settings.token_path, settings.ig_access_token)

    if not needs_refresh(state):
        return state.access_token

    if state.expires_at is None:
        notifier.log("Access token has unknown expiration; refreshing.", tag=True)
    else:
        days_left = (state.expires_at - int(time.time())) // 86400
        notifier.log(f"Access token expires in ~{days_left}d; refreshing.", tag=True)

    refreshed = refresh_long_lived_token(settings, state.access_token)
    save_token_state(settings.token_path, refreshed)

    if refreshed.expires_at is not None:
        days_left = (refreshed.expires_at - int(time.time())) // 86400
        notifier.log(f"Access token refreshed; new token valid ~{days_left}d.", tag=True)
    else:
        notifier.log("Access token refreshed; new expiration unknown.", tag=True)

    return refreshed.access_token


def fetch_latest_media(settings: Settings, access_token: str) -> list[MediaItem]:
    fields = (
        f"business_discovery.username({settings.target_username})"
        f"{{media.limit({settings.media_limit}){{id,caption,timestamp}}}}"
    )
    url = f"{_graph_base(settings)}/{settings.ig_user_id}"
    response = requests.get(
        url,
        params={"fields": fields, "access_token": access_token},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Business Discovery fetch failed (HTTP {response.status_code})")
    payload = response.json()

    media = (
        payload.get("business_discovery", {})
        .get("media", {})
        .get("data", [])
    )

    items: list[MediaItem] = []
    for entry in media:
        if not isinstance(entry, dict) or not entry.get("id"):
            continue
        items.append(
            MediaItem(
                id=str(entry["id"]),
                caption=str(entry.get("caption") or ""),
                timestamp=str(entry.get("timestamp") or ""),
            )
        )
    return items
