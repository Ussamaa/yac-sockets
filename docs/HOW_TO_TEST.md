# 🧪 How to Test Your FastAPI Market Data Service

## Quick Start (3 Steps)

### 1️⃣ Add Your Alpaca Credentials

Edit the `.env` file:
```bash
nano .env
```

Add your credentials:
```env
ALPACA_API_KEY=your_actual_key_here
ALPACA_SECRET_KEY=your_actual_secret_here
```

### 2️⃣ Start the Server

```bash
# Option A: Direct uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Option B: Using convenience script
./run_server.sh
```

You should see:
```
✅ Connected to MongoDB: trading_platform
✅ Alpaca clients initialized
🚀 Starting Alpaca stock stream...
🚀 Starting Alpaca crypto stream...
INFO: Uvicorn running on http://0.0.0.0:8001
```

### 3️⃣ Test It!

Pick any method below:

---

## Testing Method 1: Interactive HTML Client (Easiest!)

**Best for**: Visual testing and understanding how WebSockets work

```bash
# Just open the file in your browser
open demo_client.html   # macOS
xdg-open demo_client.html   # Linux
start demo_client.html  # Windows
```

**What you can do:**
- ✅ Connect/disconnect WebSocket
- ✅ Subscribe to real-time quotes (AAPL, GOOGL, BTC/USD, etc.)
- ✅ Fetch quotes via REST API
- ✅ See live updates in beautiful cards
- ✅ View activity log

**Screenshot of what you'll see:**
- Connection status indicator
- Live quote cards with prices
- Real-time P&L calculations
- Activity log with all events

---

## Testing Method 2: curl Commands (Quick!)

**Best for**: Quick API testing

### Test 1: Health Check
```bash
curl http://localhost:8001/health
```

Expected output:
```json
{
  "status": "ok",
  "service": "market-data",
  "alpaca_connected": true,
  "mongodb_connected": true
}
```

### Test 2: Root Endpoint
```bash
curl http://localhost:8001/
```

Expected output:
```json
{
  "service": "Market Data Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "websocket": "/socket.io"
}
```

### Test 3: Get Stock Quotes
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "MSFT"]}'
```

Expected output:
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
  "count": 3
}
```

### Test 4: Get Crypto Quotes
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC/USD", "ETH/USD"]}'
```

### Test 5: Mixed Stocks + Crypto
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "BTC/USD", "GOOGL", "ETH/USD"]}'
```

### Test 6: Run All Tests
```bash
./tests/test_simple_curl.sh
```

---

## Testing Method 3: Python Scripts

**Best for**: Automated testing

### Test REST API
```bash
python tests/test_rest_api.py
```

This will:
- ✅ Test health endpoint
- ✅ Test quotes endpoint with stocks
- ✅ Test quotes endpoint with crypto
- ✅ Test error handling
- ✅ Measure response times

### Test WebSocket
```bash
python tests/test_websocket.py
```

This will:
- ✅ Connect to WebSocket
- ✅ Subscribe to symbols
- ✅ Receive real-time updates
- ✅ Test unsubscribe
- ✅ Verify event handling

---

## Testing Method 4: Auto-Generated API Docs

**Best for**: Exploring all endpoints interactively

1. Start the server
2. Open in browser: http://localhost:8001/docs

You'll see:
- 📚 Interactive Swagger UI
- 🧪 Try-it-out buttons for each endpoint
- 📖 Full API documentation
- 🔍 Request/response schemas

Try it:
1. Click on "POST /api/quotes"
2. Click "Try it out"
3. Enter symbols like `["AAPL", "BTC/USD"]`
4. Click "Execute"
5. See the response!

---

## Testing Method 5: Frontend Integration

**Update your frontend to use this service:**

### JavaScript/React Example:

```javascript
// REST API - Get quotes
const getQuotes = async (symbols) => {
  const response = await fetch('http://localhost:8001/api/quotes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbols })
  });
  return await response.json();
};

// WebSocket - Real-time quotes
import io from 'socket.io-client';

const socket = io('http://localhost:8001');

socket.on('connect', () => {
  console.log('Connected to market data service');
  socket.emit('join_market', { symbols: ['AAPL', 'BTC/USD'] });
});

socket.on('quote_update', (data) => {
  console.log('Quote update:', data.symbol, data.mid_price);
  // Update your UI here
});

socket.on('subscribed', (data) => {
  console.log('Subscribed to:', data.symbols);
});
```

---

## Expected Behavior

### ✅ During Market Hours (9:30 AM - 4:00 PM ET)
- Real-time stock quotes flowing via WebSocket
- Prices updating every few seconds
- Bid/ask spreads visible
- Daily P&L calculated from previous close

### ✅ After Hours / Weekends
- Crypto quotes (BTC/USD, ETH/USD) work 24/7
- Stock quotes show last known prices
- May see "market closed" in some responses

### ✅ Cache Behavior
- First request: Fetches from Alpaca (~200-500ms)
- Subsequent requests (within 3 seconds): Returns cached (~10-50ms)
- After 3 seconds: Fetches fresh data from Alpaca

### ✅ WebSocket Behavior
- Connects to Alpaca once (server-side)
- Multiple clients can subscribe to same symbols
- Auto-reconnects if connection drops
- Only subscribes to symbols that clients request

---

## Troubleshooting

### ❌ "Alpaca not connected" in health check

**Cause:** Invalid API credentials

**Fix:**
```bash
# Check .env file
cat .env | grep ALPACA

# Make sure keys are correct (no quotes, no spaces)
ALPACA_API_KEY=PKXXXXXXXXXXXXXXXX
ALPACA_SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### ❌ "MongoDB not connected"

**Cause:** MongoDB not running

**Fix:**
```bash
# Option 1: Start MongoDB locally
sudo systemctl start mongod

# Option 2: Use Docker
docker run -d -p 27017:27017 mongo:7

# Option 3: Service works without MongoDB (previous close won't work)
```

### ❌ "No quotes received"

**Possible causes:**
1. Market is closed (for stocks)
2. Invalid symbol names
3. Alpaca paper trading account limitations

**Fix:**
```bash
# Test with crypto (works 24/7)
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC/USD"]}'

# Verify Alpaca account at: https://alpaca.markets
```

### ❌ CORS errors in browser

**Cause:** Frontend running on different port

**Fix:**
Add your frontend URL to `app/config.py`:
```python
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8080",  # Add your port
]
```

### ❌ Port 8001 already in use

**Fix:**
```bash
# Find and kill process
lsof -ti:8001 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8002
```

---

## Performance Testing

### Test Cache Effectiveness

```bash
# Request 1 (uncached) - should be slower
time curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}'

# Request 2 (cached) - should be MUCH faster
time curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}'
```

Expected:
- First request: ~200-500ms
- Cached request: ~10-50ms (10x faster!)

### Test Multiple Concurrent Clients

```bash
# Run 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/quotes \
    -H "Content-Type: application/json" \
    -d '{"symbols": ["AAPL", "GOOGL"]}' &
done
wait

# All should complete quickly due to caching
```

### Monitor Server Logs

```bash
# Watch real-time activity
uvicorn app.main:app --port 8001 --log-level debug
```

Look for:
- `📊 AAPL: $175.24` - Quote updates
- `✅ Subscribed to stock: AAPL` - New subscriptions
- Cache hits vs misses

---

## Production Testing Checklist

Before deploying to production:

- [ ] Health check returns `"status": "ok"`
- [ ] Alpaca connection successful
- [ ] MongoDB connection successful (if used)
- [ ] REST API responds within 100ms for cached quotes
- [ ] WebSocket connects and stays connected
- [ ] Real-time quotes update every few seconds
- [ ] Multiple clients can subscribe simultaneously
- [ ] Cache reduces API calls (check Alpaca usage)
- [ ] Error handling works (test with invalid symbols)
- [ ] CORS configured for your frontend domain
- [ ] Environment variables secured (not committed to git)

---

## What Success Looks Like

✅ **Server starts clean:**
```
✅ Alpaca clients initialized
✅ Connected to MongoDB: trading_platform
🚀 Starting Alpaca stock stream...
🚀 Starting Alpaca crypto stream...
INFO: Application startup complete.
```

✅ **Health check passes:**
```json
{
  "status": "ok",
  "alpaca_connected": true,
  "mongodb_connected": true
}
```

✅ **Quotes return fast:**
```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "mid_price": 175.24,
      "daily_pnl": 0.74,
      "daily_pnl_percentage": 0.42
    }
  ],
  "count": 1
}
```

✅ **WebSocket streams work:**
- Client connects
- Subscribes to symbols
- Receives real-time updates
- Updates visible in HTML client

---

## Next Steps After Testing

1. **Integrate with your frontend** - Update API endpoints to port 8001
2. **Monitor performance** - Check Alpaca API usage reduction
3. **Deploy to production** - Use Docker or your preferred method
4. **Scale if needed** - Add Redis for distributed caching
5. **Remove from Flask** - Clean up old market data code

---

## Quick Reference

| What | Command |
|------|---------|
| Start server | `uvicorn app.main:app --port 8001 --reload` |
| Visual test | Open `demo_client.html` in browser |
| Health check | `curl http://localhost:8001/health` |
| Get quotes | `curl -X POST http://localhost:8001/api/quotes -H "Content-Type: application/json" -d '{"symbols": ["AAPL"]}'` |
| API docs | http://localhost:8001/docs |
| WebSocket URL | `http://localhost:8001/socket.io` |
| Stop server | `Ctrl+C` or `pkill -f uvicorn` |

---

**Need help?** Check:
- `README.md` - Full documentation
- `QUICKSTART.md` - Setup guide
- `TESTING_GUIDE.md` - Detailed testing
- Server logs - Most errors shown there
