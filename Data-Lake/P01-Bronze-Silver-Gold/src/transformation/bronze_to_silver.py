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
from pathlib import Path
from typing import List

import pandas as pd
import sys

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
# ensure `src/` is on sys.path so we can import utils when the script
# is executed directly from the repository root
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.io_helpers import read_csv_flexible
from utils.logging_helpers import setup_logging

# -------------------------------------------------------------------
# Diretórios de trabalho
# -------------------------------------------------------------------

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")

# -------------------------------------------------------------------
# Helpers de transformação
# -------------------------------------------------------------------

def ensure_dirs() -> None:
    """Garante que a pasta Silver exista."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)


def to_snake_case(col: str) -> str:
    """
    Normaliza nome de coluna para snake_case.

    Ex.: 'Data do Acidente' -> 'data_do_acidente'
    """
    col = col.strip()
    col = col.lower()
    # substituições simples; pode ser refinado no futuro
    for char in [" ", "-", "/", ".", ";", ","]:
        col = col.replace(char, "_")
    while "__" in col:
        col = col.replace("__", "_")
    return col


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica snake_case em todos os nomes de coluna."""
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]
    return df


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza básica:
    - remove linhas totalmente vazias
    """
    df = df.copy()
    df = df.dropna(how="all")
    return df


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Conversão básica de tipos:
    - colunas com 'data' ou 'date' -> datetime (tentativa)
    - colunas contendo 'valor', 'quantidade', 'qtd', 'preco', 'preço'
      -> numéricas (tentativa, com 'coerce')
    """
    df = df.copy()

    # converter colunas de data
    for col in df.columns:
        if "data" in col or "date" in col:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception as e:
                logging.warning(
                    "Falha ao converter coluna '%s' para datetime: %s",
                    col,
                    str(e),
                )

    # detectar colunas possivelmente numéricas
    possible_numeric_cols: List[str] = [
        col
        for col in df.columns
        if any(x in col for x in ["valor", "quantidade", "qtd", "preco", "preço"])
    ]

    for col in possible_numeric_cols:
        try:
            # substituir vírgula por ponto e tentar converter
            df[col] = (
                df[col]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except Exception as e:
            logging.warning(
                "Falha ao converter coluna '%s' para numérico: %s",
                col,
                str(e),
            )

    return df


# -------------------------------------------------------------------
# Funções principais do pipeline
# -------------------------------------------------------------------

def process_file(path_bronze: Path) -> None:
    """
    Processa um único arquivo CSV da camada Bronze e salva na Silver.

    Steps:
    - leitura (robusta, via read_csv_flexible)
    - padronização de colunas
    - limpeza básica
    - conversão de tipos
    - escrita na camada Silver
    """
    logging.info("Processando arquivo Bronze -> Silver: %s", path_bronze.name)

    try:
        # leitor robusto com fallback de encoding e delimitador
        df = read_csv_flexible(path_bronze)
    except Exception as e:
        logging.error(
            "Erro ao ler arquivo '%s' com read_csv_flexible: %s",
            path_bronze.name,
            str(e),
        )
        return

    # pipeline de transformação
    df = standardize_columns(df)
    df = basic_cleaning(df)
    df = convert_types(df)

    dest = SILVER_DIR / path_bronze.name

    try:
        df.to_csv(dest, index=False)
        logging.info("Arquivo salvo na camada Silver: %s", dest)
    except Exception as e:
        logging.error(
            "Erro ao salvar arquivo na Silver '%s': %s",
            dest,
            str(e),
        )


def run_bronze_to_silver() -> None:
    """Executa o pipeline para todos os arquivos CSV da camada Bronze."""
    ensure_dirs()

    if not BRONZE_DIR.exists():
        logging.error("Diretório Bronze não encontrado: %s", BRONZE_DIR)
        return

    csv_files = list(BRONZE_DIR.glob("*.csv"))
    if not csv_files:
        logging.warning(
            "Nenhum arquivo CSV encontrado em '%s'. Nada a processar.",
            BRONZE_DIR,
        )
        return

    logging.info("Iniciando processamento Bronze -> Silver.")
    for file in csv_files:
        process_file(file)
    logging.info("Processamento Bronze -> Silver finalizado.")


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    # logging centralizado para este pipeline
    setup_logging("logs/bronze_to_silver.log")
    run_bronze_to_silver()
