from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cx_Oracle

from .config import Config
from .transform import ReportRecord


class OracleError(Exception):
    pass


@dataclass(frozen=True)
class OracleOutputs:
    documentos_file: Path
    ahorros_file: Path


def _init_oracle_client(config: Config) -> None:
    if config.oracle_lib_dir:
        cx_Oracle.init_oracle_client(lib_dir=config.oracle_lib_dir)


def _proc_name(config: Config, base_name: str) -> str:
    if config.oracle_schema:
        return f"{config.oracle_schema}.{base_name}"
    return base_name


def _call_proc_rows(cursor: cx_Oracle.Cursor, proc: str, params: list) -> list[tuple]:
    out_cursor = cursor.connection.cursor()
    cursor.callproc(proc, params + [out_cursor])
    return out_cursor.fetchall()


def build_oracle_files(
    records: list[ReportRecord],
    output_dir: Path,
    config: Config,
) -> OracleOutputs:
    logger = logging.getLogger("rpa")
    _init_oracle_client(config)

    documentos_rows: list[tuple] = []
    ahorros_rows: list[tuple] = []

    try:
        conn = cx_Oracle.connect(config.oracle_user, config.oracle_password, config.oracle_dsn)
    except cx_Oracle.DatabaseError as exc:
        raise OracleError(f"Error conectando a Oracle: {exc}") from exc

    try:
        cursor = conn.cursor()
        proc_docs = _proc_name(config, "SP_DOCUMENTOSOPO")
        proc_ahorros = _proc_name(config, "SP_CTAHORRO")

        for record in records:
            cedula = int(record.cedula)
            valor = int(record.monto)
            documentos_rows.extend(_call_proc_rows(cursor, proc_docs, [cedula, valor]))
            ahorros_rows.extend(_call_proc_rows(cursor, proc_ahorros, [cedula, valor]))
    except cx_Oracle.DatabaseError as exc:
        raise OracleError(f"Error ejecutando procedimientos Oracle: {exc}") from exc
    finally:
        conn.close()

    documentos_file = output_dir / "documentos_soporte.csv"
    ahorros_file = output_dir / "ahorros.csv"

    with documentos_file.open("w", encoding=config.output_encoding, newline="\n") as handle:
        for row in documentos_rows:
            handle.write("|".join("" if value is None else str(value) for value in row) + "\n")

    with ahorros_file.open("w", encoding=config.output_encoding, newline="\n") as handle:
        for row in ahorros_rows:
            handle.write("|".join("" if value is None else str(value) for value in row) + "\n")

    logger.info("Oracle output saved: %s", documentos_file)
    logger.info("Oracle output saved: %s", ahorros_file)
    return OracleOutputs(documentos_file=documentos_file, ahorros_file=ahorros_file)
