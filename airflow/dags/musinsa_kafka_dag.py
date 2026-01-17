"""
무신사 크롤링 DAG (v4 - Kafka 연동)
- 크롤링 → Kafka 발행
- Consumer가 별도로 PostgreSQL/OpenSearch 저장
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
    'musinsa_kafka_dag',
    default_args=default_args,
    description='무신사 상품 수집 → Kafka 발행 (v4)',
    schedule_interval='0 6 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['musinsa', 'crawling', 'kafka', 'production'],
)


# ========================================
# Task 함수들
# ========================================
def run_crawl_task(**context):
    """
    크롤링 Task
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
        filepath = save_to_file(data, prefix="crawl")
        ti.xcom_push(key='crawled_data_path', value=filepath)
        ti.xcom_push(key='use_file', value=True)
    else:
        ti.xcom_push(key='crawled_data', value=data)
        ti.xcom_push(key='use_file', value=False)
    
    logger.info(f"📦 크롤링 완료: {len(data)}건")
    return len(data)


def run_validate_task(**context):
    """
    검증 Task
    """
    from tasks.validate_task import validate_products
    from tasks.xcom_utils import load_from_file, should_use_file, save_to_file
    
    ti = context['ti']
    use_file = ti.xcom_pull(key='use_file', task_ids='crawl_task')
    
    if use_file:
        filepath = ti.xcom_pull(key='crawled_data_path', task_ids='crawl_task')
        data = load_from_file(filepath)
    else:
        data = ti.xcom_pull(key='crawled_data', task_ids='crawl_task')
    
    if not data:
        raise ValueError("크롤링 데이터가 없습니다!")
    
    valid_data, invalid_count = validate_products(data)
    
    if should_use_file(valid_data):
        filepath = save_to_file(valid_data, prefix="valid")
        ti.xcom_push(key='valid_data_path', value=filepath)
        ti.xcom_push(key='valid_use_file', value=True)
    else:
        ti.xcom_push(key='valid_data', value=valid_data)
        ti.xcom_push(key='valid_use_file', value=False)
    
    logger.info(f"✅ 검증 완료: {len(valid_data)}건 통과, {invalid_count}건 실패")
    return len(valid_data)


def run_publish_to_kafka(**context):
    """
    Kafka 발행 Task (신규!)
    - 검증된 데이터를 Kafka로 발행
    - Consumer가 PostgreSQL/OpenSearch에 저장
    """
    import json
    from kafka import KafkaProducer
    from tasks.xcom_utils import load_from_file
    from datetime import datetime, timezone, timedelta
    
    KST = timezone(timedelta(hours=9))
    
    ti = context['ti']
    use_file = ti.xcom_pull(key='valid_use_file', task_ids='validate_task')
    
    if use_file:
        filepath = ti.xcom_pull(key='valid_data_path', task_ids='validate_task')
        data = load_from_file(filepath)
    else:
        data = ti.xcom_pull(key='valid_data', task_ids='validate_task')
    
    if not data:
        logger.warning("발행할 데이터 없음")
        return {"success": 0, "failed": 0}
    
    # Kafka Producer 생성 (Docker 내부에서는 kafka:29092 사용)
    producer = KafkaProducer(
        bootstrap_servers='musinsa-kafka:29092',
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all',
        retries=3,
    )
    
    success = 0
    failed = 0
    
    for item in data:
        try:
            item['published_at'] = datetime.now(KST).isoformat()
            key = item.get('url', 'unknown')
            
            future = producer.send('musinsa-products', key=key, value=item)
            future.get(timeout=10)
            success += 1
            
        except Exception as e:
            logger.error(f"❌ 발행 실패: {e}")
            failed += 1
    
    producer.flush()
    producer.close()
    
    logger.info(f"📤 Kafka 발행 완료: 성공 {success}, 실패 {failed}")
    return {"success": success, "failed": failed}


def run_cleanup_task(**context):
    """
    정리 Task
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

publish_kafka_task = PythonOperator(
    task_id='publish_kafka_task',
    python_callable=run_publish_to_kafka,
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
crawl_task >> validate_task >> publish_kafka_task >> cleanup_task
