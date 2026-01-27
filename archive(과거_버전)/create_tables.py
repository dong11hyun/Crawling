"""
데이터베이스 테이블 생성 스크립트
- 이 스크립트를 실행하면 Product, Seller 테이블이 생성됩니다.
"""
import sys
sys.path.append('..')  # src 폴더를 path에 추가

from database.connection import engine, Base
from database.models import Product, Seller  # 모델 import 필수!

def create_tables():
    """모든 테이블 생성"""
    print("🔧 테이블 생성 시작...")
    
    # Base를 상속받은 모든 모델의 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    print("✅ 테이블 생성 완료!")
    print("   - products")
    print("   - sellers")
    print("\n💡 pgAdmin에서 확인해보세요!")
    print("   http://localhost:5050 접속")
    print("   Servers → musinsa DB → Databases → musinsa_db → Schemas → public → Tables")

if __name__ == "__main__":
    create_tables()
