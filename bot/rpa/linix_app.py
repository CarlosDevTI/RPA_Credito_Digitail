from __future__ import annotations

import logging
import time
from pathlib import Path

from pywinauto import Application, Desktop, keyboard
from pywinauto.base_wrapper import BaseWrapper

from .config import Config, RunContext
from .linix_selectors import (
    LINIX_BUTTON_AHORROS_CARGAR_ARCHIVO,
    LINIX_BUTTON_CARGUE_ARCHIVO,
    LINIX_BUTTON_CONTABILIZAR,
    LINIX_BUTTON_DOC_CARGAR_ARCHIVO,
    LINIX_CHECK_DOCS_EXISTENTES,
    LINIX_FIELD_CONTABILIZAR,
    LINIX_FIELD_DESCRIPCION,
    LINIX_FIELD_DESTINACION,
    LINIX_FIELD_MODALIDAD,
    LINIX_FIELD_PROCESO,
    LINIX_FIELD_TIPO_MOVIMIENTO,
    LINIX_MAIN_WINDOW,
    LINIX_MENU_CONTAB_MOV_PATH,
    LINIX_MENU_SOLICITUDES_PATH,
    LINIX_TAB_AHORROS,
    LINIX_TAB_DOCUMENTO_SOPORTE,
)


class LinixError(Exception):
    pass


def _connect_app(config: Config) -> Application:
    try:
        app = Application(backend="uia").connect(path=config.linix_app_path)
    except Exception:
        app = Application(backend="uia").start(config.linix_app_path)
    return app


def _get_window(app: Application, config: Config, timeout_sec: int) -> BaseWrapper:
    window_spec = LINIX_MAIN_WINDOW.copy()
    window_spec["title"] = config.linix_window_title or window_spec.get("title", "")
    window = app.window(**window_spec)
    window.wait("visible", timeout=timeout_sec)
    window.set_focus()
    return window


def _child(window: BaseWrapper, spec: dict) -> BaseWrapper:
    return window.child_window(**spec)


def _set_text(window: BaseWrapper, spec: dict, value: str) -> None:
    ctrl = _child(window, spec)
    ctrl.set_focus()
    try:
        ctrl.set_edit_text(value)
    except Exception:
        ctrl.type_keys("^a{BACKSPACE}")
        ctrl.type_keys(value, with_spaces=True)


def _click(window: BaseWrapper, spec: dict) -> None:
    ctrl = _child(window, spec)
    ctrl.set_focus()
    ctrl.click()


def _menu_select(window: BaseWrapper, path: str) -> None:
    if not path:
        return
    try:
        window.menu_select(path)
    except Exception:
        logging.getLogger("rpa").warning("No se pudo usar menu_select con '%s'", path)


def _upload_file_dialog(file_path: Path, timeout_sec: int) -> None:
    dialog = Desktop(backend="uia").window(title_re="(Abrir|Open)")
    dialog.wait("visible", timeout=timeout_sec)

    # Some legacy dialogs filter by file type; force "All files" when available.
    try:
        file_type_combo = dialog.child_window(title_re="(Tipo:|Type:)", control_type="ComboBox")
        file_type_combo.select("All Files (*)")
    except Exception:
        pass

    try:
        file_name_edit = dialog.child_window(auto_id="1148", control_type="Edit")
        file_name_edit.set_edit_text(str(file_path))
    except Exception:
        file_name_edit = dialog.child_window(control_type="Edit")
        file_name_edit.set_edit_text(str(file_path))

    dialog.child_window(title_re="(Abrir|Open)", control_type="Button").click()


def _send_text(value: str) -> None:
    keyboard.send_keys(value, with_spaces=True)


def _open_section1_and_fill(config: Config, window: BaseWrapper, wait_sec: int) -> None:
    # Keyboard-first flow for legacy LINIX windows without stable UIA identifiers.
    window.set_focus()
    keyboard.send_keys("{ENTER}")
    time.sleep(wait_sec)
    keyboard.send_keys("{ENTER}")
    time.sleep(wait_sec)
    keyboard.send_keys("{TAB}{TAB}")
    time.sleep(wait_sec)

    _send_text(config.linix_modalidad)
    keyboard.send_keys("{TAB}")
    time.sleep(wait_sec)

    # User flow indicates typing "P" autocompletes to PSC.
    _send_text(config.linix_destinacion[:1] if config.linix_destinacion else "P")
    keyboard.send_keys("{TAB}")
    time.sleep(wait_sec)

    _send_text(config.linix_contabilizar)
    keyboard.send_keys("{TAB}{TAB}")
    time.sleep(wait_sec)

    _send_text(config.linix_descripcion)
    keyboard.send_keys("{F10}")
    time.sleep(wait_sec)
    keyboard.send_keys("{ENTER}")
    time.sleep(wait_sec)


def run_linix_flow(
    config: Config,
    run_ctx: RunContext,
    linix_file: Path,
    documentos_file: Path | None,
    ahorros_file: Path | None,
) -> None:
    logger = logging.getLogger("rpa")
    try:
        timeout_sec = max(10, int(config.nav_timeout_ms / 1000))
        wait_sec = max(1, int(config.post_action_wait_ms / 1000))

        app = _connect_app(config)
        window = _get_window(app, config, timeout_sec)

        logger.info("LINIX: Paso 1 (Solicitudes resumidas)")
        _open_section1_and_fill(config, window, wait_sec)

        _click(window, LINIX_BUTTON_CARGUE_ARCHIVO)
        _upload_file_dialog(linix_file, timeout_sec)
        time.sleep(wait_sec)

        if config.dry_run:
            logger.info("DRY_RUN habilitado. Se omite 'Contabilizar'.")
        else:
            _click(window, LINIX_BUTTON_CONTABILIZAR)
            time.sleep(wait_sec)

        logger.info("LINIX: Paso 2 (Contabilizacion de movimientos)")
        _menu_select(window, LINIX_MENU_CONTAB_MOV_PATH)
        time.sleep(wait_sec)

        _set_text(window, LINIX_FIELD_PROCESO, config.linix_descripcion)
        _set_text(window, LINIX_FIELD_TIPO_MOVIMIENTO, config.linix_tipo_movimiento)
        keyboard.send_keys("{F10}")
        time.sleep(wait_sec)

        if documentos_file:
            _click(window, LINIX_TAB_DOCUMENTO_SOPORTE)
            try:
                _click(window, LINIX_CHECK_DOCS_EXISTENTES)
            except Exception:
                logger.warning("No se encontro el checkbox de documentos existentes.")
            _click(window, LINIX_BUTTON_DOC_CARGAR_ARCHIVO)
            _upload_file_dialog(documentos_file, timeout_sec)
            time.sleep(wait_sec)

        if ahorros_file:
            _click(window, LINIX_TAB_AHORROS)
            _click(window, LINIX_BUTTON_AHORROS_CARGAR_ARCHIVO)
            _upload_file_dialog(ahorros_file, timeout_sec)
            time.sleep(wait_sec)
    except Exception as exc:
        raise LinixError(str(exc)) from exc
