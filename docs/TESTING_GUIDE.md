# Testing Guide for FastAPI Market Data Service

This guide shows you how to test the Market Data Service to verify it's working correctly.

## Prerequisites

1. **Alpaca Account**: You need Alpaca API credentials
2. **Environment Setup**: Create a `.env` file with your credentials
3. **Python**: Python 3.8+ installed

## Step 1: Setup Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Alpaca credentials
# ALPACA_API_KEY=your_key_here
# ALPACA_SECRET_KEY=your_secret_here
```

## Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Start the Server

```bash
# Run in development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

You should see output like:
```
============================================================
🚀 Starting FastAPI Market Data Service...
============================================================
✅ Alpaca clients initialized
✅ Connected to MongoDB: trading_platform
✅ Alpaca streams started in background
============================================================
🌐 Server running on http://0.0.0.0:8001
📚 API Docs: http://0.0.0.0:8001/docs
🔌 WebSocket: ws://0.0.0.0:8001/socket.io
============================================================
```

## Step 4: Test with Browser

### Interactive API Documentation
Open your browser and go to: http://localhost:8001/docs

This shows the interactive Swagger UI where you can test endpoints directly.

### Test Health Check
Go to: http://localhost:8001/health

You should see:
```json
{
  "status": "ok",
  "service": "market-data",
  "alpaca_connected": true,
  "mongodb_connected": true
}
```

## Step 5: Test REST API with Curl

### Test Health Check
```bash
curl http://localhost:8001/health
```

### Test Stock Quotes
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "MSFT"]}'
```

### Test Crypto Quotes
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC/USD", "ETH/USD"]}'
```

### Run All Curl Tests
```bash
./tests/test_simple_curl.sh
```

## Step 6: Test REST API with Python Script

```bash
# Make sure server is running in another terminal
python tests/test_rest_api.py
```

Expected output:
```
============================================================
Testing Health Check Endpoint
============================================================
Status Code: 200
✅ Health check passed

============================================================
Testing Stock Quotes Endpoint
============================================================
Status Code: 200
✅ Received 3 stock quotes

Test Summary:
✅ PASS: Health Check
✅ PASS: Stock Quotes
✅ PASS: Crypto Quotes
✅ PASS: Mixed Quotes
✅ PASS: Cache Behavior

Total: 5/5 tests passed
```

## Step 7: Test WebSocket with Python Script

```bash
python tests/test_websocket.py
```

Expected output:
```
============================================================
Testing WebSocket Connection
============================================================
Connecting to ws://localhost:8001...
✅ Connected successfully
✅ Subscribed to: ['AAPL', 'GOOGL']

Waiting for real-time quotes (10 seconds)...
📊 Quote Update: AAPL = $175.24 @ 2024-01-15T14:30:00Z
📊 Quote Update: GOOGL = $140.50 @ 2024-01-15T14:30:01Z
...
```

## Step 8: Test WebSocket with JavaScript (Frontend)

Create a simple HTML file `test_websocket.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Market Data WebSocket Test</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>Market Data WebSocket Test</h1>
    <div id="status">Connecting...</div>
    <div id="quotes"></div>

    <script>
        const socket = io('http://localhost:8001');
        
        socket.on('connected', (data) => {
            document.getElementById('status').innerHTML = '✅ Connected';
            console.log('Connected:', data);
            
            // Subscribe to symbols
            socket.emit('join_market', {
                symbols: ['AAPL', 'BTC/USD', 'GOOGL']
            });
        });
        
        socket.on('subscribed', (data) => {
            console.log('Subscribed to:', data.symbols);
        });
        
        socket.on('quote_update', (data) => {
            console.log('Quote update:', data);
            const quotesDiv = document.getElementById('quotes');
            quotesDiv.innerHTML += `<p>${data.symbol}: $${data.mid_price} @ ${data.timestamp}</p>`;
        });
        
        socket.on('error', (data) => {
            console.error('Error:', data);
        });
    </script>
</body>
</html>
```

Open this file in your browser and check the console for real-time quotes.

## Step 9: Verify Cache Behavior

Watch the server logs while running the cache test:

```bash
python tests/test_rest_api.py
```

In the server logs, you should see:
```
📊 Fetched from Alpaca: AAPL = $175.24    # First request
💰 Cache hit: AAPL                        # Second request (cached)
💰 Cache hit: AAPL                        # Third request (cached)
```

This confirms the cache is working and reducing API calls.

## Step 10: Test with Multiple Clients

To test that multiple clients can receive the same data:

1. Open 2-3 browser tabs with the WebSocket test HTML
2. All should connect and receive the same quote updates
3. Server logs should show multiple clients subscribing to the same symbols

## Step 11: Performance Testing

### Test Cache Performance
```bash
# Make 100 requests for the same symbol quickly
for i in {1..100}; do
  curl -s -X POST http://localhost:8001/api/quotes \
    -H "Content-Type: application/json" \
    -d '{"symbols": ["AAPL"]}' > /dev/null
done
```

Check server logs - you should see mostly "💰 Cache hit" messages.

### Stress Test
```bash
# Install Apache Bench (if needed)
# sudo apt-get install apache2-utils

# Run 1000 requests with 10 concurrent connections
ab -n 1000 -c 10 -p payload.json -T application/json http://localhost:8001/api/quotes
```

Create `payload.json`:
```json
{"symbols": ["AAPL", "GOOGL", "BTC/USD"]}
```

## Troubleshooting

### Error: "ALPACA_API_KEY not set"
- Make sure you created `.env` file
- Verify API credentials are correct
- Restart the server after updating `.env`

### Error: "MongoDB connection failed"
- If you don't have MongoDB installed, the service will still work
- Previous close data won't be available
- To install MongoDB: `brew install mongodb-community` (Mac) or `sudo apt install mongodb` (Linux)

### No real-time quotes in WebSocket
- Verify you're subscribed to valid symbols
- Check if it's during market hours (if using paper trading, check Alpaca's data availability)
- Alpaca may throttle requests if you exceed limits

### Cache not working
- Verify TTL setting in `.env` (QUOTE_CACHE_TTL=3)
- Make requests within 3 seconds to see cache hits
- Check server logs for cache behavior

## Expected Results Summary

✅ **Health Check**: Returns status "ok" with Alpaca and MongoDB connection status
✅ **Stock Quotes**: Returns bid/ask/mid prices with P&L data
✅ **Crypto Quotes**: Returns BTC/USD and ETH/USD quotes
✅ **WebSocket**: Real-time quote updates every second during market hours
✅ **Cache**: 70-90% of requests hit cache (visible in logs)
✅ **Multiple Clients**: All clients receive same quote updates

## Next Steps

Once testing is complete:
- Point your frontend to http://localhost:8001 for market data
- Keep Flask server for trading operations
- Monitor Alpaca API usage reduction
- Consider deploying to production with Docker
