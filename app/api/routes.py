"""
REST API endpoints
Provides HTTP endpoints for quote fetching and health checks
"""
from fastapi import APIRouter, HTTPException
from app.services.quote_service import get_quotes
from app.models.schemas import QuoteRequest, QuoteResponse, HealthResponse
from app.core.alpaca_client import get_alpaca_clients
from app.core.database import get_database


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Service status and connection info
    """
    stock_client, crypto_client, stock_stream, crypto_stream = get_alpaca_clients()
    db = get_database()
    
    return {
        "status": "ok",
        "service": "market-data",
        "alpaca_connected": stock_client is not None and crypto_client is not None,
        "mongodb_connected": db is not None
    }


@router.post("/api/quotes")
async def fetch_quotes(request: QuoteRequest):
    """
    Get latest quotes for multiple symbols (with caching)
    
    Args:
        request: QuoteRequest with symbols list
        
    Returns:
        Quote data for all requested symbols
    """
    if not request.symbols:
        raise HTTPException(status_code=400, detail="symbols array required")
    
    # Clean and validate symbols
    symbols = [s.upper().strip() for s in request.symbols if s.strip()]
    
    if not symbols:
        raise HTTPException(status_code=400, detail="No valid symbols provided")
    
    quotes = await get_quotes(symbols)
    
    return {
        "quotes": quotes,
        "count": len(quotes)
    }
