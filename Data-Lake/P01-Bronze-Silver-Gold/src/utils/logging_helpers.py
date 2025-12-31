"""
logging_helpers.py

Centraliza a configuração de logging para todos os pipelines.
Permite:
- logging em arquivo e console
- formatação padronizada
- evitar handlers duplicados
"""

from __future__ import annotations
import logging
from pathlib import Path


def setup_logging(log_file: str | Path) -> None:
    """
    Configura logging para um script de pipeline.

    Parâmetro:
        log_file: caminho do arquivo de log (Path ou str)

    Uso:
        setup_logging("logs/bronze_to_silver.log")
    """

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers ao rodar várias vezes no mesmo processo
    if logger.handlers:
        return

    # Handler de arquivo
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)

    # Handler de console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
