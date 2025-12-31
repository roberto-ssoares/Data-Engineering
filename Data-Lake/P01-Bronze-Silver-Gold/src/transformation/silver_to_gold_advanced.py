
"""
Pipeline: Silver -> Gold (versão C - avançada)

Responsável por:
- Ler o dataset principal da camada Silver
- Validar schema mínimo para o pipeline
- Enriquecer o dataset (ano, mês, dia, hora, período do dia)
- Gerar:
    - Tabela de fatos: fact_acidentes
    - Dimensão de localidade: dim_localidade
- Salvar a fact particionada em ano=YYYY/mes=MM (estilo Data Lake)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Set, Dict, Any

import pandas as pd
import sys

# -------------------------------------------------------------------
# Helpers de import (mesmo padrão dos outros scripts)
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

SILVER_FILE_NAME = "dados-prf-2023.csv"  # ajuste se mudar o nome

# -------------------------------------------------------------------
# Helpers gerais
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
    """
    Valida se o dataset Silver possui o conjunto mínimo de colunas necessárias.

    Se houver colunas ausentes, gera log de erro e lança exceção.
    """
    cols = set(df.columns)
    missing = REQUIRED_COLUMNS - cols

    if missing:
        msg = f"Schema inválido. Colunas obrigatórias ausentes: {sorted(missing)}"
        logging.error(msg)
        raise ValueError(msg)

    logging.info("Schema Silver validado com sucesso. Colunas obrigatórias presentes.")


# -------------------------------------------------------------------
# Enriquecimento do dataset
# -------------------------------------------------------------------

def _extract_hour(value: Any) -> int | None:
    try:
        parts = str(value).split(":")
        return int(parts[0])
    except Exception:
        return None


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


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquecimento:
    - Converte data_inversa para datetime
    - Cria ano, mes, dia
    - Extrai hora e período do dia a partir de 'horario'
    """
    df = df.copy()

    # data_inversa -> datetime
    try:
        df["data_inversa"] = pd.to_datetime(df["data_inversa"])
    except Exception as e:
        logging.warning("Falha ao converter 'data_inversa' para datetime: %s", str(e))

    if pd.api.types.is_datetime64_any_dtype(df.get("data_inversa")):
        df["ano"] = df["data_inversa"].dt.year
        df["mes"] = df["data_inversa"].dt.month
        df["dia"] = df["data_inversa"].dt.day
    else:
        logging.warning(
            "Coluna 'data_inversa' não está em formato datetime. "
            "Colunas 'ano', 'mes', 'dia' não serão criadas."
        )

    # horario -> hora, periodo_dia
    df["hora"] = df["horario"].apply(_extract_hour)
    df["periodo_dia"] = df["hora"].apply(_periodo)

    logging.info("Enriquecimento concluído. Colunas adicionadas: ano, mes, dia, hora, periodo_dia.")
    return df


# -------------------------------------------------------------------
# Criação de Dimensões e Fatos
# -------------------------------------------------------------------

def build_dim_localidade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria dimensão de localidade com UF e município.

    Remove duplicados e ordena para uso em BI.
    """
    dim = df[["uf", "municipio"]].drop_duplicates().reset_index(drop=True)
    dim = dim.sort_values(by=["uf", "municipio"])
    logging.info("Dimensão localidade criada com shape: %s", dim.shape)
    return dim


def build_fact_acidentes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria tabela de fatos de acidentes com colunas relevantes para análise.

    Inclui:
    - data_inversa, ano, mes, dia
    - uf, municipio
    - tipo_acidente, causa_acidente
    - horario, hora, periodo_dia
    - colunas numéricas como mortos, feridos, ilesos (se existirem)
    """
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

    final_cols: List[str] = []

    for col in base_cols:
        if col in df.columns:
            final_cols.append(col)

    for col in NUMERIC_CANDIDATES:
        if col in df.columns:
            final_cols.append(col)

    fact = df[final_cols].copy()
    logging.info("Tabela fato fact_acidentes criada com shape: %s", fact.shape)
    return fact


# -------------------------------------------------------------------
# Salvando em formato particionado (ano/mes)
# -------------------------------------------------------------------

def save_dim_localidade(dim: pd.DataFrame) -> Path:
    dest = GOLD_DIR / "dim_localidade.csv"
    dim.to_csv(dest, index=False)
    logging.info("Dimensão localidade salva em: %s", dest)
    return dest


def save_fact_partitioned_by_year_month(fact: pd.DataFrame) -> None:
    """
    Salva a tabela de fatos particionada em diretórios de ano e mês.

    Exemplo:
        data/gold/ano=2023/mes=1/fact_acidentes.csv
    """
    if "ano" not in fact.columns or "mes" not in fact.columns:
        logging.warning(
            "Colunas 'ano' e 'mes' não encontradas em fact_acidentes. "
            "Salvando tabela completa sem particionamento."
        )
        dest = GOLD_DIR / "fact_acidentes.csv"
        fact.to_csv(dest, index=False)
        logging.info("Fato salvo sem particionamento em: %s", dest)
        return

    # garante tipo inteiro
    fact = fact.copy()
    fact["ano"] = fact["ano"].astype("Int64")
    fact["mes"] = fact["mes"].astype("Int64")

    grupos = fact.groupby(["ano", "mes"], dropna=False)

    for (ano, mes), df_part in grupos:
        # tratar caso de ano/mes nulos
        if pd.isna(ano) or pd.isna(mes):
            subdir = GOLD_DIR / "ano=desconhecido" / "mes=desconhecido"
        else:
            subdir = GOLD_DIR / f"ano={int(ano)}" / f"mes={int(mes):02d}"

        subdir.mkdir(parents=True, exist_ok=True)
        dest = subdir / "fact_acidentes.csv"
        df_part.to_csv(dest, index=False)
        logging.info(
            "Fato particionado salvo em: %s (shape=%s)", dest, df_part.shape
        )


# -------------------------------------------------------------------
# Pipeline principal
# -------------------------------------------------------------------

def run_silver_to_gold_advanced() -> None:
    """Executa o pipeline Silver -> Gold (versão avançada)."""
    ensure_dirs()

    try:
        df_silver = load_silver_main()
    except Exception as e:
        logging.error("Erro ao carregar Silver: %s", str(e))
        return

    # 1) valida schema
    try:
        validate_schema(df_silver)
    except Exception as e:
        logging.error("Erro de schema na Silver: %s", str(e))
        return

    # 2) enriquecer dataset
    df_enriched = enrich_dataset(df_silver)

    # 3) criar dimensão localidade
    try:
        dim_localidade = build_dim_localidade(df_enriched)
        save_dim_localidade(dim_localidade)
    except Exception as e:
        logging.error("Erro ao criar/salvar dim_localidade: %s", str(e))

    # 4) criar fato acidentes
    try:
        fact_acidentes = build_fact_acidentes(df_enriched)
        save_fact_partitioned_by_year_month(fact_acidentes)
    except Exception as e:
        logging.error("Erro ao criar/salvar fact_acidentes: %s", str(e))


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging("logs/silver_to_gold_advanced.log")
    logging.info("Iniciando pipeline Silver -> Gold (avançado).")
    run_silver_to_gold_advanced()
    logging.info("Pipeline Silver -> Gold (avançado) finalizado.")
