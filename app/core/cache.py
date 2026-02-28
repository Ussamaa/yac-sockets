"""
In-memory quote cache with TTL
Reduces redundant Alpaca API calls by caching quotes for a short period
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import asyncio


class QuoteCache:
    """In-memory cache with TTL for quote data"""
    
    def __init__(self, ttl_seconds: int = 3):
        self._cache: Dict[str, dict] = {}
        self._ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def get(self, symbol: str) -> Optional[dict]:
        """
        Get cached quote if not expired
        
        Args:
            symbol: Stock/crypto symbol
            
        Returns:
            Cached quote data or None if not found/expired
        """
        async with self._lock:
            if symbol in self._cache:
                cached_data = self._cache[symbol]
                if datetime.utcnow() < cached_data['expires_at']:
                    return cached_data['data']
                else:
                    # Expired, remove from cache
                    del self._cache[symbol]
            return None
    
    async def set(self, symbol: str, data: dict):
        """
        Cache quote data with TTL
        
        Args:
            symbol: Stock/crypto symbol
            data: Quote data to cache
        """
        async with self._lock:
            self._cache[symbol] = {
                'data': data,
                'expires_at': datetime.utcnow() + timedelta(seconds=self._ttl_seconds)
            }
    
    async def clear(self):
        """Clear all cached data"""
        async with self._lock:
            self._cache.clear()
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        async with self._lock:
            return {
                'total_cached': len(self._cache),
                'symbols': list(self._cache.keys())
            }


# Global cache instance
quote_cache = QuoteCache(ttl_seconds=3)
