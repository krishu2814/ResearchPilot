"""
Caching Service for ResearchPilot (Phase 11).

This service provides a dual-backend caching layer:
1. Redis: Used when a Redis server is available (via REDIS_URL).
2. In-Memory TTL Cache: An automatic, built-in fallback using a Python
   dictionary with expiration timestamps when Redis is not running.

Caching eliminates duplicate web searches, prevents rate limits, and
speeds up repeated research runs to near-instantaneous responses.
"""

import json
import os
import time
from typing import Any, Optional, Dict, Tuple


# Internal statistics tracking
_cache_stats = {
    "hits": 0,
    "misses": 0
}

# In-memory storage: key -> (value, expire_timestamp)
_memory_cache: Dict[str, Tuple[Any, float]] = {}

# Redis client handle
_redis_client = None
_backend_name = "memory"


# -----------------------------------------------------------------------------
# 1. Connection & Initialization
# -----------------------------------------------------------------------------
def get_cache_backend() -> str:
    """
    Initializes and detects the available cache backend ('redis' or 'memory').
    """
    global _redis_client, _backend_name

    if _redis_client is not None:
        return _backend_name

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
            decode_responses=True
        )
        client.ping()
        _redis_client = client
        _backend_name = "redis"
        print(f"[Cache Service] Connected to Redis server at: {redis_url}")
    except Exception:
        _redis_client = None
        _backend_name = "memory"
        print("[Cache Service] Redis not detected or unreachable. Using built-in in-memory TTL cache.")

    return _backend_name


# -----------------------------------------------------------------------------
# 2. Get from Cache
# -----------------------------------------------------------------------------
def get_cache(key: str) -> Optional[Any]:
    """
    Retrieves a cached value by key. Returns None if the key does not exist
    or has expired.
    """
    global _cache_stats
    backend = get_cache_backend()

    # Case A: Redis Backend
    if backend == "redis" and _redis_client:
        try:
            val_str = _redis_client.get(key)
            if val_str is not None:
                _cache_stats["hits"] += 1
                return json.loads(val_str)
            else:
                _cache_stats["misses"] += 1
                return None
        except Exception as err:
            print(f"[Cache Service] Redis get error ({err}), falling back to memory.")

    # Case B: In-Memory TTL Cache
    now = time.time()
    if key in _memory_cache:
        value, expire_at = _memory_cache[key]
        if now < expire_at:
            _cache_stats["hits"] += 1
            return value
        else:
            # Key expired
            del _memory_cache[key]

    _cache_stats["misses"] += 1
    return None


# -----------------------------------------------------------------------------
# 3. Set Cache Value
# -----------------------------------------------------------------------------
def set_cache(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """
    Stores a value in the cache with an expiration time (TTL) in seconds.
    Default TTL is 1 hour (3600 seconds).
    """
    backend = get_cache_backend()

    # Case A: Redis Backend
    if backend == "redis" and _redis_client:
        try:
            val_str = json.dumps(value)
            _redis_client.setex(key, ttl_seconds, val_str)
            return
        except Exception as err:
            print(f"[Cache Service] Redis set error ({err}), falling back to memory.")

    # Case B: In-Memory TTL Cache
    expire_at = time.time() + ttl_seconds
    _memory_cache[key] = (value, expire_at)


# -----------------------------------------------------------------------------
# 4. Clear Cache
# -----------------------------------------------------------------------------
def clear_cache() -> None:
    """
    Flushes all keys from the active cache backend.
    """
    global _memory_cache, _cache_stats
    backend = get_cache_backend()

    if backend == "redis" and _redis_client:
        try:
            _redis_client.flushdb()
            print("[Cache Service] Flushed Redis database.")
        except Exception as err:
            print(f"[Cache Service] Redis flush error: {err}")

    _memory_cache.clear()
    print("[Cache Service] In-memory cache cleared.")


# -----------------------------------------------------------------------------
# 5. Cache Statistics
# -----------------------------------------------------------------------------
def get_cache_stats() -> dict:
    """
    Returns current cache performance metrics: hits, misses, active backend,
    hit ratio, and number of stored keys.
    """
    backend = get_cache_backend()
    hits = _cache_stats["hits"]
    misses = _cache_stats["misses"]
    total = hits + misses
    hit_ratio = round(hits / total, 4) if total > 0 else 0.0

    total_keys = 0
    if backend == "redis" and _redis_client:
        try:
            total_keys = _redis_client.dbsize()
        except Exception:
            total_keys = 0
    else:
        # Filter out expired keys from memory count
        now = time.time()
        active_keys = [k for k, (_, exp) in _memory_cache.items() if now < exp]
        total_keys = len(active_keys)

    return {
        "backend": backend,
        "hits": hits,
        "misses": misses,
        "total_requests": total,
        "hit_ratio": hit_ratio,
        "total_keys": total_keys
    }
