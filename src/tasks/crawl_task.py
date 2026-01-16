"""
크롤링 Task 모듈
- 무신사 상품 데이터 수집
- v2.2_crawler.py 로직 재사용
"""
import asyncio
import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import async_playwright

# 로깅 설정
logger = logging.getLogger(__name__)


async def _extract_seller_info(page) -> Dict[str, str]:
    """
    판매자 정보 추출 (v2.2_crawler.py 로직 재사용)
    """
    try:
        # 판매자 정보 버튼 클릭
        seller_btn = page.locator("button", has_text="판매자 정보")
        if await seller_btn.count() > 0:
            expanded = await seller_btn.get_attribute("aria-expanded")
            if expanded != "true":
                await seller_btn.click()
                await asyncio.sleep(0.5)
    except Exception as e:
        logger.warning(f"판매자 버튼 클릭 실패: {e}")
    
    async def get_value(label: str) -> str:
        """XPath로 라벨 옆 텍스트 추출"""
        locator = page.locator(f"//dt[contains(., '{label}')]/following-sibling::dd[1]")
        if await locator.count() > 0:
            return await locator.inner_text()
        return ""
    
    return {
        "company": await get_value("상호"),
        "brand": await get_value("브랜드"),
        "biz_num": await get_value("사업자번호"),
        "license": await get_value("통신판매업신고"),
        "contact": await get_value("연락처"),
        "email": await get_value("E-mail"),
        "address": await get_value("영업소재지"),
    }


async def _crawl_async(keyword: str, scroll_count: int, max_products: int) -> List[Dict[str, Any]]:
    """
    비동기 크롤링 메인 로직
    """
    target_url = f"https://www.musinsa.com/search/goods?keyword={keyword}&gf=A"
    collected_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        logger.info(f"🚀 크롤링 시작: {keyword}")
        await page.goto(target_url, timeout=60000)
        
        # 스크롤
        for i in range(scroll_count):
            await page.keyboard.press("End")
            await asyncio.sleep(2)
            logger.info(f"   ⬇️ 스크롤 {i+1}/{scroll_count}")
        
        # 상품 링크 수집
        locators = page.locator("a[href*='/products/']")
        count = await locators.count()
        urls = set()
        for i in range(min(count, max_products)):
            href = await locators.nth(i).get_attribute("href")
            if href:
                if not href.startswith("http"):
                    href = "https://www.musinsa.com" + href
                urls.add(href)
        
        url_list = list(urls)
        logger.info(f"   📦 수집 대상: {len(url_list)}개")
        
        for idx, url in enumerate(url_list):
            try:
                logger.info(f"   [{idx+1}/{len(url_list)}] {url}")
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                
                # 기본 정보 추출
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
                
                # 판매자 정보 추출 (개선!)
                seller_info = await _extract_seller_info(page)
                
                collected_data.append({
                    "url": url,
                    "title": title,
                    "brand": brand or seller_info.get("brand", ""),
                    "price": price,
                    "seller_info": seller_info,
                    "crawled_at": datetime.now().isoformat()
                })
                
                logger.info(f"      ✅ 수집 완료: {title[:30]}...")
                
            except Exception as e:
                logger.error(f"      ❌ 에러: {e}")
                continue
        
        await browser.close()
    
    return collected_data


def crawl_musinsa(
    keyword: str = "패딩",
    scroll_count: int = 2,
    max_products: int = 10
) -> List[Dict[str, Any]]:
    """
    무신사 크롤링 실행 (동기 래퍼)
    
    Args:
        keyword: 검색 키워드
        scroll_count: 스크롤 횟수
        max_products: 최대 수집 상품 수
    
    Returns:
        수집된 상품 데이터 리스트
    """
    logger.info(f"📦 크롤링 파라미터: keyword={keyword}, scroll={scroll_count}, max={max_products}")
    
    data = asyncio.run(_crawl_async(keyword, scroll_count, max_products))
    
    logger.info(f"✅ 크롤링 완료: {len(data)}건")
    return data
