"""
Pipeline: Silver -> Gold (versão A - básica)

Responsável por:
- Ler o dataset principal da camada Silver
- Realizar agregações simples por UF (ou outra dimensão chave)
- Gerar uma tabela Gold com métricas básicas de acidentes
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import pandas as pd
import sys

# -------------------------------------------------------------------
# Helpers de import 
# -------------------------------------------------------------------
# ensure `src/` is on sys.path so we can import utils when the script
# is executed directly from the repository root
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.io_helpers import read_csv_flexible
from utils.logging_helpers import setup_logging

# -------------------------------------------------------------------
# Diretórios e configs
# -------------------------------------------------------------------

SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")

SILVER_FILE_NAME = "dados-prf-2023.csv"  # ajuste se o nome mudar

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def ensure_dirs() -> None:
    """Garante que a pasta Gold exista."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)


def load_silver_main() -> pd.DataFrame:
    """Carrega o dataset principal da camada Silver."""
    silver_path = SILVER_DIR / SILVER_FILE_NAME

    if not silver_path.exists():
        raise FileNotFoundError(f"Arquivo Silver não encontrado: {silver_path}")

    logging.info("Lendo arquivo Silver: %s", silver_path.name)
    df = read_csv_flexible(silver_path)
    logging.info("Arquivo Silver carregado com shape: %s", df.shape)
    return df


def build_accidents_by_uf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria uma visão agregada de acidentes por UF.

    Espera encontrar na Silver, idealmente, colunas como:
    - uf
    - mortos
    - feridos_graves
    - feridos_leves
    - ilesos

    O código é defensivo: só agrega as colunas que existirem.
    """
    if "uf" not in df.columns:
        raise KeyError(
            "Coluna 'uf' não encontrada no dataset Silver. "
            "Verifique o schema após a etapa Bronze -> Silver."
        )

    group_cols = ["uf"]
    agg_dict: dict = {}

    numeric_candidate_cols: List[str] = [
        "mortos",
        "feridos_graves",
        "feridos_leves",
        "ilesos",
    ]

    for col in numeric_candidate_cols:
        if col in df.columns:
            agg_dict[col] = "sum"

    # total de acidentes (contagem de linhas)
    df = df.copy()
    df["__ones__"] = 1
    agg_dict["__ones__"] = "sum"

    grouped = df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

    # renomear total de acidentes
    grouped = grouped.rename(columns={"__ones__": "total_acidentes"})
    #grouped.drop(columns=["__ones__"], inplace=True)
    # NÃO precisamos mais dropar "__ones__", ela já foi renomeada

    # criar taxa de mortalidade se possível
    if "mortos" in grouped.columns:
        grouped["taxa_mortalidade_por_acidente"] = (
            grouped["mortos"] / grouped["total_acidentes"]
        )

    # ordenar por total de acidentes (desc)
    grouped = grouped.sort_values(by="total_acidentes", ascending=False)

    return grouped


def save_gold_table(df_gold: pd.DataFrame, name: str) -> Path:
    """Salva uma tabela Gold em CSV na pasta Gold."""
    dest = GOLD_DIR / name
    df_gold.to_csv(dest, index=False)
    logging.info("Tabela Gold salva em: %s (shape=%s)", dest, df_gold.shape)
    return dest

# -------------------------------------------------------------------
# Pipeline principal
# -------------------------------------------------------------------

def run_silver_to_gold_basic() -> None:
    """Executa o pipeline Silver -> Gold (versão básica)."""
    ensure_dirs()

    try:
        df_silver = load_silver_main()
    except Exception as e:
        logging.error("Erro ao carregar Silver: %s", str(e))
        return

    try:
        df_gold_uf = build_accidents_by_uf(df_silver)
    except Exception as e:
        logging.error("Erro ao construir agregação por UF: %s", str(e))
        return

    save_gold_table(df_gold_uf, "acidentes_por_uf.csv")


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging("logs/silver_to_gold_basic.log")
    logging.info("Iniciando pipeline Silver -> Gold (básico).")
    run_silver_to_gold_basic()
    logging.info("Pipeline Silver -> Gold (básico) finalizado.")
