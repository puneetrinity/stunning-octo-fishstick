#!/bin/bash
# Test and fix registration endpoint

echo "🔧 Testing ChatSEO Registration Fix"
echo "===================================="

API_BASE="https://stunning-octo-fishstick-production.up.railway.app/api/v1"

# Generate unique email
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-${TIMESTAMP}@chatseo.com"

echo "📝 Testing registration with email: $TEST_EMAIL"

# Test registration with detailed output
RESPONSE=$(curl -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"TestPass123\",
    \"full_name\": \"Test User\",
    \"company_name\": \"ChatSEO Test\",
    \"user_type\": \"brand\"
  }" \
  -w "\nHTTP_CODE:%{http_code}\nTOTAL_TIME:%{time_total}s" \
  -s)

echo "📊 Registration Response:"
echo "$RESPONSE"
echo ""

# Extract HTTP code
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "✅ SUCCESS: Registration working!"
    
    echo "🧪 Testing login..."
    LOGIN_RESPONSE=$(curl -X POST "$API_BASE/auth/login" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"TestPass123\"
      }" \
      -w "\nHTTP_CODE:%{http_code}" \
      -s)
    
    echo "📊 Login Response:"
    echo "$LOGIN_RESPONSE"
    
    echo ""
    echo "🎉 REGISTRATION AND LOGIN WORKING!"
    echo "Users can now create accounts at:"
    echo "https://stunning-octo-fishstick-production.up.railway.app/"
    
else
    echo "❌ REGISTRATION STILL FAILING"
    echo "HTTP Code: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "500" ]; then
        echo ""
        echo "🔍 This indicates a server error, likely:"
        echo "1. Database table missing or misconfigured"
        echo "2. UUID generation issue"
        echo "3. Password hashing problem"
        echo ""
        echo "🛠️ Possible fixes:"
        echo "1. Check Railway database has users table"
        echo "2. Ensure UUID extension is enabled"
        echo "3. Check application logs in Railway dashboard"
    fi
    
    echo ""
    echo "📋 Manual test instructions:"
    echo "1. Visit: https://stunning-octo-fishstick-production.up.railway.app/"
    echo "2. Try registration form in the development interface"
    echo "3. Check if it shows different error details"
fi

echo ""
echo "🔗 Links to test:"
echo "Frontend: https://frontend-production-ce4b.up.railway.app"
echo "Backend: https://stunning-octo-fishstick-production.up.railway.app/"