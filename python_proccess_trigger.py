from datetime import datetime as dt
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import upload_storage
local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': dt(2024, 1, 1),
    'retries': 1,
    'provide_context': True,
    'retry_delay': timedelta(minutes=1)
}

with DAG('pipeline_trigger', default_args=default_args, schedule_interval=None) as dag:
    kafka_streaming_task = PythonOperator(
        task_id='kafka_streaming_task',
        python_callable=upload_storage,
        dag=dag,
    )   