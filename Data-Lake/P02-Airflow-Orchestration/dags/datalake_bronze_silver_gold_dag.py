from __future__ import annotations

from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

DAG_ID = "datalake_bronze_silver_gold"
SCRIPTS_DIR = "/opt/airflow/scripts"
P01_RAW_DIR = "/opt/p01/data/raw"

default_args = {
    "owner": "roberto",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "execution_timeout": timedelta(minutes=30),
}

with DAG(
    dag_id=DAG_ID,
    description="Orquestração batch Raw→Bronze→Silver→Gold (P02)",
    default_args=default_args,
    start_date=datetime(2026, 1, 1, tz="UTC"),
    schedule=None,  # manual
    catchup=False,
    max_active_runs=1,
    tags=["datalake", "batch", "p02", "airflow"],
) as dag:
    
    precheck_raw = BashOperator(
        task_id="precheck_raw",
        bash_command=f"""
    set -euo pipefail

    echo "[precheck_raw] Checking raw input folder: {P01_RAW_DIR}"

    if [ ! -d "{P01_RAW_DIR}" ]; then
      echo "[precheck_raw] ERROR: Raw folder does not exist: {P01_RAW_DIR}"
      exit 1
    fi

    FILE_COUNT=$(find "{P01_RAW_DIR}" -type f | wc -l | tr -d ' ')
    echo "[precheck_raw] Files found: $FILE_COUNT"

    if [ "$FILE_COUNT" -eq 0 ]; then
      echo "[precheck_raw] ERROR: No files found in raw folder: {P01_RAW_DIR}"
      exit 1
    fi

    echo "[precheck_raw] OK"
    """,
    )

    raw_to_bronze = BashOperator(
        task_id="raw_to_bronze",
        #bash_command=f"python {SCRIPTS_DIR}/run_raw_to_bronze.py",
        bash_command=f"""
        set -euo pipefail
        echo "[raw_to_bronze] run_id=$AIRFLOW_CTX_DAG_RUN_ID logical_date=$AIRFLOW_CTX_EXECUTION_DATE";
        python3 {SCRIPTS_DIR}/run_raw_to_bronze.py
        """,
        env={"P02_FORCE_REPROCESS_BRONZE": "1"},
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=f"""
        set -euo pipefail
        echo "[bronze_to_silver] run_id=$AIRFLOW_CTX_DAG_RUN_ID logical_date=$AIRFLOW_CTX_EXECUTION_DATE";
        python3 {SCRIPTS_DIR}/run_bronze_to_silver.py
        """,
        env={"P02_FORCE_REPROCESS_SILVER": "1"},
    )


    with TaskGroup(group_id="gold") as gold:
        
        BashOperator(
            task_id="silver_to_gold_basic",
            bash_command=f"""
            set -euo pipefail
            echo "[silver_to_gold_basic] run_id=$AIRFLOW_CTX_DAG_RUN_ID logical_date=$AIRFLOW_CTX_EXECUTION_DATE";
            python3 {SCRIPTS_DIR}/run_silver_to_gold_basic.py
            """,
        )

        BashOperator(
            task_id="silver_to_gold_analytics",
            bash_command=f"""
            set -euo pipefail
            echo "[silver_to_gold_analytics] run_id=$AIRFLOW_CTX_DAG_RUN_ID logical_date=$AIRFLOW_CTX_EXECUTION_DATE";
            python3 {SCRIPTS_DIR}/run_silver_to_gold_analytics.py
            """,
        )

        BashOperator(
            task_id="silver_to_gold_advanced",
            bash_command=f"""
            set -euo pipefail
            echo "[silver_to_gold_advanced] run_id=$AIRFLOW_CTX_DAG_RUN_ID logical_date=$AIRFLOW_CTX_EXECUTION_DATE";
            python3 {SCRIPTS_DIR}/run_silver_to_gold_advanced.py
            """,
            env={
                "P02_FORCE_REPROCESS_GOLD_ADVANCED": "1",
                "P02_FORCE_FAIL_ADVANCED": "0",  # mude para 1 quando quiser demonstrar retries
            }

)


precheck_raw >> raw_to_bronze >> bronze_to_silver >> gold




