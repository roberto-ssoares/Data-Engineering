from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime

import pandas as pd


def safe_read_excel(
    file_path: Path,
    sheet_name: str,
    nrows: int = 5,
) -> pd.DataFrame:
    """
    Lê planilha com fallback de engine.
    """
    # openpyxl costuma resolver .xlsx
    return pd.read_excel(file_path, sheet_name=sheet_name, nrows=nrows, engine="openpyxl")


def inspect_xlsx_file(file_path: Path, sample_rows: int = 5) -> dict:
    """
    Inspeciona um arquivo XLSX:
    - abas
    - colunas (header)
    - amostra (primeiras linhas)
    """
    xls = pd.ExcelFile(file_path, engine="openpyxl")
    meta: dict = {
        "file": str(file_path),
        "filename": file_path.name,
        "sheets": [],
        "inspected_at": datetime.now().isoformat(timespec="seconds"),
    }

    for sheet in xls.sheet_names:
        try:
            df = safe_read_excel(file_path, sheet, nrows=sample_rows)
            # Normaliza colunas para string (evita None/NaN)
            cols = [str(c).strip() for c in df.columns.tolist()]
            # preview = df.head(sample_rows).to_dict(orient="records")
            preview_df = df.head(sample_rows).copy()

            # Converte datetime/date para string ISO
            for col in preview_df.columns:
                if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
                    preview_df[col] = preview_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            # Converte NaN para None (JSON não tem NaN)
            preview_df = preview_df.where(pd.notnull(preview_df), None)

            preview = preview_df.to_dict(orient="records")

            meta["sheets"].append(
                {
                    "sheet_name": sheet,
                    "n_preview_rows": int(len(df)),
                    "columns": cols,
                    "preview_rows": preview,
                }
            )
        except Exception as e:
            meta["sheets"].append(
                {
                    "sheet_name": sheet,
                    "error": f"{type(e).__name__}: {e}",
                }
            )

    return meta


def main() -> None:
    # Ajuste se seu repo estiver em outro lugar
    project_root = Path(__file__).resolve().parents[1]
    raw_root = project_root / "data" / "raw" / "enade"

    if not raw_root.exists():
        raise FileNotFoundError(f"[ERRO] Não encontrei o diretório: {raw_root}")

    out_dir = project_root / "docs" / "schema_snapshot"
    out_dir.mkdir(parents=True, exist_ok=True)

    years = sorted([p for p in raw_root.iterdir() if p.is_dir() and p.name.isdigit()])

    print("============================================================")
    print("ENADE XLSX INSPECTOR")
    print("============================================================")
    print(f"Project root : {project_root}")
    print(f"Raw root     : {raw_root}")
    print(f"Years found  : {[y.name for y in years]}")
    print(f"Output dir   : {out_dir}")
    print("------------------------------------------------------------")

    all_meta: list[dict] = []

    for year_dir in years:
        year = year_dir.name
        xlsx_files = sorted(year_dir.glob("*.xlsx"))

        print(f"\n[ANO {year}] Arquivos XLSX: {len(xlsx_files)}")
        if not xlsx_files:
            continue

        for f in xlsx_files:
            print(f"  - Inspecionando: {f.name}")
            meta = inspect_xlsx_file(f, sample_rows=5)
            meta["ano_enade"] = int(year)

            # Salva um JSON por arquivo
            json_path = out_dir / f"{year}__{f.stem}__schema.json"
            with open(json_path, "w", encoding="utf-8") as fp:
                json.dump(meta, fp, ensure_ascii=False, indent=2, default=str)

            # Salva também um “columns-only” (mais prático para mapear)
            # Pega a primeira aba com colunas válidas
            cols_only = {"file": str(f), "ano_enade": int(year), "columns_by_sheet": {}}
            for sh in meta["sheets"]:
                if "columns" in sh:
                    cols_only["columns_by_sheet"][sh["sheet_name"]] = sh["columns"]

            cols_path = out_dir / f"{year}__{f.stem}__columns.json"
            with open(cols_path, "w", encoding="utf-8") as fp:
                json.dump(cols_only, fp, ensure_ascii=False, indent=2)

            all_meta.append(meta)

    # Snapshot geral (index)
    index_path = out_dir / "INDEX__schema_snapshot.json"
    with open(index_path, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "raw_root": str(raw_root),
                "files_inspected": len(all_meta),
                "items": [
                    {
                        "ano_enade": m.get("ano_enade"),
                        "filename": m.get("filename"),
                        "file": m.get("file"),
                        "sheets": [s.get("sheet_name") for s in m.get("sheets", [])],
                    }
                    for m in all_meta
                ],
            },
            fp,
            ensure_ascii=False,
            indent=2,
        )

    print("\n------------------------------------------------------------")
    print("[OK] Snapshot gerado em:")
    print(f"  {out_dir}")
    print("Arquivos principais:")
    print(f"  - {index_path.name}")
    print("  - <ano>__<arquivo>__schema.json (com preview)")
    print("  - <ano>__<arquivo>__columns.json (só colunas)")
    print("============================================================")


if __name__ == "__main__":
    main()
