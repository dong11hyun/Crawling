# Week 1 Review: 백엔드 + 데이터 엔지니어링 기초

> Week 1에서 배운 개념, 기술 스택, 코드 리뷰를 정리한 문서  
> 마지막 업데이트: 2026-01-16

---

# 📚 Part 1: 핵심 개념 정리

## 1. ORM (Object-Relational Mapping)

### 개념
- **SQL 없이** Python 객체로 데이터베이스를 다루는 기술
- 테이블 = 클래스, 행(Row) = 객체, 컬럼 = 속성

### 왜 쓰는가?
```python
# 기존 방식 (Raw SQL)
cursor.execute("INSERT INTO products (title, price) VALUES ('패딩', 50000)")

# ORM 방식 (SQLAlchemy)
product = Product(title="패딩", price=50000)
db.add(product)
db.commit()
```
- SQL Injection 방지
- 코드 가독성 향상
- 데이터베이스 변경 시 코드 수정 최소화

---

## 2. 듀얼 저장 패턴 (Dual Write)

### 개념
- 동일 데이터를 **2개 이상의 저장소**에 동시 저장
- 각 저장소의 장점을 활용

### 우리 프로젝트 적용
```
[크롤러]
    │
    ├──→ [PostgreSQL] ─ 원본 보관 (CRUD, 트랜잭션)
    │
    └──→ [OpenSearch] ─ 검색 최적화 (전문 검색, 형태소 분석)
```

### 주의점
- **데이터 정합성**: 한쪽만 저장되면 불일치 발생
- **해결책**: 트랜잭션 처리, 또는 Kafka 같은 메시지 큐 도입

---

## 3. 캐싱 (Caching)

### 개념
- 자주 조회되는 데이터를 **빠른 저장소(메모리)**에 임시 보관
- 동일 요청 시 원본 DB 접근 없이 즉시 반환

### Cache-Aside 패턴 (우리가 사용한 방식)
```
1. 캐시 확인 → 있으면 반환 (캐시 히트)
2. 없으면 DB 조회 → 결과를 캐시에 저장 → 반환 (캐시 미스)
```

### TTL (Time To Live)
- 캐시 데이터의 **유효 시간**
- 만료되면 자동 삭제 → 다음 요청 시 DB에서 다시 조회
- 우리 설정: 300초 (5분)

---

## 4. REST API 설계 원칙

### CRUD와 HTTP 메서드 매핑
| 작업 | HTTP 메서드 | 엔드포인트 예시 |
|------|------------|----------------|
| Create | POST | `/products` |
| Read (목록) | GET | `/products` |
| Read (상세) | GET | `/products/{id}` |
| Update | PUT/PATCH | `/products/{id}` |
| Delete | DELETE | `/products/{id}` |

### 응답 코드
| 코드 | 의미 | 사용 예시 |
|------|------|----------|
| 200 | 성공 | 조회, 수정 성공 |
| 201 | 생성 완료 | POST 성공 |
| 204 | 내용 없음 | DELETE 성공 |
| 400 | 잘못된 요청 | 유효성 검증 실패 |
| 404 | 찾을 수 없음 | ID가 존재하지 않음 |

---

## 5. 컨테이너화 (Containerization)

### Docker Compose
- 여러 컨테이너를 **한 번에 정의하고 실행**
- `docker-compose.yml` 파일로 인프라 코드화 (IaC)

### 우리가 사용한 컨테이너
```yaml
services:
  - opensearch-node      # 검색 엔진
  - opensearch-dashboards # 검색 엔진 GUI
  - postgres             # 관계형 DB
  - pgadmin              # DB GUI
  - redis                # 캐시 서버
```

---

# 🛠️ Part 2: 기술 스택별 역할 및 튜닝

## 1. PostgreSQL

### 역할
- **원본 데이터 저장소** (Source of Truth)
- ACID 트랜잭션 보장
- 복잡한 관계형 쿼리 지원

### 튜닝 포인트
```yaml
# docker-compose.yml에서 설정 가능
environment:
  - POSTGRES_MAX_CONNECTIONS=100      # 최대 연결 수
  - POSTGRES_SHARED_BUFFERS=256MB     # 공유 메모리
  - POSTGRES_WORK_MEM=16MB            # 정렬/해시 작업 메모리
```

### 인덱스 최적화
```sql
-- 자주 검색하는 컬럼에 인덱스 추가
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_url ON products(url);
```

---

## 2. OpenSearch

### 역할
- **전문 검색 엔진** (Full-Text Search)
- 형태소 분석 (Nori - 한국어)
- 역인덱스 기반 빠른 검색

### 튜닝 포인트
```yaml
# docker-compose.yml
environment:
  - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"  # JVM 힙 메모리
  # 운영 환경에서는 시스템 메모리의 50% 권장
```

### 인덱스 설정
```python
# init_opensearch.py
"settings": {
    "number_of_shards": 1,      # 샤드 수 (분산 저장)
    "number_of_replicas": 0,    # 복제본 (고가용성)
    "refresh_interval": "1s"    # 인덱스 갱신 주기
}
```

### 검색 품질 향상
```python
# 필드별 가중치 설정
"multi_match": {
    "query": keyword,
    "fields": ["title^2", "brand^1.5", "description"]
    # title이 2배 중요, brand가 1.5배 중요
}
```

---

## 3. Redis

### 역할
- **인메모리 캐시 서버**
- 초고속 읽기/쓰기 (마이크로초 단위)
- 키-값 저장소

### 튜닝 포인트
```yaml
# docker-compose.yml
command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
# appendonly: 영속성 보장
# maxmemory: 최대 메모리 제한
# maxmemory-policy: 메모리 초과 시 정책 (LRU = 오래된 것 삭제)
```

### TTL 전략
```python
# 데이터 특성에 따른 TTL 설정
set_cache(key, value, ttl=300)   # 검색 결과: 5분
set_cache(key, value, ttl=3600)  # 카테고리 목록: 1시간
set_cache(key, value, ttl=86400) # 정적 데이터: 24시간
```

### 캐시 무효화 전략
```python
# 데이터 변경 시 관련 캐시 삭제
def update_product(product_id, data):
    # 1. DB 업데이트
    db.update(...)
    
    # 2. 관련 캐시 삭제
    delete_cache_pattern(f"search:*")  # 검색 캐시 전체 삭제
    delete_cache(f"product:{product_id}")  # 해당 상품 캐시 삭제
```

---

## 4. FastAPI

### 역할
- **비동기 웹 프레임워크**
- 자동 API 문서화 (Swagger)
- Pydantic 기반 데이터 검증

### 튜닝 포인트
```python
# 운영 환경 실행
uvicorn api_server:app --workers 4 --host 0.0.0.0 --port 8000
# workers: CPU 코어 수만큼 설정

# 또는 gunicorn 사용
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 의존성 주입 패턴
```python
# DB 세션을 엔드포인트마다 자동 생성/정리
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    # db 세션 자동 주입
```

---

## 5. SQLAlchemy

### 역할
- **Python ORM**
- 데이터베이스 추상화
- 마이그레이션 지원 (Alembic)

### 커넥션 풀 설정
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # 기본 커넥션 수
    max_overflow=10,    # 추가 허용 커넥션
    pool_pre_ping=True, # 연결 상태 확인 (끊어진 연결 방지)
    pool_recycle=3600   # 1시간마다 연결 재생성
)
```

---

# 💻 Part 3: 코드 리뷰

## 1. database/connection.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://crawler:password@localhost:5434/musinsa_db"

engine = create_engine(
    DATABASE_URL,
    echo=True,        # ⚠️ 운영 환경에서는 False로!
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 리뷰 포인트
- ✅ `pool_size`, `max_overflow`로 커넥션 풀 관리
- ✅ `get_db()`에서 `finally`로 세션 정리 보장
- ⚠️ `DATABASE_URL`을 환경변수로 분리 권장 (`os.getenv()`)
- ⚠️ `echo=True`는 개발용, 운영에서는 False

---

## 2. database/models.py

```python
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    brand = Column(String(100), index=True)
    price = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    seller = relationship("Seller", back_populates="product", 
                         uselist=False, cascade="all, delete-orphan")
```

### 리뷰 포인트
- ✅ `index=True`로 검색 성능 최적화
- ✅ `unique=True`로 URL 중복 방지
- ✅ `cascade="all, delete-orphan"`으로 연관 데이터 자동 삭제
- ✅ `onupdate=datetime.utcnow`로 자동 업데이트 시간 기록

---

## 3. routers/products.py (CRUD API)

```python
@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # URL 중복 체크
    existing = db.query(Product).filter(Product.url == product.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 URL입니다.")
    
    db_product = Product(...)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
```

### 리뷰 포인트
- ✅ 중복 체크 후 생성 (데이터 무결성)
- ✅ `db.refresh()`로 DB에서 생성된 값(id, created_at) 로드
- ⚠️ 대량 데이터 생성 시 `bulk_insert_mappings()` 고려

---

## 4. cache.py (Redis 캐시)

```python
def generate_cache_key(prefix: str, **kwargs) -> str:
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        parts.append(str(value) if value is not None else "none")
    return ":".join(parts)
    # 결과: "search:패딩:none:none"

def get_cache(key: str) -> Optional[Any]:
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None
```

### 리뷰 포인트
- ✅ `sorted()`로 키 순서 일관성 보장
- ✅ `None` 값을 문자열 "none"으로 변환 (키 충돌 방지)
- ✅ `decode_responses=True`로 자동 문자열 변환
- ⚠️ 대용량 데이터는 압축 고려 (`gzip`)

---

## 5. v2.2_crawler.py (듀얼 저장 크롤러)

```python
def save_to_postgres(data_list: list):
    db = SessionLocal()
    try:
        for data in data_list:
            existing = db.query(Product).filter(Product.url == data["url"]).first()
            if existing:
                # UPDATE
                existing.title = data["title"]
                ...
            else:
                # INSERT
                new_product = Product(...)
                db.add(new_product)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
```

### 리뷰 포인트
- ✅ UPSERT 패턴 (있으면 UPDATE, 없으면 INSERT)
- ✅ `try-except-finally`로 안전한 트랜잭션 처리
- ✅ 에러 시 `rollback()`으로 데이터 정합성 보장
- ⚠️ 개선점: 배치 처리 (`bulk_update`, `bulk_insert`)로 성능 향상

---

## 6. api_server.py (검색 API + 캐싱)

```python
@app.get("/search")
def search_products(keyword: str, min_price: int = None, max_price: int = None):
    # 1. 캐시 확인
    cache_key = generate_cache_key("search", keyword=keyword, ...)
    cached_result = get_cache(cache_key)
    if cached_result:
        return cached_result  # 캐시 히트!
    
    # 2. OpenSearch 검색
    response = client.search(...)
    results = [hit["_source"] for hit in response["hits"]["hits"]]
    
    # 3. 결과 캐싱
    set_cache(cache_key, results, ttl=300)
    return results
```

### 리뷰 포인트
- ✅ Cache-Aside 패턴 정확히 구현
- ✅ 캐시 키에 모든 파라미터 포함 (검색 조건별 캐시)
- ⚠️ 개선점: 캐시 스탬피드 방지 (동시 요청 시 중복 쿼리)
  ```python
  # Redis Lock 활용
  if not lock.acquire():
      time.sleep(0.1)
      return get_cache(cache_key)
  ```

---

# 🎯 Part 4: 면접 대비 Q&A

### Q1. ORM의 장단점은?
**장점**: SQL Injection 방지, 코드 가독성, DB 독립성  
**단점**: 복잡한 쿼리 성능 저하, 학습 곡선

### Q2. Redis 캐시 만료 전략은?
- **TTL**: 시간 기반 자동 만료
- **LRU**: 메모리 부족 시 가장 오래된 것 삭제
- **Manual**: 데이터 변경 시 명시적 삭제

### Q3. OpenSearch vs Elasticsearch 차이?
- OpenSearch = AWS가 Elasticsearch를 포크한 오픈소스
- 기능은 거의 동일, 라이선스 차이 (Apache 2.0)

### Q4. 듀얼 저장의 데이터 정합성 문제 해결 방법?
- **동기식**: 트랜잭션으로 묶기 (성능 저하)
- **비동기식**: Kafka, Debezium으로 CDC 구현 (Week 3에서 다룸)

---

# ✅ Week 1 핵심 역량 체크리스트

| 역량 | 세부 내용 | 습득 |
|------|----------|:----:|
| ORM | SQLAlchemy 모델 정의, 관계 설정 | ✅ |
| REST API | FastAPI CRUD 엔드포인트 구현 | ✅ |
| 캐싱 | Redis Cache-Aside 패턴 | ✅ |
| 검색 | OpenSearch 쿼리, Nori 분석기 | ✅ |
| 컨테이너 | Docker Compose 멀티 서비스 | ✅ |
| 크롤링 | Playwright 비동기, 듀얼 저장 | ✅ |
