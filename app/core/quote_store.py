"""
Global in-memory quote store
Stores latest quotes from Alpaca WebSocket streams
Serves as single source of truth for all quote requests
"""
from typing import Dict, Optional
from datetime import datetime
from threading import Lock


class QuoteStore:
    """Thread-safe in-memory store for latest quotes"""
    
    def __init__(self):
        self._stocks: Dict[str, dict] = {}
        self._crypto: Dict[str, dict] = {}
        self._previous_close_cache: Dict[str, float] = {}
        self._lock = Lock()
    
    def update_stock_quote(self, symbol: str, quote_data: dict):
        """
        Update stock quote in store
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quote_data: Quote data with bid_price, ask_price, timestamp
        """
        with self._lock:
            self._stocks[symbol] = {
                **quote_data,
                'symbol': symbol,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def update_crypto_quote(self, symbol: str, quote_data: dict):
        """
        Update crypto quote in store
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC/USD')
            quote_data: Quote data with bid_price, ask_price, timestamp
        """
        with self._lock:
            self._crypto[symbol] = {
                **quote_data,
                'symbol': symbol,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        Get quote from store
        
        Args:
            symbol: Symbol to retrieve
            
        Returns:
            Quote data if exists, None otherwise
        """
        with self._lock:
            if '/' in symbol:
                return self._crypto.get(symbol)
            else:
                return self._stocks.get(symbol)
    
    def get_all_stocks(self) -> Dict[str, dict]:
        """Get all stock quotes"""
        with self._lock:
            return self._stocks.copy()
    
    def get_all_crypto(self) -> Dict[str, dict]:
        """Get all crypto quotes"""
        with self._lock:
            return self._crypto.copy()
    
    def get_all_quotes(self) -> Dict[str, dict]:
        """Get all quotes (stocks + crypto)"""
        with self._lock:
            return {**self._stocks, **self._crypto}
    
    def has_symbol(self, symbol: str) -> bool:
        """Check if symbol exists in store"""
        with self._lock:
            if '/' in symbol:
                return symbol in self._crypto
            else:
                return symbol in self._stocks
    
    def get_subscribed_symbols(self) -> list:
        """Get list of all subscribed symbols"""
        with self._lock:
            return list(self._stocks.keys()) + list(self._crypto.keys())
    
    def clear(self):
        """Clear all quotes"""
        with self._lock:
            self._stocks.clear()
            self._crypto.clear()
    
    def update_previous_close(self, symbol: str, price: float):
        """Update previous close price in cache"""
        with self._lock:
            self._previous_close_cache[symbol] = price
    
    def update_previous_closes(self, closes: Dict[str, float]):
        """Bulk update previous close prices"""
        with self._lock:
            self._previous_close_cache.update(closes)
    
    def get_previous_close(self, symbol: str) -> Optional[float]:
        """Get previous close price from cache"""
        with self._lock:
            return self._previous_close_cache.get(symbol)
    
    def get_all_previous_closes(self) -> Dict[str, float]:
        """Get all previous close prices"""
        with self._lock:
            return self._previous_close_cache.copy()
    
    def clear_previous_closes(self):
        """Clear previous close cache (e.g., at day rollover)"""
        with self._lock:
            self._previous_close_cache.clear()


# Global singleton instance
_quote_store = QuoteStore()


def get_quote_store() -> QuoteStore:
    """Get the global quote store instance"""
    return _quote_store
