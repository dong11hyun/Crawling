"""
무신사 크롤링 DAG
- 매일 오전 6시 자동 실행
- 크롤링 → 검증 → PostgreSQL/OpenSearch 저장
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os
import sys

# src 폴더를 Python path에 추가
sys.path.insert(0, '/opt/airflow/src')

# ========================================
# DAG 기본 설정
# ========================================
default_args = {
    'owner': 'musinsa-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 3,                          # 실패 시 3번 재시도
    'retry_delay': timedelta(minutes=5),   # 재시도 간격 5분
    'retry_exponential_backoff': True,     # 재시도 간격 점점 늘리기
    'max_retry_delay': timedelta(minutes=30),
    'email_on_failure': False,             # 이메일 알림 (설정 시 True)
    'email_on_retry': False,
}

dag = DAG(
    'musinsa_crawl_dag',
    default_args=default_args,
    description='무신사 상품 데이터 수집 파이프라인',
    schedule_interval='0 6 * * *',  # 매일 오전 6시 (KST 기준 조정 필요)
    catchup=False,                  # 과거 실행 건너뛰기
    max_active_runs=1,              # 동시 실행 방지
    tags=['musinsa', 'crawling', 'production'],
)


# ========================================
# Task 1: 크롤링 실행
# ========================================
def run_crawler(**context):
    """
    무신사 크롤러 실행
    - Playwright 비동기 크롤링
    - 상품 데이터 수집
    """
    import asyncio
    from playwright.async_api import async_playwright
    from opensearchpy import OpenSearch, helpers
    from datetime import datetime
    import re
    
    # 환경변수에서 설정 읽기
    OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
    OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9201))
    
    SEARCH_KEYWORD = "패딩"
    TARGET_URL = f"https://www.musinsa.com/search/goods?keyword={SEARCH_KEYWORD}&gf=A"
    SCROLL_COUNT = 2  # Airflow에서는 적게 설정
    INDEX_NAME = "musinsa_products"
    
    # OpenSearch 클라이언트
    opensearch_client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_compress=True, use_ssl=False, verify_certs=False
    )
    
    async def crawl():
        collected_data = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # headless 모드
            context = await browser.new_context()
            page = await context.new_page()
            
            print(f"🚀 크롤링 시작: {SEARCH_KEYWORD}")
            await page.goto(TARGET_URL, timeout=60000)
            
            # 스크롤
            for i in range(SCROLL_COUNT):
                await page.keyboard.press("End")
                await asyncio.sleep(2)
            
            # 상품 링크 수집
            locators = page.locator("a[href*='/products/']")
            count = await locators.count()
            urls = set()
            for i in range(min(count, 10)):  # 테스트용 10개
                href = await locators.nth(i).get_attribute("href")
                if href:
                    if not href.startswith("http"):
                        href = "https://www.musinsa.com" + href
                    urls.add(href)
            
            url_list = list(urls)
            print(f"   수집 대상: {len(url_list)}개")
            
            for url in url_list:
                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # 데이터 추출
                    title_loc = page.locator("meta[property='og:title']").first
                    title = await title_loc.get_attribute("content") if await title_loc.count() > 0 else "제목없음"
                    
                    brand_loc = page.locator("meta[property='product:brand']").first
                    brand = await brand_loc.get_attribute("content") if await brand_loc.count() > 0 else ""
                    
                    price_loc = page.locator("meta[property='product:price:amount']").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.get_attribute("content")
                        price_num = re.sub(r'[^0-9]', '', str(price_text))
                        price = int(price_num) if price_num else 0
                    else:
                        price = 0
                    
                    collected_data.append({
                        "url": url,
                        "title": title,
                        "brand": brand,
                        "price": price,
                        "seller_info": {},
                        "crawled_at": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"   ❌ 에러: {e}")
                    continue
            
            await browser.close()
        
        return collected_data
    
    # 크롤링 실행
    data = asyncio.run(crawl())
    
    # XCom으로 다음 Task에 전달
    context['ti'].xcom_push(key='crawled_data', value=data)
    print(f"✅ 크롤링 완료: {len(data)}건")
    
    return len(data)


# ========================================
# Task 2: 데이터 검증
# ========================================
def validate_data(**context):
    """
    크롤링 데이터 품질 검증
    - 필수 필드 확인
    - 가격 범위 확인
    """
    # XCom에서 데이터 가져오기
    ti = context['ti']
    data = ti.xcom_pull(key='crawled_data', task_ids='crawl_task')
    
    if not data:
        raise ValueError("❌ 크롤링 데이터가 없습니다!")
    
    valid_data = []
    invalid_count = 0
    
    for item in data:
        # 필수 필드 검증
        if not item.get('url') or not item.get('title'):
            invalid_count += 1
            continue
        
        # 가격 범위 검증 (음수 방지)
        if item.get('price', 0) < 0:
            item['price'] = 0
        
        valid_data.append(item)
    
    print(f"✅ 검증 완료: 유효 {len(valid_data)}건, 무효 {invalid_count}건")
    
    # 다음 Task로 전달
    ti.xcom_push(key='valid_data', value=valid_data)
    
    return len(valid_data)


# ========================================
# Task 3: 데이터 저장
# ========================================
def load_data(**context):
    """
    검증된 데이터를 PostgreSQL + OpenSearch에 저장
    """
    from opensearchpy import OpenSearch, helpers
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # XCom에서 검증된 데이터 가져오기
    ti = context['ti']
    data = ti.xcom_pull(key='valid_data', task_ids='validate_task')
    
    if not data:
        print("⚠️ 저장할 데이터가 없습니다.")
        return 0
    
    # ---- PostgreSQL 저장 ----
    try:
        DB_URL = os.getenv('MUSINSA_DB_URL')
        if DB_URL:
            engine = create_engine(DB_URL)
            Session = sessionmaker(bind=engine)
            db = Session()
            
            # 간단히 raw SQL로 저장 (models import 이슈 회피)
            for item in data:
                db.execute(
                    """
                    INSERT INTO products (url, title, brand, price, created_at, updated_at)
                    VALUES (:url, :title, :brand, :price, NOW(), NOW())
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        brand = EXCLUDED.brand,
                        price = EXCLUDED.price,
                        updated_at = NOW()
                    """,
                    item
                )
            db.commit()
            db.close()
            print(f"   💾 PostgreSQL 저장 완료: {len(data)}건")
    except Exception as e:
        print(f"   ⚠️ PostgreSQL 저장 실패: {e}")
    
    # ---- OpenSearch 저장 ----
    try:
        OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
        OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9201))
        
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_compress=True, use_ssl=False, verify_certs=False
        )
        
        docs = [{"_index": "musinsa_products", "_source": item} for item in data]
        success, failed = helpers.bulk(client, docs)
        print(f"   🔍 OpenSearch 저장 완료: 성공 {success}, 실패 {failed}")
    except Exception as e:
        print(f"   ⚠️ OpenSearch 저장 실패: {e}")
    
    return len(data)


# ========================================
# Task 정의
# ========================================
crawl_task = PythonOperator(
    task_id='crawl_task',
    python_callable=run_crawler,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_task',
    python_callable=validate_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_task',
    python_callable=load_data,
    dag=dag,
)

# ========================================
# Task 의존성 (순서)
# ========================================
crawl_task >> validate_task >> load_task
