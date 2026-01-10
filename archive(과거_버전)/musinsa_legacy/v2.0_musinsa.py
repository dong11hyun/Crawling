import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random

# ==========================================
# [설정] 스크롤 횟수 및 저장 파일명
# ==========================================
SEARCH_KEYWORD = "패딩"
TARGET_URL = f"https://www.musinsa.com/search/goods?keyword={SEARCH_KEYWORD}&gf=A"
SCROLL_COUNT = 5  # 테스트용으로 5번만 스크롤 (원하는 만큼 늘리세요)
OUTPUT_FILE = "musinsa_padding_info.csv"

async def run():
    async with async_playwright() as p:
        # 1. 브라우저 실행 (headless=False로 하면 브라우저가 뜨는게 보임)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # -------------------------------------------------------
        # 1단계: 검색 페이지에서 상품 URL 수집 (무한 스크롤)
        # -------------------------------------------------------
        print(f"🚀 [1단계] '{SEARCH_KEYWORD}' 검색 페이지 접속 중...")
        await page.goto(TARGET_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        print(f"   ⬇️ 스크롤 {SCROLL_COUNT}회 진행 중...")
        for i in range(SCROLL_COUNT):
            # 스크롤을 바닥까지 내림
            await page.keyboard.press("End")
            await asyncio.sleep(random.uniform(1.5, 3.0)) # 로딩 대기 (사람처럼)
            print(f"   - 스크롤 {i+1}/{SCROLL_COUNT} 완료")

        # 상품 링크 추출 (href 속성 수집)
        # 무신사 상품 링크는 보통 /products/숫자 형태임
        print("   🔍 상품 링크 추출 중...")
        product_locators = page.locator("a[href*='/products/']")
        count = await product_locators.count()
        
        product_urls = set()
        for i in range(count):
            href = await product_locators.nth(i).get_attribute("href")
            if href:
                # https가 없는 상대경로일 경우 처리
                if not href.startswith("http"):
                    href = "https://www.musinsa.com" + href
                product_urls.add(href)
        
        # 중복 제거 후 리스트 변환
        url_list = list(product_urls)
        print(f"   ✅ 총 {len(url_list)}개의 상품 URL 확보 완료!")

        # -------------------------------------------------------
        # 2단계: 각 상품 상세 페이지 접속 및 정보 추출
        # -------------------------------------------------------
        print(f"\n🚀 [2단계] 상세 정보 수집 시작 (총 {len(url_list)}개)")
        results = []

        for idx, url in enumerate(url_list):
            try:
                print(f"   [{idx+1}/{len(url_list)}] 접속 중: {url}")
                await page.goto(url, timeout=30000)
                
                # '판매자 정보' 텍스트가 보일 때까지 대기 (혹은 페이지 로딩 대기)
                try:
                    # 아코디언이 닫혀있을 수 있으므로 '판매자 정보' 버튼을 찾아 클릭 시도
                    seller_btn = page.locator("button:has-text('판매자 정보')")
                    if await seller_btn.count() > 0:
                        # aria-expanded가 false면 클릭해서 열기
                        is_expanded = await seller_btn.get_attribute("aria-expanded")
                        if is_expanded == "false":
                            await seller_btn.click()
                            await asyncio.sleep(0.5)
                except:
                    pass # 이미 열려있거나 버튼이 다를 경우 패스

                # 데이터 추출 (XPath 사용 - 클래스명이 바뀌어도 대응 가능하도록)
                info = {
                    "상품URL": url,
                    "상호/대표자": await get_text_by_label(page, "상호 / 대표자"),
                    "브랜드": await get_text_by_label(page, "브랜드"),
                    "사업자번호": await get_text_by_label(page, "사업자번호"),
                    "연락처": await get_text_by_label(page, "연락처"),
                    "E-mail": await get_text_by_label(page, "E-mail"),
                    "영업소재지": await get_text_by_label(page, "영업소재지"),
                }
                
                print(f"      👉 수집: {info['상호/대표자']} / {info['브랜드']}")
                results.append(info)

                # 봇 탐지 방지용 짧은 대기
                await asyncio.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"      ❌ 에러 발생: {e}")
                continue

        # -------------------------------------------------------
        # 3단계: 파일 저장
        # -------------------------------------------------------
        if results:
            df = pd.DataFrame(results)
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            print(f"\n🎉 [완료] '{OUTPUT_FILE}' 파일로 저장되었습니다.")
        else:
            print("\n⚠️ 수집된 데이터가 없습니다.")

        await browser.close()

async def get_text_by_label(page, label_text):
    """
    <dt>라벨</dt><dd>값</dd> 구조에서 라벨 텍스트로 값을 찾는 함수
    """
    try:
        # dt 태그 중 label_text를 포함하는 요소를 찾고, 그 바로 뒤의 dd 태그 텍스트 추출
        locator = page.locator(f"//dt[contains(., '{label_text}')]/following-sibling::dd[1]")
        if await locator.count() > 0:
            return await locator.inner_text()
        return "-"
    except:
        return "-"

if __name__ == "__main__":
    asyncio.run(run())