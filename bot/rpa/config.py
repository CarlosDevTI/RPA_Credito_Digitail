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
    core_login_url: str
    core_username: str
    core_password: str
    core_section1_url: str
    core_section2_url: str
    core_section1_fields: dict
    core_section2_fields: dict
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
        core_login_url=_env_required("CORE_LOGIN_URL"),
        core_username=_env_required("CORE_USERNAME"),
        core_password=_env_required("CORE_PASSWORD"),
        core_section1_url=_env_required("CORE_SECTION1_URL"),
        core_section2_url=_env_required("CORE_SECTION2_URL"),
        core_section1_fields=_env_json_dict("CORE_SECTION1_FIELDS_JSON"),
        core_section2_fields=_env_json_dict("CORE_SECTION2_FIELDS_JSON"),
        run_context=run_context,
    )
