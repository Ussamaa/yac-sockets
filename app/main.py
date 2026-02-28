"""
FastAPI Market Data Service - Main Application
Entry point with startup/shutdown events
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.core.alpaca_client import initialize_alpaca_clients
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import router
from app.api.websocket import sio
from app.services.stock_stream import start_stock_stream
from app.services.crypto_stream import start_crypto_stream
from app.core.startup import initialize_market_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 60)
    print("🚀 Starting FastAPI Market Data Service...")
    print("=" * 60)
    
    # Initialize Alpaca clients
    try:
        initialize_alpaca_clients()
        print("✅ Alpaca clients initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Alpaca clients: {e}")
        print("⚠️  Make sure ALPACA_API_KEY and ALPACA_SECRET_KEY are set in .env")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("⚠️  Service will continue without MongoDB (previous close data unavailable)")
    
    # Initialize market data: fetch initial quotes and subscribe to defaults
    try:
        await initialize_market_data()
    except Exception as e:
        print(f"⚠️  Market data initialization warning: {e}")
        print("⚠️  Service will continue and populate data as streams connect")
    
    # Start Alpaca WebSocket streams in background
    asyncio.create_task(start_stock_stream())
    asyncio.create_task(start_crypto_stream())
    print("✅ Alpaca streams started in background")
    
    print("=" * 60)
    print(f"🌐 Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔌 WebSocket: ws://{settings.HOST}:{settings.PORT}/socket.io")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n" + "=" * 60)
    print("🛑 Shutting down...")
    await close_mongo_connection()
    print("=" * 60)


# Create FastAPI app
app = FastAPI(
    title="Market Data Service",
    description="Real-time market data microservice for trading platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - add before routes
# NOTE: Using ["*"] for development. In production, specify exact origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development (including file://)
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include REST API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Market Data Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/socket.io"
    }


# CRITICAL: Wrap the entire app with Socket.IO
# This MUST be at the very end, after all routes are defined  
# Socket.IO will intercept /socket.io/* requests and forward others to FastAPI
import socketio as socketio_module

# Store reference to original FastAPI app for lifespan management
_fastapi_app = app

# Global flag to ensure startup runs only once
_startup_complete = False

# Create wrapper with manual startup/shutdown to trigger lifespan
# NOTE: Socket.IO ASGIApp wrapper does NOT trigger FastAPI lifespan events
# So we manually call the startup/shutdown logic here
async def startup():
    """Startup callback for Socket.IO wrapper - manually triggers FastAPI lifespan startup"""
    global _startup_complete
    
    # CRITICAL: Ensure this only runs ONCE
    # Socket.IO may call this on every lifespan request, which blocks the event loop
    if _startup_complete:
        print("⚠️  Startup already completed, skipping...")
        return
    
    print("Socket.IO startup callback triggered")
    
    # Manually execute the lifespan startup logic
    print("=" * 60)
    print("🚀 Starting FastAPI Market Data Service...")
    print("=" * 60)
    
    # Initialize Alpaca clients
    try:
        initialize_alpaca_clients()
        print("✅ Alpaca clients initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Alpaca clients: {e}")
        print("⚠️  Make sure ALPACA_API_KEY and ALPACA_SECRET_KEY are set in .env")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("⚠️  Service will continue without MongoDB (previous close data unavailable)")
    
    # Initialize market data: fetch initial quotes and subscribe to defaults
    try:
        await initialize_market_data()
    except Exception as e:
        print(f"⚠️  Market data initialization warning: {e}")
        print("⚠️  Service will continue and populate data as streams connect")
    
    # Start Alpaca WebSocket streams in background
    asyncio.create_task(start_stock_stream())
    asyncio.create_task(start_crypto_stream())
    print("✅ Alpaca streams started in background")
    
    print("=" * 60)
    print(f"🌐 Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔌 WebSocket: ws://{settings.HOST}:{settings.PORT}/socket.io")
    print("=" * 60)
    
    # Mark startup as complete
    _startup_complete = True

async def shutdown():
    """Shutdown callback for Socket.IO wrapper - manually triggers FastAPI lifespan shutdown"""
    print("Socket.IO shutdown callback triggered")
    
    # Manually execute the lifespan shutdown logic
    print("\n" + "=" * 60)
    print("🛑 Shutting down...")
    await close_mongo_connection()
    print("=" * 60)

app = socketio_module.ASGIApp(
    sio, 
    other_asgi_app=app, 
    socketio_path='socket.io',
    on_startup=startup,
    on_shutdown=shutdown
)
