"""
SocketIO WebSocket handlers
Handles client WebSocket connections for real-time quotes
"""
import socketio
from app.services.stock_stream import subscribe_to_stock, unsubscribe_from_stock, set_socketio_instance as set_stock_sio
from app.services.crypto_stream import subscribe_to_crypto, unsubscribe_from_crypto, set_socketio_instance as set_crypto_sio


# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Adjust for production
    logger=True,
    engineio_logger=True  # Enable to debug connection issues
)

# Set SocketIO instance for stream services
set_stock_sio(sio)
set_crypto_sio(sio)


@sio.event
async def connect(sid, environ):
    """Client connected"""
    print(f"✅ Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to market data service'}, room=sid)


@sio.event
async def disconnect(sid):
    """Client disconnected"""
    print(f"❌ Client disconnected: {sid}")


@sio.event
async def join_market(sid, data):
    """
    Subscribe to market data for symbols
    
    Args:
        sid: Socket ID
        data: {'symbols': ['AAPL', 'BTC/USD']}
    """
    if not isinstance(data, dict):
        await sio.emit('error', {'message': 'Invalid data format'}, room=sid)
        return
    
    symbols = data.get('symbols', [])
    
    if not symbols:
        await sio.emit('error', {'message': 'No symbols provided'}, room=sid)
        return
    
    subscribed = []
    
    for symbol in symbols:
        symbol = symbol.upper().strip()
        room = f'market_{symbol}'
        
        # Join SocketIO room
        await sio.enter_room(sid, room)
        
        # Subscribe to Alpaca stream
        if '/' in symbol:
            subscribe_to_crypto(symbol)
        else:
            subscribe_to_stock(symbol)
        
        subscribed.append(symbol)
        print(f"👤 {sid} joined {room}")
    
    await sio.emit('subscribed', {'symbols': subscribed}, room=sid)


@sio.event
async def leave_market(sid, data):
    """
    Unsubscribe from market data
    
    Args:
        sid: Socket ID
        data: {'symbols': ['AAPL']}
    """
    if not isinstance(data, dict):
        await sio.emit('error', {'message': 'Invalid data format'}, room=sid)
        return
    
    symbols = data.get('symbols', [])
    
    if not symbols:
        await sio.emit('error', {'message': 'No symbols provided'}, room=sid)
        return
    
    unsubscribed = []
    
    for symbol in symbols:
        symbol = symbol.upper().strip()
        room = f'market_{symbol}'
        
        # Leave SocketIO room
        await sio.leave_room(sid, room)
        
        # Check if anyone else is in the room
        # If not, unsubscribe from Alpaca stream
        try:
            room_participants = sio.manager.get_participants('/', room)
            if len(room_participants) == 0:
                if '/' in symbol:
                    unsubscribe_from_crypto(symbol)
                else:
                    unsubscribe_from_stock(symbol)
        except:
            # If we can't get participants, just unsubscribe to be safe
            if '/' in symbol:
                unsubscribe_from_crypto(symbol)
            else:
                unsubscribe_from_stock(symbol)
        
        unsubscribed.append(symbol)
        print(f"👤 {sid} left {room}")
    
    await sio.emit('unsubscribed', {'symbols': unsubscribed}, room=sid)
