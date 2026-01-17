"""
OpenSearch Consumer
- Kafka에서 상품 데이터 소비 → OpenSearch 저장
"""
import os
import sys
import logging
from datetime import datetime, timezone, timedelta

# 상위 폴더 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka_client.consumer import ProductConsumer
from opensearchpy import OpenSearch

# 한국 시간
KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)

# OpenSearch 설정
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9201))
INDEX_NAME = "musinsa_products"


def get_opensearch_client():
    """OpenSearch 클라이언트 생성"""
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False
    )


def save_to_opensearch(data: dict) -> bool:
    """
    상품 데이터를 OpenSearch에 저장
    
    Args:
        data: Kafka 메시지 (상품 데이터)
    
    Returns:
        성공 여부
    """
    try:
        client = get_opensearch_client()
        
        url = data.get("url")
        if not url:
            logger.warning("URL 없음, 스킵")
            return False
        
        # 인덱싱 시간 추가
        data["indexed_at"] = datetime.now(KST).isoformat()
        
        # 문서 ID를 URL 해시로 사용 (중복 방지)
        doc_id = str(hash(url))
        
        response = client.index(
            index=INDEX_NAME,
            id=doc_id,
            body=data
        )
        
        result = response.get("result", "unknown")
        logger.info(f"🔍 OpenSearch {result}: {url}")
        
        return result in ["created", "updated"]
        
    except Exception as e:
        logger.error(f"❌ OpenSearch 저장 실패: {e}")
        return False


def run_opensearch_consumer():
    """OpenSearch Consumer 실행"""
    print("="*60)
    print("🔍 OpenSearch Consumer 시작")
    print("   Kafka → OpenSearch")
    print("   종료: Ctrl+C")
    print("="*60)
    
    consumer = ProductConsumer(group_id="opensearch-consumer-group")
    consumer.consume(handler=save_to_opensearch)


if __name__ == "__main__":
    run_opensearch_consumer()
