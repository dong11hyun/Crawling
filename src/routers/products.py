"""
상품 CRUD API 라우터
- POST   /products      : 상품 생성
- GET    /products      : 상품 목록 조회 (페이지네이션)
- GET    /products/{id} : 상품 상세 조회
- PUT    /products/{id} : 상품 수정
- DELETE /products/{id} : 상품 삭제
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from database.models import Product, Seller
from database.schemas import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductListResponse
)

router = APIRouter(
    prefix="/products",
    tags=["상품 관리"]
)


# ========================================
# CREATE - 상품 생성
# ========================================
@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    새 상품을 생성합니다.
    - 판매자 정보도 함께 저장 가능
    """
    # URL 중복 체크
    existing = db.query(Product).filter(Product.url == product.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 URL입니다.")
    
    # Product 생성
    db_product = Product(
        url=product.url,
        title=product.title,
        brand=product.brand,
        price=product.price
    )
    
    # Seller 정보가 있으면 함께 생성
    if product.seller:
        db_seller = Seller(
            company=product.seller.company,
            brand=product.seller.brand,
            biz_num=product.seller.biz_num,
            license=product.seller.license,
            contact=product.seller.contact,
            email=product.seller.email,
            address=product.seller.address
        )
        db_product.seller = db_seller
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


# ========================================
# READ - 상품 목록 조회 (페이지네이션)
# ========================================
@router.get("", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지당 개수"),
    brand: str = Query(None, description="브랜드 필터"),
    db: Session = Depends(get_db)
):
    """
    상품 목록을 조회합니다.
    - 페이지네이션 지원
    - 브랜드 필터링 가능
    """
    query = db.query(Product)
    
    # 브랜드 필터
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션 적용
    offset = (page - 1) * size
    products = query.order_by(Product.id.desc()).offset(offset).limit(size).all()
    
    return ProductListResponse(
        total=total,
        page=page,
        size=size,
        items=products
    )


# ========================================
# READ - 상품 상세 조회
# ========================================
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    특정 상품의 상세 정보를 조회합니다.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    return product


# ========================================
# UPDATE - 상품 수정
# ========================================
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """
    상품 정보를 수정합니다.
    - 부분 업데이트 가능 (변경할 필드만 전송)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    # 전달된 필드만 업데이트
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return product


# ========================================
# DELETE - 상품 삭제
# ========================================
@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    상품을 삭제합니다.
    - 연결된 판매자 정보도 함께 삭제됩니다 (Cascade)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    db.delete(product)
    db.commit()
    
    return None
