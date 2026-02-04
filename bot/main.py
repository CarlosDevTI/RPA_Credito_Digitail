from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .rpa.config import load_config
from .rpa.core_upload import CoreUploadError, upload_to_core
from .rpa.download import DownloadError, download_portal_file
from .rpa.logging_utils import log_exception, safe_screenshot, setup_logging
from .rpa.transform import TransformError, transform_file


def main() -> None:
    config = load_config()
    run_ctx = config.run_context
    logger = setup_logging(run_ctx.run_dir)
    logger.info("Run started: %s", run_ctx.run_dir)

    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.headless, slow_mo=config.slow_mo_ms)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(config.timeout_ms)
            page.set_default_navigation_timeout(config.nav_timeout_ms)

            downloaded_path = download_portal_file(page, config, run_ctx)
            output_path = transform_file(downloaded_path, run_ctx.outputs_dir)
            upload_to_core(page, config, run_ctx, output_path)

            logger.info("Run completed OK.")
            context.close()
            browser.close()
    except (DownloadError, TransformError, CoreUploadError, PlaywrightTimeoutError) as exc:
        log_exception(logger, "Run failed: %s", exc)
        if page:
            safe_screenshot(page, run_ctx, "error")
        sys.exit(1)
    except Exception as exc:
        log_exception(logger, "Unexpected error: %s", exc)
        if page:
            safe_screenshot(page, run_ctx, "error_unexpected")
        sys.exit(2)


if __name__ == "__main__":
    main()
