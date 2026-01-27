"""
Airflow 테스트 DAG
- 환경 설정이 제대로 되었는지 확인용
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# DAG 기본 설정
default_args = {
    'owner': 'musinsa-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'test_dag',
    default_args=default_args,
    description='Airflow 환경 테스트용 DAG',
    schedule_interval=None,  # 수동 실행만
    catchup=False,
    tags=['test'],
)


def hello_world():
    """간단한 테스트 함수"""
    print("🎉 Hello from Airflow!")
    print(f"현재 시간: {datetime.now()}")
    return "success"


# Task 정의
task_hello = PythonOperator(
    task_id='hello_task',
    python_callable=hello_world,
    dag=dag,
)

task_date = BashOperator(
    task_id='print_date',
    bash_command='echo "현재 날짜: $(date)"',
    dag=dag,
)

# Task 순서 정의
task_hello >> task_date
