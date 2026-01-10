"""
Pipeline: Bronze -> Silver

Responsável por:
- Ler arquivos CSV da camada Bronze (usando leitor robusto)
- Padronizar nomes de colunas (snake_case)
- Limpar linhas totalmente vazias
- Tentar converter tipos (datas, numéricos)
- Salvar arquivos tratados na camada Silver
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd

# -------------------------------------------------------------------
# Project paths (robusto para execução via Airflow/Docker)
# -------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parents[1]   # .../p01/src
PROJECT_DIR = SRC_DIR.parent                    # .../p01

# garante que `src/` esteja no sys.path para imports internos
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.io_helpers import read_csv_flexible
from utils.logging_helpers import setup_logging

# -------------------------------------------------------------------
# Diretórios de trabalho (absolutos a partir do projeto)
# -------------------------------------------------------------------
DATA_DIR = PROJECT_DIR / "data"
LOGS_DIR = PROJECT_DIR / "logs"

BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"

# -------------------------------------------------------------------
# Helpers de transformação
# -------------------------------------------------------------------

def ensure_dirs() -> None:
    """Garante que a pasta Silver exista."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)


def to_snake_case(col: str) -> str:
    col = col.strip().lower()
    for char in [" ", "-", "/", ".", ";", ","]:
        col = col.replace(char, "_")
    while "__" in col:
        col = col.replace("__", "_")
    return col


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    return df


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    return df.dropna(how="all")


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in df.columns:
        if "data" in col or "date" in col:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception as e:
                logging.warning("Falha ao converter '%s' para datetime: %s", col, str(e))

    possible_numeric_cols: List[str] = [
        col for col in df.columns
        if any(x in col for x in ["valor", "quantidade", "qtd", "preco", "preço"])
    ]

    for col in possible_numeric_cols:
        try:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except Exception as e:
            logging.warning("Falha ao converter '%s' para numérico: %s", col, str(e))

    return df


# -------------------------------------------------------------------
# Funções principais do pipeline
# -------------------------------------------------------------------

def process_file(path_bronze: Path) -> None:
    logging.info("Processando Bronze -> Silver: %s", path_bronze.name)

    try:
        df = read_csv_flexible(path_bronze)
    except Exception as e:
        logging.error("Erro ao ler '%s': %s", path_bronze.name, str(e))
        return

    df = convert_types(basic_cleaning(standardize_columns(df)))

    dest = SILVER_DIR / path_bronze.name
    try:
        df.to_csv(dest, index=False)
        logging.info("Arquivo salvo na Silver: %s", dest)
    except Exception as e:
        logging.error("Erro ao salvar '%s': %s", dest, str(e))


def run_bronze_to_silver() -> None:
    ensure_dirs()

    logging.info("Contexto: cwd=%s", Path.cwd())
    logging.info("PROJECT_DIR=%s", PROJECT_DIR)
    logging.info("BRONZE_DIR=%s | SILVER_DIR=%s", BRONZE_DIR, SILVER_DIR)

    if not BRONZE_DIR.exists():
        logging.error("Diretório Bronze não encontrado: %s", BRONZE_DIR)
        return

    csv_files = [p for p in BRONZE_DIR.glob("*.csv") if p.is_file()]
    logging.info("Arquivos CSV encontrados na Bronze: %d", len(csv_files))

    if not csv_files:
        logging.warning("Nada a processar em '%s'.", BRONZE_DIR)
        return

    for file in csv_files:
        process_file(file)

    logging.info("Processamento Bronze -> Silver finalizado.")


if __name__ == "__main__":
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(str(LOGS_DIR / "bronze_to_silver.log"))
    run_bronze_to_silver()
