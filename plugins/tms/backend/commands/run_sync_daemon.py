from __future__ import annotations

import logging
import sys
from datetime import timedelta

from plugins.tms.backend.services.cron import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stdout,
)


def main() -> int:
    run_scheduler(interval=timedelta(minutes=5))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
