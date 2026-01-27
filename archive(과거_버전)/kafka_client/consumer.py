"""
Kafka Consumer 모듈
- Kafka에서 상품 데이터 소비
- PostgreSQL/OpenSearch에 저장
"""
import json
import logging
import signal
import sys
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone, timedelta

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from .config import KAFKA_BOOTSTRAP_SERVERS, TOPIC_PRODUCTS, TOPIC_PRODUCTS_DLQ

# 한국 시간
KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ProductConsumer:
    """상품 데이터 Kafka Consumer"""
    
    def __init__(
        self,
        group_id: str = "musinsa-consumer-group",
        bootstrap_servers: str = None,
        topics: list = None
    ):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.group_id = group_id
        self.topics = topics or [TOPIC_PRODUCTS]
        self.consumer = None
        self.running = False
        self._connect()
        self._setup_signal_handlers()
    
    def _connect(self):
        """Kafka Consumer 연결"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # 수동 커밋
                max_poll_records=100,
            )
            logger.info(f"✅ Consumer 연결 성공: {self.bootstrap_servers}")
            logger.info(f"   Group ID: {self.group_id}")
            logger.info(f"   Topics: {self.topics}")
        except Exception as e:
            logger.error(f"❌ Consumer 연결 실패: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """종료 시그널 핸들러"""
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, signum, frame):
        """안전한 종료"""
        logger.info("🛑 종료 신호 수신, Consumer 정리 중...")
        self.running = False
    
    def consume(
        self,
        handler: Callable[[Dict[str, Any]], bool],
        batch_size: int = 10
    ):
        """
        메시지 소비 루프
        
        Args:
            handler: 메시지 처리 함수 (성공 시 True 반환)
            batch_size: 커밋 전 처리할 메시지 수
        """
        self.running = True
        processed = 0
        failed = 0
        
        logger.info("🚀 Consumer 시작, 메시지 대기 중...")
        
        try:
            while self.running:
                # 메시지 폴링 (1초 타임아웃)
                messages = self.consumer.poll(timeout_ms=1000)
                
                if not messages:
                    continue
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            # 핸들러 호출
                            success = handler(record.value)
                            
                            if success:
                                processed += 1
                                logger.info(
                                    f"✅ 처리 완료: partition={record.partition}, "
                                    f"offset={record.offset}, key={record.key}"
                                )
                            else:
                                failed += 1
                                logger.warning(f"⚠️ 처리 실패: {record.key}")
                            
                        except Exception as e:
                            failed += 1
                            logger.error(f"❌ 처리 에러: {e}")
                        
                        # 배치 커밋
                        if (processed + failed) % batch_size == 0:
                            self.consumer.commit()
                            logger.info(f"📝 오프셋 커밋: {processed + failed}건 처리됨")
                
        except KeyboardInterrupt:
            logger.info("⌨️ 키보드 인터럽트")
        finally:
            # 최종 커밋
            self.consumer.commit()
            self.close()
            logger.info(f"📊 최종 결과: 성공 {processed}, 실패 {failed}")
    
    def consume_once(self, handler: Callable[[Dict[str, Any]], bool], timeout_ms: int = 5000):
        """
        한 번만 소비 (테스트/배치용)
        
        Args:
            handler: 메시지 처리 함수
            timeout_ms: 대기 시간
        """
        messages = self.consumer.poll(timeout_ms=timeout_ms)
        processed = 0
        
        for topic_partition, records in messages.items():
            for record in records:
                if handler(record.value):
                    processed += 1
        
        self.consumer.commit()
        return processed
    
    def close(self):
        """Consumer 종료"""
        if self.consumer:
            self.consumer.close()
            logger.info("🔌 Consumer 종료")
