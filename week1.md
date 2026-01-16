# Week 1: 백엔드 기본 + 심화

> 동료가 처음부터 따라할 때 **반드시 실행해야 하는 명령어** 모음  
> 마지막 업데이트: 2026-01-16

---

## Day 1: PostgreSQL 환경 구축
- **뭘 하는 건가?**: Docker로 PostgreSQL 데이터베이스와 pgAdmin(GUI 관리도구) 컨테이너를 실행
- **왜 필요한가?**: 크롤링한 원본 데이터를 안정적으로 저장할 관계형 DB가 필요하기 때문

### 1. Docker 컨테이너 실행
```bash
cd C:\B2_crawling
docker-compose up -d
```

### 2. 컨테이너 상태 확인
```bash
docker ps
```
- `musinsa-postgres` ✅
- `musinsa-pgadmin` ✅
- `opensearch-node` ✅
- `opensearch-dashboards` ✅

### 3. pgAdmin 접속 및 DB 연결
- **URL**: http://localhost:5050
- **로그인**: `admin@admin.com` / `admin`
- **서버 등록**:
  - Host: `musinsa-postgres`
  - Port: `5432`
  - Database: `musinsa_db`
  - User: `crawler`
  - Password: `password`

---

## Day 2: SQLAlchemy 모델 정의
- **뭘 하는 건가?**: Python 코드로 DB 테이블 구조(Product, Seller)를 정의하고 실제 테이블 생성
- **왜 필요한가?**: SQL 직접 작성 대신 Python 객체로 DB를 다루기 위해 (ORM 패턴)

```
Day 2: SQLAlchemy 모델 정의
├── [x] requirements.txt에 sqlalchemy, pydantic 추가
├── [x] database/connection.py - DB 연결 설정
├── [x] database/models.py - Product, Seller 모델
├── [x] database/schemas.py - Pydantic 스키마
├── [x] create_tables.py - 테이블 생성 스크립트
└── [x] 테이블 생성 완료 (products, sellers)
```
### 1. 의존성 설치
```bash
pip install sqlalchemy==2.0.23 pydantic==2.5.0
```

### 2. 테이블 생성
```bash
cd C:\B2_crawling\src
python create_tables.py
```

### 3. 확인
- pgAdmin → musinsa_db → Schemas → public → **Tables**
- `products` 테이블 ✅
- `sellers` 테이블 ✅

---

## Day 3: CRUD API 구현
- **뭘 하는 건가?**: PostgreSQL 데이터를 생성/조회/수정/삭제하는 REST API 엔드포인트 구현
- **왜 필요한가?**: 크롤러가 저장한 데이터를 외부에서 관리/조회할 수 있게 하기 위해

```
Day 3: CRUD API 구현
├── [x] routers/__init__.py - 라우터 패키지
├── [x] routers/products.py - 상품 CRUD API
└── [x] api_server.py - 라우터 등록
```

### 1. API 서버 실행
```bash
cd C:\B2_crawling\src
python api_server.py
```

### 2. Swagger UI 테스트
- **URL**: http://localhost:8000/docs
- `POST /products` - 상품 생성
- `GET /products` - 목록 조회
- `GET /products/{id}` - 상세 조회
- `PUT /products/{id}` - 수정
- `DELETE /products/{id}` - 삭제

### 3. 테스트 데이터 예시 (POST /products)
```json
{
  "url": "https://www.musinsa.com/products/12345",
  "title": "테스트 패딩 자켓",
  "brand": "노스페이스",
  "price": 150000,
  "seller": {
    "company": "테스트 회사",
    "brand": "노스페이스",
    "contact": "02-1234-5678"
  }
}
```

### 4. 확인
- Swagger에서 `201` 응답 ✅
- pgAdmin에서 products 테이블 데이터 확인 ✅

---

## Day 4: 크롤러 연동 (듀얼 저장)
- **뭘 하는 건가?**: 크롤러가 수집한 데이터를 PostgreSQL + OpenSearch 양쪽에 동시 저장
- **왜 필요한가?**: PostgreSQL = 원본 보관(CRUD), OpenSearch = 빠른 검색 (각각 장점 활용)

```
Day 4: 크롤러 연동
├── [x] v2.2_crawler.py - 듀얼 저장 버전 크롤러
├── [x] save_to_postgres() - PostgreSQL UPSERT
└── [x] save_to_opensearch() - OpenSearch Bulk Insert
```

### 1. 크롤러 실행
```bash
cd C:\B2_crawling\src
python v2.2_crawler.py
```
```bash
#인덱스 삭제시 재생성방법
python init_opensearch.py
```
### 2. 확인
- pgAdmin → products 테이블에 데이터 ✅
- OpenSearch Dashboards (http://localhost:5601) → Discover ✅

---

## Day 5~7: Redis 캐싱
- **뭘 하는 건가?**: 검색 결과를 Redis에 임시 저장, 동일 검색 시 빠르게 반환
- **왜 필요한가?**: OpenSearch 쿼리 부하 감소 + 응답 속도 10배↑ 향상

```
Day 5~7: Redis 캐싱
├── [x] docker-compose.yml - Redis 서비스 추가
├── [x] cache.py - 캐시 유틸리티 (get/set/delete)
└── [x] api_server.py - 검색 API에 캐싱 적용
```

### 1. Redis 의존성 설치
```bash
pip install redis
```

### 2. Redis 컨테이너 실행
```bash
cd C:\B2_crawling
docker-compose up -d redis
```

### 3. API 서버 재시작
```bash
cd C:\B2_crawling\src
python api_server.py
```

### 4. 테스트
1. http://localhost:8000/docs → `/search` 실행
2. 터미널 로그 확인:
   - 첫 번째 요청: `❌ 캐시 미스` → `💾 캐시 저장`
   - 두 번째 요청: `🎯 캐시 히트`

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| pgAdmin | http://localhost:5050 | DB 관리 |
| OpenSearch Dashboards | http://localhost:5601 | 검색 데이터 |
| FastAPI Swagger | http://localhost:8000/docs | API 테스트 |
| PostgreSQL | localhost:5434 | DB 직접 연결 시 |
| OpenSearch | localhost:9201 | API 직접 호출 시 |
| Redis | localhost:6380 | 캐시 서버 |

