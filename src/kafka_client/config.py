"""
Kafka 클라이언트 설정
- Producer/Consumer 공통 설정
"""
import os
from typing import Dict, Any

# Kafka 브로커 주소
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Topic 이름
TOPIC_PRODUCTS = "musinsa-products"
TOPIC_PRODUCTS_DLQ = "musinsa-products-dlq"  # Dead Letter Queue

# Producer 설정
PRODUCER_CONFIG: Dict[str, Any] = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "value_serializer": lambda v: __import__('json').dumps(v, ensure_ascii=False).encode('utf-8'),
    "key_serializer": lambda k: k.encode('utf-8') if k else None,
    "acks": "all",  # 모든 복제본이 수신 확인
    "retries": 3,   # 재시도 횟수
    "max_in_flight_requests_per_connection": 1,  # 순서 보장
}

# Consumer 설정
CONSUMER_CONFIG: Dict[str, Any] = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "value_deserializer": lambda v: __import__('json').loads(v.decode('utf-8')),
    "auto_offset_reset": "earliest",  # 처음부터 읽기
    "enable_auto_commit": False,      # 수동 커밋 (정확한 처리 보장)
    "group_id": "musinsa-consumer-group",
}
