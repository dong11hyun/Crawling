"""
Redis 캐시 유틸리티
- 검색 결과 캐싱
- TTL(Time To Live) 기반 자동 만료
"""
import redis
import json
from typing import Optional, Any

# ========================================
# Redis 연결
# ========================================
redis_client = redis.Redis(
    host='localhost',
    port=6380,  # docker-compose에서 6380:6379로 매핑
    db=0,
    decode_responses=True  # 문자열로 자동 디코딩
)

# 기본 TTL (5분)
DEFAULT_TTL = 300


def generate_cache_key(prefix: str, **kwargs) -> str:
    """
    캐시 키 생성
    예: search:패딩:0:100000 (검색어:최소가격:최대가격)
    """
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        parts.append(str(value) if value is not None else "none")
    return ":".join(parts)


def get_cache(key: str) -> Optional[Any]:
    """
    캐시에서 데이터 조회
    - 있으면 JSON 파싱해서 반환
    - 없으면 None
    """
    try:
        data = redis_client.get(key)
        if data:
            print(f"   🎯 캐시 히트: {key}")
            return json.loads(data)
        print(f"   ❌ 캐시 미스: {key}")
        return None
    except Exception as e:
        print(f"   ⚠️ 캐시 조회 실패: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
    """
    캐시에 데이터 저장
    - TTL(초) 후 자동 삭제
    """
    try:
        redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        print(f"   💾 캐시 저장: {key} (TTL: {ttl}초)")
        return True
    except Exception as e:
        print(f"   ⚠️ 캐시 저장 실패: {e}")
        return False


def delete_cache(key: str) -> bool:
    """캐시 삭제"""
    try:
        redis_client.delete(key)
        return True
    except:
        return False


def delete_cache_pattern(pattern: str) -> int:
    """
    패턴에 맞는 모든 캐시 삭제
    예: delete_cache_pattern("search:*") → 모든 검색 캐시 삭제
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except:
        return 0


def get_cache_stats() -> dict:
    """캐시 통계 조회"""
    try:
        info = redis_client.info()
        return {
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_keys": redis_client.dbsize(),
            "hits": info.get("keyspace_hits"),
            "misses": info.get("keyspace_misses"),
        }
    except Exception as e:
        return {"error": str(e)}
