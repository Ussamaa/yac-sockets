"""
Alpaca client initialization
Initializes Alpaca API clients for stocks and crypto (historical data + live streams)
"""
from alpaca.data import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.live import StockDataStream, CryptoDataStream
from app.config import settings


# Global clients
stock_data_client = None
crypto_data_client = None
stock_stream = None
crypto_stream = None


def initialize_alpaca_clients():
    """
    Initialize Alpaca API clients (call on startup)
    Returns tuple of (stock_data_client, crypto_data_client, stock_stream, crypto_stream)
    """
    global stock_data_client, crypto_data_client, stock_stream, crypto_stream
    
    stock_data_client = StockHistoricalDataClient(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY
    )
    
    crypto_data_client = CryptoHistoricalDataClient(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY
    )
    
    stock_stream = StockDataStream(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY
    )
    
    crypto_stream = CryptoDataStream(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY
    )
    
    return stock_data_client, crypto_data_client, stock_stream, crypto_stream


def get_alpaca_clients():
    """Get initialized Alpaca clients"""
    return stock_data_client, crypto_data_client, stock_stream, crypto_stream
