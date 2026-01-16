"""
데이터 검증 Task 모듈
- 크롤링 데이터 품질 검사
- 필수 필드, 가격 범위 등 검증
"""
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def validate_products(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    크롤링 데이터 검증
    
    Args:
        data: 크롤링된 상품 데이터 리스트
    
    Returns:
        (유효한 데이터 리스트, 무효 데이터 개수)
    """
    if not data:
        logger.warning("⚠️ 검증할 데이터가 없습니다.")
        return [], 0
    
    valid_data = []
    invalid_count = 0
    
    for item in data:
        errors = []
        
        # 1. 필수 필드 검증
        if not item.get("url"):
            errors.append("URL 없음")
        if not item.get("title"):
            errors.append("제목 없음")
        
        # 2. URL 형식 검증
        url = item.get("url", "")
        if url and not url.startswith("https://www.musinsa.com"):
            errors.append("잘못된 URL 형식")
        
        # 3. 가격 범위 검증
        price = item.get("price", 0)
        if not isinstance(price, (int, float)):
            item["price"] = 0
            errors.append("가격 타입 오류 → 0으로 수정")
        elif price < 0:
            item["price"] = 0
            errors.append("음수 가격 → 0으로 수정")
        elif price > 100_000_000:  # 1억 이상 비정상
            errors.append("비정상적으로 높은 가격")
        
        # 4. 제목 길이 검증
        title = item.get("title", "")
        if len(title) > 500:
            item["title"] = title[:500]
            errors.append("제목 길이 초과 → 500자로 자름")
        
        # 결과 처리
        if errors and "URL 없음" in errors:
            invalid_count += 1
            logger.warning(f"❌ 무효 데이터: {errors}")
        else:
            if errors:
                logger.info(f"⚠️ 수정된 데이터: {errors}")
            valid_data.append(item)
    
    logger.info(f"✅ 검증 완료: 유효 {len(valid_data)}건, 무효 {invalid_count}건")
    
    return valid_data, invalid_count
