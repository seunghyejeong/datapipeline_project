from datetime import datetime as dt
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import pendulum
from kafka_streaming import kafka_streaming
import time

local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': dt(2024, 1, 1),
    'retries': 1,
    'provide_context': True,
    'retry_delay': timedelta(minutes=1)
}

with DAG('pipeline', default_args=default_args, schedule_interval=None) as dag:
    deploy_kafka_resource = BashOperator(
        task_id='deploy_kafka_resource',
        bash_command='kubectl apply -f /opt/airflow/kafka',
        dag=dag,
        )
    kafka_streaming_task = PythonOperator(
        task_id='kafka_streaming_task',
        python_callable=kafka_streaming,
        dag=dag,
    )
    spark_messaging_task = BashOperator(
        task_id='spark_messaging_task',
        bash_command='kubectl apply -f /opt/airflow/spark/sparkJob.yaml',
        dag=dag,
    )

deploy_kafka_resource >> [kafka_streaming_task, spark_messaging_task]
