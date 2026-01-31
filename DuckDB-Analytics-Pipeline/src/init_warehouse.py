from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = PROJECT_ROOT / "warehouse"
DB_PATH = WAREHOUSE / "enade.duckdb"

WAREHOUSE.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH))

print(f"[OK] Warehouse criado/conectado em: {DB_PATH}")

con.close()
