# 벡터 검색 (Semantic Search) 구현 문서

> 무신사 크롤링 프로젝트에 AI 기반 시맨틱 검색 기능 추가

## 목차
1. [개요](#개요)
2. [구현 배경](#구현-배경)
3. [기술 스택](#기술-스택)
4. [파일 구조](#파일-구조)
5. [구현 상세](#구현-상세)
6. [API 사용법](#api-사용법)
7. [테스트 결과](#테스트-결과)
8. [한계점 및 개선 방향](#한계점-및-개선-방향)

---

## 개요

기존 **키워드 매칭 검색**에서 **벡터 기반 시맨틱 검색**으로 확장하여, 검색어와 정확히 일치하지 않아도 **의미적으로 유사한 상품**을 찾을 수 있도록 개선했습니다.

### Before vs After

| 검색 방식 | "따뜻한 겨울 아우터" 검색 시 |
|-----------|---------------------------|
| **기존 키워드 검색** | title에 "따뜻한", "겨울", "아우터" 포함된 상품만 (215개) |
| **벡터 시맨틱 검색** | WINTER PARKA, 다운자켓, 푸퍼 등 의미 유사 상품 포함 |

---

## 구현 배경

### 문제점
- 2만여개 패딩 데이터 중 "패딩" 검색 시 ~5,000개만 검색됨
- "다운자켓", "푸퍼", "점퍼" 등 연관 상품 누락
- 무신사 실제 검색은 카테고리 + 시맨틱 검색으로 전체 표시

### 해결 방안
1. **동의어 사전** - 간단하지만 수동 관리 필요
2. **벡터 DB** - AI 기반 의미 검색 ✅ 선택
3. **전체 표시** - 검색 기능 의미 없음

---

## 기술 스택

### 임베딩 모델
```
모델명: paraphrase-multilingual-MiniLM-L12-v2
제공: sentence-transformers (HuggingFace)
차원: 384
특징: 한국어 포함 50개 언어 지원
비용: 무료 (오픈소스)
```

### 벡터 저장소
```
OpenSearch k-NN Plugin
방식: HNSW (Hierarchical Navigable Small World)
유사도: Cosine Similarity
엔진: nmslib
```

### 대안 모델 (추후 업그레이드 가능)
| 모델 | 특징 | 비용 |
|------|------|------|
| OpenAI text-embedding-3-small | 더 정확함 | 유료 |
| Google text-embedding-004 | 한국어 우수 | 유료 |
| KoSimCSE | 한국어 특화 | 무료 |

---

## 파일 구조

```
src/
├── embedding_model.py      # 🆕 임베딩 모델 모듈
├── init_opensearch_knn.py  # 🆕 k-NN 인덱스 생성
├── generate_embeddings.py  # 🆕 상품 임베딩 생성 & 적재
├── api_server.py           # 📝 /search/vector 엔드포인트 추가
└── ...

frontend/
├── index_vector.html       # 🆕 벡터 검색 전용 UI
├── index_v2.html           # 기존 키워드 검색 UI
└── ...
```

---

## 구현 상세

### 1. 임베딩 모델 (`embedding_model.py`)

```python
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(MODEL_NAME)

def encode_text(text: str) -> list:
    """텍스트를 384차원 벡터로 변환"""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
```

**특징:**
- 싱글톤 패턴으로 모델 1회만 로딩
- 배치 처리 지원 (`encode_texts_batch`)
- L2 정규화 적용 (코사인 유사도 최적화)

---

### 2. k-NN 인덱스 (`init_opensearch_knn.py`)

```python
index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        }
    },
    "mappings": {
        "properties": {
            # 기존 필드들...
            "title_vector": {
                "type": "knn_vector",
                "dimension": 384,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib"
                }
            }
        }
    }
}
```

**HNSW 파라미터:**
- `ef_construction: 128` - 인덱스 빌드 품질
- `m: 24` - 노드당 연결 수
- `ef_search: 100` - 검색 정확도

---

### 3. 임베딩 생성 (`generate_embeddings.py`)

```bash
# 실행 명령어
python src/generate_embeddings.py "data/crawl_result_v5_패딩.json"
```

**처리 흐름:**
1. JSON 파일 로드 (22,956개 상품)
2. 각 상품 `title`을 384차원 벡터로 변환
3. `title_vector` 필드 추가
4. OpenSearch에 bulk 적재

**성능:**
- 처리 시간: ~15분
- 처리 속도: 25.6개/초
- 고유 문서: 22,401개 (중복 제거)

---

### 4. API 엔드포인트 (`api_server.py`)

```python
@app.get("/search/vector")
def vector_search(
    keyword: str,      # 검색어
    k: int = 20,       # 반환 개수
    min_price: int = None,
    max_price: int = None
):
    # 1. 검색어 → 벡터 변환
    query_vector = encode_text(keyword)
    
    # 2. k-NN 검색
    knn_query = {
        "query": {
            "knn": {
                "title_vector": {
                    "vector": query_vector,
                    "k": k
                }
            }
        }
    }
    
    return client.search(body=knn_query, index=INDEX_NAME)
```

---

### 5. 프론트엔드 (`index_vector.html`)

**특징:**
- 모던 그라디언트 디자인 (보라~파랑)
- **유사도 점수 배지** 표시
- 결과 수 조절 (20~200개)
- 가격 필터 지원
- 검색 소요 시간 표시

**접근:** `frontend/index_vector.html` 브라우저에서 열기

---

## API 사용법

### 벡터 검색
```bash
# 기본 검색
GET /search/vector?keyword=따뜻한 겨울 아우터

# 결과 수 지정
GET /search/vector?keyword=패딩&k=50

# 가격 필터
GET /search/vector?keyword=패딩&min_price=50000&max_price=100000
```

### 응답 예시
```json
{
  "total": 20,
  "items": [
    {
      "goodsNo": 5660886,
      "title": "하트 패딩",
      "brand": "미닝러스",
      "price": 44000,
      "_score": 0.95  // 유사도 점수
    }
  ]
}
```

---

## 테스트 결과

### 검색어별 비교

| 검색어 | 키워드 검색 | 벡터 검색 |
|--------|-------------|-----------|
| "패딩" | title에 "패딩" 포함만 | 다운자켓, 푸퍼 등 포함 |
| "따뜻한 겨울 아우터" | 215개 (텍스트 매칭) | WINTER PARKA 등 |
| "다운자켓" | ~1,000개 | 패딩, 푸퍼 등 연관 |

### 색상 인식 테스트

"따뜻한"과 각 색상 단어의 유사도:

| 색상 | 유사도 | 해석 |
|------|--------|------|
| 베이지 | 0.48 | ✅ 따뜻한 색상 인식 |
| 아이보리 | 0.43 | ✅ 따뜻한 색상 인식 |
| 네이비 | 0.39 | 중간 |
| 블랙 | 0.34 | 중립 |
| 블루 | 0.23 | ❌ 차가운 색상 (낮음) |

**결론:** 모델이 색채 이론을 **부분적으로** 이해하지만 전문 지식은 제한적

---

## 한계점 및 개선 방향

### 현재 한계점

1. **의미 이해 한계**
   - 패션 전문 용어 인식 부족
   - 브랜드-스타일 연관성 미반영

2. **검색 정확도**
   - 무료 모델 사용으로 정확도 제한
   - 한국어 특화 모델이 아님

3. **성능**
   - 첫 검색 시 모델 로딩 지연 (~5초)
   - 대용량 데이터 시 임베딩 생성 시간 증가

### 개선 방향

1. **모델 업그레이드**
   - OpenAI `text-embedding-3-small` (더 정확)
   - 한국어 특화 `KoSimCSE` 모델

2. **하이브리드 검색**
   - 키워드 + 벡터 점수 결합
   - 카테고리 필터 추가

3. **동의어 사전 보강**
   - 패딩 = 다운자켓 = 푸퍼 = 점퍼
   - 따뜻한 → 베이지, 브라운, 카멜

4. **캐싱**
   - 자주 검색되는 쿼리 벡터 캐싱
   - Redis 활용

---

## 참고 자료

- [sentence-transformers 공식 문서](https://www.sbert.net/)
- [OpenSearch k-NN Plugin](https://opensearch.org/docs/latest/search-plugins/knn/)
- [HuggingFace 모델](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
