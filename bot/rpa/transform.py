from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Iterable


class TransformError(Exception):
    pass


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="replace").splitlines()


def _detect_delimiter(lines: Iterable[str]) -> str | None:
    sample = [line for line in lines if line.strip()][:20]
    if not sample:
        return None

    if any(" | " in line for line in sample):
        return " | "
    if any("|" in line for line in sample):
        return "|"
    if any("\t" in line for line in sample):
        return "\t"
    if any("," in line for line in sample):
        return ","
    return None


def _split_line(line: str, delimiter: str) -> list[str]:
    if delimiter in {" | ", "|"}:
        parts = line.split("|")
    else:
        parts = line.split(delimiter)
    return [part.strip() for part in parts]


def transform_file(input_path: Path, output_dir: Path) -> Path:
    logger = logging.getLogger("rpa")
    lines = _read_lines(input_path)
    delimiter = _detect_delimiter(lines)
    if not delimiter:
        original_copy = output_dir / f"original_{input_path.name}"
        shutil.copy2(input_path, original_copy)
        raise TransformError(
            f"No se pudo detectar separador. Original guardado en: {original_copy}"
        )

    output_path = output_dir / f"{input_path.stem}_normalized.csv"
    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        for line in lines:
            if line.strip() == "":
                continue
            parts = _split_line(line, delimiter)
            output_file.write(" | ".join(parts) + "\n")

    logger.info("Transformed file saved: %s", output_path)
    return output_path
