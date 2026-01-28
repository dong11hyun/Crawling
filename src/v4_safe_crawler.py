"""
무신사 크롤러 v4 - 안전 수집 (1000건)
- Rate Limiting + 랜덤 딜레이
- User-Agent 로테이션
- 429 에러 핸들링
- 진행 상태 저장 (중단 시 재개)
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import random
import os
from datetime import datetime
from opensearchpy import OpenSearch  # OpenSearch 클라이언트 추가

# ================= 설정 =================
SEARCH_KEYWORD = "패딩"
MAX_PRODUCTS = 1000
BATCH_SIZE = 60  # API에서 한 번에 가져올 개수

# 딜레이 설정 (초) - 1.8배 증속
API_DELAY = 0.6      # 목록 API
HTML_DELAY = 1.2     # 상세 페이지
RANDOM_RANGE = (0.3, 0.7)  # 추가 랜덤 딜레이

# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# 파일 경로
PROGRESS_FILE = "data/progress.json"
JSONL_FILE = "data/crawl_progress_{keyword}.jsonl"  # 점진적 저장용
OUTPUT_FILE = "data/crawl_result_{keyword}_{timestamp}.json"

# 전역 중지 플래그
STOP_CRAWLER_FLAG = False

def stop_crawling():
    """크롤링 중지"""
    global STOP_CRAWLER_FLAG
    STOP_CRAWLER_FLAG = True
    print("\n🛑 크롤링 중지 요청됨!")

# 전역 진행 상태 (초기값)
CRAWL_PROGRESS = {
    "status": "idle",       # idle, running, finished, stopped
    "keyword": "",
    "total": 0,             # 목표 개수
    "current": 0,           # 현재 수집 개수
    "start_time": 0.0,      # 시작 시간 (ETA 계산용)
}



def get_headers():
    """랜덤 User-Agent 헤더 생성"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/html",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://www.musinsa.com/",
    }


def safe_delay(base_delay: float):
    """랜덤 딜레이 적용"""
    delay = base_delay + random.uniform(*RANDOM_RANGE)
    time.sleep(delay)


def load_progress() -> set:
    """이전 진행 상태 로드"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('collected_ids', []))
    return set()


def save_progress(collected_ids: set):
    """진행 상태 저장"""
    os.makedirs('data', exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'collected_ids': list(collected_ids)}, f)


def append_to_jsonl(filepath: str, data: dict):
    """JSONL 파일에 한 줄씩 추가 (점진적 저장)"""
    os.makedirs('data', exist_ok=True)
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def load_jsonl(filepath: str) -> list:
    """JSONL 파일에서 기존 데이터 로드"""
    results = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    return results


def get_product_list(keyword: str, page: int, size: int = 60, session=None) -> list:
    """상품 목록 API 호출"""
    url = "https://api.musinsa.com/api2/dp/v1/plp/goods"
    params = {
        "gf": "A",
        "keyword": keyword,
        "sortCode": "POPULAR",
        "isUsed": "false",
        "page": page,
        "size": size,
        "caller": "SEARCH"
    }
    
    for attempt in range(3):
        try:
            response = session.get(url, params=params, headers=get_headers(), timeout=15)
            
            if response.status_code == 429:
                print(f"   ⚠️ 429 Too Many Requests - 60초 대기...")
                time.sleep(60)
                continue
            
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("list", [])
            
        except Exception as e:
            print(f"   ❌ API 호출 실패 (시도 {attempt+1}/3): {e}")
            time.sleep(10)
    
    return []


def get_seller_info(goods_no: int, session=None) -> dict:
    """상품 상세 페이지에서 판매자 정보 추출"""
    url = f"https://www.musinsa.com/products/{goods_no}"
    
    for attempt in range(3):
        try:
            response = session.get(url, headers=get_headers(), timeout=15)
            
            if response.status_code == 429:
                print(f"   ⚠️ 429 Too Many Requests - 60초 대기...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            
            if not next_data_script:
                return {}
            
            data = json.loads(next_data_script.string)
            company = data.get('props', {}).get('pageProps', {}).get('meta', {}).get('data', {}).get('company', {})
            
            if not company:
                return {}
            
            return {
                "company": company.get('name', ''),
                "ceo": company.get('ceoName', ''),
                "biz_num": company.get('businessNumber', ''),
                "license": company.get('mailOrderReportNumber', ''),
                "contact": company.get('phoneNumber', ''),
                "email": company.get('email', ''),
                "address": f"{company.get('address', '')} {company.get('detailAddress', '')}".strip()
            }
            
        except Exception as e:
            print(f"   ❌ HTML 파싱 실패 (시도 {attempt+1}/3): {e}")
            time.sleep(5)
    
    return {}


    return {}


def get_opensearch_client():
    """OpenSearch 클라이언트 생성"""
    return OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9201}],  # Docker 매핑 포트 확인
        http_auth=None,
        use_ssl=False,
        verify_certs=False,
        timeout=30
    )


def index_to_opensearch(client, data: dict, index_name: str = "musinsa_products"):
    """OpenSearch에 데이터 실시간 적재"""
    try:
        # ID를 지정하여 중복 방지 (Upsert 효과)
        doc_id = str(data['goodsNo'])
        
        # _index, _source 구조 제거하고 순수 데이터만 적재 (OpenSearchpy가 알아서 처리)
        # 단, 날짜 필드는 ISO 형식으로 맞추는게 좋음
        if 'crawled_at' not in data:
            data['crawled_at'] = datetime.now().isoformat()

        client.index(
            index=index_name,
            body=data,
            id=doc_id,
            refresh=True # 즉시 검색 가능하게 함 (부하가 조금 있지만 실시간성 위해)
        )
        # print(f"      🚀 OpenSearch 적재 완료: {doc_id}")
    except Exception as e:
        print(f"      ❌ OpenSearch 적재 실패: {e}")


def run_crawler(keyword: str = SEARCH_KEYWORD, max_products: int = MAX_PRODUCTS):
    """메인 크롤러 실행"""
    global STOP_CRAWLER_FLAG, CRAWL_PROGRESS
    STOP_CRAWLER_FLAG = False  # 시작 시 플래그 초기화
    
    start_time = time.time()
    
    # 진행 상태 초기화
    CRAWL_PROGRESS.update({
        "status": "running",
        "keyword": keyword,
        "total": max_products,
        "current": 0,
        "start_time": start_time
    })
    
    print("=" * 60)
    print(f"🚀 무신사 크롤러 v4 (안전 수집) 시작")
    print(f"   검색어: {keyword}")
    print(f"   목표: {max_products}개")
    print("=" * 60)
    
    # 세션 생성 (쿠키 유지)
    session = requests.Session()
    
    # OpenSearch 클라이언트 생성
    try:
        os_client = get_opensearch_client()
        # 연결 테스트
        if os_client.ping():
            print("   ✅ OpenSearch 연결 성공")
        else:
            print("   ⚠️ OpenSearch 연결 실패 (Docker 확인 필요)")
            os_client = None
    except Exception as e:
        print(f"   ⚠️ OpenSearch 초기화 에러: {e}")
        os_client = None
    
    # 이전 진행 상태 로드
    collected_ids = load_progress()
    if collected_ids:
        print(f"📂 이전 진행 상태 복원: {len(collected_ids)}개 이미 수집됨")
    
    # 1단계: 상품 목록 수집
    print(f"\n🔍 [1단계] 상품 목록 API 호출 중...")
    
    all_products = []
    page = 1
    
    while len(all_products) < max_products:
        if STOP_CRAWLER_FLAG:
            print("   🛑 [1단계] 사용자 중단 요청으로 종료")
            CRAWL_PROGRESS["status"] = "stopped"
            break

        products = get_product_list(keyword, page, BATCH_SIZE, session)
        
        if not products:
            print(f"   더 이상 상품이 없습니다.")
            break
        
        # 이미 수집한 항목 제외
        new_products = [p for p in products if p.get('goodsNo') not in collected_ids]
        all_products.extend(new_products)
        
        print(f"   페이지 {page}: {len(new_products)}개 추가 (총 {len(all_products)}개)")
        
        page += 1
        safe_delay(API_DELAY)
        
        if len(all_products) >= max_products:
            all_products = all_products[:max_products]
            break
    
    print(f"   ✅ 수집할 상품: {len(all_products)}개")
    
    # 2단계: 판매자 정보 수집
    print(f"\n📦 [2단계] 판매자 정보 수집 중...")
    print(f"   💾 점진적 저장 활성화 (JSONL)")
    
    # JSONL 파일 경로
    jsonl_path = JSONL_FILE.format(keyword=keyword)
    
    # 기존 JSONL 데이터 로드 (재개 시)
    results = load_jsonl(jsonl_path)
    if results:
        print(f"   📂 기존 데이터 복원: {len(results)}개")
    
    total = len(all_products)
    
    for idx, product in enumerate(all_products):
        if STOP_CRAWLER_FLAG:
            print(f"   🛑 [2단계] 사용자 중단 요청으로 종료 ({idx}개 수집됨)")
            CRAWL_PROGRESS["status"] = "stopped"
            break

        goods_no = product.get("goodsNo")
        goods_name = product.get("goodsName", "")[:30]
        
        # 진행률 표시
        progress = (idx + 1) / total * 100
        print(f"   [{idx+1}/{total}] ({progress:.1f}%) {goods_name}...")
        
        # 판매자 정보 추출
        seller_info = get_seller_info(goods_no, session)
        
        # 결과 조합
        result = {
            "goodsNo": goods_no,
            "title": product.get("goodsName"),
            "brand": product.get("brandName"),
            "price": product.get("price"),
            "normalPrice": product.get("normalPrice"),
            "saleRate": product.get("saleRate"),
            "url": f"https://www.musinsa.com/products/{goods_no}",
            "thumbnail": product.get("thumbnail"),
            "seller_info": seller_info
        }
        
        # ✅ 즉시 JSONL에 저장 (점진적 저장)
        append_to_jsonl(jsonl_path, result)
        results.append(result)
        
        # 실시간 진행률 업데이트
        CRAWL_PROGRESS["current"] = len(results)
        
        # ✅ OpenSearch 실시간 적재
        if os_client:
            index_to_opensearch(os_client, result)
        
        # 진행 상태 저장 (100개마다)
        collected_ids.add(goods_no)
        if (idx + 1) % 100 == 0:
            save_progress(collected_ids)
            print(f"   💾 진행 상태 저장 완료 ({idx+1}개)")
            print(f"   📄 JSONL 파일: {jsonl_path}")
        
        # 딜레이
        safe_delay(HTML_DELAY)
    
    # 최종 저장 (JSONL → JSON 변환)
    elapsed = time.time() - start_time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_FILE.format(keyword=keyword, timestamp=timestamp)
    
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 진행 상태 및 JSONL 정리
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)  # JSONL은 JSON으로 변환 완료 후 삭제
    
    print("\n" + "=" * 60)
    print(f"🎉 수집 완료!")
    print(f"   총 수집: {len(results)}개")
    print(f"   소요 시간: {elapsed/60:.1f}분")
    print(f"   저장 위치: {output_path}")
    print("=" * 60)
    
    # 완료 상태 업데이트
    if not STOP_CRAWLER_FLAG:
        CRAWL_PROGRESS["status"] = "finished"
        CRAWL_PROGRESS["current"] = len(results)

    return results


if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else SEARCH_KEYWORD
    max_items = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_PRODUCTS
    run_crawler(keyword=keyword, max_products=max_items)
