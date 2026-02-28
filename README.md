# FastAPI Market Data Service

A dedicated 24/7 Market Data Microservice that acts as an "antenna" for Alpaca market data streams.

## Features

- ✅ **Persistent WebSocket connections** to Alpaca (stocks + crypto)
- ✅ **In-memory caching** with intelligent TTL (3 seconds)
- ✅ **Real-time price updates** to multiple frontend clients via WebSocket
- ✅ **REST API** for on-demand quote requests
- ✅ **Previous close data** for daily P&L calculations
- ✅ **Reduced API calls** to Alpaca (70-90% reduction)
- ✅ **High performance** async FastAPI implementation

## Architecture

```
Frontend(s) ──► FastAPI Market Data ──► Alpaca WebSocket (24/7)
                     (Port 8001)              (Single connection)
```

## Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
MONGODB_URL=mongodb://localhost:27017
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Production mode
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### 4. Access the Service

- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **WebSocket**: ws://localhost:8001/socket.io

## API Endpoints

### REST API

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "service": "market-data",
  "alpaca_connected": true,
  "mongodb_connected": true
}
```

#### Get Quotes
```bash
POST /api/quotes
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOGL", "BTC/USD", "ETH/USD"]
}
```

Response:
```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "bid_price": 175.23,
      "ask_price": 175.25,
      "mid_price": 175.24,
      "spread": 0.02,
      "previous_close": 174.50,
      "daily_pnl": 0.74,
      "daily_pnl_percentage": 0.42,
      "timestamp": "2024-01-15T14:30:00Z"
    }
  ],
  "count": 1
}
```

### WebSocket Events

#### Connect to WebSocket
```javascript
const socket = io('http://localhost:8001');
```

#### Subscribe to Market Data
```javascript
socket.emit('join_market', {
  symbols: ['AAPL', 'BTC/USD']
});
```

#### Receive Real-time Updates
```javascript
socket.on('quote_update', (data) => {
  console.log(data);
  // {
  //   symbol: 'AAPL',
  //   bid_price: 175.23,
  //   ask_price: 175.25,
  //   mid_price: 175.24,
  //   timestamp: '2024-01-15T14:30:00Z'
  // }
});
```

#### Unsubscribe from Market Data
```javascript
socket.emit('leave_market', {
  symbols: ['AAPL']
});
```

## Testing

See `tests/` directory for test scripts:

```bash
# Test REST API
python tests/test_rest_api.py

# Test WebSocket
python tests/test_websocket.py

# Test with curl
curl http://localhost:8001/health
```

## Project Structure

```
fastapi-market-data/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── core/
│   │   ├── alpaca_client.py    # Alpaca client initialization
│   │   ├── database.py         # MongoDB connection
│   │   └── cache.py            # In-memory quote cache
│   ├── services/
│   │   ├── stock_stream.py     # Stock WebSocket handler
│   │   ├── crypto_stream.py    # Crypto WebSocket handler
│   │   ├── quote_service.py    # Quote fetching & caching
│   │   └── previous_close.py   # Daily close price management
│   ├── api/
│   │   ├── routes.py           # REST API endpoints
│   │   └── websocket.py        # SocketIO event handlers
│   └── models/
│       └── schemas.py          # Pydantic models
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Cache Behavior

The service implements intelligent caching to reduce Alpaca API calls:

1. **User A** requests AAPL quote → Cache miss → Fetch from Alpaca → Cache for 3 seconds
2. **User B** requests AAPL quote (1 second later) → Cache hit → Return cached data (no Alpaca call)
3. After 3 seconds → Cache expires → Next request fetches fresh data

**Result**: 70-90% reduction in API calls during active trading hours.

## Production Deployment

### Docker

```bash
# Build image
docker build -t fastapi-market-data .

# Run container
docker run -p 8001:8001 --env-file .env fastapi-market-data
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Monitoring

- Check server logs for real-time activity
- Monitor cache hit rates (look for "💰 Cache hit" messages)
- Track WebSocket subscriptions (look for "✅ Subscribed" messages)
- Monitor Alpaca API usage reduction

## Troubleshooting

### Alpaca stream not connecting
- Check API credentials in `.env`
- Verify network connectivity
- Check Alpaca service status

### Quotes not updating in real-time
- Verify WebSocket subscription
- Check room names match symbols
- Ensure stream is running

### Cache not working
- Check QUOTE_CACHE_TTL setting
- Monitor memory usage
- Verify cache logic in logs

### MongoDB connection errors
- Verify MONGODB_URL in `.env`
- Check MongoDB is running
- Ensure database exists

## License

MIT
