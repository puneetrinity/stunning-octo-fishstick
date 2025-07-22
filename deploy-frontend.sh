#!/bin/bash
# Deploy frontend to Railway

echo "🚀 Deploying ChatSEO Frontend to Railway"
echo "========================================"

# Switch to frontend directory
cd frontend

# Deploy to Railway
echo "📦 Deploying frontend service..."
railway up --service frontend

echo "✅ Frontend deployment initiated!"
echo ""
echo "Frontend will be available at:"
echo "https://frontend-production-XXXX.up.railway.app"
echo ""
echo "Check deployment status:"
echo "railway logs --service frontend"