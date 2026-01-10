import asyncio
from playwright.async_api import async_playwright
import random
import csv
import os

# 결과 저장 파일명
FILE_NAME = "sellers_result.csv"

# 파일 쓰기 충돌 방지용 락
file_lock = asyncio.Lock()

async def save_to_csv(data):
    """데이터를 엑셀(csv) 파일에 한 줄씩 저장 (비동기 Lock + 재시도 로직)"""
    async with file_lock:
        for attempt in range(5): # 최대 5번 재시도
            try:
                file_exists = os.path.isfile(FILE_NAME)
                with open(FILE_NAME, mode='a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["순위", "상품명", "상호", "사업자번호", "연락처", "URL"])
                    
                    writer.writerow([
                        data['rank'], 
                        data['name'], 
                        data['seller'], 
                        data['biz'], 
                        data['contact'], 
                        data['url']
                    ])
                print(f"   💾 [저장 완료] {data['name'][:15]}...")
                return # 성공 시 함수 종료
            except PermissionError:
                if attempt < 4:
                    print(f"   ⚠️ 파일이 열려있어 저장 대기 중... ({attempt+1}/5)")
                    await asyncio.sleep(1)
                else:
                    print(f"   ❌ [저장 실패] 엑셀 파일을 닫아주세요! ({data['name'][:10]})")
            except Exception as e:
                print(f"   ❌ 저장 오류: {e}")
                return

async def process_product(context, prod, semaphore):
    """개별 상품 정보를 새 탭에서 수집하는 비동기 함수"""
    async with semaphore:
        page = await context.new_page()
        try:
            print(f"▶ {prod['rank']}등 상품 접속 중... (탭 열림)")
            
            # 리소스 차단 (속도 향상)
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font"] 
                else route.continue_())

            await page.goto(prod['url'], timeout=60000)
            
            # [속도 튜닝 적용] 자바스크립트로 강제 스크롤
            # ----------------------------------------------------------
            # 기존: for문 돌면서 휠 굴리기 (약 4~5초 소요)
            # 수정: 자바스크립트로 바닥으로 순간이동 (약 0.1초 소요)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 데이터 로딩을 위해 딱 1초만 대기 (충분함)
            await asyncio.sleep(1) 

            # 정보 추출
            seller, biz, contact = "-", "-", "-"
            
            # 테이블 찾기
            if await page.locator("table.prod-delivery-return-policy-table").count() > 0:
                # 텍스트가 포함된 th의 형제 td 찾기
                if await page.locator("//th[contains(., '상호')]/following-sibling::td[1]").count() > 0:
                    seller = await page.locator("//th[contains(., '상호')]/following-sibling::td[1]").inner_text()
                if await page.locator("//th[contains(., '사업자')]/following-sibling::td[1]").count() > 0:
                    biz = await page.locator("//th[contains(., '사업자')]/following-sibling::td[1]").inner_text()
                if await page.locator("//th[contains(., '연락처')]/following-sibling::td[1]").count() > 0:
                    contact = await page.locator("//th[contains(., '연락처')]/following-sibling::td[1]").inner_text()
            
            # CSV 파일 저장 (await 필수)
            await save_to_csv({
                "rank": prod['rank'],
                "name": prod['name'],
                "seller": seller.strip(),
                "biz": biz.strip(),
                "contact": contact.strip(),
                "url": prod['url']
            })
            
            # 봇 탐지 회피용 짧은 휴식
            await asyncio.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"   ❌ {prod['rank']}등 에러 발생: {e}")
        finally:
            await page.close()

async def run_bot():
    print("🚀 [비동기 모드] 크롬(9222)에 연결 시도...")
    
    async with async_playwright() as p:
        try:
            # 1. 켜져있는 디버깅 크롬에 연결
            browser = await p.chromium.connect_over_cdp("http://localhost:9222") #chrome devtools Protocol
            context = browser.contexts[0]
            
            # 검색용 메인 페이지 (기존 탭 사용)
            if len(context.pages) > 0:
                page = context.pages[0]
            else:
                page = await context.new_page()

            product_list = []
            collected = 0
            keyword = "딸기"

            # 1페이지부터 2페이지까지 반복 (URL 수집 단계)
            for page_num in range(1, 3):
                print(f"\n📄 [페이지 {page_num}] URL 수집 중...")
                await page.goto(f"https://www.coupang.com/np/search?component=&q={keyword}&channel=user&page={page_num}", timeout=10000)
                await asyncio.sleep(2)
                
                if await page.locator("ul#product-list li").count() > 0:
                    items = page.locator("ul#product-list > li")
                else:
                    items = page.locator("ul#productList > li.search-product")
                
                count = await items.count()
                if count == 0:
                    print("❌ 상품을 못 찾았습니다.")
                    continue

                for i in range(count):
                    try:
                        item = items.nth(i)
                        link_element = item.locator("a")
                        if await link_element.count() == 0: continue
                        href = await link_element.get_attribute("href")
                        if not href: continue

                        full_url = "https://www.coupang.com" + href
                        name = (await item.inner_text()).split("\n")[0]
                        
                        product_list.append({
                            "rank": collected + 1,
                            "name": name,
                            "url": full_url
                        })
                        collected += 1
                        
                    except Exception as e:
                        continue
                print(f"   ✅ 현재까지 {collected}개 URL 확보")

            print(f"\n⚡ 총 {len(product_list)}개 상품 병렬 수집 시작! (최대 5개 탭 동시 실행)\n")

            # 2. 병렬 처리 (Semaphore로 동시 접속 수 제한)
            semaphore = asyncio.Semaphore(5) # 탭 5개 제한
            tasks = [process_product(context, prod, semaphore) for prod in product_list]
            
            # 모든 작업이 끝날 때까지 대기
            await asyncio.gather(*tasks)

            print("\n🎉 [작업 끝] 'sellers_result.csv' 파일을 확인해주세요!")

        except Exception as e:
            print(f"🚫 치명적 오류: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())