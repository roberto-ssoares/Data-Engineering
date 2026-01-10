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
import sys
from pathlib import Path
from typing import List, Optional

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
GOLD_DIR = DATA_DIR / "gold_analytics"

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


def add_ones_column(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna auxiliar __ones__ para contagens."""
    df = df.copy()
    df["__ones__"] = 1
    return df


def aggregate_with_count(
    df: pd.DataFrame,
    group_cols: List[str],
    numeric_cols: Optional[List[str]] = None,
    count_col_name: str = "total_acidentes",
) -> pd.DataFrame:
    """
    Função genérica para agregar:
    - agrupa por group_cols
    - soma colunas numéricas fornecidas (se existirem)
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

    numeric_candidate_cols: List[str] = ["mortos", "feridos_graves", "feridos_leves", "ilesos"]

    grouped = aggregate_with_count(
        df,
        group_cols=["uf"],
        numeric_cols=numeric_candidate_cols,
        count_col_name="total_acidentes",
    )

    if "mortos" in grouped.columns:
        grouped["taxa_mortalidade_por_acidente"] = grouped["mortos"] / grouped["total_acidentes"]

    return grouped.sort_values(by="total_acidentes", ascending=False)


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

    return grouped.sort_values(by="total_acidentes", ascending=False)


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

    return grouped.sort_values(by="total_acidentes", ascending=False)


def build_accidents_by_periodo_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregação: acidentes por faixa de horário (período do dia).

    Requer uma coluna 'horario' em formato HH:MM ou similar.
    Cria faixas: madrugada, manhã, tarde, noite, desconhecido.
    """
    if "horario" not in df.columns:
        raise KeyError("Coluna 'horario' não encontrada na Silver.")

    df = df.copy()

    def _extract_hour(value) -> Optional[int]:
        try:
            parts = str(value).split(":")
            return int(parts[0])
        except Exception:
            return None

    def _periodo(hora: Optional[int]) -> str:
        if hora is None:
            return "desconhecido"
        if 0 <= hora < 6:
            return "madrugada"
        if 6 <= hora < 12:
            return "manha"
        if 12 <= hora < 18:
            return "tarde"
        if 18 <= hora <= 23:
            return "noite"
        return "desconhecido"

    df["hora"] = df["horario"].apply(_extract_hour)
    df["periodo_dia"] = df["hora"].apply(_periodo)

    grouped = aggregate_with_count(
        df,
        group_cols=["periodo_dia"],
        numeric_cols=None,
        count_col_name="total_acidentes",
    )

    return grouped.sort_values(by="total_acidentes", ascending=False)


def save_gold_table(df_gold: pd.DataFrame, name: str) -> Path:
    """Salva uma tabela Gold em CSV na pasta Gold."""
    dest = GOLD_DIR / name
    df_gold.to_csv(dest, index=False)
    logging.info("Tabela Gold salva em: %s (shape=%s)", dest, df_gold.shape)
    return dest


def run_silver_to_gold_analytics() -> None:
    """Executa o pipeline Silver -> Gold (versão analítica)."""
    ensure_dirs()

    logging.info("Contexto: cwd=%s", Path.cwd())
    logging.info("SILVER_DIR=%s | GOLD_DIR=%s", SILVER_DIR, GOLD_DIR)

    df_silver = load_silver_main()

    # 1) acidentes por UF
    df_uf = build_accidents_by_uf(df_silver)
    save_gold_table(df_uf, "gold_acidentes_por_uf.csv")

    # 2) acidentes por tipo
    df_tipo = build_accidents_by_tipo(df_silver)
    save_gold_table(df_tipo, "gold_acidentes_por_tipo.csv")

    # 3) acidentes por causa
    df_causa = build_accidents_by_causa(df_silver)
    save_gold_table(df_causa, "gold_acidentes_por_causa.csv")

    # 4) acidentes por período do dia (opcional: se a coluna existir)
    if "horario" in df_silver.columns:
        df_periodo = build_accidents_by_periodo_dia(df_silver)
        save_gold_table(df_periodo, "gold_acidentes_por_periodo_dia.csv")
    else:
        logging.warning("Coluna 'horario' não existe na Silver. Pulando 'periodo_dia'.")


if __name__ == "__main__":
    ensure_dirs()
    setup_logging(str(LOGS_DIR / "silver_to_gold_analytics.log"))
    logging.info("Iniciando pipeline Silver -> Gold (analítico).")
    run_silver_to_gold_analytics()
    logging.info("Pipeline Silver -> Gold (analítico) finalizado.")
