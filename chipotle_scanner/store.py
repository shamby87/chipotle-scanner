"""JSON persistence for seen Instagram media ids."""

from __future__ import annotations

import json
from pathlib import Path


def load_seen_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        return set()

    seen = data.get("seen_ids", [])
    if not isinstance(seen, list):
        return set()

    return {str(item) for item in seen}


def save_seen_ids(path: Path, seen_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"seen_ids": sorted(seen_ids)}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
