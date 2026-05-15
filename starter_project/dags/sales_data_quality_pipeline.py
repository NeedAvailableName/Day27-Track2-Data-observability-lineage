from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    try:
        from airflow.datasets import Dataset
    except ImportError:
        Dataset = None
except ImportError:  # pragma: no cover
    DAG = None
    Dataset = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def validate_orders_task() -> dict:
    from src.config import AIRFLOW_INPUT_FILE, DISCORD_WEBHOOK_URL, SUMMARY_FILE
    from src.validation import run_lab_check

    summary = run_lab_check(
        input_path=AIRFLOW_INPUT_FILE,
        output_path=SUMMARY_FILE,
        allow_failure=False,
        skip_discord=not bool(DISCORD_WEBHOOK_URL),
    )
    return summary


if DAG is not None:
    from src.config import AIRFLOW_INPUT_FILE, SUMMARY_FILE

    # Define datasets for lineage
    # We use file:// schema for local files
    input_dataset = Dataset(f"file://{AIRFLOW_INPUT_FILE}") if Dataset else AIRFLOW_INPUT_FILE
    output_dataset = Dataset(f"file://{SUMMARY_FILE}") if Dataset else SUMMARY_FILE

    with DAG(
        dag_id="sales_data_quality_pipeline",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["lab", "data-quality", "discord", "lineage"],
    ) as dag:
        validate_orders = PythonOperator(
            task_id="validate_orders",
            python_callable=validate_orders_task,
            inlets=[input_dataset],
            outlets=[output_dataset],
        )
else:  # pragma: no cover
    dag = None
