from __future__ import annotations

import csv
import logging
from pathlib import Path


def setup_logging(log_dir: str | Path = "logs") -> logging.Logger:
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ngo_enricher")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(path / "run.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def append_error(row_number: int, ngo_name: str, website: str, code: str, detail: str, log_dir: str | Path = "logs") -> None:
    path = Path(log_dir) / "errors.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not exists:
            writer.writerow(["row_number", "ngo_name", "website", "error_code", "detail"])
        writer.writerow([row_number, ngo_name, website, code, detail])
