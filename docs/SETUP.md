# 프로젝트 설치 및 실행 가이드

## 📋 사전 요구사항

- **Python 3.11+**
- **Docker** (OpenSearch용)
- **Git**

---

## 🚀 빠른 시작

### 1. 가상환경 설정

```bash
# 프로젝트 폴더로 이동
cd B2_crawling

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. 패키지 설치 & Docker 재빌드

```bash
pip install -r requirements.txt

# 벡터 검색용 추가 패키지
pip install sentence-transformers

# 도커 재빌드
docker-compose up --build -d
```

### 3. OpenSearch 실행 (Docker)

```bash
docker-compose up -d
```

OpenSearch가 `localhost:9201`에서 실행됩니다.

### 4. 인덱스 초기화

```bash
# 기본 인덱스 (키워드 검색만)
python src/init_opensearch.py

# 또는 k-NN 인덱스 (벡터 검색 포함)
python src/init_opensearch_knn.py
```

### 5. 데이터 적재

```bash
# 기본 적재 (벡터 없음)
python src/reload_opensearch.py data/crawl_result_v5_패딩_20260202_180355.json --recreate

# 벡터 임베딩 포함 적재 (권장)
python src/generate_embeddings.py data/crawl_result_v5_패딩_20260202_180355.json
```

> ⚠️ 첫 실행 시 임베딩 모델 다운로드 (~500MB, 1회만)  
> ⚠️ 임베딩 생성 소요 시간: 2만개 기준 ~15분

### 6. API 서버 실행

```bash
python src/api_server.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 7. 프론트엔드 접속

- **키워드 검색:** `frontend/index_v2.html` 브라우저에서 열기
- **벡터 검색:** `frontend/index_vector.html` 브라우저에서 열기
- **API 문서:** http://localhost:8000/docs

---

## 📦 전체 명령어 요약

```bash
# 1. 가상환경
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Mac/Linux

# 2. 패키지 설치
pip install -r requirements.txt
pip install sentence-transformers

# 3. OpenSearch
docker-compose up -d

# 4. 인덱스 + 데이터
python src/init_opensearch_knn.py
python src/generate_embeddings.py data/crawl_result_v5_패딩_20260202_180355.json

# 5. 서버 실행
python src/api_server.py
```

---

## 🔧 트러블슈팅

### OpenSearch 연결 실패
```bash
# Docker 컨테이너 상태 확인
docker ps

# 재시작
docker-compose restart
```

### 모델 로딩 오류
```bash
# 캐시 삭제 후 재다운로드
rm -rf ~/.cache/huggingface
python src/embedding_model.py  # 테스트
```

### 포트 충돌
```bash
# 8000 포트 사용 중이면
# api_server.py 마지막 줄에서 port 변경
uvicorn.run("api_server:app", host="0.0.0.0", port=8001, reload=True)
```

---

## 📁 주요 파일 설명

| 파일 | 설명 |
|------|------|
| `src/api_server.py` | FastAPI 서버 |
| `src/embedding_model.py` | 임베딩 모델 |
| `src/init_opensearch_knn.py` | k-NN 인덱스 생성 |
| `src/generate_embeddings.py` | 벡터 생성 & 적재 |
| `src/reload_opensearch.py` | 데이터 재적재 |
| `frontend/index_v2.html` | 키워드 검색 UI |
| `frontend/index_vector.html` | 벡터 검색 UI |

---

## 🌐 API 엔드포인트

| 엔드포인트 | 설명 |
|------------|------|
| `GET /search?keyword=패딩` | 키워드 검색 |
| `GET /search/vector?keyword=따뜻한&k=20` | 벡터 검색 |
| `GET /docs` | Swagger API 문서 |
