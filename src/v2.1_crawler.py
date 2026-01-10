import asyncio
from playwright.async_api import async_playwright
from opensearchpy import OpenSearch, helpers
import random
import re

# ================= 설정 =================
SEARCH_KEYWORD = "패딩"
TARGET_URL = f"https://www.musinsa.com/search/goods?keyword={SEARCH_KEYWORD}&gf=A"
SCROLL_COUNT = 3
INDEX_NAME = "musinsa_products"

# OpenSearch 클라이언트 연결
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_compress=True, use_ssl=False, verify_certs=False
)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_context()
        page = await page.new_page()

        print(f"🚀 [1단계] 무신사 '{SEARCH_KEYWORD}' 검색 시작")
        await page.goto(TARGET_URL, timeout=60000)
        
        # 스크롤
        for i in range(SCROLL_COUNT):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
            print(f"   ⬇️ 스크롤 {i+1}/{SCROLL_COUNT}")

        # 상품 링크 수집
        print("   🔍 상품 링크 추출 중...")
        locators = page.locator("a[href*='/products/']")
        count = await locators.count()
        urls = set()
        for i in range(min(count, 20)): # 테스트용으로 20개만 제한 (나중에 푸세요)
            href = await locators.nth(i).get_attribute("href")
            if href:
                if not href.startswith("http"): href = "https://www.musinsa.com" + href
                urls.add(href)
        
        url_list = list(urls)
        print(f"   ✅ 수집할 상품 개수: {len(url_list)}개")

        # -------------------------------------------------------
        # [데이터 수집 및 전처리]
        # -------------------------------------------------------
        docs = [] # OpenSearch에 넣을 데이터 바구니

        for idx, url in enumerate(url_list):
            try:
                print(f"   [{idx+1}] 접속: {url}")
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded") # 페이지 로딩 대기

                # -------------------------------------------------------
                # [중요] '판매자 정보' 버튼 클릭 (아코디언 펼치기)
                # -------------------------------------------------------
                # 버튼을 클릭해야 숨겨진 <dl> 태그가 나옵니다.
                try:
                    # '판매자 정보'라는 글자가 포함된 버튼 찾기
                    seller_btn = page.locator("button", has_text="판매자 정보")
                    if await seller_btn.count() > 0:
                        # 이미 열려있는지 확인 (aria-expanded 속성)
                        expanded = await seller_btn.get_attribute("aria-expanded")
                        if expanded != "true":
                            await seller_btn.click()
                            await asyncio.sleep(0.5) # 펼쳐지는 애니메이션 대기
                except Exception as e:
                    print(f"      ⚠️ 판매자 정보 버튼 클릭 실패 (이미 열려있을 수 있음): {e}")

                # -------------------------------------------------------
                # [데이터 추출] 라벨(dt)을 찾아서 값(dd) 가져오기
                # -------------------------------------------------------
                
                # 도우미 함수: 특정 라벨 옆의 텍스트 가져오기
                async def get_value(label):
                    # XPath 해석: dt 태그 중에 'label' 텍스트를 포함하는 녀석의 -> 바로 다음 형제 dd 태그
                    locator = page.locator(f"//dt[contains(., '{label}')]/following-sibling::dd[1]")
                    if await locator.count() > 0:
                        return await locator.inner_text()
                    return "" # 없으면 빈 문자열

                # 1. 판매자 정보 수집
                info_company = await get_value("상호")   # "상호 / 대표자" 중 '상호'만 써도 찾음
                info_brand = await get_value("브랜드")
                info_biz_num = await get_value("사업자번호")
                info_mail_order = await get_value("통신판매업신고")
                info_contact = await get_value("연락처")
                info_email = await get_value("E-mail")     # 대소문자 주의
                info_address = await get_value("영업소재지")

                # -------------------------------------------------------
                # [수정됨] 2. 기본 정보 수집 (Strict Mode 에러 해결)
                # -------------------------------------------------------
                # .first를 붙여서 중복된 태그 중 첫 번째만 가져오게 함
                title_loc = page.locator("meta[property='og:title']").first 
                title = await title_loc.get_attribute("content") if await title_loc.count() > 0 else "제목없음"
                
                # 브랜드도 혹시 모르니 .first 붙이기
                brand_loc = page.locator("meta[property='product:brand']").first
                # 브랜드가 메타태그에 없으면 seller_info에서 가져온 값 사용
                if await brand_loc.count() > 0:
                     brand_meta = await brand_loc.get_attribute("content")
                else:
                     brand_meta = info_brand # 위에서 수집한 판매자 정보 활용

                # 가격도 .first
                price_loc = page.locator("meta[property='product:price:amount']").first
                if await price_loc.count() > 0:
                    price_text = await price_loc.get_attribute("content")
                    # 정규표현식으로 숫자만 추출
                    price_num = re.sub(r'[^0-9]', '', str(price_text))
                    price = int(price_num) if price_num else 0
                else:
                    price = 0
                
                # 3. 데이터 조립
                doc = {
                    "_index": INDEX_NAME,
                    "_source": {
                        "url": url,
                        "title": title,
                        "brand": brand_meta, # 👈 여기가 빠져 있었습니다!
                        "price": price,      # 👈 이것도 추가!
                        "seller_info": {  # 깔끔하게 객체로 묶음
                            "company": info_company,
                            "brand": info_brand,
                            "biz_num": info_biz_num,
                            "license": info_mail_order,
                            "contact": info_contact,
                            "email": info_email,
                            "address": info_address
                        },
                        "created_at": "2025-12-20"
                    }
                }
                docs.append(doc)
                print(f"      👉 수집완료: {info_company} / {info_brand}")

            except Exception as e:
                print(f"      ❌ 에러: {e}")
                continue

        # -------------------------------------------------------
        # [Bulk Insert] 데이터를 한 번에 밀어넣기
        # -------------------------------------------------------
        if docs:
            print(f"\n🚀 OpenSearch에 데이터 {len(docs)}건 적재 시작...")
            success, failed = helpers.bulk(client, docs)
            print(f"🎉 적재 완료! 성공: {success}, 실패: {failed}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())