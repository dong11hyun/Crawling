"""
Kafka Producer 모듈
- 크롤링 데이터를 Kafka로 발행
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import KAFKA_BOOTSTRAP_SERVERS, TOPIC_PRODUCTS

# 한국 시간
KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)


class ProductProducer:
    """상품 데이터 Kafka Producer"""
    
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Kafka Producer 연결"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',           # 모든 복제본 수신 확인
                retries=3,            # 재시도 횟수
                max_in_flight_requests_per_connection=1,  # 순서 보장
            )
            logger.info(f"✅ Kafka Producer 연결 성공: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"❌ Kafka Producer 연결 실패: {e}")
            raise
    
    def send(self, product: Dict[str, Any], key: str = None) -> bool:
        """
        단일 상품 발행
        
        Args:
            product: 상품 데이터
            key: 파티션 키 (기본값: URL)
        
        Returns:
            성공 여부
        """
        try:
            # 키가 없으면 URL 사용
            if key is None:
                key = product.get("url", "unknown")
            
            # 발행 시간 추가
            product["published_at"] = datetime.now(KST).isoformat()
            
            future = self.producer.send(
                TOPIC_PRODUCTS,
                key=key,
                value=product
            )
            
            # 동기 대기 (선택적)
            result = future.get(timeout=10)
            
            logger.info(f"📤 발행 성공: partition={result.partition}, offset={result.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ 발행 실패: {e}")
            return False
    
    def send_batch(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        배치 발행 (여러 상품 한번에)
        
        Args:
            products: 상품 데이터 리스트
        
        Returns:
            {"success": 성공 개수, "failed": 실패 개수}
        """
        success = 0
        failed = 0
        
        for product in products:
            if self.send(product):
                success += 1
            else:
                failed += 1
        
        # 버퍼 플러시
        self.producer.flush()
        
        logger.info(f"📦 배치 발행 완료: 성공 {success}, 실패 {failed}")
        return {"success": success, "failed": failed}
    
    def close(self):
        """Producer 종료"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("🔌 Producer 종료")


# 싱글톤 인스턴스 (편의용)
_producer_instance: Optional[ProductProducer] = None


def get_producer() -> ProductProducer:
    """싱글톤 Producer 반환"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = ProductProducer()
    return _producer_instance


def publish_products(products: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    상품 데이터 발행 (간편 함수)
    
    Args:
        products: 상품 데이터 리스트
    
    Returns:
        {"success": 성공 개수, "failed": 실패 개수}
    """
    producer = get_producer()
    return producer.send_batch(products)
