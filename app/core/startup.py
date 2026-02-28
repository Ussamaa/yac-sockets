"""
Startup initialization for market data service
- Subscribe to default symbols on server start
- Fetch initial prices from Alpaca API
- Start WebSocket streams
"""
import asyncio
from app.core.alpaca_client import get_alpaca_clients
from app.services.stock_stream import subscribe_to_stock
from app.services.crypto_stream import subscribe_to_crypto
from app.core.quote_store import get_quote_store


# Default symbols to subscribe on startup
DEFAULT_STOCK_SYMBOLS = [
    "AAPL",   # Apple
    "GOOGL",  # Google
    "MSFT",   # Microsoft
    "AMZN",   # Amazon
    "TSLA",   # Tesla
    "NVDA",   # NVIDIA
    "META",   # Meta
    "NFLX",   # Netflix
]

DEFAULT_CRYPTO_SYMBOLS = [
    "BTC/USD",  # Bitcoin
    "ETH/USD",  # Ethereum
    "DOGE/USD", # Dogecoin
    "SHIB/USD", # Shiba Inu
]


async def fetch_initial_quotes():
    """
    Fetch initial quotes from Alpaca API for default symbols
    This populates the quote store before WebSocket updates arrive
    
    NOTE: Alpaca SDK uses synchronous HTTP calls, so we run them in a thread pool
    to avoid blocking the async event loop
    """
    import concurrent.futures
    
    stock_client, crypto_client, _, _ = get_alpaca_clients()
    quote_store = get_quote_store()
    
    print("🔄 Fetching initial quotes from Alpaca API...")
    
    # Helper function to fetch stock quotes (runs in thread pool)
    def fetch_stock_quotes():
        if not stock_client or not DEFAULT_STOCK_SYMBOLS:
            return {}
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            request_params = StockLatestQuoteRequest(
                symbol_or_symbols=DEFAULT_STOCK_SYMBOLS,
                feed='iex'
            )
            return stock_client.get_stock_latest_quote(request_params)
        except Exception as e:
            print(f"⚠️ Error fetching initial stock quotes: {e}")
            return {}
    
    # Helper function to fetch crypto quotes (runs in thread pool)
    def fetch_crypto_quotes():
        if not crypto_client or not DEFAULT_CRYPTO_SYMBOLS:
            return {}
        try:
            from alpaca.data.requests import CryptoLatestQuoteRequest
            request_params = CryptoLatestQuoteRequest(symbol_or_symbols=DEFAULT_CRYPTO_SYMBOLS)
            return crypto_client.get_crypto_latest_quote(request_params)
        except Exception as e:
            print(f"⚠️ Error fetching initial crypto quotes: {e}")
            return {}
    
    # Run blocking Alpaca API calls in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Fetch stock and crypto quotes concurrently in thread pool
        stock_future = loop.run_in_executor(executor, fetch_stock_quotes)
        crypto_future = loop.run_in_executor(executor, fetch_crypto_quotes)
        
        # Wait for both to complete
        stock_quotes, crypto_quotes = await asyncio.gather(stock_future, crypto_future)
    
    # Process stock quotes
    for symbol, quote in stock_quotes.items():
        quote_data = {
            'symbol': symbol,
            'bid_price': float(quote.bid_price) if quote.bid_price else 0,
            'ask_price': float(quote.ask_price) if quote.ask_price else 0,
            'timestamp': quote.timestamp.isoformat() if quote.timestamp else None,
        }
        bid = quote_data['bid_price']
        ask = quote_data['ask_price']
        quote_data['mid_price'] = (bid + ask) / 2 if (bid and ask) else (bid or ask)
        
        quote_store.update_stock_quote(symbol, quote_data)
        print(f"✅ Initial: {symbol} = ${quote_data['mid_price']:.2f}")
    
    # Process crypto quotes
    for symbol, quote in crypto_quotes.items():
        quote_data = {
            'symbol': symbol,
            'bid_price': float(quote.bid_price) if quote.bid_price else 0,
            'ask_price': float(quote.ask_price) if quote.ask_price else 0,
            'timestamp': quote.timestamp.isoformat() if quote.timestamp else None,
        }
        bid = quote_data['bid_price']
        ask = quote_data['ask_price']
        quote_data['mid_price'] = (bid + ask) / 2 if (bid and ask) else (bid or ask)
        
        quote_store.update_crypto_quote(symbol, quote_data)
        print(f"✅ Initial: {symbol} = ${quote_data['mid_price']:.2f}")
    
    print(f"✅ Initial quotes loaded: {len(quote_store.get_all_quotes())} symbols")


def subscribe_default_symbols():
    """
    Subscribe to default symbols on Alpaca WebSocket streams
    This ensures we get real-time updates for popular symbols
    """
    print("🔔 Subscribing to default symbols...")
    
    # Subscribe to stocks
    for symbol in DEFAULT_STOCK_SYMBOLS:
        subscribe_to_stock(symbol)
    
    # Subscribe to crypto
    for symbol in DEFAULT_CRYPTO_SYMBOLS:
        subscribe_to_crypto(symbol)
    
    print(f"✅ Subscribed to {len(DEFAULT_STOCK_SYMBOLS)} stocks and {len(DEFAULT_CRYPTO_SYMBOLS)} crypto")


async def initialize_market_data():
    """
    Initialize market data service on startup:
    1. Fetch initial quotes from API
    2. Load previous close prices
    3. Subscribe to default symbols on WebSocket
    """
    print("\n" + "="*60)
    print("🚀 Initializing Market Data Service")
    print("="*60)
    
    # Fetch initial quotes
    await fetch_initial_quotes()
    
    # Load previous close prices for default symbols
    await load_previous_closes()
    
    # Subscribe to WebSocket streams
    subscribe_default_symbols()
    
    print("="*60)
    print("✅ Market Data Service Ready")
    print("="*60 + "\n")


async def load_previous_closes():
    """
    Load previous close prices for default symbols
    This populates the cache for daily P&L calculations
    """
    from app.services.previous_close import load_or_fetch_previous_closes
    from app.core.quote_store import get_quote_store
    
    print("🔄 Loading previous close prices...")
    
    # Combine all default symbols
    all_symbols = DEFAULT_STOCK_SYMBOLS + DEFAULT_CRYPTO_SYMBOLS
    
    # Load/fetch previous closes
    previous_closes = await load_or_fetch_previous_closes(all_symbols)
    
    # Store in quote store cache
    quote_store = get_quote_store()
    quote_store.update_previous_closes(previous_closes)
    
    print(f"✅ Previous close cache initialized with {len(previous_closes)} symbols")
