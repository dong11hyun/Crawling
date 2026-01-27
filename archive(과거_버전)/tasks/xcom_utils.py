"""
XCom 유틸리티 모듈
- 소량 데이터: XCom 직접 전달
- 대용량 데이터: 파일로 저장 후 경로 전달
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 한국 시간
KST = timezone(timedelta(hours=9))

# 데이터 저장 경로 (Airflow 컨테이너 내부)
DATA_DIR = "/opt/airflow/data"


def save_to_file(data: Any, prefix: str = "crawl") -> str:
    """
    대용량 데이터를 파일로 저장하고 경로 반환
    
    Args:
        data: 저장할 데이터 (JSON 직렬화 가능해야 함)
        prefix: 파일명 접두사
    
    Returns:
        저장된 파일 경로
    """
    # 디렉토리 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    # JSON 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 파일 저장 완료: {filepath} ({len(data)}건)")
    return filepath


def load_from_file(filepath: str) -> Optional[Any]:
    """
    파일에서 데이터 로드
    
    Args:
        filepath: 로드할 파일 경로
    
    Returns:
        로드된 데이터 또는 None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"📁 파일 로드 완료: {filepath}")
        return data
    except Exception as e:
        logger.error(f"❌ 파일 로드 실패: {e}")
        return None


def cleanup_old_files(days: int = 7) -> int:
    """
    오래된 파일 정리
    
    Args:
        days: 며칠 이상 된 파일 삭제
    
    Returns:
        삭제된 파일 개수
    """
    import time
    
    if not os.path.exists(DATA_DIR):
        return 0
    
    deleted = 0
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for filename in os.listdir(DATA_DIR):
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                deleted += 1
                logger.info(f"🗑️ 삭제: {filename}")
    
    logger.info(f"🧹 정리 완료: {deleted}개 파일 삭제")
    return deleted


# XCom 크기 제한 (바이트)
XCOM_SIZE_LIMIT = 48000  # 약 48KB (Airflow 기본 제한)


def should_use_file(data: Any) -> bool:
    """
    데이터 크기에 따라 파일 사용 여부 결정
    """
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        return len(json_str.encode('utf-8')) > XCOM_SIZE_LIMIT
    except:
        return True  # 직렬화 실패 시 파일 사용
