import os
import subprocess
import sys
from datetime import datetime, timezone

P01_ROOT = "/opt/p01"
P01_SRC = "/opt/p01/src"

LAYER_NAME = "bronze"
BRONZE_DIR = f"{P01_ROOT}/data/{LAYER_NAME}"
SUCCESS_MARKER = "_SUCCESS"


def _fmt_mtime(path: str) -> str:
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()

def _clean_bronze_dir() -> int:
    """Remove files from BRONZE_DIR except .gitkeep (and directories)."""
    removed = 0
    if not os.path.isdir(BRONZE_DIR):
        return removed

    for name in os.listdir(BRONZE_DIR):
        p = os.path.join(BRONZE_DIR, name)

        # Preserve .gitkeep
        if name == ".gitkeep":
            continue

        # Remove only files (not folders)
        if os.path.isfile(p):
            os.remove(p)
            removed += 1

    return removed

def _snapshot_files(directory: str) -> dict:
    """Return {filepath: mtime} snapshot for regular files in directory."""
    snap = {}
    if not os.path.isdir(directory):
        return snap

    for name in os.listdir(directory):
        p = os.path.join(directory, name)
        if os.path.isfile(p):
            snap[p] = os.path.getmtime(p)
    return snap

def _write_success_marker():
    processed_at = datetime.now(timezone.utc).isoformat()

    run_id = os.getenv("AIRFLOW_CTX_DAG_RUN_ID") or "manual"
    logical_date = (
        os.getenv("AIRFLOW_CTX_EXECUTION_DATE")
        or os.getenv("AIRFLOW_CTX_LOGICAL_DATE")
        or processed_at
    )

    marker_path = os.path.join(BRONZE_DIR, SUCCESS_MARKER)

    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"layer={LAYER_NAME}\n")
        f.write(f"utc_processed_at={processed_at}\n")
        f.write(f"run_id={run_id}\n")
        f.write(f"logical_date={logical_date}\n")

    print(
        f"[P02 raw_to_bronze] wrote marker: {marker_path} "
        f"run_id={run_id} logical_date={logical_date}"
    )

    print(
        f"[P02 raw_to_bronze] wrote marker: {marker_path} "
        f"mtime={_fmt_mtime(marker_path)} size_bytes={os.path.getsize(marker_path)}"
    )

def main():
    # Toggle para reprocessamento completo da camada Bronze
    FORCE = os.getenv("P02_FORCE_REPROCESS_BRONZE", "0") == "1"

    if not os.path.isdir(BRONZE_DIR):
        raise RuntimeError(f"Bronze dir not found: {BRONZE_DIR}")

    if FORCE:
        removed = _clean_bronze_dir()
        print(f"[P02 raw_to_bronze] FORCE enabled: cleaned bronze layer, removed_files={removed}")

    before = _snapshot_files(BRONZE_DIR)

    PY_BIN = os.getenv("AIRFLOW_PY_BIN", "/home/airflow/.local/bin/python3")
    cmd = [PY_BIN, f"{P01_SRC}/ingestion/ingest_raw_to_bronze.py"]
    print(f"[P02 raw_to_bronze] python_bin={PY_BIN}")
    print(f"[P02 raw_to_bronze] running: {' '.join(cmd)} (cwd={P01_ROOT})")

    env = os.environ.copy()
    # garante imports internos do P01 via /opt/p01/src quando necessário
    #env["PYTHONPATH"] = P01_SRC
    env["PYTHONPATH"] = f"{P01_SRC}:{env.get('PYTHONPATH','')}".strip(":")
    
    #result = subprocess.run(cmd, check=False, cwd=P01_ROOT, env=env)
    result = subprocess.run(cmd, cwd=P01_ROOT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        print("[P02 raw_to_bronze] STDOUT:\n", result.stdout)
        print("[P02 raw_to_bronze] STDERR:\n", result.stderr)
        raise RuntimeError(f"raw_to_bronze failed with exit code {result.returncode}")

    # Snapshot depois
    after = _snapshot_files(BRONZE_DIR)

    # Lista de arquivos "de dados" (ignorando .gitkeep)
    data_files = [f for f in after.keys() if not os.path.basename(f).startswith(".") and os.path.basename(f) != SUCCESS_MARKER]
    print(f"[P02 raw_to_bronze] bronze_files={len(data_files)} in {BRONZE_DIR}")

    # Validar saída mínima (evitar _SUCCESS vazio)
    if len(data_files) == 0:
        raise RuntimeError(
            f"No output data files produced in {GOLD_DIR}. "
            "Refusing to write _SUCCESS."
            )

    # Detectar atualizações
    changed = []
    for f, m_after in after.items():
        m_before = before.get(f)
        if (m_before is None) or (m_after > m_before):
            # Ignora marker aqui; ele será tratado depois
            if os.path.basename(f) != SUCCESS_MARKER:
                changed.append(f)

    if not changed and not FORCE:
        print("[P02 raw_to_bronze] INFO: No bronze data files updated in this run (idempotency/skip).")
    else:
        print("[P02 raw_to_bronze] Updated/created bronze data files:")
        for f in sorted(changed):
            print(f"  - {f} mtime={_fmt_mtime(f)} size_bytes={os.path.getsize(f)}")

    # Sempre escrever marcador de sucesso (evidência auditável de execução)
    _write_success_marker()

    print("[P02 raw_to_bronze] done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[P02 raw_to_bronze] ERROR: {e}")
        sys.exit(1)
