from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Page

from .config import Config, RunContext
from .logging_utils import safe_screenshot
from .selectors import (
    CORE_LOGIN_PASSWORD,
    CORE_LOGIN_SUBMIT,
    CORE_LOGIN_SUCCESS,
    CORE_LOGIN_USERNAME,
    CORE_SECTION1_CONTABILIZAR_BUTTON,
    CORE_SECTION1_FIELD_SELECTORS,
    CORE_SECTION1_SUCCESS_MESSAGE,
    CORE_SECTION1_UPLOAD_INPUT,
    CORE_SECTION2_CONTABILIZAR_BUTTON,
    CORE_SECTION2_FIELD_SELECTORS,
    CORE_SECTION2_SUCCESS_MESSAGE,
    CORE_SECTION2_UPLOAD_INPUT,
)


class CoreUploadError(Exception):
    pass


def _core_login(page: Page, config: Config, run_ctx: RunContext) -> None:
    logger = logging.getLogger("rpa")
    logger.info("Core login: %s", config.core_login_url)

    page.goto(config.core_login_url, wait_until="domcontentloaded")
    page.wait_for_selector(CORE_LOGIN_USERNAME)
    page.fill(CORE_LOGIN_USERNAME, config.core_username)
    page.fill(CORE_LOGIN_PASSWORD, config.core_password)
    safe_screenshot(page, run_ctx, "core_before_login_submit")
    page.click(CORE_LOGIN_SUBMIT)
    page.wait_for_selector(CORE_LOGIN_SUCCESS)
    safe_screenshot(page, run_ctx, "core_after_login")


def _fill_fields(page: Page, fields: dict, selectors: dict, section_name: str) -> None:
    for key, value in fields.items():
        selector = selectors.get(key)
        if not selector:
            raise CoreUploadError(
                f"Missing selector for field '{key}' in {section_name}"
            )
        page.fill(selector, str(value))


def _upload_section(
    page: Page,
    config: Config,
    run_ctx: RunContext,
    section_name: str,
    url: str,
    fields: dict,
    selectors: dict,
    upload_selector: str,
    contabilizar_selector: str,
    success_selector: str,
    file_path: Path,
) -> None:
    logger = logging.getLogger("rpa")
    logger.info("Opening %s: %s", section_name, url)

    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(upload_selector)

    _fill_fields(page, fields, selectors, section_name)
    page.set_input_files(upload_selector, str(file_path))
    page.wait_for_timeout(config.post_action_wait_ms)

    safe_screenshot(page, run_ctx, f"{section_name}_before_contabilizar")

    if config.dry_run:
        logger.info("DRY_RUN enabled. Skipping contabilizar in %s.", section_name)
        return

    page.click(contabilizar_selector)
    page.wait_for_selector(success_selector, timeout=config.nav_timeout_ms)
    safe_screenshot(page, run_ctx, f"{section_name}_after_success")


def upload_to_core(
    page: Page,
    config: Config,
    run_ctx: RunContext,
    file_path: Path,
) -> None:
    try:
        _core_login(page, config, run_ctx)

        _upload_section(
            page=page,
            config=config,
            run_ctx=run_ctx,
            section_name="core_section1",
            url=config.core_section1_url,
            fields=config.core_section1_fields,
            selectors=CORE_SECTION1_FIELD_SELECTORS,
            upload_selector=CORE_SECTION1_UPLOAD_INPUT,
            contabilizar_selector=CORE_SECTION1_CONTABILIZAR_BUTTON,
            success_selector=CORE_SECTION1_SUCCESS_MESSAGE,
            file_path=file_path,
        )

        _upload_section(
            page=page,
            config=config,
            run_ctx=run_ctx,
            section_name="core_section2",
            url=config.core_section2_url,
            fields=config.core_section2_fields,
            selectors=CORE_SECTION2_FIELD_SELECTORS,
            upload_selector=CORE_SECTION2_UPLOAD_INPUT,
            contabilizar_selector=CORE_SECTION2_CONTABILIZAR_BUTTON,
            success_selector=CORE_SECTION2_SUCCESS_MESSAGE,
            file_path=file_path,
        )
    except Exception as exc:
        logging.getLogger("rpa").exception("Core upload failed")
        safe_screenshot(page, run_ctx, "core_error")
        raise CoreUploadError(str(exc)) from exc
