"""
상품 데이터 임베딩 생성 및 OpenSearch 적재 스크립트
- JSON 파일에서 상품 로드
- 각 상품 title을 벡터로 변환
- k-NN 인덱스에 bulk 적재
"""
import json
import os
import sys
import argparse
from datetime import datetime
from opensearchpy import OpenSearch, helpers

# 임베딩 모델 임포트
from embedding_model import encode_texts_batch, get_embedding_dimension

# ================= 설정 =================
HOST = 'localhost'
PORT = 9201
INDEX_NAME = "musinsa_products"


def get_client():
    """OpenSearch 클라이언트 생성"""
    return OpenSearch(
        hosts=[{'host': HOST, 'port': PORT}],
        http_auth=('admin', 'admin'),
        use_ssl=False,
        verify_certs=False,
        timeout=60
    )


def load_data(filepath: str) -> list:
    """JSON 또는 JSONL 파일 로드"""
    is_jsonl = filepath.lower().endswith('.jsonl')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        if is_jsonl:
            items = [json.loads(line) for line in f if line.strip()]
        else:
            items = json.load(f)
    
    return items


def generate_embeddings_and_load(client, items: list, batch_size: int = 100):
    """임베딩 생성 후 OpenSearch 적재"""
    total = len(items)
    success_count = 0
    fail_count = 0
    
    print(f"\n📦 총 {total:,}개 아이템 임베딩 생성 및 적재 시작...")
    print(f"   배치 크기: {batch_size}")
    print(f"   벡터 차원: {get_embedding_dimension()}")
    print("-" * 50)
    
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        
        # 1. 제목 추출
        titles = [item.get('title', '') for item in batch]
        
        # 2. 임베딩 생성 (배치)
        embeddings = encode_texts_batch(titles, show_progress=False)
        
        # 3. OpenSearch 액션 생성
        actions = []
        for item, embedding in zip(batch, embeddings):
            doc_id = str(item.get('goodsNo', ''))
            if not doc_id:
                fail_count += 1
                continue
            
            # 벡터 필드 추가
            item['title_vector'] = embedding
            
            if 'crawled_at' not in item:
                item['crawled_at'] = datetime.now().isoformat()
            
            actions.append({
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": item
            })
        
        # 4. Bulk 적재
        try:
            success, failed = helpers.bulk(client, actions, refresh=False)
            success_count += success
            if failed:
                fail_count += len(failed)
        except Exception as e:
            print(f"❌ Bulk 오류: {e}")
            fail_count += len(batch)
        
        # 진행률 출력
        progress = min(i + batch_size, total)
        pct = (progress / total) * 100
        print(f"   [{progress:,}/{total:,}] ({pct:.1f}%) - 성공: {success_count:,}")
    
    # 최종 refresh
    client.indices.refresh(index=INDEX_NAME)
    
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(description="상품 데이터 임베딩 생성 및 OpenSearch 적재")
    parser.add_argument("data_file", help="적재할 JSON/JSONL 파일 경로")
    parser.add_argument("--batch-size", type=int, default=100, help="배치 크기 (기본값: 100)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_file):
        print(f"❌ 파일을 찾을 수 없습니다: {args.data_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 상품 데이터 임베딩 & OpenSearch 적재")
    print("=" * 60)
    print(f"   파일: {args.data_file}")
    print(f"   인덱스: {INDEX_NAME}")
    print("=" * 60)
    
    # 1. OpenSearch 연결
    print("\n🔗 OpenSearch 연결 중...")
    client = get_client()
    
    if not client.ping():
        print("❌ OpenSearch 연결 실패!")
        sys.exit(1)
    print("   ✅ 연결 성공")
    
    # 2. 데이터 로드
    print(f"\n📄 데이터 파일 로드 중...")
    items = load_data(args.data_file)
    print(f"   ✅ {len(items):,}개 아이템 로드 완료")
    
    # 3. 임베딩 생성 및 적재
    start_time = datetime.now()
    success, fail = generate_embeddings_and_load(client, items, args.batch_size)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 4. 결과 출력
    print("\n" + "=" * 60)
    print("🎉 임베딩 & 적재 완료!")
    print("=" * 60)
    print(f"   성공: {success:,}개")
    print(f"   실패: {fail}개")
    print(f"   소요 시간: {elapsed:.1f}초")
    print(f"   처리 속도: {success/elapsed:.1f}개/초")
    
    # 인덱스 통계
    stats = client.indices.stats(index=INDEX_NAME)
    doc_count = stats['indices'][INDEX_NAME]['primaries']['docs']['count']
    print(f"\n   📊 현재 인덱스 문서 수: {doc_count:,}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
