#!/bin/bash
# Railway Deployment Script for ChatSEO Platform

echo "🚀 ChatSEO Platform - Railway Deployment Script"
echo "=============================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI found"

# Login check
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "railway login"
    exit 1
fi

echo "✅ Logged in to Railway"

# Check if we're in a Railway project
if ! railway status &> /dev/null; then
    echo "🔧 Creating new Railway project..."
    railway init --name "chat-seo-platform"
fi

echo "✅ Railway project ready"

# Add PostgreSQL database
echo "🐘 Adding PostgreSQL database..."
echo "Note: You may need to add PostgreSQL manually in the Railway dashboard"
echo "      Visit: https://railway.com and add a PostgreSQL service"

# Deploy the application
echo "🚀 Deploying application..."
railway up --service web

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Visit your Railway dashboard"
echo "2. Add PostgreSQL service if not already added"
echo "3. Set environment variables:"
echo "   - OPENAI_API_KEY=your-key"
echo "   - ANTHROPIC_API_KEY=your-key"
echo "   - GOOGLE_API_KEY=your-key"
echo ""
echo "Your project URL: https://railway.com"