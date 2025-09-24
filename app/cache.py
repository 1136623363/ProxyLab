from typing import Any, Optional, Dict
import asyncio
import time
import hashlib
from functools import wraps
import json

class SimpleCache:
    """简单的内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if time.time() > item['expires_at']:
            del self.cache[key]
            return None
        
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        
        # 检查缓存大小限制
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """清理过期项"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time > item['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self) -> None:
        """移除最旧的缓存项"""
        if not self.cache:
            return
        
        # 找到最旧的项
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].get('created_at', 0))
        del self.cache[oldest_key]

# 全局缓存实例
cache = SimpleCache(default_ttl=300)  # 默认5分钟过期

def cached(prefix: str, ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> None:
    """根据模式删除缓存"""
    keys_to_delete = [key for key in cache.cache.keys() if pattern in key]
    for key in keys_to_delete:
        cache.delete(key)

# 定期清理过期缓存的异步任务
async def cleanup_cache_task():
    """定期清理过期缓存"""
    while True:
        await asyncio.sleep(300)  # 每5分钟清理一次
        cache.cleanup_expired()
