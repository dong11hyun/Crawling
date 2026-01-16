"""
Pydantic 스키마 정의
- API 요청/응답 유효성 검사
- SQLAlchemy 모델과 분리하여 관리
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========================================
# Seller 스키마
# ========================================
class SellerBase(BaseModel):
    """판매자 기본 정보"""
    company: Optional[str] = None
    brand: Optional[str] = None
    biz_num: Optional[str] = None
    license: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class SellerCreate(SellerBase):
    """판매자 생성 시 사용"""
    pass


class SellerResponse(SellerBase):
    """판매자 응답 시 사용"""
    id: int
    product_id: int

    class Config:
        from_attributes = True  # SQLAlchemy 모델 → Pydantic 변환 허용


# ========================================
# Product 스키마
# ========================================
class ProductBase(BaseModel):
    """상품 기본 정보"""
    url: str = Field(..., max_length=500)
    title: str = Field(..., max_length=500)
    brand: Optional[str] = Field(None, max_length=100)
    price: int = Field(default=0, ge=0)  # 0 이상


class ProductCreate(ProductBase):
    """상품 생성 시 사용 (판매자 정보 포함 가능)"""
    seller: Optional[SellerCreate] = None


class ProductUpdate(BaseModel):
    """상품 수정 시 사용 (부분 업데이트 가능)"""
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[int] = None


class ProductResponse(ProductBase):
    """상품 응답 시 사용"""
    id: int
    created_at: datetime
    updated_at: datetime
    seller: Optional[SellerResponse] = None

    class Config:
        from_attributes = True


# ========================================
# 페이지네이션 응답
# ========================================
class ProductListResponse(BaseModel):
    """상품 목록 응답 (페이지네이션)"""
    total: int
    page: int
    size: int
    items: list[ProductResponse]
