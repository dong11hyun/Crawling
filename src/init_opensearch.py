from opensearchpy import OpenSearch

# 1. OpenSearch 접속 정보
HOST = 'localhost'
PORT = 9201  # Docker 매핑 포트
AUTH = ('admin', 'admin')  # 보안 모드일 경우 필요

client = OpenSearch(
    hosts=[{'host': HOST, 'port': PORT}],
    http_compress=True,
    http_auth=AUTH, # 보안 모드일 경우 필요
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
            "goodsNo": { "type": "integer" },
            "title": {
                "type": "text",
                "analyzer": "korean_analyzer",
                "fields": {
                    "keyword": { "type": "keyword" }
                }
            },
            "brand": { "type": "keyword" },
            "price": { "type": "integer" },
            "normalPrice": { "type": "integer" },
            "saleRate": { "type": "integer" },
            "url": { "type": "keyword" },
            "thumbnail": { "type": "keyword" },
            "crawled_at": { "type": "date" },
            "seller_info": {
                "type": "object",
                "properties": {
                    "company": { "type": "keyword" },
                    "ceo": { "type": "keyword" },
                    "biz_num": { "type": "keyword" },
                    "license": { "type": "keyword" },
                    "contact": { "type": "keyword" },
                    "email": { "type": "keyword" },
                    "address": { "type": "text" }
                }
            }
        }
    }
}

# 3. 기존에 있다면 삭제하고 새로 생성 (초기화)
if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)
    print(f"🗑️ 기존 '{index_name}' 인덱스를 삭제했습니다.")

client.indices.create(index=index_name, body=index_body)
print(f"✅ '{index_name}' 인덱스를 성공적으로 생성했습니다!")