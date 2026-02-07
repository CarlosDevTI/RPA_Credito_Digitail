from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class RunContext:
    run_dir: Path
    downloads_dir: Path
    outputs_dir: Path
    screenshots_dir: Path


@dataclass(frozen=True)
class Config:
    headless: bool
    dry_run: bool
    timeout_ms: int
    nav_timeout_ms: int
    slow_mo_ms: int
    post_action_wait_ms: int
    portal_url: str
    portal_login_url: str
    portal_needs_login: bool
    portal_username: str
    portal_password: str
    portal_report_type_text: str
    portal_date_format: str
    output_encoding: str
    periodicidad_default: str
    enable_linix: bool
    linix_app_path: str
    linix_window_title: str
    linix_descripcion: str
    linix_modalidad: str
    linix_destinacion: str
    linix_contabilizar: str
    linix_tipo_movimiento: str
    enable_oracle: bool
    oracle_user: str
    oracle_password: str
    oracle_dsn: str
    oracle_lib_dir: str
    oracle_schema: str
    run_context: RunContext


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _env_required(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required env var: {name}")
    return value


def _env_json_dict(name: str) -> dict:
    value = os.getenv(name, "").strip()
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {name}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def _create_run_context() -> RunContext:
    runs_dir = Path("runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs_dir / ts
    downloads_dir = run_dir / "downloads"
    outputs_dir = run_dir / "outputs"
    screenshots_dir = run_dir / "screenshots"
    for path in (run_dir, downloads_dir, outputs_dir, screenshots_dir):
        path.mkdir(parents=True, exist_ok=True)
    return RunContext(
        run_dir=run_dir,
        downloads_dir=downloads_dir,
        outputs_dir=outputs_dir,
        screenshots_dir=screenshots_dir,
    )


def load_config() -> Config:
    load_dotenv()

    run_context = _create_run_context()

    portal_needs_login = _env_bool("PORTAL_NEEDS_LOGIN", True)
    portal_username = os.getenv("PORTAL_USERNAME", "")
    portal_password = os.getenv("PORTAL_PASSWORD", "")
    if portal_needs_login and (not portal_username or not portal_password):
        raise ValueError("PORTAL_USERNAME and PORTAL_PASSWORD are required when PORTAL_NEEDS_LOGIN=true")

    enable_linix = _env_bool("ENABLE_LINIX", True)
    enable_oracle = _env_bool("ENABLE_ORACLE", True)

    linix_app_path = os.getenv("LINIX_APP_PATH", "")
    linix_window_title = os.getenv("LINIX_WINDOW_TITLE", "")
    if enable_linix and (not linix_app_path or not linix_window_title):
        raise ValueError("LINIX_APP_PATH and LINIX_WINDOW_TITLE are required when ENABLE_LINIX=true")

    oracle_user = os.getenv("ORACLE_USER", "")
    oracle_password = os.getenv("ORACLE_PASSWORD", "")
    oracle_dsn = os.getenv("ORACLE_DSN", "")
    if enable_oracle and (not oracle_user or not oracle_password or not oracle_dsn):
        raise ValueError("ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN are required when ENABLE_ORACLE=true")

    return Config(
        headless=_env_bool("HEADLESS", True),
        dry_run=_env_bool("DRY_RUN", False),
        timeout_ms=_env_int("TIMEOUT_MS", 30000),
        nav_timeout_ms=_env_int("NAV_TIMEOUT_MS", 60000),
        slow_mo_ms=_env_int("SLOW_MO_MS", 0),
        post_action_wait_ms=_env_int("POST_ACTION_WAIT_MS", 1500),
        portal_url=_env_required("PORTAL_URL"),
        portal_login_url=os.getenv("PORTAL_LOGIN_URL", ""),
        portal_needs_login=portal_needs_login,
        portal_username=portal_username,
        portal_password=portal_password,
        portal_report_type_text=os.getenv("PORTAL_REPORT_TYPE_TEXT", "").strip(),
        portal_date_format=os.getenv("PORTAL_DATE_FORMAT", "%m/%d/%Y").strip(),
        output_encoding=os.getenv("OUTPUT_ENCODING", "utf-8").strip(),
        periodicidad_default=os.getenv("PERIODICIDAD_DEFAULT", "1").strip(),
        enable_linix=enable_linix,
        linix_app_path=linix_app_path,
        linix_window_title=linix_window_title,
        linix_descripcion=os.getenv("LINIX_DESCRIPCION", "Desembolso Credito Digital").strip(),
        linix_modalidad=os.getenv("LINIX_MODALIDAD", "112").strip(),
        linix_destinacion=os.getenv("LINIX_DESTINACION", "PSC").strip(),
        linix_contabilizar=os.getenv("LINIX_CONTABILIZAR", "101").strip(),
        linix_tipo_movimiento=os.getenv("LINIX_TIPO_MOVIMIENTO", "NCV").strip(),
        enable_oracle=enable_oracle,
        oracle_user=oracle_user,
        oracle_password=oracle_password,
        oracle_dsn=oracle_dsn,
        oracle_lib_dir=os.getenv("ORACLE_LIB_DIR", "").strip(),
        oracle_schema=os.getenv("ORACLE_SCHEMA", "").strip(),
        run_context=run_context,
    )
