# 🛒 무신사 판매자 정보 수집 프로젝트

> 조사업계용 무신사 판매자 정보 크롤링 & 검색 시스템

---

## 📜 과거 버전 히스토리

### 🚀 초기 개발 여정 (v0.9 ~ v2.1)

> **쿠팡 (v0.9~v1.1) → IP 차단 → 무신사 (v2.0~v2.1)**

| 버전 | 핵심 변경 | 성과 | 문제점 |
|------|----------|------|--------|
| **v0.9** | 동기식 + CDP 연결 | MVP 완성 | 5건당 50초, 봇 탐지 |
| **v1.0** | 비동기 전환 + Semaphore | **10배 속도 개선** | CSV 파일 충돌 |
| **v1.1** | SQLite + Batch Insert | 안정성 확보 | **쿠팡 IP 차단** |
| **v1.2** | Django + Celery + Redis | 분산 처리 검증 | 오버엔지니어링 |
| **v2.0** | 무신사 전환 + OpenSearch | 한글 검색 지원 | 동적 클래스명 이슈 |
| **v2.1** | FastAPI + 웹 프론트엔드 | 검색 서비스 완성 | Playwright 느림 |

#### 핵심 기술적 해결

| 문제 | 해결책 |
|------|--------|
| 봇 탐지 | Chrome CDP 연결 (사용자 브라우저에 기생) |
| 동적 클래스명 | Meta Tag + XPath 상대 위치 활용 |
| 파일 충돌 | CSV → SQLite → OpenSearch 진화 |
| 비동기 I/O | `asyncio.Lock()`, `as_completed()` |

#### 교훈

> ✅ **속도**: 동기 → 비동기로 10배 개선  
> ✅ **안정성**: 파일 → DB → 검색엔진으로 진화  
> ❌ **복잡도**: Celery, Kafka 등 과도한 인프라 → v3에서 경량화

---

### Week 1-3: 인프라 학습 (Airflow, Kafka)

### Week 1: 백엔드 + 데이터 엔지니어링 기초

| 구현 내용 | 배운 점 |
|-----------|---------|
| SQLAlchemy ORM | SQL Injection 방지, DB 추상화 |
| 듀얼 저장 패턴 | PostgreSQL(원본) + OpenSearch(검색) 동시 저장 |
| Redis 캐싱 | Cache-Aside 패턴, TTL 설정 |
| FastAPI CRUD | REST API 설계, Pydantic 검증 |
| Docker Compose | 멀티 컨테이너 인프라 구축 |

**교훈**: 듀얼 저장 시 **데이터 정합성** 관리가 어려움 → 트랜잭션 처리 또는 메시지 큐 필요

---

### Week 2: Airflow 워크플로우 오케스트레이션

| 구현 내용 | 배운 점 |
|-----------|---------|
| DAG 스케줄링 | cron 표현식, `catchup=False` |
| XCom 데이터 전달 | Task 간 통신, 48KB 크기 제한 대응 |
| 커스텀 Docker 이미지 | Playwright 포함 Airflow 이미지 빌드 |
| 재시도 전략 | 지수 백오프 (Exponential Backoff) |

**교훈**: Airflow는 **복잡한 워크플로우**에 적합하지만, 단순 스크립트에는 **오버엔지니어링**

---

### Week 3: Kafka 실시간 스트리밍

| 구현 내용 | 배운 점 |
|-----------|---------|
| Producer/Consumer | 메시지 발행/소비, acks 옵션 |
| Consumer Group | 파티션 분배, 병렬 처리 |
| DLQ (Dead Letter Queue) | 실패 메시지 격리 및 재처리 |
| Docker 네트워크 | external 네트워크, 컨테이너 간 통신 |

**교훈**: Kafka는 **대규모 분산 시스템**에 필수지만, 소량 데이터에는 **복잡도만 증가**

---

### v1~v2 최종 반성

> ❌ Playwright 브라우저 자동화 → **상품 10개 수집에 1분 이상 소요**  
> ❌ Kafka, Airflow, K8s 등 과도한 인프라 → **관리 복잡도 폭증**  
> ✅ 학습 목표는 달성했으나, **실용성 부족**으로 v3에서 경량화 결정

---

## 🚀 새로운 방향 (v3) - 하이브리드 크롤러

### 핵심 발견

#### 1. 상품 목록 API 발견 ✅
```
GET https://api.musinsa.com/api2/dp/v1/plp/goods
    ?gf=A
    &keyword=패딩
    &sortCode=POPULAR
    &size=10
    &caller=SEARCH
```
→ 상품명, 가격, 브랜드, goodsNo 등 **즉시 반환** (0.5초)

#### 2. 판매자 정보 API는 없음 ❌
```
GET https://goods-detail.musinsa.com/api/v2/goods/{goodsNo}  → 400 Error
GET https://www.musinsa.com/api/goods/{goodsNo}              → 404 Error
```
→ 내부 API로 보호됨, 직접 호출 불가

#### 3. 판매자 정보는 HTML 내 JSON에 존재
```html
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "meta": {
        "data": {
          "company": {
            "name": "㈜영원아웃도어",
            "ceoName": "성기학",
            "businessNumber": "1108127101",
            "phoneNumber": "070-5014-3989",
            "email": "biz@leecompany.kr",
            "address": "경기 성남시 중원구..."
          }
        }
      }
    }
  }
}
</script>
```
→ Next.js SSR 방식으로 페이지에 포함됨

---

## 🔄 v3 크롤러 동작 방식

```
┌──────────────────────────────────────────┐
│ 1단계: 상품 목록 API 호출 (0.5초)         │
│ api.musinsa.com → [goodsNo 10개 수집]    │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ 2단계: 각 상품 HTML 요청 + JSON 파싱       │
│ musinsa.com/products/{goodsNo}           │
│ → __NEXT_DATA__에서 company 추출          │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ 결과: data/crawl_result_{keyword}.json   │
└──────────────────────────────────────────┘
```

---

## ⚡ 속도 비교

| 버전 | 방식 | 상품 10개 소요 시간 |
|------|------|---------------------|
| v1~v2 | Playwright (브라우저) | **60초 이상** |
| **v3** | API + HTML 파싱 | **5~10초** |

---

## 📁 핵심 파일

| 파일 | 설명 |
|------|------|
| `src/v3_fast_crawler.py` | 🚀 새 하이브리드 크롤러 |
| `src/api_server.py` | FastAPI 검색 API |
| `frontend/index.html` | 검색 UI |
| `data/crawl_result_*.json` | 수집 결과 |

---

## 🛠️ 실행 방법

### 1. 크롤링 실행
```bash
cd C:\B2_crawling
.\venv\Scripts\activate
pip install beautifulsoup4  # 최초 1회

python src/v3_fast_crawler.py 패딩
```

### 2. 검색 서비스 실행
```bash
docker-compose up -d          # OpenSearch 실행
python src/init_opensearch.py # 인덱스 초기화
python src/api_server.py      # API 서버
```

### 3. 접속
- **Swagger UI**: http://localhost:8000/docs
- **Frontend**: `frontend/index.html` 열기

---

## � 수집 데이터 구조

```json
{
  "goodsNo": 5841944,
  "title": "NJ1DR03B 남성 액트 프리 EX 하이브리드 다운 자켓",
  "brand": "노스페이스",
  "price": 216300,
  "normalPrice": 309000,
  "saleRate": 30,
  "url": "https://www.musinsa.com/products/5841944",
  "seller_info": {
    "company": "㈜영원아웃도어",
    "ceo": "성기학",
    "biz_num": "1108127101",
    "license": "2013-경기성남-0984",
    "contact": "070-5014-3989",
    "email": "biz@leecompany.kr",
    "address": "경기 성남시 중원구 사기막골로 169 (상대원동)"
  }
}
```

---

## �️ 레거시 코드

| 폴더/파일 | 용도 | 상태 |
|-----------|------|------|
| `archive/` | 쿠팡, 무신사 초기 버전 | 보관 |
| `src/v2.1_crawler.py` | Playwright 크롤러 | 레거시 |
| `src/v2.2_crawler.py` | PostgreSQL 듀얼 저장 | 레거시 |
| `airflow/` | 스케줄링 DAG | 미사용 |
| `k8s/` | 쿠버네티스 배포 | 미사용 |
| `src/kafka_client/` | 스트리밍 | 미사용 |

---

## 📌 개발 기록

- **2025.11.22** - 프로젝트 시작 (Playwright 기반)
- **2025.12.19** - v1.2 OpenSearch 통합
- **2026.01.10** - 폴더 구조 리팩토링
- **2026.01.27** - 🚀 **v3 하이브리드 크롤러 개발** (API + HTML 파싱)