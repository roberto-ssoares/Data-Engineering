"""
Pipeline: Silver -> Gold (versão B - analítica)

Responsável por:
- Ler o dataset principal da camada Silver
- Gerar múltiplas tabelas analíticas para consumo em dashboards:
    - acidentes por UF
    - acidentes por tipo de acidente
    - acidentes por causa de acidente
    - acidentes por faixa de horário (opcional)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import pandas as pd
import sys

# -------------------------------------------------------------------
# Helpers de import (igual aos outros pipelines)
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

SILVER_FILE_NAME = "dados-prf-2023.csv"  # ajuste se mudar o nome do arquivo

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


def add_ones_column(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna auxiliar __ones__ para contagens."""
    df = df.copy()
    df["__ones__"] = 1
    return df


def aggregate_with_count(
    df: pd.DataFrame,
    group_cols: List[str],
    numeric_cols: List[str] | None = None,
    count_col_name: str = "total_acidentes",
) -> pd.DataFrame:
    """
    Função genérica para agregar:
    - agrupa por group_cols
    - soma colunas numéricas fornecidas
    - conta total de registros usando __ones__
    """
    df = add_ones_column(df)

    agg_dict: dict = {"__ones__": "sum"}

    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = "sum"

    grouped = df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

    grouped = grouped.rename(columns={"__ones__": count_col_name})

    return grouped


def build_accidents_by_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Agregação: acidentes por UF."""
    if "uf" not in df.columns:
        raise KeyError("Coluna 'uf' não encontrada na Silver.")

    numeric_candidate_cols: List[str] = [
        "mortos",
        "feridos_graves",
        "feridos_leves",
        "ilesos",
    ]

    grouped = aggregate_with_count(
        df,
        group_cols=["uf"],
        numeric_cols=numeric_candidate_cols,
        count_col_name="total_acidentes",
    )

    if "mortos" in grouped.columns:
        grouped["taxa_mortalidade_por_acidente"] = (
            grouped["mortos"] / grouped["total_acidentes"]
        )

    grouped = grouped.sort_values(by="total_acidentes", ascending=False)
    return grouped


def build_accidents_by_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """Agregação: acidentes por tipo de acidente."""
    if "tipo_acidente" not in df.columns:
        raise KeyError("Coluna 'tipo_acidente' não encontrada na Silver.")

    grouped = aggregate_with_count(
        df,
        group_cols=["tipo_acidente"],
        numeric_cols=None,
        count_col_name="total_acidentes",
    )

    grouped = grouped.sort_values(by="total_acidentes", ascending=False)
    return grouped


def build_accidents_by_causa(df: pd.DataFrame) -> pd.DataFrame:
    """Agregação: acidentes por causa de acidente."""
    if "causa_acidente" not in df.columns:
        raise KeyError("Coluna 'causa_acidente' não encontrada na Silver.")

    grouped = aggregate_with_count(
        df,
        group_cols=["causa_acidente"],
        numeric_cols=None,
        count_col_name="total_acidentes",
    )

    grouped = grouped.sort_values(by="total_acidentes", ascending=False)
    return grouped


def build_accidents_by_periodo_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregação: acidentes por faixa de horário (período do dia).

    Requer uma coluna 'horario' em formato HH:MM ou similar.
    Cria faixas aproximadas: madrugada, manhã, tarde, noite.
    """
    if "horario" not in df.columns:
        raise KeyError("Coluna 'horario' não encontrada na Silver.")

    df = df.copy()

    # tentar extrair hora como inteiro
    def _extract_hour(value) -> int | None:
        try:
            # suporta "HH:MM" ou "HH:MM:SS"
            parts = str(value).split(":")
            return int(parts[0])
        except Exception:
            return None

    df["hora"] = df["horario"].apply(_extract_hour)

    # define faixa de horário
    def _periodo(hora: int | None) -> str:
        if hora is None:
            return "desconhecido"
        if 0 <= hora < 6:
            return "madrugada"
        if 6 <= hora < 12:
            return "manhã"
        if 12 <= hora < 18:
            return "tarde"
        if 18 <= hora <= 23:
            return "noite"
        return "desconhecido"

    df["periodo_dia"] = df["hora"].apply(_periodo)

    grouped = aggregate_with_count(
        df,
        group_cols=["periodo_dia"],
        numeric_cols=None,
        count_col_name="total_acidentes",
    )

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

def run_silver_to_gold_analytics() -> None:
    """Executa o pipeline Silver -> Gold (versão analítica)."""
    ensure_dirs()

    try:
        df_silver = load_silver_main()
    except Exception as e:
        logging.error("Erro ao carregar Silver: %s", str(e))
        return

    # 1) acidentes por UF
    try:
        df_uf = build_accidents_by_uf(df_silver)
        save_gold_table(df_uf, "gold_acidentes_por_uf.csv")
    except Exception as e:
        logging.error("Erro ao gerar acidentes por UF: %s", str(e))

    # 2) acidentes por tipo
    try:
        df_tipo = build_accidents_by_tipo(df_silver)
        save_gold_table(df_tipo, "gold_acidentes_por_tipo.csv")
    except Exception as e:
        logging.error("Erro ao gerar acidentes por tipo: %s", str(e))

    # 3) acidentes por causa
    try:
        df_causa = build_accidents_by_causa(df_silver)
        save_gold_table(df_causa, "gold_acidentes_por_causa.csv")
    except Exception as e:
        logging.error("Erro ao gerar acidentes por causa: %s", str(e))

    # 4) acidentes por período do dia (se possível)
    try:
        df_periodo = build_accidents_by_periodo_dia(df_silver)
        save_gold_table(df_periodo, "gold_acidentes_por_periodo_dia.csv")
    except Exception as e:
        logging.error("Erro ao gerar acidentes por período do dia: %s", str(e))


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging("logs/silver_to_gold_analytics.log")
    logging.info("Iniciando pipeline Silver -> Gold (analítico).")
    run_silver_to_gold_analytics()
    logging.info("Pipeline Silver -> Gold (analítico) finalizado.")

