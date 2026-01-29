"""
무신사 크롤러 v5 - 병렬 수집 (ThreadPoolExecutor)
- v4의 모든 기능 유지
- ThreadPoolExecutor로 병렬 처리 (max_workers=4)
- 예상 속도: v4 대비 3~4배 향상
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import random
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from opensearchpy import OpenSearch, helpers
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ================= 설정 =================
SEARCH_KEYWORD = "패딩"
MAX_PRODUCTS = 1000
BATCH_SIZE = 60
MAX_WORKERS = 2  # 동시 처리 워커 수 (2개로 축소 - 차단 방지)

# 딜레이 설정 (초) - 각 요청 간 대기 시간 증가
API_DELAY = 0.8
HTML_DELAY = 1.5  # 병렬 처리 시 개별 워커 딜레이 (더 느리게)
RANDOM_RANGE = (0.3, 0.8)  # 추가 랜덤 딜레이 증가

# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# 파일 경로
PROGRESS_FILE = "data/progress_v5.json"
JSONL_FILE = "data/crawl_progress_v5_{keyword}.jsonl"
OUTPUT_FILE = "data/crawl_result_v5_{keyword}_{timestamp}.json"

# 전역 중지 플래그
STOP_CRAWLER_FLAG = False

# Thread-safe 락
results_lock = threading.Lock()
progress_lock = threading.Lock()

# 로거 설정
def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("MusinsaCrawlerV5")
    logger.setLevel(logging.INFO)
    
    filename = os.path.join(log_dir, "crawler_v5.log")
    file_handler = TimedRotatingFileHandler(
        filename, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("[%(asctime)s] [%(threadName)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()

def stop_crawling():
    global STOP_CRAWLER_FLAG
    STOP_CRAWLER_FLAG = True
    logger.warning("\n🛑 크롤링 중지 요청됨!")

# 전역 진행 상태
CRAWL_PROGRESS = {
    "status": "idle",
    "keyword": "",
    "total": 0,
    "current": 0,
    "start_time": 0.0,
    "version": "v5"
}

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/html",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://www.musinsa.com/",
    }

def safe_delay(base_delay: float):
    delay = base_delay + random.uniform(*RANDOM_RANGE)
    time.sleep(delay)

def load_progress(keyword: str = "") -> set:
    """진행 상태 로드: progress_v5.json 또는 JSONL 파일에서 복구"""
    collected_ids = set()
    
    # 1. progress_v5.json에서 로드 시도
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            collected_ids = set(data.get('collected_ids', []))
            if collected_ids:
                return collected_ids
    
    # 2. JSONL 파일에서 복구 시도 (progress_v5.json이 없거나 비어있을 때)
    if keyword:
        jsonl_path = JSONL_FILE.format(keyword=keyword)
        if os.path.exists(jsonl_path):
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            if 'goodsNo' in item:
                                collected_ids.add(item['goodsNo'])
                        except:
                            pass
    
    return collected_ids

def save_progress(collected_ids: set):
    """수집된 ID 목록을 파일에 저장 (실시간)"""
    os.makedirs('data', exist_ok=True)
    with progress_lock:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({'collected_ids': list(collected_ids)}, f)

def append_to_jsonl(filepath: str, data: dict):
    os.makedirs('data', exist_ok=True)
    with results_lock:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

def load_jsonl(filepath: str) -> list:
    results = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    return results

def get_product_list(keyword: str, page: int, size: int = 60, session=None) -> list:
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
                logger.warning(f"   ⚠️ 429 Too Many Requests - 60초 대기...")
                time.sleep(60)
                continue
            
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("list", [])
            
        except Exception as e:
            logger.error(f"   ❌ API 호출 실패 (시도 {attempt+1}/3): {e}", exc_info=True)
            time.sleep(10)
    
    return []

def get_seller_info(goods_no: int, session=None) -> dict:
    """상품 상세 페이지에서 판매자 정보 추출 (워커에서 호출)"""
    url = f"https://www.musinsa.com/products/{goods_no}"
    
    # 개별 워커 딜레이 (병렬 처리 시 부하 분산)
    safe_delay(HTML_DELAY)
    
    for attempt in range(3):
        try:
            response = session.get(url, headers=get_headers(), timeout=15)
            
            if response.status_code == 429:
                logger.warning(f"   ⚠️ 429 Too Many Requests - 60초 대기...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except Exception:
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
            logger.error(f"   ❌ HTML 파싱 실패 (시도 {attempt+1}/3): {e}", exc_info=True)
            time.sleep(5)
    
    return {}

def get_opensearch_client():
    return OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9201}],
        http_auth=None,
        use_ssl=False,
        verify_certs=False,
        timeout=30
    )

def flush_bulk_buffer(client, buffer: list):
    if not buffer:
        return
    try:
        success, _ = helpers.bulk(client, buffer, refresh=True)
        logger.info(f"      🚀 [Bulk] {len(buffer)}개 아이템 OpenSearch 적재 완료")
        buffer.clear()
    except Exception as e:
        logger.error(f"      ❌ [Bulk] 적재 실패: {e}", exc_info=True)

def add_to_bulk_buffer(buffer: list, data: dict, index_name: str = "musinsa_products"):
    doc_id = str(data['goodsNo'])
    if 'crawled_at' not in data:
        data['crawled_at'] = datetime.now().isoformat()
    action = {
        "_index": index_name,
        "_id": doc_id,
        "_source": data
    }
    buffer.append(action)

def process_single_product(product: dict, session, collected_ids: set, jsonl_path: str, bulk_buffer: list, os_client):
    """단일 상품 처리 (워커 함수)"""
    global STOP_CRAWLER_FLAG, CRAWL_PROGRESS
    
    if STOP_CRAWLER_FLAG:
        return None
    
    goods_no = product.get("goodsNo")
    goods_name = product.get("goodsName", "")[:30]
    
    logger.info(f"   처리 중: {goods_name}...")
    
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
        "seller_info": seller_info,
        "crawled_at": datetime.now().isoformat()
    }
    
    # Thread-safe 저장
    append_to_jsonl(jsonl_path, result)
    
    # 수집 ID 추가 및 저장
    with progress_lock:
        collected_ids.add(goods_no)
        CRAWL_PROGRESS["current"] = len(collected_ids)
    
    # 진행 상태 파일에 저장 (10개마다)
    if len(collected_ids) % 10 == 0:
        save_progress(collected_ids)
    
    # Bulk 버퍼 추가 (Thread-safe)
    if os_client:
        with results_lock:
            add_to_bulk_buffer(bulk_buffer, result)
            if len(bulk_buffer) >= 20:
                flush_bulk_buffer(os_client, bulk_buffer)
    
    return result

def run_crawler(keyword: str = SEARCH_KEYWORD, max_products: int = MAX_PRODUCTS):
    """메인 크롤러 실행 (v5 - 병렬 처리)"""
    global STOP_CRAWLER_FLAG, CRAWL_PROGRESS
    STOP_CRAWLER_FLAG = False
    
    start_time = time.time()
    
    CRAWL_PROGRESS.update({
        "status": "running",
        "keyword": keyword,
        "total": max_products,
        "current": 0,
        "start_time": start_time,
        "version": "v5"
    })
    
    logger.info("=" * 60)
    logger.info(f"🚀 무신사 크롤러 v5 (병렬 수집) 시작")
    logger.info(f"   검색어: {keyword}")
    logger.info(f"   목표: {max_products}개")
    logger.info(f"   병렬 워커: {MAX_WORKERS}개")
    logger.info("=" * 60)
    
    session = requests.Session()
    
    try:
        os_client = get_opensearch_client()
        if os_client.ping():
            logger.info("   ✅ OpenSearch 연결 성공")
        else:
            logger.warning("   ⚠️ OpenSearch 연결 실패")
            os_client = None
    except Exception as e:
        logger.error(f"   ⚠️ OpenSearch 초기화 에러: {e}", exc_info=True)
        os_client = None
    
    collected_ids = load_progress(keyword)
    if collected_ids:
        logger.info(f"📂 이전 진행 상태 복원: {len(collected_ids)}개 이미 수집됨")
    
    # 1단계: 상품 목록 수집
    logger.info(f"\n🔍 [1단계] 상품 목록 API 호출 중...")
    
    bulk_buffer = []
    all_products = []
    page = 1
    
    while len(all_products) < max_products:
        if STOP_CRAWLER_FLAG:
            logger.warning("   🛑 [1단계] 사용자 중단 요청으로 종료")
            CRAWL_PROGRESS["status"] = "stopped"
            break

        products = get_product_list(keyword, page, BATCH_SIZE, session)
        
        if not products:
            logger.info(f"   더 이상 상품이 없습니다.")
            break
        
        new_products = [p for p in products if p.get('goodsNo') not in collected_ids]
        all_products.extend(new_products)
        
        logger.info(f"   페이지 {page}: {len(new_products)}개 추가 (총 {len(all_products)}개)")
        
        page += 1
        safe_delay(API_DELAY)
        
        if len(all_products) >= max_products:
            all_products = all_products[:max_products]
            break
    
    logger.info(f"   ✅ 수집할 상품: {len(all_products)}개")
    
    # 2단계: 판매자 정보 수집 (병렬 처리)
    logger.info(f"\n📦 [2단계] 판매자 정보 병렬 수집 중... (워커: {MAX_WORKERS}개)")
    
    jsonl_path = JSONL_FILE.format(keyword=keyword)
    results = load_jsonl(jsonl_path)
    if results:
        logger.info(f"   📂 기존 데이터 복원: {len(results)}개")
    
    CRAWL_PROGRESS["total"] = len(all_products)
    
    # ThreadPoolExecutor로 병렬 처리
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_single_product, 
                product, session, collected_ids, jsonl_path, bulk_buffer, os_client
            ): product for product in all_products
        }
        
        for future in as_completed(futures):
            if STOP_CRAWLER_FLAG:
                logger.warning("   🛑 [2단계] 사용자 중단 요청 감지")
                executor.shutdown(wait=False, cancel_futures=True)
                break
            
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"   ❌ 워커 에러: {e}", exc_info=True)
    
    # 최종 저장
    elapsed = time.time() - start_time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_FILE.format(keyword=keyword, timestamp=timestamp)
    
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if os_client and bulk_buffer:
        logger.info("   🧹 남은 데이터 Bulk 적재 중...")
        flush_bulk_buffer(os_client, bulk_buffer)
    
    # 정리
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎉 수집 완료!")
    logger.info(f"   총 수집: {len(results)}개")
    logger.info(f"   소요 시간: {elapsed/60:.1f}분")
    logger.info(f"   저장 위치: {output_path}")
    logger.info("=" * 60)
    
    if not STOP_CRAWLER_FLAG:
        CRAWL_PROGRESS["status"] = "finished"
        CRAWL_PROGRESS["current"] = len(results)

    return results


if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else SEARCH_KEYWORD
    max_items = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_PRODUCTS
    run_crawler(keyword=keyword, max_products=max_items)
