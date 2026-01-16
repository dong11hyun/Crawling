"""
데이터 저장 Task 모듈
- PostgreSQL + OpenSearch 듀얼 저장
"""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def load_to_postgres(data: List[Dict[str, Any]], db_url: str = None) -> int:
    """
    PostgreSQL에 데이터 저장 (UPSERT)
    
    Args:
        data: 저장할 데이터 리스트
        db_url: 데이터베이스 URL (없으면 환경변수에서 읽음)
    
    Returns:
        저장된 데이터 개수
    """
    if not data:
        return 0
    
    db_url = db_url or os.getenv("MUSINSA_DB_URL", "postgresql://crawler:password@localhost:5434/musinsa_db")
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        saved_count = 0
        for item in data:
            try:
                # UPSERT 쿼리
                db.execute(
                    text("""
                        INSERT INTO products (url, title, brand, price, created_at, updated_at)
                        VALUES (:url, :title, :brand, :price, NOW(), NOW())
                        ON CONFLICT (url) DO UPDATE SET
                            title = EXCLUDED.title,
                            brand = EXCLUDED.brand,
                            price = EXCLUDED.price,
                            updated_at = NOW()
                    """),
                    {
                        "url": item["url"],
                        "title": item["title"],
                        "brand": item.get("brand", ""),
                        "price": item.get("price", 0)
                    }
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"PostgreSQL 개별 저장 실패: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"💾 PostgreSQL 저장 완료: {saved_count}건")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        return 0


def load_to_opensearch(data: List[Dict[str, Any]], host: str = None, port: int = None) -> int:
    """
    OpenSearch에 데이터 저장 (Bulk Insert)
    
    Args:
        data: 저장할 데이터 리스트
        host: OpenSearch 호스트
        port: OpenSearch 포트
    
    Returns:
        저장된 데이터 개수
    """
    if not data:
        return 0
    
    host = host or os.getenv("OPENSEARCH_HOST", "localhost")
    port = port or int(os.getenv("OPENSEARCH_PORT", 9201))
    
    try:
        from opensearchpy import OpenSearch, helpers
        
        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False
        )
        
        # Bulk 문서 생성
        docs = []
        for item in data:
            docs.append({
                "_index": "musinsa_products",
                "_source": {
                    **item,
                    "indexed_at": datetime.now().isoformat()
                }
            })
        
        success, failed = helpers.bulk(client, docs)
        
        logger.info(f"🔍 OpenSearch 저장 완료: 성공 {success}, 실패 {failed}")
        return success
        
    except Exception as e:
        logger.error(f"❌ OpenSearch 저장 실패: {e}")
        return 0


def load_to_storage(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    듀얼 저장 실행 (PostgreSQL + OpenSearch)
    
    Args:
        data: 저장할 데이터 리스트
    
    Returns:
        {"postgres": 저장 개수, "opensearch": 저장 개수}
    """
    if not data:
        logger.warning("⚠️ 저장할 데이터가 없습니다.")
        return {"postgres": 0, "opensearch": 0}
    
    logger.info(f"📦 듀얼 저장 시작: {len(data)}건")
    
    postgres_count = load_to_postgres(data)
    opensearch_count = load_to_opensearch(data)
    
    logger.info(f"✅ 듀얼 저장 완료!")
    
    return {
        "postgres": postgres_count,
        "opensearch": opensearch_count
    }
