#!/bin/bash
# Fix frontend deployment on Railway

echo "🔧 Fixing ChatSEO Frontend Deployment"
echo "===================================="

# Change to frontend directory
cd frontend

echo "📦 Switching to frontend service..."
railway service frontend

echo "🚀 Redeploying frontend from correct directory..."
railway up

echo "✅ Frontend redeployment initiated!"
echo ""
echo "Monitor progress:"
echo "railway logs"
echo ""
echo "Frontend URL:"
echo "https://frontend-production-ce4b.up.railway.app"
echo ""
echo "Wait 2-3 minutes for deployment to complete..."