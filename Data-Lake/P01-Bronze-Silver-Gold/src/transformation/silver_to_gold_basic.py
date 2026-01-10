"""
Pipeline: Silver -> Gold (versão A - básica)

Responsável por:
- Ler o dataset principal da camada Silver
- Realizar agregações simples por UF
- Gerar uma tabela Gold com métricas básicas de acidentes
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

SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold_basic"

# Nome do arquivo principal na Silver (ajuste se necessário)
SILVER_FILE_NAME = "dados-prf-2023.csv"
# Carrega o dataset principal da camada Silver.
silver_path = SILVER_DIR / SILVER_FILE_NAME

def ensure_dirs() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)


def load_silver_main() -> pd.DataFrame:
    
    if not silver_path.exists():
        raise FileNotFoundError(f"Arquivo Silver não encontrado: {silver_path}")

    logging.info("Lendo arquivo Silver: %s", silver_path)
    df = read_csv_flexible(silver_path)
    logging.info("Arquivo Silver carregado com shape=%s", df.shape)
    return df


def build_accidents_by_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Cria uma visão agregada de acidentes por UF."""
    if "uf" not in df.columns:
        raise KeyError(
            "Coluna 'uf' não encontrada no dataset Silver. "
            "Verifique o schema após a etapa Bronze -> Silver."
        )

    agg_dict: dict = {}
    numeric_candidate_cols: List[str] = ["mortos", "feridos_graves", "feridos_leves", "ilesos"]

    for col in numeric_candidate_cols:
        if col in df.columns:
            agg_dict[col] = "sum"

    # total de acidentes (contagem de linhas)
    df = df.copy()
    df["__ones__"] = 1
    agg_dict["__ones__"] = "sum"

    grouped = df.groupby(["uf"], dropna=False).agg(agg_dict).reset_index()
    grouped = grouped.rename(columns={"__ones__": "total_acidentes"})

    if "mortos" in grouped.columns:
        grouped["taxa_mortalidade_por_acidente"] = grouped["mortos"] / grouped["total_acidentes"]

    grouped = grouped.sort_values(by="total_acidentes", ascending=False)
    return grouped


def save_gold_table(df_gold: pd.DataFrame, name: str) -> Path:
    """Salva uma tabela Gold em CSV na pasta Gold."""
    dest = GOLD_DIR / name
    df_gold.to_csv(dest, index=False)
    logging.info("Tabela Gold salva em: %s (shape=%s)", dest, df_gold.shape)
    return dest


def run_silver_to_gold_basic() -> None:
    """Executa o pipeline Silver -> Gold (versão básica)."""
    ensure_dirs()

    logging.info("Contexto: cwd=%s", Path.cwd())
    logging.info("SILVER_DIR=%s | GOLD_DIR=%s", SILVER_DIR, GOLD_DIR)

    df_silver = load_silver_main()
    df_gold_uf = build_accidents_by_uf(df_silver)
    save_gold_table(df_gold_uf, "acidentes_por_uf.csv")


if __name__ == "__main__":
    ensure_dirs()
    setup_logging(str(LOGS_DIR / "silver_to_gold_basic.log"))
    logging.info("Iniciando pipeline Silver -> Gold (básico).")
    run_silver_to_gold_basic()
    logging.info("Pipeline Silver -> Gold (básico) finalizado.")
