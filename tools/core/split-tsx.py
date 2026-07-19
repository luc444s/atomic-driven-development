#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    root_tools = Path(__file__).resolve().parents[1]
    source = root_tools / "split-tsx.py"
    runpy.run_path(str(source), run_name="__main__")


if __name__ == "__main__":
    main()
