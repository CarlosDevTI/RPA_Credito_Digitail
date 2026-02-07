from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

from .config import Config, RunContext
from .logging_utils import safe_screenshot
from .selectors import (
    PORTAL_LOGIN_PASSWORD,
    PORTAL_LOGIN_SUBMIT,
    PORTAL_LOGIN_SUCCESS,
    PORTAL_LOGIN_USERNAME,
    PORTAL_MENU_REPORTS,
    PORTAL_REPORT_END_DATE,
    PORTAL_REPORT_GENERATE_BUTTON,
    PORTAL_REPORT_START_DATE,
    PORTAL_REPORT_TYPE_SELECT,
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


def _format_report_date(config: Config) -> str:
    return datetime.now().strftime(config.portal_date_format)


def _open_reports(page: Page, config: Config, run_ctx: RunContext) -> None:
    logger = logging.getLogger("rpa")
    logger.info("Opening reports page")

    page.goto(config.portal_url, wait_until="domcontentloaded")
    if PORTAL_MENU_REPORTS:
        page.wait_for_selector(PORTAL_MENU_REPORTS)
        page.click(PORTAL_MENU_REPORTS)

    page.wait_for_selector(PORTAL_REPORT_TYPE_SELECT)
    if config.portal_report_type_text:
        page.select_option(PORTAL_REPORT_TYPE_SELECT, label=config.portal_report_type_text)

    report_date = _format_report_date(config)
    page.fill(PORTAL_REPORT_START_DATE, report_date)
    page.fill(PORTAL_REPORT_END_DATE, report_date)
    safe_screenshot(page, run_ctx, "portal_reports_ready")


def download_portal_file(page: Page, config: Config, run_ctx: RunContext) -> Path:
    logger = logging.getLogger("rpa")
    try:
        if config.portal_needs_login:
            _portal_login(page, config, run_ctx)
        _open_reports(page, config, run_ctx)

        with page.expect_download(timeout=config.nav_timeout_ms) as download_info:
            page.click(PORTAL_REPORT_GENERATE_BUTTON)
        download = download_info.value

        suggested = download.suggested_filename or "reporte.xlsx"
        dest = run_ctx.downloads_dir / f"{run_ctx.run_dir.name}_{suggested}"
        download.save_as(dest)
        logger.info("Downloaded file saved: %s", dest)
        safe_screenshot(page, run_ctx, "portal_after_download")
        return dest
    except Exception as exc:
        logger.exception("Download failed")
        safe_screenshot(page, run_ctx, "portal_error")
        raise DownloadError(str(exc)) from exc
