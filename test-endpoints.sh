#!/bin/bash
# Test Railway deployment endpoints

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 ChatSEO Platform - Endpoint Testing${NC}"
echo "=========================================="

# Get Railway deployment URL
echo -e "${YELLOW}Getting Railway deployment URL...${NC}"
RAILWAY_URL=$(railway domain 2>/dev/null | grep -o 'https://[^[:space:]]*' | head -1)

if [ -z "$RAILWAY_URL" ]; then
    echo -e "${YELLOW}No custom domain found, checking for Railway-generated domain...${NC}"
    # Try to get the URL from Railway status or project info
    RAILWAY_URL="https://web-production-XXXX.up.railway.app"
    echo -e "${YELLOW}Please replace XXXX with your actual Railway domain from the dashboard${NC}"
    echo -e "${YELLOW}Or provide the URL manually:${NC}"
    read -p "Enter your Railway app URL: " RAILWAY_URL
fi

if [ -z "$RAILWAY_URL" ]; then
    echo -e "${RED}❌ No Railway URL provided. Please check your Railway dashboard.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Testing Railway deployment at: $RAILWAY_URL${NC}"
echo ""

# Test function
test_endpoint() {
    local endpoint="$1"
    local description="$2"
    local expected_status="$3"
    
    echo -e "${BLUE}Testing ${description}...${NC}"
    echo "🔗 $RAILWAY_URL$endpoint"
    
    response=$(curl -s -w "\n%{http_code}" "$RAILWAY_URL$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ SUCCESS: HTTP $http_code${NC}"
        if [ ! -z "$body" ]; then
            echo "📄 Response:"
            echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        fi
    else
        echo -e "${RED}❌ FAILED: HTTP $http_code (expected $expected_status)${NC}"
        if [ ! -z "$body" ]; then
            echo "📄 Response:"
            echo "$body"
        fi
    fi
    echo ""
}

# Test all endpoints
echo -e "${YELLOW}🏥 Testing Health Endpoints${NC}"
echo "------------------------"

test_endpoint "/health" "Health Check" "200"
test_endpoint "/ready" "Readiness Check" "200"

echo -e "${YELLOW}📚 Testing Documentation${NC}"
echo "------------------------"

test_endpoint "/docs" "API Documentation" "200"
test_endpoint "/redoc" "ReDoc Documentation" "200"

echo -e "${YELLOW}🔐 Testing API Routes${NC}"
echo "------------------------"

test_endpoint "/api/v1/auth" "Auth Routes (should show method not allowed)" "405"
test_endpoint "/" "Root Endpoint" "200"

echo -e "${YELLOW}🔍 Testing Database Connection${NC}"
echo "------------------------"

# Test ready endpoint specifically for database status
echo -e "${BLUE}Checking database connection status...${NC}"
ready_response=$(curl -s "$RAILWAY_URL/ready" 2>/dev/null)
if echo "$ready_response" | grep -q "database.*connected"; then
    echo -e "${GREEN}✅ Database is connected${NC}"
else
    echo -e "${YELLOW}⚠️  Database status unclear. Response:${NC}"
    echo "$ready_response" | python3 -m json.tool 2>/dev/null || echo "$ready_response"
fi

echo ""
echo -e "${BLUE}🎉 Endpoint testing complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "• Health endpoint: $RAILWAY_URL/health"
echo "• Ready endpoint: $RAILWAY_URL/ready"
echo "• API docs: $RAILWAY_URL/docs"
echo "• ReDoc: $RAILWAY_URL/redoc"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set API keys in Railway dashboard if not already done"
echo "2. Test API functionality with your API keys"
echo "3. Check Railway logs: railway logs"
echo "4. Monitor performance in Railway dashboard"