from __future__ import annotations

import logging
from pathlib import Path

from .config import RunContext


def setup_logging(run_dir: Path) -> logging.Logger:
    log_file = run_dir / "bot.log"
    logger = logging.getLogger("rpa")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def log_exception(logger: logging.Logger, message: str, *args: object) -> None:
    logger.exception(message, *args)


def safe_screenshot(page, run_ctx: RunContext, name: str) -> None:
    try:
        path = run_ctx.screenshots_dir / f"{name}.png"
        page.screenshot(path=path, full_page=True)
    except Exception:
        logging.getLogger("rpa").exception("Failed to capture screenshot: %s", name)
