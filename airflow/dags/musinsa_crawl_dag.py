"""
무신사 크롤링 DAG (v3 - XCom 최적화)
- 소량 데이터: XCom 직접 전달
- 대용량 데이터: 파일로 저장 후 경로 전달
- src/tasks/xcom_utils.py 사용
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
logger = logging.getLogger(__name__)

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
    description='무신사 상품 데이터 수집 파이프라인 (v3 - XCom 최적화)',
    schedule_interval='0 6 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['musinsa', 'crawling', 'production'],
)


# ========================================
# Task 함수들 (XCom 최적화 적용)
# ========================================
def run_crawl_task(**context):
    """
    크롤링 Task
    - 데이터 크기에 따라 XCom 또는 파일 사용
    """
    from tasks.crawl_task import crawl_musinsa
    from tasks.xcom_utils import should_use_file, save_to_file
    
    # 크롤링 실행
    data = crawl_musinsa(
        keyword="패딩",
        scroll_count=2,
        max_products=15
    )
    
    ti = context['ti']
    
    # 데이터 크기에 따라 전달 방식 결정
    if should_use_file(data):
        # 대용량: 파일로 저장 후 경로 전달
        filepath = save_to_file(data, prefix="crawl")
        ti.xcom_push(key='crawled_data_path', value=filepath)
        ti.xcom_push(key='use_file', value=True)
        logger.info(f"📁 대용량 데이터 → 파일 저장: {filepath}")
    else:
        # 소량: XCom 직접 전달
        ti.xcom_push(key='crawled_data', value=data)
        ti.xcom_push(key='use_file', value=False)
        logger.info(f"📦 소량 데이터 → XCom 직접 전달")
    
    return len(data)


def run_validate_task(**context):
    """
    검증 Task
    - XCom 또는 파일에서 데이터 로드
    """
    from tasks.validate_task import validate_products
    from tasks.xcom_utils import load_from_file, should_use_file, save_to_file
    
    ti = context['ti']
    use_file = ti.xcom_pull(key='use_file', task_ids='crawl_task')
    
    # 데이터 로드 (파일 또는 XCom)
    if use_file:
        filepath = ti.xcom_pull(key='crawled_data_path', task_ids='crawl_task')
        data = load_from_file(filepath)
        logger.info(f"📁 파일에서 데이터 로드: {filepath}")
    else:
        data = ti.xcom_pull(key='crawled_data', task_ids='crawl_task')
        logger.info(f"📦 XCom에서 데이터 로드")
    
    if not data:
        raise ValueError("크롤링 데이터가 없습니다!")
    
    # 검증 실행
    valid_data, invalid_count = validate_products(data)
    
    # 결과 전달 (크기에 따라)
    if should_use_file(valid_data):
        filepath = save_to_file(valid_data, prefix="valid")
        ti.xcom_push(key='valid_data_path', value=filepath)
        ti.xcom_push(key='valid_use_file', value=True)
    else:
        ti.xcom_push(key='valid_data', value=valid_data)
        ti.xcom_push(key='valid_use_file', value=False)
    
    return len(valid_data)


def run_load_task(**context):
    """
    저장 Task
    - XCom 또는 파일에서 데이터 로드
    """
    from tasks.load_task import load_to_storage
    from tasks.xcom_utils import load_from_file
    
    ti = context['ti']
    use_file = ti.xcom_pull(key='valid_use_file', task_ids='validate_task')
    
    # 데이터 로드
    if use_file:
        filepath = ti.xcom_pull(key='valid_data_path', task_ids='validate_task')
        data = load_from_file(filepath)
    else:
        data = ti.xcom_pull(key='valid_data', task_ids='validate_task')
    
    if not data:
        return {"postgres": 0, "opensearch": 0}
    
    # 저장 실행
    result = load_to_storage(data)
    
    return result


def run_cleanup_task(**context):
    """
    정리 Task - 7일 이상 된 임시 파일 삭제
    """
    from tasks.xcom_utils import cleanup_old_files
    
    deleted = cleanup_old_files(days=7)
    return deleted


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

cleanup_task = PythonOperator(
    task_id='cleanup_task',
    python_callable=run_cleanup_task,
    dag=dag,
)

# ========================================
# Task 의존성
# ========================================
crawl_task >> validate_task >> load_task >> cleanup_task
