#!/usr/bin/env python3
"""
Test script for REST API endpoints
Run the server first: uvicorn app.main:app --port 8001
"""
import requests
import json
import sys


BASE_URL = "http://localhost:8001"


def test_health_check():
    """Test health check endpoint"""
    print("=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_quotes_stocks():
    """Test fetching stock quotes"""
    print("\n" + "=" * 60)
    print("Testing Stock Quotes Endpoint")
    print("=" * 60)
    
    payload = {
        "symbols": ["AAPL", "GOOGL", "MSFT"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('count') > 0:
                print(f"✅ Received {data['count']} stock quotes")
                return True
            else:
                print("❌ No quotes returned")
                return False
        else:
            print("❌ Request failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_quotes_crypto():
    """Test fetching crypto quotes"""
    print("\n" + "=" * 60)
    print("Testing Crypto Quotes Endpoint")
    print("=" * 60)
    
    payload = {
        "symbols": ["BTC/USD", "ETH/USD"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('count') > 0:
                print(f"✅ Received {data['count']} crypto quotes")
                return True
            else:
                print("❌ No quotes returned")
                return False
        else:
            print("❌ Request failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_quotes_mixed():
    """Test fetching mixed stock and crypto quotes"""
    print("\n" + "=" * 60)
    print("Testing Mixed Quotes Endpoint")
    print("=" * 60)
    
    payload = {
        "symbols": ["AAPL", "BTC/USD", "GOOGL", "ETH/USD"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('count') > 0:
                print(f"✅ Received {data['count']} mixed quotes")
                return True
            else:
                print("❌ No quotes returned")
                return False
        else:
            print("❌ Request failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_cache_behavior():
    """Test cache behavior by making repeated requests"""
    print("\n" + "=" * 60)
    print("Testing Cache Behavior (watch server logs)")
    print("=" * 60)
    
    payload = {
        "symbols": ["AAPL"]
    }
    
    print("Making 3 requests in quick succession...")
    print("First request should fetch from Alpaca, next 2 should hit cache")
    
    for i in range(3):
        try:
            response = requests.post(
                f"{BASE_URL}/api/quotes",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"Request {i+1}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('quotes'):
                    quote = data['quotes'][0]
                    print(f"  AAPL: ${quote.get('mid_price', 'N/A')}")
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    print("✅ Cache test completed (check server logs for cache hits)")
    return True


if __name__ == "__main__":
    print("\n🚀 FastAPI Market Data Service - REST API Tests")
    print(f"Base URL: {BASE_URL}")
    print("\nMake sure the server is running:")
    print("uvicorn app.main:app --port 8001\n")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Stock Quotes", test_get_quotes_stocks()))
    results.append(("Crypto Quotes", test_get_quotes_crypto()))
    results.append(("Mixed Quotes", test_get_quotes_mixed()))
    results.append(("Cache Behavior", test_cache_behavior()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)
