"""
Quote service - Fetch quotes from in-memory store or Alpaca API
Handles both stocks and crypto, integrates with cache and previous close data
"""
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest
from app.core.alpaca_client import get_alpaca_clients
from app.core.cache import quote_cache
from app.services.previous_close import get_previous_close
from app.core.quote_store import get_quote_store
from app.services.stock_stream import subscribe_to_stock
from app.services.crypto_stream import subscribe_to_crypto
from datetime import datetime
from typing import List


async def get_quotes(symbols: List[str]) -> list:
    """
    Fetch latest quotes for multiple symbols (stocks + crypto)
    Uses cache to reduce redundant Alpaca API calls
    
    Args:
        symbols: List of stock/crypto symbols
        
    Returns:
        List of quote data dictionaries
    """
    # Separate stocks from crypto
    stock_symbols = [s for s in symbols if '/' not in s]
    crypto_symbols = [s for s in symbols if '/' in s]
    
    quotes_data = []
    
    # Fetch stock quotes
    if stock_symbols:
        quotes_data.extend(await _fetch_stock_quotes(stock_symbols))
    
    # Fetch crypto quotes
    if crypto_symbols:
        quotes_data.extend(await _fetch_crypto_quotes(crypto_symbols))
    
    return quotes_data


async def _fetch_stock_quotes(symbols: List[str]) -> list:
    """
    Fetch stock quotes from in-memory store or Alpaca API
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        List of stock quote data
    """
    stock_data_client, _, _, _ = get_alpaca_clients()
    quote_store = get_quote_store()
    results = []
    
    if not stock_data_client:
        return [{'symbol': s, 'error': 'Stock data client not initialized'} for s in symbols]
    
    for symbol in symbols:
        # Check in-memory store first (populated by WebSocket)
        stored_quote = quote_store.get_quote(symbol)
        if stored_quote:
            print(f"⚡ From store: {symbol}")
            
            # Get previous close for P&L calculation from cache
            previous_close = quote_store.get_previous_close(symbol)
            if previous_close is None:
                # Not in cache, fetch it
                previous_close = await get_previous_close(symbol)
                if previous_close:
                    quote_store.update_previous_close(symbol, previous_close)
            
            mid_price = stored_quote.get('mid_price', 0)
            
            # Calculate daily P&L
            if previous_close and previous_close > 0:
                daily_pnl = mid_price - previous_close
                daily_pnl_percentage = (daily_pnl / previous_close) * 100
            else:
                daily_pnl = 0
                daily_pnl_percentage = 0
            
            quote_data = {
                'symbol': symbol,
                'bid_price': round(stored_quote.get('bid_price', 0), 2),
                'ask_price': round(stored_quote.get('ask_price', 0), 2),
                'mid_price': round(mid_price, 2),
                'spread': round(stored_quote.get('ask_price', 0) - stored_quote.get('bid_price', 0), 2),
                'previous_close': round(previous_close, 2) if previous_close else None,
                'daily_pnl': round(daily_pnl, 2),
                'daily_pnl_percentage': round(daily_pnl_percentage, 2),
                'timestamp': stored_quote.get('timestamp')
            }
            results.append(quote_data)
            continue
        
        # Not in store - fetch from Alpaca API and subscribe for future updates
        print(f"🔍 Not in store, fetching from Alpaca: {symbol}")
        try:
            request_params = StockLatestQuoteRequest(
                symbol_or_symbols=[symbol],
                feed='iex'
            )
            stock_quotes = stock_data_client.get_stock_latest_quote(request_params)
            
            if symbol in stock_quotes:
                quote = stock_quotes[symbol]
                bid = float(quote.bid_price) if quote.bid_price else 0
                ask = float(quote.ask_price) if quote.ask_price else 0
                mid_price = (bid + ask) / 2 if (bid and ask) else (bid or ask)
                
                # Get previous close for P&L from cache
                previous_close = quote_store.get_previous_close(symbol)
                if previous_close is None:
                    # Not in cache, fetch it
                    previous_close = await get_previous_close(symbol)
                    if previous_close:
                        quote_store.update_previous_close(symbol, previous_close)
                
                # Calculate daily P&L
                if previous_close and previous_close > 0:
                    daily_pnl = mid_price - previous_close
                    daily_pnl_percentage = (daily_pnl / previous_close) * 100
                else:
                    daily_pnl = 0
                    daily_pnl_percentage = 0
                
                quote_data = {
                    'symbol': symbol,
                    'bid_price': round(bid, 2),
                    'ask_price': round(ask, 2),
                    'mid_price': round(mid_price, 2),
                    'spread': round(ask - bid, 2) if (ask and bid) else 0,
                    'previous_close': round(previous_close, 2) if previous_close else None,
                    'daily_pnl': round(daily_pnl, 2),
                    'daily_pnl_percentage': round(daily_pnl_percentage, 2),
                    'timestamp': quote.timestamp.isoformat() if quote.timestamp else datetime.utcnow().isoformat()
                }
                
                # Store in quote store for future requests
                quote_store.update_stock_quote(symbol, quote_data)
                
                # Subscribe to WebSocket for real-time updates
                subscribe_to_stock(symbol)
                
                print(f"📊 Fetched from Alpaca & subscribed: {symbol} = ${mid_price:.2f}")
                results.append(quote_data)
            else:
                results.append({'symbol': symbol, 'error': 'Quote not found'})
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            results.append({'symbol': symbol, 'error': str(e)})
    
    return results


async def _fetch_crypto_quotes(symbols: List[str]) -> list:
    """
    Fetch crypto quotes from in-memory store or Alpaca API
    
    Args:
        symbols: List of crypto symbols
        
    Returns:
        List of crypto quote data
    """
    _, crypto_data_client, _, _ = get_alpaca_clients()
    quote_store = get_quote_store()
    results = []
    
    if not crypto_data_client:
        return [{'symbol': s, 'error': 'Crypto data client not initialized'} for s in symbols]
    
    for symbol in symbols:
        # Check in-memory store first (populated by WebSocket)
        stored_quote = quote_store.get_quote(symbol)
        if stored_quote:
            print(f"⚡ From store: {symbol}")
            
            # Get previous close for P&L calculation from cache
            previous_close = quote_store.get_previous_close(symbol)
            if previous_close is None:
                # Not in cache, fetch it
                previous_close = await get_previous_close(symbol)
                if previous_close:
                    quote_store.update_previous_close(symbol, previous_close)
            
            mid_price = stored_quote.get('mid_price', 0)
            
            # Calculate daily P&L
            if previous_close and previous_close > 0:
                daily_pnl = mid_price - previous_close
                daily_pnl_percentage = (daily_pnl / previous_close) * 100
            else:
                daily_pnl = 0
                daily_pnl_percentage = 0
            
            quote_data = {
                'symbol': symbol,
                'bid_price': round(stored_quote.get('bid_price', 0), 2),
                'ask_price': round(stored_quote.get('ask_price', 0), 2),
                'mid_price': round(mid_price, 2),
                'spread': round(stored_quote.get('ask_price', 0) - stored_quote.get('bid_price', 0), 2),
                'previous_close': round(previous_close, 2) if previous_close else None,
                'daily_pnl': round(daily_pnl, 2),
                'daily_pnl_percentage': round(daily_pnl_percentage, 2),
                'timestamp': stored_quote.get('timestamp')
            }
            results.append(quote_data)
            continue
        
        # Not in store - fetch from Alpaca API and subscribe for future updates
        print(f"🔍 Not in store, fetching from Alpaca: {symbol}")
        try:
            request_params = CryptoLatestQuoteRequest(symbol_or_symbols=[symbol])
            crypto_quotes = crypto_data_client.get_crypto_latest_quote(request_params)
            
            if symbol in crypto_quotes:
                quote = crypto_quotes[symbol]
                bid = float(quote.bid_price) if quote.bid_price else 0
                ask = float(quote.ask_price) if quote.ask_price else 0
                mid_price = (bid + ask) / 2 if (bid and ask) else (bid or ask)
                
                # Get previous close for P&L from cache
                previous_close = quote_store.get_previous_close(symbol)
                if previous_close is None:
                    # Not in cache, fetch it
                    previous_close = await get_previous_close(symbol)
                    if previous_close:
                        quote_store.update_previous_close(symbol, previous_close)
                
                # Calculate daily P&L
                if previous_close and previous_close > 0:
                    daily_pnl = mid_price - previous_close
                    daily_pnl_percentage = (daily_pnl / previous_close) * 100
                else:
                    daily_pnl = 0
                    daily_pnl_percentage = 0
                
                quote_data = {
                    'symbol': symbol,
                    'bid_price': round(bid, 2),
                    'ask_price': round(ask, 2),
                    'mid_price': round(mid_price, 2),
                    'spread': round(ask - bid, 2) if (ask and bid) else 0,
                    'previous_close': round(previous_close, 2) if previous_close else None,
                    'daily_pnl': round(daily_pnl, 2),
                    'daily_pnl_percentage': round(daily_pnl_percentage, 2),
                    'timestamp': quote.timestamp.isoformat() if quote.timestamp else datetime.utcnow().isoformat()
                }
                
                # Store in quote store for future requests
                quote_store.update_crypto_quote(symbol, quote_data)
                
                # Subscribe to WebSocket for real-time updates
                subscribe_to_crypto(symbol)
                
                print(f"₿ Fetched from Alpaca & subscribed: {symbol} = ${mid_price:.2f}")
                results.append(quote_data)
            else:
                results.append({'symbol': symbol, 'error': 'Quote not found'})
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            results.append({'symbol': symbol, 'error': str(e)})
    
    return results
