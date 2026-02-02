"""
OpenSearch 재적재 스크립트
- JSONL 파일을 읽어서 OpenSearch에 bulk 적재
- 기존 인덱스 초기화 또는 유지 옵션 제공
python src/reload_opensearch.py "data/crawl_result_v5_패딩_20260202_180355.json" --recreate
"""
import json
import os
import sys
import argparse
from datetime import datetime
from opensearchpy import OpenSearch, helpers

# ================= 설정 =================
HOST = 'localhost'
PORT = 9201
INDEX_NAME = "musinsa_products"

# 인덱스 매핑 (init_opensearch.py와 동일)
INDEX_BODY = {
    "settings": {
        "index": {
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


def get_client():
    """OpenSearch 클라이언트 생성"""
    return OpenSearch(
        hosts=[{'host': HOST, 'port': PORT}],
        http_auth=('admin', 'admin'),
        use_ssl=False,
        verify_certs=False,
        timeout=60
    )


def create_index(client, index_name: str, recreate: bool = False):
    """인덱스 생성 (recreate=True면 기존 인덱스 삭제 후 생성)"""
    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print(f"🗑️  기존 '{index_name}' 인덱스 삭제 완료")
    
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=INDEX_BODY)
        print(f"✅ '{index_name}' 인덱스 생성 완료")
    else:
        print(f"ℹ️  '{index_name}' 인덱스가 이미 존재합니다. 기존 인덱스에 적재합니다.")


def load_data(filepath: str) -> list:
    """JSON 또는 JSONL 파일 로드 (확장자로 자동 판별)"""
    items = []
    
    # 확장자 확인
    is_jsonl = filepath.lower().endswith('.jsonl')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        if is_jsonl:
            # JSONL: 줄 단위로 파싱
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    items.append(item)
                except json.JSONDecodeError as e:
                    print(f"⚠️  {line_num}번째 줄 JSON 파싱 오류: {e}")
        else:
            # JSON: 전체 파일을 배열로 파싱
            try:
                items = json.load(f)
                if not isinstance(items, list):
                    print("⚠️  JSON 파일이 배열 형식이 아닙니다.")
                    items = [items]
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {e}")
                return []
    
    return items


def bulk_load(client, items: list, index_name: str, batch_size: int = 500):
    """Bulk API로 데이터 적재"""
    total = len(items)
    success_count = 0
    fail_count = 0
    
    print(f"\n📦 총 {total:,}개 아이템 적재 시작...")
    print(f"   배치 크기: {batch_size}")
    print("-" * 50)
    
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        actions = []
        
        for item in batch:
            doc_id = str(item.get('goodsNo', ''))
            if not doc_id:
                fail_count += 1
                continue
            
            # crawled_at이 없으면 현재 시간으로 설정
            if 'crawled_at' not in item:
                item['crawled_at'] = datetime.now().isoformat()
            
            actions.append({
                "_index": index_name,
                "_id": doc_id,
                "_source": item
            })
        
        try:
            success, failed = helpers.bulk(client, actions, refresh=False)
            success_count += success
            if failed:
                fail_count += len(failed)
            
            progress = min(i + batch_size, total)
            pct = (progress / total) * 100
            print(f"   [{progress:,}/{total:,}] ({pct:.1f}%) - 성공: {success_count:,}, 실패: {fail_count}")
            
        except Exception as e:
            print(f"❌ Bulk 적재 오류: {e}")
            fail_count += len(batch)
    
    # 최종 refresh
    client.indices.refresh(index=index_name)
    
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description="JSON/JSONL 파일을 OpenSearch에 재적재",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python reload_opensearch.py data/crawl_result_v5_패딩_20260202_180355.json
  python reload_opensearch.py data/crawl_progress_v5_패딩.jsonl --recreate
  python reload_opensearch.py data/crawl_result.json --batch-size 1000
        """
    )
    parser.add_argument("data_file", help="적재할 JSON 또는 JSONL 파일 경로")
    parser.add_argument("--recreate", action="store_true", 
                        help="인덱스 삭제 후 재생성 (기존 데이터 삭제)")
    parser.add_argument("--index", default=INDEX_NAME, 
                        help=f"인덱스 이름 (기본값: {INDEX_NAME})")
    parser.add_argument("--batch-size", type=int, default=500, 
                        help="Bulk 배치 크기 (기본값: 500)")
    
    args = parser.parse_args()
    
    # 파일 존재 확인
    if not os.path.exists(args.data_file):
        print(f"❌ 파일을 찾을 수 없습니다: {args.data_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 OpenSearch 재적재 스크립트")
    print("=" * 60)
    print(f"   파일: {args.data_file}")
    print(f"   인덱스: {args.index}")
    print(f"   인덱스 초기화: {'예' if args.recreate else '아니오 (기존 데이터 유지)'}")
    print("=" * 60)
    
    # 1. OpenSearch 연결
    print("\n🔗 OpenSearch 연결 중...")
    client = get_client()
    
    if not client.ping():
        print("❌ OpenSearch 연결 실패!")
        sys.exit(1)
    print("   ✅ 연결 성공")
    
    # 2. 인덱스 생성/확인
    print("\n📋 인덱스 설정 중...")
    create_index(client, args.index, args.recreate)
    
    # 3. JSON/JSONL 파일 로드
    print(f"\n📄 데이터 파일 로드 중...")
    items = load_data(args.data_file)
    print(f"   ✅ {len(items):,}개 아이템 로드 완료")
    
    # 4. Bulk 적재
    start_time = datetime.now()
    success, fail = bulk_load(client, items, args.index, args.batch_size)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 5. 결과 출력
    print("\n" + "=" * 60)
    print("🎉 적재 완료!")
    print("=" * 60)
    print(f"   성공: {success:,}개")
    print(f"   실패: {fail}개")
    print(f"   소요 시간: {elapsed:.1f}초")
    print(f"   처리 속도: {success/elapsed:.1f}개/초")
    
    # 인덱스 통계
    stats = client.indices.stats(index=args.index)
    doc_count = stats['indices'][args.index]['primaries']['docs']['count']
    print(f"\n   📊 현재 인덱스 문서 수: {doc_count:,}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
