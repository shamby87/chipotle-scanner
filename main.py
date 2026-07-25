#!/usr/bin/env python3
"""Entry point for cron: load env, run one scan, exit."""

from __future__ import annotations

import sys

from chipotle_scanner.runner import run


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
