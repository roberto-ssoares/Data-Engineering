from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

from utils.logging_helpers import setup_logging

# -------------------------------------------------------------------
# Project paths (robusto para execução via Airflow/Docker)
# -------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parents[1]   # .../p01/src
PROJECT_DIR = SRC_DIR.parent                    # .../p01

# garante que `src/` esteja no sys.path para imports internos
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# -------------------------------------------------------------------
# Diretórios de trabalho (absolutos a partir do projeto)
# -------------------------------------------------------------------
DATA_DIR = PROJECT_DIR / "data"
LOGS_DIR = PROJECT_DIR / "logs"

RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"


def ensure_dirs() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)


def ingest_files() -> None:
    """
    Simple local ingestion:
    copies all files from raw/ to bronze/.

    Observação: usamos shutil.copyfile para evitar problemas de permissão
    em volumes montados do Windows (utime/chmod/copy2).
    """
    if not RAW_DIR.exists():
        logging.error("RAW_DIR não existe: %s", RAW_DIR)
        return

    files = list(RAW_DIR.glob("*"))
    if not files:
        logging.warning("Nenhum arquivo encontrado em: %s", RAW_DIR)
        return

    copied = 0
    for file in files:
        if file.is_dir():
            continue
        if file.name.startswith("."):  # ignora dotfiles (inclui .gitkeep)
            continue

        dest = BRONZE_DIR / file.name
        shutil.copyfile(file, dest)
        copied += 1
        logging.info("Ingested %s -> %s", file.name, dest)

    logging.info("raw_to_bronze finalizado. arquivos_copiados=%d", copied)


if __name__ == "__main__":
    ensure_dirs()
    setup_logging(str(LOGS_DIR / "raw_to_bronze.log"))
    ingest_files()
