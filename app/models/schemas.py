"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class QuoteRequest(BaseModel):
    """Request model for quote fetching"""
    symbols: List[str]


class QuoteData(BaseModel):
    """Quote data model"""
    symbol: str
    bid_price: float
    ask_price: float
    mid_price: float
    spread: float
    previous_close: Optional[float] = None
    daily_pnl: float = 0.0
    daily_pnl_percentage: float = 0.0
    timestamp: str
    error: Optional[str] = None


class QuoteResponse(BaseModel):
    """Response model for quote endpoint"""
    quotes: List[QuoteData]
    count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    alpaca_connected: bool
    mongodb_connected: bool


class SubscriptionRequest(BaseModel):
    """WebSocket subscription request"""
    symbols: List[str]
