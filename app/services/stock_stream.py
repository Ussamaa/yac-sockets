"""
Stock WebSocket stream service
Maintains 24/7 connection to Alpaca stock quotes, broadcasts to clients
"""
import asyncio
from alpaca.data.live import StockDataStream
from app.core.alpaca_client import get_alpaca_clients
from app.core.quote_store import get_quote_store


# Track active subscriptions
active_stock_subscriptions = set()

# Will be set from websocket module to avoid circular import
_sio = None


def set_socketio_instance(sio):
    """Set SocketIO instance for broadcasting"""
    global _sio
    _sio = sio


async def stock_quote_handler(quote):
    """
    Handle incoming stock quotes from Alpaca
    Broadcast to all clients in the symbol's room
    
    Args:
        quote: Alpaca quote object
    """
    symbol = quote.symbol
    
    quote_data = {
        'symbol': symbol,
        'bid_price': float(quote.bid_price) if quote.bid_price else 0,
        'ask_price': float(quote.ask_price) if quote.ask_price else 0,
        'timestamp': quote.timestamp.isoformat() if quote.timestamp else None
    }
    
    # Calculate mid price
    bid = quote_data['bid_price']
    ask = quote_data['ask_price']
    mid_price = (bid + ask) / 2 if (bid and ask) else (bid or ask)
    quote_data['mid_price'] = mid_price
    
    # Get previous close for P&L calculation
    quote_store = get_quote_store()
    previous_close = quote_store.get_previous_close(symbol)
    
    # Calculate daily P&L
    if previous_close and previous_close > 0:
        daily_pnl = mid_price - previous_close
        daily_pnl_percentage = (daily_pnl / previous_close) * 100
    else:
        daily_pnl = 0
        daily_pnl_percentage = 0
    
    quote_data['previous_close'] = round(previous_close, 2) if previous_close else None
    quote_data['daily_pnl'] = round(daily_pnl, 2)
    quote_data['daily_pnl_percentage'] = round(daily_pnl_percentage, 2)
    quote_data['spread'] = round(ask - bid, 2) if (ask and bid) else 0
    
    # Update global quote store (single source of truth)
    quote_store.update_stock_quote(symbol, quote_data)
    
    # Broadcast to WebSocket clients (if SocketIO is available)
    if _sio:
        await _sio.emit('quote_update', quote_data, room=f'market_{symbol}')
    
    print(f"📊 {symbol}: ${mid_price:.2f} (P&L: ${daily_pnl:+.2f})")


async def start_stock_stream():
    """
    Start Alpaca stock WebSocket stream (called on server startup)
    
    IMPORTANT: Alpaca's _run_forever() is a blocking call that runs an internal event loop.
    We run it in a thread pool to avoid blocking FastAPI's async event loop.
    """
    _, _, stock_stream, _ = get_alpaca_clients()
    
    if not stock_stream:
        print("❌ Stock stream not initialized")
        return
    
    print("🚀 Starting Alpaca stock stream...")
    
    def run_stream_blocking():
        """Blocking function to run in thread pool"""
        try:
            # Subscribe to any existing symbols
            if active_stock_subscriptions:
                stock_stream.subscribe_quotes(stock_quote_handler, *active_stock_subscriptions)
            
            # Run forever (blocking call with internal event loop)
            stock_stream.run()
        except Exception as e:
            print(f"❌ Stock stream error: {e}")
    
    # Run the blocking Alpaca stream in a thread pool to avoid blocking FastAPI's event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_stream_blocking)


def subscribe_to_stock(symbol: str):
    """
    Add symbol to stock stream subscriptions
    
    Args:
        symbol: Stock symbol to subscribe to
    """
    _, _, stock_stream, _ = get_alpaca_clients()
    
    if not stock_stream:
        print(f"❌ Cannot subscribe to {symbol}: stock stream not initialized")
        return
    
    if symbol not in active_stock_subscriptions:
        active_stock_subscriptions.add(symbol)
        stock_stream.subscribe_quotes(stock_quote_handler, symbol)
        print(f"✅ Subscribed to stock: {symbol}")


def unsubscribe_from_stock(symbol: str):
    """
    Remove symbol from stock stream subscriptions
    
    Args:
        symbol: Stock symbol to unsubscribe from
    """
    _, _, stock_stream, _ = get_alpaca_clients()
    
    if not stock_stream:
        return
    
    if symbol in active_stock_subscriptions:
        active_stock_subscriptions.remove(symbol)
        stock_stream.unsubscribe_quotes(symbol)
        print(f"❌ Unsubscribed from stock: {symbol}")
