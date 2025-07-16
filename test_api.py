#!/usr/bin/env python3
"""
Test script to verify ChatSEO API endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_pricing_endpoint():
    """Test pricing endpoint"""
    print("\n💰 Testing pricing endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pricing/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Brand plans: {len(data.get('brand_plans', []))}")
            print(f"Agency plans: {len(data.get('agency_plans', []))}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("\n👤 Testing user registration...")
    try:
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "company_name": "Test Company",
            "user_type": "brand",
            "plan_type": "brand_starter"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Access token received: {data.get('access_token')[:20]}...")
            return True, data.get('access_token')
        else:
            print(f"Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"Error: {e}")
        return False, None

def main():
    """Run all tests"""
    print("🚀 Starting ChatSEO API Tests...")
    
    # Give API time to start
    time.sleep(2)
    
    success = True
    
    # Test health check
    if not test_health_check():
        success = False
    
    # Test pricing endpoint
    if not test_pricing_endpoint():
        success = False
    
    # Test user registration
    reg_success, token = test_user_registration()
    if not reg_success:
        success = False
    
    if success:
        print("\n✅ All tests passed!")
        print("🌐 API is running successfully")
        print(f"📖 Visit {BASE_URL}/docs for API documentation")
    else:
        print("\n❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    main()