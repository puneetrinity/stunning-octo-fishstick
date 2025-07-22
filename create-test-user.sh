#!/bin/bash
# Create a test user for ChatSEO Platform

echo "🔐 ChatSEO Platform - Create Test User"
echo "======================================"

API_BASE="https://stunning-octo-fishstick-production.up.railway.app/api/v1"

echo "📝 Registering test user..."

# Create test user
curl -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@chatseo.com",
    "password": "Demo123456",
    "full_name": "Demo User",
    "company_name": "ChatSEO Demo Company",
    "user_type": "brand"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "🧪 Testing login..."

# Test login
curl -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@chatseo.com",
    "password": "Demo123456"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "✅ Test user credentials:"
echo "Email: demo@chatseo.com"
echo "Password: Demo123456"
echo ""
echo "🚀 Use these credentials to login to:"
echo "Frontend: https://frontend-production-ce4b.up.railway.app"
echo "Backend Dev Interface: https://stunning-octo-fishstick-production.up.railway.app"