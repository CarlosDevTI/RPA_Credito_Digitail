from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .rpa.config import load_config
from .rpa.download import DownloadError, download_portal_file
from .rpa.logging_utils import log_exception, safe_screenshot, setup_logging
from .rpa.linix_app import LinixError, run_linix_flow
from .rpa.oracle_proc import OracleError, build_oracle_files
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
            context.close()
            browser.close()
            page = None

            transform_result = transform_file(
                downloaded_path,
                run_ctx.outputs_dir,
                config.output_encoding,
                config.periodicidad_default,
            )

            oracle_outputs = None
            if config.enable_oracle:
                oracle_outputs = build_oracle_files(
                    transform_result.records,
                    run_ctx.outputs_dir,
                    config,
                )

            if config.enable_linix:
                run_linix_flow(
                    config=config,
                    run_ctx=run_ctx,
                    linix_file=transform_result.linix_file,
                    documentos_file=oracle_outputs.documentos_file if oracle_outputs else None,
                    ahorros_file=oracle_outputs.ahorros_file if oracle_outputs else None,
                )

            logger.info("Run completed OK.")
    except (DownloadError, TransformError, OracleError, LinixError, PlaywrightTimeoutError) as exc:
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
