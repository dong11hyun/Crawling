from fastapi import FastAPI, Query
from opensearchpy import OpenSearch
from pydantic import BaseModel
from typing import List, Optional
# api_server.py 상단 임포트 부분에 추가
from fastapi.middleware.cors import CORSMiddleware

# 1. 앱(App) 생성: 서버의 간판을 답니다.
app = FastAPI(
    title="Musinsa Search Engine",
    description="무신사 크롤링 데이터를 검색하는 API입니다.",
    version="1.0.0"
)

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
    company: str
    brand: str
    contact: Optional[str] = None # 없을 수도 있으니 Optional

class ProductSchema(BaseModel):
    title: str
    brand: str
    price: int
    url: str
    seller_info: Optional[SellerInfo] = None # 중첩된 구조 처리

# 4. 검색 API 만들기 (GET /search)
# 사용자가 /search?keyword=패딩&min_price=50000 처럼 요청하면 이 함수가 실행됩니다.
@app.get("/search", response_model=List[ProductSchema])
def search_products(
    keyword: str = Query(..., description="검색할 상품명 (예: 패딩)"),
    min_price: int = Query(None, description="최소 가격"),
    max_price: int = Query(None, description="최대 가격")
):
    # --- [OpenSearch 쿼리 작성 (주문서)] ---
    # 복잡해 보이지만 'bool' 쿼리의 기본 구조입니다.
    # must: 반드시 포함해야 함 (검색어)
    # filter: 점수엔 영향 없지만 걸러냄 (가격 등)
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": keyword,           # 사용자가 입력한 단어
                            "fields": ["title^2", "brand"], # 제목(2배 중요), 브랜드에서 찾기
                            "analyzer": "nori"          # 한국어 분석기 사용
                        }
                    }
                ],
                "filter": []
            }
        },
        "size": 30 # 결과는 30개까지만
    }

    # 가격 필터가 있다면 조건 추가 (Range Query)
    if min_price or max_price:
        price_range = {"range": {"price": {}}}
        if min_price:
            price_range["range"]["price"]["gte"] = min_price # gte: 크거나 같다
        if max_price:
            price_range["range"]["price"]["lte"] = max_price # lte: 작거나 같다
        
        search_query["query"]["bool"]["filter"].append(price_range)

    # --- [검색 실행] ---
    try:
        response = client.search(
            body=search_query,
            index=INDEX_NAME
        )
    except Exception as e:
        print(f"Error: {e}")
        return []

    # --- [결과 정리] ---
    # OpenSearch의 복잡한 응답에서 실제 데이터(_source)만 뽑아서 리스트로 만듦
    results = [hit["_source"] for hit in response["hits"]["hits"]]
    
    return results

# 터미널에서 'python api_server.py'로 실행할 때를 위한 코드
if __name__ == "__main__":
    import uvicorn
    # reload=True: 코드를 수정하면 서버가 알아서 재시작됨 (개발할 때 꿀기능)
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)