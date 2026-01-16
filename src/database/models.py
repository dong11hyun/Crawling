"""
SQLAlchemy ORM 모델 정의
- Product: 상품 정보
- Seller: 판매자 정보
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .connection import Base


class Product(Base):
    """
    상품 테이블
    - OpenSearch에도 저장되지만, 여기가 원본 데이터 (Source of Truth)
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, index=True, nullable=False)  # 상품 URL (중복 방지)
    title = Column(String(500), nullable=False)  # 상품명
    brand = Column(String(100), index=True)  # 브랜드명 (검색용 인덱스)
    price = Column(Integer, default=0)  # 가격 (원)
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)  # 최초 수집 시각
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 마지막 업데이트
    
    # 관계 설정 (1:1 - 상품 하나에 판매자 정보 하나)
    seller = relationship("Seller", back_populates="product", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title[:20]}...', brand='{self.brand}')>"


class Seller(Base):
    """
    판매자 정보 테이블
    - Product와 1:1 관계
    """
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True)
    
    company = Column(String(200))  # 상호 / 대표자
    brand = Column(String(100))  # 판매자 브랜드
    biz_num = Column(String(50))  # 사업자번호
    license = Column(String(100))  # 통신판매업신고
    contact = Column(String(50))  # 연락처
    email = Column(String(100))  # 이메일
    address = Column(Text)  # 영업소재지
    
    # 관계 설정
    product = relationship("Product", back_populates="seller")

    def __repr__(self):
        return f"<Seller(id={self.id}, company='{self.company}')>"
