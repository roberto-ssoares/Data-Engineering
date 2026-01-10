import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

P01_ROOT = "/opt/p01"
P01_SRC = "/opt/p01/src"

LAYER_NAME = "gold_advanced"
GOLD_DIR = f"{P01_ROOT}/data/{LAYER_NAME}"
SUCCESS_MARKER = "_SUCCESS"


def _fmt_mtime(path: str) -> str:
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat()


def _clean_dir(directory: str) -> int:
    """
    Remove files/dirs from directory except .gitkeep.
    Cuidado: aqui removemos também subpastas (partições ano=/mes=).
    """
    removed = 0
    if not os.path.isdir(directory):
        return removed

    for name in os.listdir(directory):
        p = os.path.join(directory, name)

        # Preserve .gitkeep
        if name == ".gitkeep":
            continue

        if os.path.isfile(p):
            os.remove(p)
            removed += 1
        elif os.path.isdir(p):
            shutil.rmtree(p)
            removed += 1

    return removed


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
                # arquivo pode sumir entre walk e stat
                continue
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
        f"[P02 silver_to_gold_advanced] wrote marker: {marker_path} "
        f"mtime={_fmt_mtime(marker_path)} size_bytes={os.path.getsize(marker_path)}"
    )


def _run_p01(script_path: str) -> None:

    PY_BIN = os.getenv("AIRFLOW_PY_BIN", "/home/airflow/.local/bin/python3")
    cmd = [PY_BIN, script_path]
    print(f"[P02 silver_to_gold_advanced] python_bin={PY_BIN}")

    env = os.environ.copy()
    #env["PYTHONPATH"] = P01_SRC
    env["PYTHONPATH"] = f"{P01_SRC}:{env.get('PYTHONPATH','')}".strip(":")

    print(f"[P02 silver_to_gold_advanced] running: {' '.join(cmd)} (cwd={P01_ROOT})")

    result = subprocess.run(
        cmd,
        cwd=P01_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.stdout.strip():
        print("[P02 silver_to_gold_advanced] P01 STDOUT:\n", result.stdout)

    if result.returncode != 0:
        print("[P02 silver_to_gold_advanced] P01 STDERR:\n", result.stderr)
        raise RuntimeError(f"silver_to_gold_advanced failed with exit code {result.returncode}")


def main() -> None:
    FORCE = os.getenv("P02_FORCE_REPROCESS_GOLD_ADVANCED", "0") == "1"

    # garantir diretório existir (para marker e para escrita do pipeline)
    os.makedirs(GOLD_DIR, exist_ok=True)

    if FORCE:
        removed = _clean_dir(GOLD_DIR)
        print(
            "[P02 silver_to_gold_advanced] FORCE enabled: cleaned gold_advanced layer, "
            f"removed_entries={removed}"
        )

    before = _snapshot_files_recursive(GOLD_DIR)

    # roda o P01 advanced
    _run_p01(f"{P01_SRC}/transformation/silver_to_gold_advanced.py")

    after = _snapshot_files_recursive(GOLD_DIR)

    # filtra arquivos "de dados" (ignora dotfiles e marker)
    data_files = [
        f for f in after.keys()
        if not os.path.basename(f).startswith(".")
        and os.path.basename(f) != SUCCESS_MARKER
    ]
    print(f"[P02 silver_to_gold_advanced] gold_advanced_files={len(data_files)} in {GOLD_DIR}")

    # Validar saída mínima (evitar _SUCCESS vazio)
    if len(data_files) == 0:
        raise RuntimeError(
            f"No output data files produced in {GOLD_DIR}. "
            "Refusing to write _SUCCESS."
            )

    # detectar mudanças (mtime/size)
    changed = []
    for f, (m_after, s_after) in after.items():
        if os.path.basename(f) == SUCCESS_MARKER:
            continue

        prev = before.get(f)
        if prev is None:
            changed.append((f, "CREATED", m_after, s_after))
        else:
            m_before, s_before = prev
            if (m_after > m_before) or (s_after != s_before):
                changed.append((f, "UPDATED", m_after, s_after))

    if not changed and not FORCE:
        print("[P02 silver_to_gold_advanced] INFO: No gold_advanced files updated in this run (idempotency/skip).")
    else:
        print("[P02 silver_to_gold_advanced] Changed files:")
        for f, kind, m, s in sorted(changed, key=lambda x: x[0]):
            print(f"  - {kind}: {f} mtime={datetime.fromtimestamp(m, tz=timezone.utc).isoformat()} size_bytes={s}")

    # marcador de evidência
    _write_success_marker()
    print("[P02 silver_to_gold_advanced] done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[P02 silver_to_gold_advanced] ERROR: {e}")
        sys.exit(1)
