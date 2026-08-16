"""Airflow DAG: extract -> transform -> load -> train. Weekly."""

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
from src import extract, load, train

with DAG(
    dag_id="quake_etl_train",
    schedule="@weekly",
    start_date=datetime(2026,8,16),
    catchup=False,
) as dag:
    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract.main
    )
    load_task = PythonOperator(
        task_id="load",
        python_callable=load.main
    )
    train_task = PythonOperator(
        task_id="train",
        python_callable=train.main
    )
    extract_task >> load_task >> train_task

