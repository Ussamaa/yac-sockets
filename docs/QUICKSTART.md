# QuickStart Guide - FastAPI Market Data Service

Get up and running in 5 minutes!

## 🚀 Quick Setup

### 1. Create Environment File
```bash
cp .env.example .env
```

### 2. Add Your Alpaca Credentials
Edit `.env` and add your credentials:
```
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
```

### 3. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 4. Start the Server
```bash
# Option 1: Use the convenience script
./run_server.sh

# Option 2: Run directly
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🧪 Quick Test

Once the server is running, test it immediately:

### Test 1: Browser
Open: http://localhost:8001/docs

You'll see the interactive API documentation.

### Test 2: Curl (Health Check)
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

### Test 3: Get Stock Quotes
```bash
curl -X POST http://localhost:8001/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL"]}'
```

### Test 4: Run Test Suite
```bash
# REST API tests
python tests/test_rest_api.py

# WebSocket tests
python tests/test_websocket.py

# Or use curl tests
./tests/test_simple_curl.sh
```

## 📊 What You'll See

When the server starts:
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

When quotes are fetched:
```
📊 Fetched from Alpaca: AAPL = $175.24
💰 Cache hit: AAPL
📊 Fetched from Alpaca: BTC/USD = $42155.00
```

## 🔗 Frontend Integration

Update your frontend to use the new service:

```javascript
// REST API - Get quotes
fetch('http://localhost:8001/api/quotes', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ symbols: ['AAPL', 'BTC/USD'] })
})
.then(res => res.json())
.then(data => console.log(data));

// WebSocket - Real-time quotes
const socket = io('http://localhost:8001');

socket.on('connected', () => {
  socket.emit('join_market', { symbols: ['AAPL', 'BTC/USD'] });
});

socket.on('quote_update', (data) => {
  console.log(`${data.symbol}: $${data.mid_price}`);
});
```

## 📦 Docker Setup (Optional)

```bash
# Start with Docker Compose (includes MongoDB)
docker-compose up -d

# Check logs
docker-compose logs -f fastapi-market
```

## 🎯 Key Endpoints

- **API Docs**: http://localhost:8001/docs
- **Health**: http://localhost:8001/health
- **Quotes**: POST http://localhost:8001/api/quotes
- **WebSocket**: ws://localhost:8001/socket.io

## 📖 Full Documentation

- `README.md` - Complete documentation
- `TESTING_GUIDE.md` - Detailed testing instructions

## ⚙️ Configuration

All settings are in `.env`:
- `QUOTE_CACHE_TTL=3` - Cache duration in seconds
- `PORT=8001` - Server port
- `ALLOWED_ORIGINS` - CORS settings

## 🆘 Troubleshooting

**Server won't start?**
- Check `.env` file exists and has valid credentials
- Make sure port 8001 is not in use

**No quotes returned?**
- Verify Alpaca credentials are correct
- Check if it's market hours (or use paper trading data)

**MongoDB errors?**
- Service works without MongoDB (previous close data unavailable)
- Install MongoDB or use Docker Compose

## ✅ Next Steps

1. ✅ Server running? → Test endpoints
2. ✅ Tests passing? → Connect frontend
3. ✅ Frontend working? → Monitor cache performance
4. ✅ Everything good? → Deploy to production

**Happy Trading! 🚀📈**
