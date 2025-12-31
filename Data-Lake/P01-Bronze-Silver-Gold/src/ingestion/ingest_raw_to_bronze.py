import os
import shutil
from pathlib import Path

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")

def ensure_dirs():
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

def ingest_files():
    """
    Simple local ingestion:
    copies all files from raw/ to bronze/.
    In a real scenario, this would be replaced by
    S3 downloads or streaming ingestion.
    """
    for file in RAW_DIR.glob("*"):
        if file.is_file():
            dest = BRONZE_DIR / file.name
            shutil.copy2(file, dest)
            print(f"Ingested {file.name} -> {dest}")

if __name__ == "__main__":
    ensure_dirs()
    ingest_files()
