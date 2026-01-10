import os
import subprocess
import sys
from datetime import datetime, timezone

P01_ROOT = "/opt/p01"
P01_SRC = "/opt/p01/src"

LAYER_NAME = "gold_basic"
GOLD_DIR = f"{P01_ROOT}/data/{LAYER_NAME}"
SUCCESS_MARKER = "_SUCCESS"


def _fmt_mtime(path: str) -> str:
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()

def _snapshot_files_recursive(directory: str) -> dict:
    """
    Snapshot recursivo: {filepath: (mtime, size_bytes)}
    """
    snap = {}
    if not os.path.isdir(directory):
        return snap

    for root, _, files in os.walk(directory):
        for name in files:
            p = os.path.join(root, name)
            try:
                snap[p] = (os.path.getmtime(p), os.path.getsize(p))
            except FileNotFoundError:
                continue
    return snap

def _snapshot_files(directory: str) -> dict:
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

    marker_path = os.path.join(GOLD_DIR, SUCCESS_MARKER)

    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"layer={LAYER_NAME}\n")
        f.write(f"utc_processed_at={processed_at}\n")
        f.write(f"run_id={run_id}\n")
        f.write(f"logical_date={logical_date}\n")

    print(
        f"[P02 silver_to_gold_basic] wrote marker: {marker_path} "
        f"mtime={_fmt_mtime(marker_path)} size_bytes={os.path.getsize(marker_path)}"
    )

def _run_p01(script_path: str) -> None:
    

    PY_BIN = os.getenv("AIRFLOW_PY_BIN", "/home/airflow/.local/bin/python3")
    cmd = [PY_BIN, script_path]
    print(f"[P02 silver_to_gold_basic] python_bin={PY_BIN}")

    env = os.environ.copy()
    #env["PYTHONPATH"] = P01_SRC
    env["PYTHONPATH"] = f"{P01_SRC}:{env.get('PYTHONPATH','')}".strip(":")
    print(f"[P02 silver_to_gold_basic] running: {' '.join(cmd)} (cwd={P01_ROOT})")

    result = subprocess.run(cmd, cwd=P01_ROOT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        print("[P02 silver_to_gold_basic] STDOUT:\n", result.stdout)
        print("[P02 silver_to_gold_basic] STDERR:\n", result.stderr)
        raise RuntimeError(f"silver_to_gold_basic failed with exit code {result.returncode}")

    if result.stdout.strip():
        print("[P02 silver_to_gold_basic] P01 STDOUT:\n", result.stdout)


def main() -> None:
    FORCE = os.getenv("P02_FORCE_REPROCESS_GOLD_BASIC", "0") == "1"

    os.makedirs(GOLD_DIR, exist_ok=True)

    if FORCE:
        removed = _clean_dir(GOLD_DIR)
        print(f"[P02 silver_to_gold_basic] FORCE enabled: cleaned gold_basic layer, removed_files={removed}")

    before = _snapshot_files(GOLD_DIR)

    _run_p01(f"{P01_SRC}/transformation/silver_to_gold_basic.py")

    after = _snapshot_files(GOLD_DIR)

    data_files = [
        f for f in after.keys()
        if not os.path.basename(f).startswith(".")
        and os.path.basename(f) != SUCCESS_MARKER
    ]
    print(f"[P02 silver_to_gold_basic] gold_basic_files={len(data_files)} in {GOLD_DIR}")

    # Validar saída mínima (evitar _SUCCESS vazio)
    if len(data_files) == 0:
        raise RuntimeError(
            f"No output data files produced in {GOLD_DIR}. "
            "Refusing to write _SUCCESS."
            )

    changed = []
    for f, m_after in after.items():
        m_before = before.get(f)
        if (m_before is None) or (m_after > m_before):
            if os.path.basename(f) != SUCCESS_MARKER:
                changed.append(f)

    if not changed and not FORCE:
        print("[P02 silver_to_gold_basic] INFO: No gold_basic data files updated in this run (idempotency/skip).")
    else:
        print("[P02 silver_to_gold_basic] Updated/created gold_basic data files:")
        for f in sorted(changed):
            print(f"  - {f} mtime={_fmt_mtime(f)} size_bytes={os.path.getsize(f)}")

    _write_success_marker()
    print("[P02 silver_to_gold_basic] done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[P02 silver_to_gold_basic] ERROR: {e}")
        sys.exit(1)
