"""
Pipeline: Silver -> Gold (versão C - avançada)

Responsável por:
- Ler o dataset principal da camada Silver
- Validar schema mínimo para o pipeline
- Enriquecer o dataset (ano, mês, dia, hora, período do dia)
- Gerar:
    - Tabela de fatos: fact_acidentes (particionada por ano/mes)
    - Dimensão de localidade: dim_localidade
- Salvar a fact particionada em ano=YYYY/mes=MM (estilo Data Lake)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, List, Optional, Set

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

# IMPORTANTE: advanced em uma camada separada (para não misturar com gold simples/analytics)
GOLD_ADV_DIR = DATA_DIR / "gold_advanced"

# Nome do arquivo principal na Silver (ajuste se necessário)
SILVER_FILE_NAME = "dados-prf-2023.csv"
# Carrega o dataset principal da camada Silver.
silver_path = SILVER_DIR / SILVER_FILE_NAME

def ensure_dirs() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_ADV_DIR.mkdir(parents=True, exist_ok=True)


def load_silver_main() -> pd.DataFrame:

    if not silver_path.exists():
        raise FileNotFoundError(f"Arquivo Silver não encontrado: {silver_path}")

    logging.info("Lendo arquivo Silver: %s", silver_path)
    df = read_csv_flexible(silver_path)
    logging.info("Arquivo Silver carregado com shape=%s", df.shape)
    return df


# -------------------------------------------------------------------
# Validação de schema
# -------------------------------------------------------------------

REQUIRED_COLUMNS: Set[str] = {
    "data_inversa",
    "uf",
    "municipio",
    "tipo_acidente",
    "causa_acidente",
    "horario",
}

NUMERIC_CANDIDATES: List[str] = [
    "mortos",
    "feridos_graves",
    "feridos_leves",
    "ilesos",
]


def validate_schema(df: pd.DataFrame) -> None:
    cols = set(df.columns)
    missing = REQUIRED_COLUMNS - cols

    if missing:
        msg = f"Schema inválido. Colunas obrigatórias ausentes: {sorted(missing)}"
        logging.error(msg)
        raise ValueError(msg)

    logging.info("Schema Silver validado com sucesso.")


# -------------------------------------------------------------------
# Enriquecimento do dataset
# -------------------------------------------------------------------

def _extract_hour(value: Any) -> Optional[int]:
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


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquecimento:
    - data_inversa -> datetime (tentativa)
    - cria ano, mes, dia
    - horario -> hora e periodo_dia
    """
    df = df.copy()

    # data_inversa -> datetime
    try:
        df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    except Exception as e:
        logging.warning("Falha ao converter 'data_inversa' para datetime: %s", str(e))

    # ano/mes/dia (somente onde data_inversa for válida)
    if "data_inversa" in df.columns and pd.api.types.is_datetime64_any_dtype(df["data_inversa"]):
        df["ano"] = df["data_inversa"].dt.year
        df["mes"] = df["data_inversa"].dt.month
        df["dia"] = df["data_inversa"].dt.day
    else:
        logging.warning("Coluna 'data_inversa' não está datetime. 'ano/mes/dia' não serão criadas.")

    # horario -> hora, periodo_dia
    df["hora"] = df["horario"].apply(_extract_hour)
    df["periodo_dia"] = df["hora"].apply(_periodo)

    logging.info("Enriquecimento concluído. Colunas adicionadas: ano, mes, dia, hora, periodo_dia.")
    return df


# -------------------------------------------------------------------
# Dimensão e Fato
# -------------------------------------------------------------------

def build_dim_localidade(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["uf", "municipio"]].drop_duplicates().reset_index(drop=True)
    dim = dim.sort_values(by=["uf", "municipio"])
    logging.info("Dimensão dim_localidade criada com shape=%s", dim.shape)
    return dim


def build_fact_acidentes(df: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "data_inversa",
        "ano",
        "mes",
        "dia",
        "uf",
        "municipio",
        "tipo_acidente",
        "causa_acidente",
        "horario",
        "hora",
        "periodo_dia",
    ]

    final_cols: List[str] = [c for c in base_cols if c in df.columns]
    for c in NUMERIC_CANDIDATES:
        if c in df.columns:
            final_cols.append(c)

    fact = df[final_cols].copy()
    logging.info("Fato fact_acidentes criado com shape=%s", fact.shape)
    return fact


# -------------------------------------------------------------------
# Salvando
# -------------------------------------------------------------------

def save_dim_localidade(dim: pd.DataFrame) -> Path:
    dest = GOLD_ADV_DIR / "dim_localidade.csv"
    dim.to_csv(dest, index=False)
    logging.info("Dimensão dim_localidade salva em: %s", dest)
    return dest


def save_fact_partitioned_by_year_month(fact: pd.DataFrame) -> None:
    """
    Exemplo:
      data/gold_advanced/ano=2023/mes=01/fact_acidentes.csv
    """
    if "ano" not in fact.columns or "mes" not in fact.columns:
        logging.warning("Sem 'ano/mes'. Salvando fact completa sem particionamento.")
        dest = GOLD_ADV_DIR / "fact_acidentes.csv"
        fact.to_csv(dest, index=False)
        logging.info("Fato salvo sem particionamento em: %s", dest)
        return

    fact = fact.copy()

    # Garantir inteiros “seguros” (permitindo NaN)
    fact["ano"] = fact["ano"].astype("Int64")
    fact["mes"] = fact["mes"].astype("Int64")

    grupos = fact.groupby(["ano", "mes"], dropna=False)

    for (ano, mes), df_part in grupos:
        if pd.isna(ano) or pd.isna(mes):
            subdir = GOLD_ADV_DIR / "ano=desconhecido" / "mes=desconhecido"
        else:
            subdir = GOLD_ADV_DIR / f"ano={int(ano)}" / f"mes={int(mes):02d}"

        subdir.mkdir(parents=True, exist_ok=True)
        dest = subdir / "fact_acidentes.csv"
        df_part.to_csv(dest, index=False)

        logging.info("Fato particionado salvo em: %s (shape=%s)", dest, df_part.shape)


# -------------------------------------------------------------------
# Pipeline principal
# -------------------------------------------------------------------

def run_silver_to_gold_advanced() -> None:
    ensure_dirs()

    logging.info("Contexto: cwd=%s", Path.cwd())
    logging.info("SILVER_DIR=%s | GOLD_ADV_DIR=%s", SILVER_DIR, GOLD_ADV_DIR)

    df_silver = load_silver_main()
    validate_schema(df_silver)

    df_enriched = enrich_dataset(df_silver)

    # Dimensão
    dim_localidade = build_dim_localidade(df_enriched)
    save_dim_localidade(dim_localidade)

    # Fato particionada
    fact_acidentes = build_fact_acidentes(df_enriched)
    save_fact_partitioned_by_year_month(fact_acidentes)


if __name__ == "__main__":
    ensure_dirs()
    setup_logging(str(LOGS_DIR / "silver_to_gold_advanced.log"))
    logging.info("Iniciando pipeline Silver -> Gold (avançado).")
    run_silver_to_gold_advanced()
    logging.info("Pipeline Silver -> Gold (avançado) finalizado.")
