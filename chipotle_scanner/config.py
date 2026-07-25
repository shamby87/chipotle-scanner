"""Load settings from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SEEN_POSTS_PATH = DATA_DIR / "seen_posts.json"
TOKEN_PATH = DATA_DIR / "token.json"

DEFAULT_TARGET_USERNAME = "pgatour"
DEFAULT_GRAPH_VERSION = "v25.0"
DEFAULT_MEDIA_LIMIT = 5
TOKEN_REFRESH_WITHIN_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class Settings:
    ig_user_id: str
    ig_access_token: str
    meta_app_id: str
    meta_app_secret: str
    discord_webhook: str
    discord_user_id: str
    target_username: str = DEFAULT_TARGET_USERNAME
    graph_version: str = DEFAULT_GRAPH_VERSION
    media_limit: int = DEFAULT_MEDIA_LIMIT
    root_dir: Path = ROOT_DIR
    seen_posts_path: Path = SEEN_POSTS_PATH
    token_path: Path = TOKEN_PATH


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    return Settings(
        ig_user_id=_require("IG_USER_ID"),
        ig_access_token=_require("IG_ACCESS_TOKEN"),
        meta_app_id=_require("META_APP_ID"),
        meta_app_secret=_require("META_APP_SECRET"),
        discord_webhook=_require("DISCORD_WEBHOOK"),
        discord_user_id=_require("USER_ID"),
        target_username=os.environ.get("TARGET_USERNAME", DEFAULT_TARGET_USERNAME).strip()
        or DEFAULT_TARGET_USERNAME,
        graph_version=os.environ.get("GRAPH_VERSION", DEFAULT_GRAPH_VERSION).strip()
        or DEFAULT_GRAPH_VERSION,
        media_limit=int(os.environ.get("MEDIA_LIMIT", str(DEFAULT_MEDIA_LIMIT))),
    )
