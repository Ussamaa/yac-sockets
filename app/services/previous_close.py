"""
Previous close price management
Fetches and caches previous day's close prices for P&L calculations
"""
from app.core.database import get_database
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from app.core.alpaca_client import get_alpaca_clients
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
import asyncio
import concurrent.futures


# In-memory cache for previous closes (refreshed daily)
_previous_close_cache = {}


def get_today_date_string() -> str:
    """Get today's date in YYYY-MM-DD format (UTC)"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


async def get_previous_close(symbol: str) -> float:
    """
    Get previous close price for a symbol
    First checks cache, then MongoDB, then fetches from Alpaca if needed
    
    Args:
        symbol: Stock/crypto symbol
        
    Returns:
        Previous close price or 0 if not found
    """
    if symbol in _previous_close_cache:
        return _previous_close_cache[symbol]
    
    # Load from DB or fetch from Alpaca
    result = await load_or_fetch_previous_closes([symbol])
    
    return result.get(symbol, 0)


async def load_or_fetch_previous_closes(symbols: List[str]) -> Dict[str, float]:
    """
    Load previous close prices from DB or fetch from Alpaca if not available.
    
    Args:
        symbols: List of symbols (e.g., ['AAPL', 'MSFT', 'BTC/USD', 'ETH/USD'])
    
    Returns:
        dict: {symbol: previous_close_price}
        
    Example:
        >>> await load_or_fetch_previous_closes(['AAPL', 'BTC/USD'])
        {'AAPL': 150.25, 'BTC/USD': 43250.75}
    """
    stock_data_client, crypto_data_client, _, _ = get_alpaca_clients()
    
    today = get_today_date_string()
    result = {}
    symbols_to_fetch = []
    
    print(f"📊 Loading previous close prices for date: {today}")
    
    # Step 1: Try to load from MongoDB database
    db = get_database()
    if db is not None:
        for symbol in symbols:
            try:
                close_doc = await db.daily_closes.find_one({
                    'symbol': symbol,
                    'date': today
                })
                
                if close_doc and 'close_price' in close_doc:
                    price = float(close_doc['close_price'])
                    result[symbol] = price
                    _previous_close_cache[symbol] = price
                    print(f"✅ Loaded from DB: {symbol} = ${price:,.2f}")
                else:
                    symbols_to_fetch.append(symbol)
            except Exception as e:
                print(f"⚠️ DB error for {symbol}: {e}")
                symbols_to_fetch.append(symbol)
    else:
        symbols_to_fetch = symbols
    
    # Step 2: If some symbols not in DB, fetch from Alpaca
    if symbols_to_fetch:
        # Separate symbols by type (stocks vs crypto)
        stock_symbols = [s for s in symbols_to_fetch if '/' not in s]
        crypto_symbols = [s for s in symbols_to_fetch if '/' in s]
        
        # Fetch stock previous closes
        if stock_symbols and stock_data_client:
            await _fetch_stock_previous_closes(
                stock_data_client, 
                stock_symbols, 
                today, 
                result
            )
        
        # Fetch crypto previous closes
        if crypto_symbols and crypto_data_client:
            await _fetch_crypto_previous_closes(
                crypto_data_client, 
                crypto_symbols, 
                today, 
                result
            )
    
    print(f"✅ Loaded {len(result)} previous close prices")
    return result


async def _fetch_stock_previous_closes(
    alpaca_data_client,
    stock_symbols: List[str],
    today: str,
    result: Dict[str, float]
):
    """
    Fetch stock previous closes from Alpaca Bars API
    
    Args:
        alpaca_data_client: Alpaca StockHistoricalDataClient instance
        stock_symbols: List of stock symbols (e.g., ['AAPL', 'MSFT'])
        today: Today's date string (YYYY-MM-DD)
        result: Dictionary to populate with results
    """
    print(f"📡 Fetching stock previous closes from Alpaca for: {stock_symbols}")
    
    db = get_database()
    
    # Run blocking Alpaca API call in thread pool
    loop = asyncio.get_event_loop()
    
    def fetch_bars():
        try:
            now = datetime.now(timezone.utc)
            
            # Look back up to 7 days to account for weekends and holidays
            start_time = now - timedelta(days=7)
            end_time = now
            
            # Create Alpaca bars request
            request_params = StockBarsRequest(
                symbol_or_symbols=stock_symbols,
                timeframe=TimeFrame.Day,
                start=start_time,
                end=end_time,
                feed='iex'
            )
            
            return alpaca_data_client.get_stock_bars(request_params)
        except Exception as e:
            print(f"❌ Error fetching stock bars from Alpaca: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        bars = await loop.run_in_executor(executor, fetch_bars)
    
    if bars and bars.df is not None and not bars.df.empty:
        for symbol in stock_symbols:
            try:
                # Select data for this symbol and get the last close
                symbol_data = bars.df.xs(symbol)
                close_price = float(symbol_data.iloc[-1]['close'])
                result[symbol] = close_price
                _previous_close_cache[symbol] = close_price
                
                # Store in database for future use (cache for the day)
                if db is not None:
                    await db.daily_closes.update_one(
                        {'symbol': symbol, 'date': today},
                        {
                            '$set': {
                                'symbol': symbol,
                                'date': today,
                                'close_price': close_price,
                                'updated_at': datetime.now(timezone.utc)
                            }
                        },
                        upsert=True
                    )
                
                print(f"✅ Fetched and stored: {symbol} = ${close_price:,.2f}")
                
            except KeyError:
                print(f"⚠️ No data available for {symbol}")
                result[symbol] = 0
            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {e}")
                result[symbol] = 0
    else:
        print(f"⚠️ No stock bar data returned from Alpaca")
        for symbol in stock_symbols:
            result[symbol] = 0


async def _fetch_crypto_previous_closes(
    alpaca_crypto_client,
    crypto_symbols: List[str],
    today: str,
    result: Dict[str, float]
):
    """
    Fetch crypto previous closes from Alpaca Crypto Bars API
    
    Args:
        alpaca_crypto_client: Alpaca CryptoHistoricalDataClient instance
        crypto_symbols: List of crypto pairs (e.g., ['BTC/USD', 'ETH/USD'])
        today: Today's date string (YYYY-MM-DD)
        result: Dictionary to populate with results
    """
    print(f"📡 Fetching crypto previous closes from Alpaca for: {crypto_symbols}")
    
    db = get_database()
    
    # Run blocking Alpaca API call in thread pool
    loop = asyncio.get_event_loop()
    
    def fetch_bars():
        try:
            now = datetime.now(timezone.utc)
            
            # Look back 2 days to get yesterday's close (crypto is 24/7)
            start_time = now - timedelta(days=2)
            end_time = now - timedelta(days=1)
            
            # Create Alpaca crypto bars request
            request_params = CryptoBarsRequest(
                symbol_or_symbols=crypto_symbols,
                timeframe=TimeFrame.Day,
                start=start_time,
                end=end_time
            )
            
            return alpaca_crypto_client.get_crypto_bars(request_params)
        except Exception as e:
            print(f"❌ Error fetching crypto bars from Alpaca: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        bars = await loop.run_in_executor(executor, fetch_bars)
    
    if bars and bars.df is not None and not bars.df.empty:
        for symbol in crypto_symbols:
            try:
                # Select data for this symbol and get the last close
                symbol_data = bars.df.xs(symbol)
                close_price = float(symbol_data.iloc[-1]['close'])
                result[symbol] = close_price
                _previous_close_cache[symbol] = close_price
                
                # Store in database for future use (cache for the day)
                if db is not None:
                    await db.daily_closes.update_one(
                        {'symbol': symbol, 'date': today},
                        {
                            '$set': {
                                'symbol': symbol,
                                'date': today,
                                'close_price': close_price,
                                'updated_at': datetime.now(timezone.utc)
                            }
                        },
                        upsert=True
                    )
                
                print(f"✅ Fetched and stored: {symbol} = ${close_price:,.2f}")
                
            except KeyError:
                print(f"⚠️ No data available for {symbol}")
                result[symbol] = 0
            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {e}")
                result[symbol] = 0
    else:
        print(f"⚠️ No crypto bar data returned from Alpaca")
        for symbol in crypto_symbols:
            result[symbol] = 0


async def clear_previous_close_cache():
    """Clear cache (call at market open to refresh)"""
    global _previous_close_cache
    _previous_close_cache = {}
    print("🔄 Previous close cache cleared")
