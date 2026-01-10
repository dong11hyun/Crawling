from celery import shared_task
from playwright.async_api import async_playwright
import asyncio
from asgiref.sync import sync_to_async
from .models import Book

@shared_task
def start_book_crawler():
    """Django에서 호출하는 진입점"""
    asyncio.run(crawl_books_logic())
    return "책 수집 작업 완료"

async def crawl_books_logic():
    print("📚 [Books to Scrape] 고속 수집 시작...")
    
    async with async_playwright() as p:
        # headless=True: 브라우저 창을 띄우지 않고 백그라운드에서 실행 (속도 빠름)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        target_url = "http://books.toscrape.com/catalogue/category/books_1/index.html"
        await page.goto(target_url)
        
        # 책 목록 요소 찾기
        articles = page.locator("article.product_pod")
        count = await articles.count()
        print(f"   📖 발견된 책: {count}권")

        for i in range(count):
            book = articles.nth(i)
            
            # 1. 정보 추출
            # 제목 (h3 태그 밑에 a 태그의 title 속성에 전체 제목이 있음)
            title = await book.locator("h3 a").get_attribute("title")
            
            # 가격
            price = await book.locator(".price_color").inner_text()
            
            # 재고
            stock = await book.locator(".instock.availability").inner_text()
            
            # 평점 (클래스 이름이 'star-rating Three' 이런 식임)
            rating_class = await book.locator(".star-rating").get_attribute("class")
            rating = rating_class.split(" ")[-1] # 'Three'만 추출
            
            # URL
            relative_url = await book.locator("h3 a").get_attribute("href")
            # 상대 경로(../../) 처리
            clean_url = "http://books.toscrape.com/catalogue/" + relative_url.replace("../", "")

            # 2. DB 저장 (Django ORM)
            # update_or_create: 이미 있는 URL이면 업데이트, 없으면 생성
            await sync_to_async(Book.objects.update_or_create)(
                url=clean_url,
                defaults={
                    'title': title,
                    'price': price,
                    'stock': stock.strip(),
                    'rating': rating
                }
            )
            print(f"   💾 저장: {title[:15]}... ({price})")

        print("🎉 [완료] 수집 끝!")
        await browser.close()