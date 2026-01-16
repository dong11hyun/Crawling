# Week 1: 백엔드 기본 + 심화

> 동료가 처음부터 따라할 때 **반드시 실행해야 하는 명령어** 모음  
> 마지막 업데이트: 2026-01-16

---

## Day 1: PostgreSQL 환경 구축

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
> (예정)

---

## Day 4: 크롤러 연동
> (예정)

---

## Day 5~7: Redis 캐싱
> (예정)

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| pgAdmin | http://localhost:5050 | DB 관리 |
| OpenSearch Dashboards | http://localhost:5601 | 검색 데이터 |
| FastAPI Swagger | http://localhost:8000/docs | API 테스트 |
| PostgreSQL | localhost:5434 | DB 직접 연결 시 |
| OpenSearch | localhost:9201 | API 직접 호출 시 |
