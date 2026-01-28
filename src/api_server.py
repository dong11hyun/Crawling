import sys
import os

# 현재 파일의 부모 디렉토리(src)를 넘어, 프로젝트 루트(B2_crawling)를 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from opensearchpy import OpenSearch
from pydantic import BaseModel
from typing import List, Optional
# api_server.py 상단 임포트 부분에 추가
from fastapi.middleware.cors import CORSMiddleware

# [Day 3] CRUD API 라우터 임포트 (v4에서는 미사용으로 주석 처리)
# from routers import products_router

# 1. 앱(App) 생성: 서버의 간판을 답니다.
app = FastAPI(
    title="Musinsa Search Engine",
    description="무신사 크롤링 데이터를 검색하는 API입니다.",
    version="2.0.0"  # 버전 업!
)

# [Day 3] 상품 CRUD 라우터 등록 (v4에서는 미사용으로 주석 처리)
# app.include_router(products_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 곳에서 접속 허용 (보안상 실무에선 특정 도메인만 넣지만, 지금은 *로)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. OpenSearch 연결: 창고지기 고용
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9201}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)

INDEX_NAME = "musinsa_products"

# 3. 응답 모델 정의 (Pydantic): 손님에게 보여줄 메뉴판 양식
# 데이터가 어떻게 생겼는지 정의해두면, FastAPI가 알아서 검사하고 문서를 만들어줍니다.
class SellerInfo(BaseModel):
    company: Optional[str] = None
    brand: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    biz_num: Optional[str] = None
    address: Optional[str] = None
    ceo: Optional[str] = None       # 추가
    license: Optional[str] = None   # 추가


class ProductSchema(BaseModel):
    goodsNo: Optional[int] = None   # 추가
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[int] = 0
    normalPrice: Optional[int] = 0  # 추가
    saleRate: Optional[int] = 0     # 추가
    url: Optional[str] = None
    thumbnail: Optional[str] = None # 추가
    seller_info: Optional[SellerInfo] = None

# 4. 검색 API 만들기 (GET /search)
# 사용자가 /search?keyword=패딩&min_price=50000 처럼 요청하면 이 함수가 실행됩니다.
# [Day 5~7] Redis 캐싱 적용
from cache import get_cache, set_cache, generate_cache_key

@app.get("/search", response_model=List[ProductSchema], tags=["검색"])
def search_products(
    keyword: str = Query(..., description="검색할 상품명 (예: 패딩)"),
    min_price: int = Query(None, description="최소 가격"),
    max_price: int = Query(None, description="최대 가격"),
    skip: int = Query(0, description="검색 시작 위치 (페이지네이션)")  # 추가
):
    # --- [1. 캐시 확인] ---
    # 캐시 키에 skip 포함 (페이지별로 캐싱)
    cache_key = generate_cache_key("search", keyword=keyword, min_price=min_price, max_price=max_price, skip=skip)
    cached_result = get_cache(cache_key)
    
    if cached_result is not None:
        # 캐시 히트! OpenSearch 쿼리 없이 바로 반환
        return cached_result
    
    # --- [2. 캐시 미스 → OpenSearch 검색] ---
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": keyword,
                            "fields": ["title^2", "brand"],
                            "analyzer": "nori"
                        }
                    }
                ],
                "filter": []
            }
        },
        "from": skip,     # 시작 위치 적용
        "size": 20        # 무한 스크롤을 위해 한 번에 20개씩 로딩
    }

    # 가격 필터
    if min_price or max_price:
        price_range = {"range": {"price": {}}}
        if min_price:
            price_range["range"]["price"]["gte"] = min_price
        if max_price:
            price_range["range"]["price"]["lte"] = max_price
        search_query["query"]["bool"]["filter"].append(price_range)

    try:
        response = client.search(body=search_query, index=INDEX_NAME)
    except Exception as e:
        print(f"Error: {e}")
        return []

    results = [hit["_source"] for hit in response["hits"]["hits"]]
    
    # --- [3. 결과 캐싱] ---
    set_cache(cache_key, results, ttl=300)  # 5분간 캐시
    
    return results

# 터미널에서 'python api_server.py'로 실행할 때를 위한 코드
if __name__ == "__main__":
    import uvicorn
    # reload=True: 코드를 수정하면 서버가 알아서 재시작됨 (개발할 때 꿀기능)
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)