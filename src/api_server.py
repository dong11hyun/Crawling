import sys
import os

# 현재 파일의 부모 디렉토리(src)를 넘어, 프로젝트 루트(B2_crawling)를 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from opensearchpy import OpenSearch
from pydantic import BaseModel
from typing import List, Optional
import glob # 추가
import json # 추가
# api_server.py 상단 임포트 부분에 추가
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from v4_safe_crawler import run_crawler as run_crawler_v4, stop_crawling as stop_crawling_v4, CRAWL_PROGRESS as CRAWL_PROGRESS_V4
from v5_fast_crawler import run_crawler as run_crawler_v5, stop_crawling as stop_crawling_v5, CRAWL_PROGRESS as CRAWL_PROGRESS_V5


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

class SearchResponse(BaseModel):
    total: int
    items: List[ProductSchema]

# 4. 검색 API 만들기 (GET /search)
# 사용자가 /search?keyword=패딩&min_price=50000 처럼 요청하면 이 함수가 실행됩니다.
# [Day 5~7] Redis 캐싱 적용
from cache import get_cache, set_cache, generate_cache_key

@app.get("/search", response_model=SearchResponse, tags=["검색"])
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
        return {"total": 0, "items": []}

    total_hits = response["hits"]["total"]["value"]
    items = [hit["_source"] for hit in response["hits"]["hits"]]
    
    result_data = {"total": total_hits, "items": items}

    # --- [3. 결과 캐싱] ---
    set_cache(cache_key, result_data, ttl=300)  # 5분간 캐시
    
    return result_data

# 🆕 벡터 검색 API (k-NN 시맨틱 검색)
from embedding_model import encode_text, get_model

@app.get("/search/vector", response_model=SearchResponse, tags=["검색"])
def vector_search(
    keyword: str = Query(..., description="검색할 키워드 (시맨틱 검색)"),
    k: int = Query(20, description="반환할 상품 수"),
    min_price: int = Query(None, description="최소 가격"),
    max_price: int = Query(None, description="최대 가격")
):
    """
    🚀 벡터 기반 시맨틱 검색
    - 검색어를 벡터로 변환하여 유사한 상품 검색
    - '패딩' 검색 시 '다운자켓', '푸퍼' 등 연관 상품도 검색됨
    """
    # 검색어를 벡터로 변환
    query_vector = encode_text(keyword)
    
    # k-NN 검색 쿼리
    knn_query = {
        "size": k,
        "query": {
            "knn": {
                "title_vector": {
                    "vector": query_vector,
                    "k": k
                }
            }
        },
        "_source": {
            "excludes": ["title_vector"]  # 벡터 필드는 응답에서 제외
        }
    }
    
    # 가격 필터가 있으면 post_filter로 적용
    if min_price or max_price:
        price_filter = {"range": {"price": {}}}
        if min_price:
            price_filter["range"]["price"]["gte"] = min_price
        if max_price:
            price_filter["range"]["price"]["lte"] = max_price
        knn_query["post_filter"] = {"bool": {"filter": [price_filter]}}
    
    try:
        response = client.search(body=knn_query, index=INDEX_NAME)
    except Exception as e:
        print(f"Vector Search Error: {e}")
        return {"total": 0, "items": []}
    
    total_hits = response["hits"]["total"]["value"]
    items = []
    for hit in response["hits"]["hits"]:
        item = hit["_source"]
        item["_score"] = hit["_score"]  # 유사도 점수 포함
        items.append(item)
    
    return {"total": total_hits, "items": items}


# 5. 크롤링 트리거 API (POST /crawl)
class CrawlRequest(BaseModel):
    keyword: str
    max_products: int = 100
    version: str = "v4"  # "v4" or "v5"

@app.post("/crawl", tags=["크롤링"])
def trigger_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    백그라운드에서 크롤러를 실행합니다.
    version: "v4" (안정) 또는 "v5" (빠름)
    """
    if request.version == "v5":
        background_tasks.add_task(run_crawler_v5, keyword=request.keyword, max_products=request.max_products)
        version_label = "v5 (병렬 처리)"
    else:
        background_tasks.add_task(run_crawler_v4, keyword=request.keyword, max_products=request.max_products)
        version_label = "v4 (안정)"
    
    return {
        "message": f"크롤링 작업이 시작되었습니다. (검색어: {request.keyword}, 목표: {request.max_products}개, 버전: {version_label})",
        "status": "processing",
        "version": request.version
    }

@app.post("/stop-crawl", tags=["크롤링"])
def request_stop_crawling(version: str = "v4"):
    """
    실행 중인 크롤링 작업을 즉시 중단합니다.
    """
    if version == "v5":
        stop_crawling_v5()
    else:
        stop_crawling_v4()
    return {"message": "크롤링 중지 요청을 보냈습니다.", "status": "stopped", "version": version}

@app.get("/crawl-status", tags=["크롤링"])
def get_crawl_status(version: str = None):
    """
    현재 크롤링 진행 상황을 반환합니다.
    version이 지정되지 않으면 마지막 실행된 버전의 상태를 반환합니다.
    """
    if version == "v5":
        return CRAWL_PROGRESS_V5
    elif version == "v4":
        return CRAWL_PROGRESS_V4
    else:
        # 마지막으로 실행된 버전 반환
        if CRAWL_PROGRESS_V5.get("start_time", 0) > CRAWL_PROGRESS_V4.get("start_time", 0):
            return CRAWL_PROGRESS_V5
        return CRAWL_PROGRESS_V4

@app.get("/latest-crawl", tags=["크롤링"])
def get_latest_crawl_result():
    """
    가장 최근에 수집된 JSON 파일의 내용을 반환합니다.
    """
    # data 폴더 내의 crawl_result_*.json 패턴 검색
    list_of_files = glob.glob('data/crawl_result_*.json')
    
    if not list_of_files:
        return {"total": 0, "items": [], "message": "아직 수집된 데이터가 없습니다."}
        
    # 수정 시간 기준 최신 파일 찾기
    latest_file = max(list_of_files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return {
            "total": len(data), 
            "items": data, 
            "filename": os.path.basename(latest_file),
            "message": "최근 수집 데이터를 불러왔습니다."
        }
    except Exception as e:
        return {"total": 0, "items": [], "message": f"파일 읽기 오류: {str(e)}"}

# 터미널에서 'python api_server.py'로 실행할 때를 위한 코드
if __name__ == "__main__":
    import uvicorn
    # reload=True: 코드를 수정하면 서버가 알아서 재시작됨 (개발할 때 꿀기능)
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)