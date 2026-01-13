from opensearchpy import OpenSearch

# 1. OpenSearch 연결 정보
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9201}],  # docker-compose에서 9201:9200으로 매핑됨
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)

index_name = "musinsa_products"

# 2. 인덱스 설정 (매핑 정의)
index_body = {
    "settings": {
        "index": {
            "analysis": {
                "tokenizer": {
                    "nori_user_dict": {
                        "type": "nori_tokenizer",
                        "decompound_mode": "mixed" # 합성어 분리 (여성패딩 -> 여성, 패딩)
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
            "title": { # 상품명
                "type": "text",
                "analyzer": "korean_analyzer" # 한국어 분석 적용
            },
            "brand": { # 브랜드
                "type": "keyword" # 정확히 일치해야 검색됨 (필터용)
            },
            "price": { # 가격
                "type": "integer" # 숫자 계산 및 범위 검색용
            },
            "url": { "type": "keyword" },
            "image_url": { "type": "keyword" }
        }
    }
}

# 3. 기존에 있다면 삭제하고 새로 생성 (초기화)
if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)
    print(f"🗑️ 기존 '{index_name}' 인덱스를 삭제했습니다.")

client.indices.create(index=index_name, body=index_body)
print(f"✅ '{index_name}' 인덱스를 성공적으로 생성했습니다!")