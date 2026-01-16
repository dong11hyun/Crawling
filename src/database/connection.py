"""
PostgreSQL 데이터베이스 연결 설정
- SQLAlchemy 엔진 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ========================================
# 데이터베이스 연결 URL
# ========================================
# 형식: postgresql://유저명:비밀번호@호스트:포트/데이터베이스명
DATABASE_URL = "postgresql://crawler:password@localhost:5434/musinsa_db"

# ========================================
# SQLAlchemy 엔진 생성
# ========================================
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로그 출력 (개발용, 운영 시 False)
    pool_size=5,  # 커넥션 풀 크기
    max_overflow=10,  # 추가 허용 커넥션 수
)

# ========================================
# 세션 팩토리
# ========================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ========================================
# Base 클래스 (모든 모델이 상속)
# ========================================
Base = declarative_base()

# ========================================
# FastAPI 의존성 주입용 함수
# ========================================
def get_db():
    """
    API 엔드포인트에서 DB 세션을 가져올 때 사용
    
    사용 예시:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db)):
            return db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
