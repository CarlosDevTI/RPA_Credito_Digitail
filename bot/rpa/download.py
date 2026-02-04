from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Page

from .config import Config, RunContext
from .logging_utils import safe_screenshot
from .selectors import (
    PORTAL_DOWNLOAD_BUTTON,
    PORTAL_LOGIN_PASSWORD,
    PORTAL_LOGIN_SUBMIT,
    PORTAL_LOGIN_SUCCESS,
    PORTAL_LOGIN_USERNAME,
)


class DownloadError(Exception):
    pass


def _portal_login(page: Page, config: Config, run_ctx: RunContext) -> None:
    logger = logging.getLogger("rpa")
    login_url = config.portal_login_url or config.portal_url
    logger.info("Portal login: %s", login_url)

    page.goto(login_url, wait_until="domcontentloaded")
    page.wait_for_selector(PORTAL_LOGIN_USERNAME)
    page.fill(PORTAL_LOGIN_USERNAME, config.portal_username)
    page.fill(PORTAL_LOGIN_PASSWORD, config.portal_password)
    safe_screenshot(page, run_ctx, "portal_before_login_submit")
    page.click(PORTAL_LOGIN_SUBMIT)
    page.wait_for_selector(PORTAL_LOGIN_SUCCESS)
    safe_screenshot(page, run_ctx, "portal_after_login")


def download_portal_file(page: Page, config: Config, run_ctx: RunContext) -> Path:
    logger = logging.getLogger("rpa")
    try:
        if config.portal_needs_login:
            _portal_login(page, config, run_ctx)
        else:
            page.goto(config.portal_url, wait_until="domcontentloaded")

        page.wait_for_selector(PORTAL_DOWNLOAD_BUTTON)
        safe_screenshot(page, run_ctx, "portal_before_download")

        with page.expect_download(timeout=config.nav_timeout_ms) as download_info:
            page.click(PORTAL_DOWNLOAD_BUTTON)
        download = download_info.value

        suggested = download.suggested_filename or "download.txt"
        dest = run_ctx.downloads_dir / f"{run_ctx.run_dir.name}_{suggested}"
        download.save_as(dest)
        logger.info("Downloaded file saved: %s", dest)
        safe_screenshot(page, run_ctx, "portal_after_download")
        return dest
    except Exception as exc:
        logger.exception("Download failed")
        safe_screenshot(page, run_ctx, "portal_error")
        raise DownloadError(str(exc)) from exc
