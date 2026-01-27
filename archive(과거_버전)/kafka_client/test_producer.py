"""
Producer 테스트 스크립트
- 실제 상품 데이터 형식으로 Kafka 발행 테스트
"""
from kafka_client.producer import ProductProducer, publish_products

# 테스트 상품 데이터
test_products = [
    {
        "url": "https://www.musinsa.com/products/12345",
        "title": "테스트 패딩 자켓 - 블랙",
        "brand": "테스트브랜드",
        "price": 89000,
        "seller_info": {
            "company": "테스트 주식회사",
            "biz_num": "123-45-67890",
            "address": "서울시 강남구"
        },
        "crawled_at": "2026-01-17T15:30:00+09:00"
    },
    {
        "url": "https://www.musinsa.com/products/12346",
        "title": "테스트 맨투맨 - 그레이",
        "brand": "테스트브랜드",
        "price": 45000,
        "seller_info": {
            "company": "테스트 주식회사",
            "biz_num": "123-45-67890",
            "address": "서울시 강남구"
        },
        "crawled_at": "2026-01-17T15:30:00+09:00"
    },
    {
        "url": "https://www.musinsa.com/products/12347",
        "title": "테스트 청바지 - 인디고",
        "brand": "데님브랜드",
        "price": 69000,
        "seller_info": {
            "company": "데님 주식회사",
            "biz_num": "987-65-43210",
            "address": "서울시 마포구"
        },
        "crawled_at": "2026-01-17T15:30:00+09:00"
    }
]


if __name__ == "__main__":
    print("🚀 Producer 테스트 시작")
    print("="*50)
    
    # 방법 1: 클래스 직접 사용
    print("\n📦 방법 1: ProductProducer 클래스")
    producer = ProductProducer()
    
    for i, product in enumerate(test_products[:2]):
        print(f"\n[{i+1}] {product['title']}")
        success = producer.send(product)
        print(f"    결과: {'✅ 성공' if success else '❌ 실패'}")
    
    producer.close()
    
    # 방법 2: 간편 함수 사용
    print("\n" + "="*50)
    print("\n📦 방법 2: publish_products() 함수")
    result = publish_products(test_products)
    print(f"    결과: 성공 {result['success']}, 실패 {result['failed']}")
    
    print("\n" + "="*50)
    print("🎉 테스트 완료!")
    print("   Kafka UI에서 메시지 확인: http://localhost:8088")
