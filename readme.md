# 🛒 무신사 판매자 정보 수집 프로젝트

> 조사업계용 무신사 판매자 정보 크롤링 & 검색 시스템

---

## 📜 과거 버전 요약 (v1~v2)

Playwright 기반 브라우저 자동화로 크롤링 → OpenSearch 저장 → FastAPI 검색 API 구축.  
Kafka, Airflow, K8s 등 인프라 학습용으로 과도하게 확장됨. 상품 10개 수집에 1분 이상 소요.

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