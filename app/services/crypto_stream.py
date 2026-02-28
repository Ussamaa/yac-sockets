"""
Crypto WebSocket stream service
Maintains 24/7 connection to Alpaca crypto quotes (BTC/USD, ETH/USD), broadcasts to clients
"""
import asyncio
from alpaca.data.live import CryptoDataStream
from app.core.alpaca_client import get_alpaca_clients
from app.core.quote_store import get_quote_store


# Track active crypto subscriptions
active_crypto_subscriptions = set()

# Will be set from websocket module to avoid circular import
_sio = None


def set_socketio_instance(sio):
    """Set SocketIO instance for broadcasting"""
    global _sio
    _sio = sio


async def crypto_quote_handler(quote):
    """
    Handle incoming crypto quotes from Alpaca
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
    quote_store.update_crypto_quote(symbol, quote_data)
    
    # Broadcast to WebSocket clients (if SocketIO is available)
    if _sio:
        await _sio.emit('quote_update', quote_data, room=f'market_{symbol}')
    
    print(f"₿ {symbol}: ${mid_price:.2f} (P&L: ${daily_pnl:+.2f})")


async def start_crypto_stream():
    """
    Start Alpaca crypto WebSocket stream (called on server startup)
    
    IMPORTANT: Alpaca's _run_forever() is a blocking call that runs an internal event loop.
    We run it in a thread pool to avoid blocking FastAPI's async event loop.
    """
    _, _, _, crypto_stream = get_alpaca_clients()
    
    if not crypto_stream:
        print("❌ Crypto stream not initialized")
        return
    
    print("🚀 Starting Alpaca crypto stream...")
    
    def run_stream_blocking():
        """Blocking function to run in thread pool"""
        try:
            # Subscribe to any existing symbols
            if active_crypto_subscriptions:
                crypto_stream.subscribe_quotes(crypto_quote_handler, *active_crypto_subscriptions)
            
            # Run forever (blocking call with internal event loop)
            crypto_stream.run()
        except Exception as e:
            print(f"❌ Crypto stream error: {e}")
    
    # Run the blocking Alpaca stream in a thread pool to avoid blocking FastAPI's event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_stream_blocking)


def subscribe_to_crypto(symbol: str):
    """
    Add symbol to crypto stream subscriptions
    
    Args:
        symbol: Crypto symbol to subscribe to (e.g., BTC/USD)
    """
    _, _, _, crypto_stream = get_alpaca_clients()
    
    if not crypto_stream:
        print(f"❌ Cannot subscribe to {symbol}: crypto stream not initialized")
        return
    
    if symbol not in active_crypto_subscriptions:
        active_crypto_subscriptions.add(symbol)
        crypto_stream.subscribe_quotes(crypto_quote_handler, symbol)
        print(f"✅ Subscribed to crypto: {symbol}")


def unsubscribe_from_crypto(symbol: str):
    """
    Remove symbol from crypto stream subscriptions
    
    Args:
        symbol: Crypto symbol to unsubscribe from
    """
    _, _, _, crypto_stream = get_alpaca_clients()
    
    if not crypto_stream:
        return
    
    if symbol in active_crypto_subscriptions:
        active_crypto_subscriptions.remove(symbol)
        crypto_stream.unsubscribe_quotes(symbol)
        print(f"❌ Unsubscribed from crypto: {symbol}")
