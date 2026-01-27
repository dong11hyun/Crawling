"""
무신사 크롤러 v3 - 하이브리드 (API + HTML 파싱)
- 1단계: 상품 목록 API로 빠르게 수집
- 2단계: 상품 상세 HTML 파싱으로 판매자 정보 수집

속도: Playwright 대비 약 10배 빠름
"""
import requests
from bs4 import BeautifulSoup
import time
import json

# ================= 설정 =================
SEARCH_KEYWORD = "패딩"
MAX_PRODUCTS = 10

# 헤더 설정 (User-Agent 필수)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.musinsa.com/"
}


def get_product_list(keyword: str, size: int = 10) -> list:
    """
    1단계: 상품 검색 API로 상품 목록 가져오기
    """
    url = "https://api.musinsa.com/api2/dp/v1/plp/goods"
    params = {
        "gf": "A",
        "keyword": keyword,
        "sortCode": "POPULAR",
        "isUsed": "false",
        "page": 1,
        "size": size,
        "caller": "SEARCH"
    }
    
    print(f"🔍 [1단계] '{keyword}' 검색 API 호출 중...")
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        products = data.get("data", {}).get("list", [])
        print(f"   ✅ 상품 {len(products)}개 발견!")
        
        return products
    except Exception as e:
        print(f"   ❌ API 호출 실패: {e}")
        return []


def get_seller_info(goods_no: int) -> dict:
    """
    2단계: 상품 상세 페이지의 __NEXT_DATA__ JSON에서 판매자 정보 추출
    """
    url = f"https://www.musinsa.com/products/{goods_no}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # __NEXT_DATA__ script 태그에서 JSON 추출
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if not next_data_script:
            print(f"      ⚠️ __NEXT_DATA__ not found")
            return {}
        
        import json
        data = json.loads(next_data_script.string)
        
        # company 객체 추출
        company = data.get('props', {}).get('pageProps', {}).get('meta', {}).get('data', {}).get('company', {})
        
        if not company:
            return {}
        
        seller_info = {
            "company": company.get('name', ''),
            "ceo": company.get('ceoName', ''),
            "biz_num": company.get('businessNumber', ''),
            "license": company.get('mailOrderReportNumber', ''),
            "contact": company.get('phoneNumber', ''),
            "email": company.get('email', ''),
            "address": f"{company.get('address', '')} {company.get('detailAddress', '')}".strip()
        }
        
        return seller_info
    
    except Exception as e:
        print(f"      ⚠️ JSON 파싱 실패: {e}")
        return {}


def run_crawler(keyword: str = SEARCH_KEYWORD, max_products: int = MAX_PRODUCTS):
    """
    메인 크롤러 실행
    """
    start_time = time.time()
    
    print("=" * 50)
    print("🚀 무신사 크롤러 v3 (하이브리드) 시작")
    print("=" * 50)
    
    # 1단계: 상품 목록 API 호출
    products = get_product_list(keyword, max_products)
    
    if not products:
        print("❌ 상품을 찾을 수 없습니다.")
        return []
    
    # 2단계: 각 상품의 판매자 정보 수집
    print(f"\n📦 [2단계] 판매자 정보 수집 중...")
    
    results = []
    for idx, product in enumerate(products):
        goods_no = product.get("goodsNo")
        goods_name = product.get("goodsName", "")[:30]  # 30자 제한
        
        print(f"   [{idx+1}/{len(products)}] {goods_name}...")
        
        # 판매자 정보 파싱
        seller_info = get_seller_info(goods_no)
        
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
        results.append(result)
        
        # Rate limiting (0.5초 딜레이)
        time.sleep(0.5)
    
    # 결과 출력
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"🎉 수집 완료! 총 {len(results)}개 상품")
    print(f"⏱️  소요 시간: {elapsed:.1f}초")
    print("=" * 50)
    
    # 결과 미리보기
    print("\n📋 수집 결과 미리보기:")
    for r in results[:3]:
        print(f"\n   📦 {r['title'][:40]}...")
        print(f"      가격: {r['price']:,}원")
        print(f"      판매자: {r['seller_info'].get('company', 'N/A')}")
        print(f"      연락처: {r['seller_info'].get('contact', 'N/A')}")
    
    # JSON 파일로 저장
    output_file = f"data/crawl_result_{keyword}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 결과 저장: {output_file}")
    
    return results


if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else SEARCH_KEYWORD
    run_crawler(keyword=keyword)
