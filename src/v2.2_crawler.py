"""
무신사 크롤러 v2.2 - 듀얼 저장 (PostgreSQL + OpenSearch)
- PostgreSQL: 원본 데이터 보관 (Source of Truth)
- OpenSearch: 검색용 인덱스
"""
import asyncio
from playwright.async_api import async_playwright
from opensearchpy import OpenSearch, helpers
import re
from datetime import datetime

# ================= 설정 =================
SEARCH_KEYWORD = "패딩"
TARGET_URL = f"https://www.musinsa.com/search/goods?keyword={SEARCH_KEYWORD}&gf=A"
SCROLL_COUNT = 3
INDEX_NAME = "musinsa_products"

# ================= OpenSearch 연결 =================
opensearch_client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9201}],
    http_compress=True, use_ssl=False, verify_certs=False
)

# ================= PostgreSQL 연결 =================
from database.connection import SessionLocal
from database.models import Product, Seller


def save_to_postgres(data_list: list):
    """
    PostgreSQL에 데이터 저장 (UPSERT - 있으면 업데이트, 없으면 생성)
    """
    db = SessionLocal()
    saved_count = 0
    
    try:
        for data in data_list:
            # URL로 기존 데이터 조회
            existing = db.query(Product).filter(Product.url == data["url"]).first()
            
            if existing:
                # 기존 데이터 업데이트
                existing.title = data["title"]
                existing.brand = data["brand"]
                existing.price = data["price"]
                existing.updated_at = datetime.utcnow()
                
                # Seller 정보도 업데이트
                if existing.seller:
                    existing.seller.company = data["seller_info"]["company"]
                    existing.seller.brand = data["seller_info"]["brand"]
                    existing.seller.biz_num = data["seller_info"]["biz_num"]
                    existing.seller.license = data["seller_info"]["license"]
                    existing.seller.contact = data["seller_info"]["contact"]
                    existing.seller.email = data["seller_info"]["email"]
                    existing.seller.address = data["seller_info"]["address"]
            else:
                # 새 데이터 생성
                new_product = Product(
                    url=data["url"],
                    title=data["title"],
                    brand=data["brand"],
                    price=data["price"]
                )
                
                new_seller = Seller(
                    company=data["seller_info"]["company"],
                    brand=data["seller_info"]["brand"],
                    biz_num=data["seller_info"]["biz_num"],
                    license=data["seller_info"]["license"],
                    contact=data["seller_info"]["contact"],
                    email=data["seller_info"]["email"],
                    address=data["seller_info"]["address"]
                )
                new_product.seller = new_seller
                db.add(new_product)
            
            saved_count += 1
        
        db.commit()
        print(f"   💾 PostgreSQL 저장 완료: {saved_count}건")
        
    except Exception as e:
        db.rollback()
        print(f"   ❌ PostgreSQL 저장 실패: {e}")
    finally:
        db.close()


def save_to_opensearch(docs: list):
    """
    OpenSearch에 Bulk Insert
    """
    if not docs:
        return
    
    try:
        success, failed = helpers.bulk(opensearch_client, docs)
        print(f"   🔍 OpenSearch 저장 완료: 성공 {success}, 실패 {failed}")
    except Exception as e:
        print(f"   ❌ OpenSearch 저장 실패: {e}")


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

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
        for i in range(min(count, 20)):  # 테스트용 20개 제한
            href = await locators.nth(i).get_attribute("href")
            if href:
                if not href.startswith("http"):
                    href = "https://www.musinsa.com" + href
                urls.add(href)
        
        url_list = list(urls)
        print(f"   ✅ 수집할 상품 개수: {len(url_list)}개")

        # -------------------------------------------------------
        # [데이터 수집]
        # -------------------------------------------------------
        collected_data = []  # PostgreSQL용
        opensearch_docs = []  # OpenSearch용

        for idx, url in enumerate(url_list):
            try:
                print(f"   [{idx+1}] 접속: {url}")
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")

                # 판매자 정보 버튼 클릭
                try:
                    seller_btn = page.locator("button", has_text="판매자 정보")
                    if await seller_btn.count() > 0:
                        expanded = await seller_btn.get_attribute("aria-expanded")
                        if expanded != "true":
                            await seller_btn.click()
                            await asyncio.sleep(0.5)
                except:
                    pass

                # 데이터 추출 헬퍼 함수
                async def get_value(label):
                    locator = page.locator(f"//dt[contains(., '{label}')]/following-sibling::dd[1]")
                    if await locator.count() > 0:
                        return await locator.inner_text()
                    return ""

                # 판매자 정보 수집
                info_company = await get_value("상호")
                info_brand = await get_value("브랜드")
                info_biz_num = await get_value("사업자번호")
                info_mail_order = await get_value("통신판매업신고")
                info_contact = await get_value("연락처")
                info_email = await get_value("E-mail")
                info_address = await get_value("영업소재지")

                # 기본 정보 수집
                title_loc = page.locator("meta[property='og:title']").first
                title = await title_loc.get_attribute("content") if await title_loc.count() > 0 else "제목없음"

                brand_loc = page.locator("meta[property='product:brand']").first
                brand_meta = await brand_loc.get_attribute("content") if await brand_loc.count() > 0 else info_brand

                price_loc = page.locator("meta[property='product:price:amount']").first
                if await price_loc.count() > 0:
                    price_text = await price_loc.get_attribute("content")
                    price_num = re.sub(r'[^0-9]', '', str(price_text))
                    price = int(price_num) if price_num else 0
                else:
                    price = 0

                # 데이터 구조화
                data = {
                    "url": url,
                    "title": title,
                    "brand": brand_meta,
                    "price": price,
                    "seller_info": {
                        "company": info_company,
                        "brand": info_brand,
                        "biz_num": info_biz_num,
                        "license": info_mail_order,
                        "contact": info_contact,
                        "email": info_email,
                        "address": info_address
                    }
                }
                collected_data.append(data)

                # OpenSearch용 문서
                opensearch_docs.append({
                    "_index": INDEX_NAME,
                    "_source": {
                        **data,
                        "created_at": datetime.now().isoformat()
                    }
                })

                print(f"      👉 수집완료: {info_company} / {title[:20]}...")

            except Exception as e:
                print(f"      ❌ 에러: {e}")
                continue

        # -------------------------------------------------------
        # [듀얼 저장] PostgreSQL + OpenSearch
        # -------------------------------------------------------
        if collected_data:
            print(f"\n🚀 데이터 {len(collected_data)}건 저장 시작...")
            
            # 1. PostgreSQL 저장 (원본)
            save_to_postgres(collected_data)
            
            # 2. OpenSearch 저장 (검색용)
            save_to_opensearch(opensearch_docs)
            
            print("🎉 듀얼 저장 완료!")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
