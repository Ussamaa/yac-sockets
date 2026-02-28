#!/usr/bin/env python3
"""
Test script for WebSocket connections
Run the server first: uvicorn app.main:app --port 8001
"""
import socketio
import time
import asyncio


def test_websocket_connection():
    """Test WebSocket connection and subscriptions"""
    print("=" * 60)
    print("Testing WebSocket Connection")
    print("=" * 60)
    
    # Create SocketIO client
    sio = socketio.Client()
    
    # Event handlers
    @sio.on('connected')
    def on_connected(data):
        print(f"✅ Connected to server: {data}")
    
    @sio.on('subscribed')
    def on_subscribed(data):
        print(f"✅ Subscribed to: {data.get('symbols', [])}")
    
    @sio.on('quote_update')
    def on_quote_update(data):
        symbol = data.get('symbol', 'Unknown')
        mid_price = data.get('mid_price', 0)
        timestamp = data.get('timestamp', 'N/A')
        print(f"📊 Quote Update: {symbol} = ${mid_price:.2f} @ {timestamp}")
    
    @sio.on('unsubscribed')
    def on_unsubscribed(data):
        print(f"❌ Unsubscribed from: {data.get('symbols', [])}")
    
    @sio.on('error')
    def on_error(data):
        print(f"❌ Error: {data}")
    
    try:
        # Connect to server
        print("\nConnecting to ws://localhost:8001...")
        sio.connect('http://localhost:8001')
        print("✅ Connected successfully")
        
        # Subscribe to stocks
        print("\nSubscribing to stock symbols: AAPL, GOOGL")
        sio.emit('join_market', {'symbols': ['AAPL', 'GOOGL']})
        
        # Wait for quotes
        print("\nWaiting for real-time quotes (10 seconds)...")
        time.sleep(10)
        
        # Subscribe to crypto
        print("\nSubscribing to crypto symbols: BTC/USD, ETH/USD")
        sio.emit('join_market', {'symbols': ['BTC/USD', 'ETH/USD']})
        
        # Wait for more quotes
        print("\nWaiting for more quotes (10 seconds)...")
        time.sleep(10)
        
        # Unsubscribe from stocks
        print("\nUnsubscribing from stocks: AAPL, GOOGL")
        sio.emit('leave_market', {'symbols': ['AAPL', 'GOOGL']})
        
        # Wait a bit more
        print("\nWaiting for crypto quotes only (5 seconds)...")
        time.sleep(5)
        
        # Disconnect
        print("\nDisconnecting...")
        sio.disconnect()
        print("✅ Disconnected successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_websocket_async():
    """Test WebSocket with async client"""
    print("\n" + "=" * 60)
    print("Testing WebSocket with Async Client")
    print("=" * 60)
    
    sio = socketio.AsyncClient()
    
    @sio.on('connected')
    async def on_connected(data):
        print(f"✅ Connected to server: {data}")
    
    @sio.on('subscribed')
    async def on_subscribed(data):
        print(f"✅ Subscribed to: {data.get('symbols', [])}")
    
    @sio.on('quote_update')
    async def on_quote_update(data):
        symbol = data.get('symbol', 'Unknown')
        mid_price = data.get('mid_price', 0)
        print(f"📊 {symbol}: ${mid_price:.2f}")
    
    try:
        # Connect
        print("\nConnecting to ws://localhost:8001...")
        await sio.connect('http://localhost:8001')
        print("✅ Connected successfully")
        
        # Subscribe
        print("\nSubscribing to: AAPL, BTC/USD")
        await sio.emit('join_market', {'symbols': ['AAPL', 'BTC/USD']})
        
        # Wait for quotes
        print("\nWaiting for quotes (15 seconds)...")
        await asyncio.sleep(15)
        
        # Disconnect
        print("\nDisconnecting...")
        await sio.disconnect()
        print("✅ Disconnected successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 FastAPI Market Data Service - WebSocket Tests")
    print("Base URL: ws://localhost:8001")
    print("\nMake sure the server is running:")
    print("uvicorn app.main:app --port 8001\n")
    
    # Test synchronous client
    test_websocket_connection()
    
    # Test async client
    print("\n" + "=" * 60)
    asyncio.run(test_websocket_async())
    
    print("\n" + "=" * 60)
    print("✅ WebSocket tests completed")
    print("=" * 60)
