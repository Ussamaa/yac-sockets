#!/bin/bash
# Simple curl-based tests for the Market Data Service

BASE_URL="http://localhost:8001"

echo "========================================"
echo "FastAPI Market Data Service - Curl Tests"
echo "========================================"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Root Endpoint
echo "Test 2: Root Endpoint"
echo "--------------------"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""
echo ""

# Test 3: Stock Quotes
echo "Test 3: Stock Quotes (AAPL, GOOGL)"
echo "--------------------"
curl -s -X POST "$BASE_URL/api/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL"]}' | python3 -m json.tool
echo ""
echo ""

# Test 4: Crypto Quotes
echo "Test 4: Crypto Quotes (BTC/USD, ETH/USD)"
echo "--------------------"
curl -s -X POST "$BASE_URL/api/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC/USD", "ETH/USD"]}' | python3 -m json.tool
echo ""
echo ""

# Test 5: Mixed Quotes
echo "Test 5: Mixed Quotes (Stocks + Crypto)"
echo "--------------------"
curl -s -X POST "$BASE_URL/api/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "BTC/USD", "MSFT", "ETH/USD"]}' | python3 -m json.tool
echo ""
echo ""

echo "========================================"
echo "All tests completed!"
echo "========================================"
