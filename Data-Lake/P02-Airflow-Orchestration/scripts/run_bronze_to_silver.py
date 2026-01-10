import os
import subprocess
import sys
from datetime import datetime, timezone

P01_ROOT = "/opt/p01"
P01_SRC = "/opt/p01/src"

LAYER_NAME = "silver"
SILVER_DIR = f"{P01_ROOT}/data/{LAYER_NAME}"
SUCCESS_MARKER = "_SUCCESS"


def _fmt_mtime(path: str) -> str:
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()


def _clean_dir(directory: str) -> int:
    removed = 0
    if not os.path.isdir(directory):
        return removed
    for name in os.listdir(directory):
        if name in [".gitkeep", SUCCESS_MARKER]:
            continue
        p = os.path.join(directory, name)
        if os.path.isfile(p):
            os.remove(p)
            removed += 1
    return removed


def _snapshot_files(directory: str) -> dict:
    snap = {}
    if not os.path.isdir(directory):
        return snap
    for name in os.listdir(directory):
        if name in [".gitkeep", SUCCESS_MARKER]:
            continue
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

    marker_path = os.path.join(SILVER_DIR, SUCCESS_MARKER)

    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"layer={LAYER_NAME}\n")
        f.write(f"utc_processed_at={processed_at}\n")
        f.write(f"run_id={run_id}\n")
        f.write(f"logical_date={logical_date}\n")

    print(
        f"[P02 bronze_to_silver] wrote marker: {marker_path} "
        f"mtime={_fmt_mtime(marker_path)} size_bytes={os.path.getsize(marker_path)}"
    )


def _run_p01(script_path: str) -> None:
    # Pré-checks (falha rápida e clara)
    if not os.path.isdir(P01_ROOT):
        raise RuntimeError(f"P01_ROOT not found: {P01_ROOT}")
    if not os.path.isfile(script_path):
        raise RuntimeError(f"P01 script not found: {script_path}")

    PY_BIN = os.getenv("AIRFLOW_PY_BIN", "/home/airflow/.local/bin/python3")
    cmd = [PY_BIN, script_path]
    print(f"[P02 bronze_to_silver] python_bin={PY_BIN}")

    env = os.environ.copy()

    # Se você quiser manter PYTHONPATH, faça append (não sobrescreva)
    env["PYTHONPATH"] = f"{P01_SRC}:{env.get('PYTHONPATH','')}".strip(":")

    print(f"[P02 bronze_to_silver] running: {' '.join(cmd)} (cwd={P01_ROOT})")

    result = subprocess.run(
        cmd,
        cwd=P01_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print("[P02 bronze_to_silver] STDOUT:\n", result.stdout)
        print("[P02 bronze_to_silver] STDERR:\n", result.stderr)
        raise RuntimeError(f"bronze_to_silver failed with exit code {result.returncode}")

    if result.stdout.strip():
        print("[P02 bronze_to_silver] P01 STDOUT:\n", result.stdout)


def main() -> None:
    FORCE = os.getenv("P02_FORCE_REPROCESS_SILVER", "0") == "1"

    # Garante diretório existir para o marker, e para limpeza quando FORCE
    os.makedirs(SILVER_DIR, exist_ok=True)

    if FORCE:
        removed = _clean_dir(SILVER_DIR)
        print(f"[P02 bronze_to_silver] FORCE enabled: cleaned silver layer, removed_files={removed}")

    before = _snapshot_files(SILVER_DIR)

    _run_p01(f"{P01_SRC}/transformation/bronze_to_silver.py")

    after = _snapshot_files(SILVER_DIR)

    data_files = list(after.keys())
    print(f"[P02 bronze_to_silver] silver_files={len(data_files)} in {SILVER_DIR}")

    # Validar saída mínima (evitar _SUCCESS vazio)
    if len(data_files) == 0:
        raise RuntimeError(
            f"No output data files produced in {SILVER_DIR}. "
            "Refusing to write _SUCCESS."
            )

    changed = []
    for f, m_after in after.items():
        m_before = before.get(f)
        if (m_before is None) or (m_after > m_before):
            changed.append(f)

    if not changed and not FORCE:
        print("[P02 bronze_to_silver] INFO: No silver data files updated in this run (idempotency/skip).")
    else:
        print("[P02 bronze_to_silver] Updated/created silver data files:")
        for f in sorted(changed):
            print(f"  - {f} mtime={_fmt_mtime(f)} size_bytes={os.path.getsize(f)}")

    #_write_success_marker(SILVER_DIR, "silver")
    _write_success_marker()
    print("[P02 bronze_to_silver] done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[P02 bronze_to_silver] ERROR: {e}")
        sys.exit(1)
