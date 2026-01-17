"""
PostgreSQL Consumer
- Kafka에서 상품 데이터 소비 → PostgreSQL 저장
"""
import os
import sys
import logging

# 상위 폴더 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka_client.consumer import ProductConsumer
from database.connection import SessionLocal
from database.models import Product, Seller

logger = logging.getLogger(__name__)


def save_to_postgres(data: dict) -> bool:
    """
    상품 데이터를 PostgreSQL에 저장 (UPSERT)
    
    Args:
        data: Kafka 메시지 (상품 데이터)
    
    Returns:
        성공 여부
    """
    db = SessionLocal()
    try:
        url = data.get("url")
        if not url:
            logger.warning("URL 없음, 스킵")
            return False
        
        # 기존 상품 조회
        existing = db.query(Product).filter(Product.url == url).first()
        
        if existing:
            # UPDATE
            existing.title = data.get("title", existing.title)
            existing.brand = data.get("brand", existing.brand)
            existing.price = data.get("price", existing.price)
            logger.info(f"📝 UPDATE: {url}")
        else:
            # INSERT
            new_product = Product(
                url=url,
                title=data.get("title", ""),
                brand=data.get("brand", ""),
                price=data.get("price", 0),
            )
            db.add(new_product)
            
            # Seller 정보가 있으면 추가
            seller_info = data.get("seller_info", {})
            if seller_info and any(seller_info.values()):
                db.flush()  # product.id 생성
                new_seller = Seller(
                    product_id=new_product.id,
                    company=seller_info.get("company", ""),
                    brand=seller_info.get("brand", ""),
                    biz_num=seller_info.get("biz_num", ""),
                    license=seller_info.get("license", ""),
                    contact=seller_info.get("contact", ""),
                    email=seller_info.get("email", ""),
                    address=seller_info.get("address", ""),
                )
                db.add(new_seller)
            
            logger.info(f"➕ INSERT: {url}")
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ PostgreSQL 저장 실패: {e}")
        return False
    finally:
        db.close()


def run_postgres_consumer():
    """PostgreSQL Consumer 실행"""
    print("="*60)
    print("🐘 PostgreSQL Consumer 시작")
    print("   Kafka → PostgreSQL")
    print("   종료: Ctrl+C")
    print("="*60)
    
    consumer = ProductConsumer(group_id="postgres-consumer-group")
    consumer.consume(handler=save_to_postgres)


if __name__ == "__main__":
    run_postgres_consumer()
