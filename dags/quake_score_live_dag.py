"""Airflow DAG: pull live feed -> score -> store predictions. Hourly."""

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
from src import score

with DAG(
    dag_id="quake_score_live",
    schedule="@hourly",
    start_date=datetime(2026,8,16),
    catchup=False,
) as dag:
    score_live = PythonOperator(
        task_id="score",
        python_callable=score.main
    )
    score_live