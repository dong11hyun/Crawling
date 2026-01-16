"""
무신사 크롤링 DAG (v2 - 모듈화)
- src/tasks/ 모듈 사용
- 재사용 가능한 Task 구조
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import logging

# src 폴더를 Python path에 추가
sys.path.insert(0, '/opt/airflow/src')

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# ========================================
# DAG 기본 설정
# ========================================
default_args = {
    'owner': 'musinsa-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

dag = DAG(
    'musinsa_crawl_dag',
    default_args=default_args,
    description='무신사 상품 데이터 수집 파이프라인 (v2 - 모듈화)',
    schedule_interval='0 6 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['musinsa', 'crawling', 'production'],
)


# ========================================
# Task 함수들 (모듈 호출)
# ========================================
def run_crawl_task(**context):
    """크롤링 Task - src/tasks/crawl_task.py 사용"""
    from tasks.crawl_task import crawl_musinsa
    
    # 파라미터 설정
    data = crawl_musinsa(
        keyword="패딩",
        scroll_count=2,
        max_products=15
    )
    
    # XCom으로 다음 Task에 전달
    context['ti'].xcom_push(key='crawled_data', value=data)
    
    return len(data)


def run_validate_task(**context):
    """검증 Task - src/tasks/validate_task.py 사용"""
    from tasks.validate_task import validate_products
    
    # XCom에서 데이터 가져오기
    ti = context['ti']
    data = ti.xcom_pull(key='crawled_data', task_ids='crawl_task')
    
    if not data:
        raise ValueError("크롤링 데이터가 없습니다!")
    
    valid_data, invalid_count = validate_products(data)
    
    # 다음 Task로 전달
    ti.xcom_push(key='valid_data', value=valid_data)
    
    return len(valid_data)


def run_load_task(**context):
    """저장 Task - src/tasks/load_task.py 사용"""
    from tasks.load_task import load_to_storage
    
    # XCom에서 검증된 데이터 가져오기
    ti = context['ti']
    data = ti.xcom_pull(key='valid_data', task_ids='validate_task')
    
    if not data:
        return {"postgres": 0, "opensearch": 0}
    
    result = load_to_storage(data)
    
    return result


# ========================================
# Task 정의
# ========================================
crawl_task = PythonOperator(
    task_id='crawl_task',
    python_callable=run_crawl_task,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_task',
    python_callable=run_validate_task,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=run_load_task,
    dag=dag,
)

# ========================================
# Task 의존성
# ========================================
crawl_task >> validate_task >> load_task
