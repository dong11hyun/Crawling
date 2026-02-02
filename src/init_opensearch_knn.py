"""
OpenSearch k-NN 인덱스 초기화 스크립트
- 벡터 검색을 위한 k-NN 설정 포함
- 기존 인덱스 삭제 후 재생성
"""
from opensearchpy import OpenSearch

# OpenSearch 접속 정보
HOST = 'localhost'
PORT = 9201
AUTH = ('admin', 'admin')

client = OpenSearch(
    hosts=[{'host': HOST, 'port': PORT}],
    http_compress=True,
    http_auth=AUTH,
    use_ssl=False,
    verify_certs=False,
)

INDEX_NAME = "musinsa_products"

# k-NN 벡터 검색을 위한 인덱스 설정
index_body = {
    "settings": {
        "index": {
            "knn": True,  # k-NN 활성화
            "knn.algo_param.ef_search": 100,  # 검색 정확도 (높을수록 정확, 느림)
            "analysis": {
                "tokenizer": {
                    "nori_user_dict": {
                        "type": "nori_tokenizer",
                        "decompound_mode": "mixed"
                    }
                },
                "analyzer": {
                    "korean_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_user_dict"
                    }
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # 기존 필드들
            "goodsNo": {"type": "integer"},
            "title": {
                "type": "text",
                "analyzer": "korean_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "brand": {"type": "keyword"},
            "price": {"type": "integer"},
            "normalPrice": {"type": "integer"},
            "saleRate": {"type": "integer"},
            "url": {"type": "keyword"},
            "thumbnail": {"type": "keyword"},
            "crawled_at": {"type": "date"},
            "seller_info": {
                "type": "object",
                "properties": {
                    "company": {"type": "keyword"},
                    "ceo": {"type": "keyword"},
                    "biz_num": {"type": "keyword"},
                    "license": {"type": "keyword"},
                    "contact": {"type": "keyword"},
                    "email": {"type": "keyword"},
                    "address": {"type": "text"}
                }
            },
            # 🆕 벡터 필드 추가
            "title_vector": {
                "type": "knn_vector",
                "dimension": 384,  # paraphrase-multilingual-MiniLM-L12-v2 출력 차원
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",  # 코사인 유사도
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 24
                    }
                }
            }
        }
    }
}


def create_knn_index(recreate: bool = True):
    """k-NN 인덱스 생성"""
    
    if recreate and client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
        print(f"🗑️  기존 '{INDEX_NAME}' 인덱스 삭제 완료")
    
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"✅ '{INDEX_NAME}' k-NN 인덱스 생성 완료!")
        print(f"   - 벡터 필드: title_vector (768차원)")
        print(f"   - 유사도 방식: cosinesimil (코사인 유사도)")
    else:
        print(f"ℹ️  '{INDEX_NAME}' 인덱스가 이미 존재합니다.")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OpenSearch k-NN 인덱스 초기화")
    print("=" * 60)
    
    # 연결 테스트
    if client.ping():
        print("✅ OpenSearch 연결 성공")
    else:
        print("❌ OpenSearch 연결 실패")
        exit(1)
    
    # 인덱스 생성
    create_knn_index(recreate=True)
    
    print("=" * 60)
