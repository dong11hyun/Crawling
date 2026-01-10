import asyncio
from playwright.async_api import async_playwright
import random
import sqlite3
import os

# DB 파일명
DB_NAME = "sellers.db"

# ==========================================
# [1] 데이터베이스(SQLite) 관련 함수
# ==========================================
def init_db():
    """DB 테이블이 없으면 생성하는 함수"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 이미 존재하면 건너뛰고, 없으면 새로 만듦
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            product_name TEXT,
            seller_name TEXT,
            biz_no TEXT,
            contact TEXT,
            url TEXT UNIQUE,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("📁 [시스템] 데이터베이스(DB) 초기화 완료")

def save_batch_to_db(batch_data):
    """데이터를 10개씩 묶어서 한 번에 저장 (속도/안정성 UP)"""
    if not batch_data:
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # INSERT OR REPLACE: URL이 중복되면 업데이트, 없으면 추가
        cursor.executemany('''
            INSERT OR REPLACE INTO sellers (rank, product_name, seller_name, biz_no, contact, url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', batch_data)
        conn.commit()
        print(f"   💾 [Batch] {len(batch_data)}개 데이터 DB 저장 완료!")
    except Exception as e:
        print(f"   ❌ DB 저장 중 에러: {e}")
    finally:
        conn.close()

# ==========================================
# [2] 크롤링 로직 (비동기)
# ==========================================
async def process_product(context, prod):
    """개별 상품 정보를 수집하는 일꾼 함수"""
    page = await context.new_page()
    
    try:
        # ⚡ [속도 최적화 1] 불필요한 리소스(이미지, 폰트, 미디어) 차단
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())

        # 페이지 이동
        # print(f"▶ {prod['rank']}등 접속...") 
        await page.goto(prod['url'], timeout=30000)
        
        # ⚡ [속도 최적화 2] JS로 즉시 하단 이동 (기존 스크롤보다 빠름)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5) # 로딩 대기 (최소화)

        # 데이터 추출 초기값
        seller, biz, contact = "-", "-", "-"
        
        # 테이블 존재 여부 확인 (3초까지만 기다림)
        try:
            await page.wait_for_selector("table.prod-delivery-return-policy-table", timeout=3000)
            
            # 정보 추출 (XPath 활용)
            if await page.locator("//th[contains(., '상호')]/following-sibling::td[1]").count() > 0:
                seller = await page.locator("//th[contains(., '상호')]/following-sibling::td[1]").inner_text()
            if await page.locator("//th[contains(., '사업자')]/following-sibling::td[1]").count() > 0:
                biz = await page.locator("//th[contains(., '사업자')]/following-sibling::td[1]").inner_text()
            if await page.locator("//th[contains(., '연락처')]/following-sibling::td[1]").count() > 0:
                contact = await page.locator("//th[contains(., '연락처')]/following-sibling::td[1]").inner_text()

            # 결과 반환 (튜플 형태)
            print(f"   ✅ 추출 성공: {seller.strip()} / {biz.strip()}")
            return (
                prod['rank'], 
                prod['name'], 
                seller.strip(), 
                biz.strip(), 
                contact.strip(), 
                prod['url']
            )

        except:
            # 테이블 로딩 실패 시 (품절, 로켓직구 등)
            print(f"   ⚠️ 정보 없음 (패스): {prod['rank']}등")
            return None

    except Exception as e:
        print(f"   ❌ 에러 ({prod['rank']}등): {e}")
        return None
    finally:
        await page.close() # 탭 닫기 (메모리 누수 방지)

# ==========================================
# [3] 메인 실행부
# ==========================================
async def run_bot():
    print("🚀 [최적화 모드] 크롬(9222)에 연결 시도...")
    
    # DB 초기화
    init_db()

    async with async_playwright() as p:
        try:
            # 1. 켜져있는 디버깅 크롬에 연결
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            
            # 메인 페이지 (URL 수집용)
            if len(context.pages) > 0:
                page = context.pages[0]
            else:
                page = await context.new_page()

            product_list = []
            collected = 0
            keyword = "딸기" # 검색어 수정 가능

            # ----------------------------------------------------
            # 1단계: URL 수집 (지도 그리기)
            # ----------------------------------------------------
            print("\n🔍 1단계: 상품 URL 수집 시작...")
            for page_num in range(1, 3): # 1~2페이지 수집
                await page.goto(f"https://www.coupang.com/np/search?component=&q={keyword}&channel=user&page={page_num}", timeout=30000)
                await asyncio.sleep(2)
                
                # HTML 구조에 따른 선택자 자동 감지
                if await page.locator("ul#product-list li").count() > 0:
                    items = page.locator("ul#product-list > li")
                else:
                    items = page.locator("ul#productList > li.search-product")
                
                count = await items.count()
                
                for i in range(count):
                    try:
                        item = items.nth(i)
                        link_el = item.locator("a")
                        
                        if await link_el.count() == 0: continue
                        href = await link_el.get_attribute("href")
                        
                        if not href: continue

                        full_url = "https://www.coupang.com" + href
                        raw_name = await item.inner_text()
                        name = raw_name.split("\n")[0]
                        
                        collected += 1
                        product_list.append({
                            "rank": collected,
                            "name": name,
                            "url": full_url
                        })
                    except:
                        continue
                print(f"   📄 {page_num}페이지 완료. 누적 {len(product_list)}개")

            print(f"\n⚡ 2단계: 총 {len(product_list)}개 상품 병렬 수집 시작! (이미지 차단 + DB 저장)\n")

            # ----------------------------------------------------
            # 2단계: 상세 정보 수집 (병렬 + 배치 저장)
            # ----------------------------------------------------
            semaphore = asyncio.Semaphore(5) # 동시 접속 5개 제한
            
            async def safe_process(prod):
                async with semaphore:
                    # 봇 탐지 회피를 위한 미세한 랜덤 딜레이
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    return await process_product(context, prod)

            # 전체 작업을 예약 (아직 실행 안 됨)
            tasks = [safe_process(prod) for prod in product_list]
            
            # 작업을 실행하면서 결과가 나오는 대로 처리 (as_completed)
            batch_buffer = []
            
            for future in asyncio.as_completed(tasks):
                result = await future
                if result:
                    batch_buffer.append(result)
                
                # 10개가 모이면 DB에 저장하고 비움 (Batch Save)
                if len(batch_buffer) >= 10:
                    save_batch_to_db(batch_buffer)
                    batch_buffer = []
            
            # 남은 데이터 저장
            if batch_buffer:
                save_batch_to_db(batch_buffer)

            print("\n🎉 [모든 작업 완료] 'sellers.db' 파일에 저장되었습니다.")
            print("💡 팁: 'DB Browser for SQLite' 프로그램으로 파일을 열어보세요.")

        except Exception as e:
            print(f"🚫 실행 중 오류 발생: {e}")
            print("💡 팁: 크롬 디버깅 모드가 켜져 있는지 확인하세요.")

if __name__ == "__main__":
    asyncio.run(run_bot())