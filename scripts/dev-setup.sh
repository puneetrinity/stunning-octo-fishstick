#!/bin/bash

# Development setup script
echo "🚀 Setting up ChatSEO Platform development environment..."

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
    echo "⚠️  Please update the .env file with your actual configuration"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec app alembic upgrade head

# Create initial data (if needed)
echo "📊 Setting up initial data..."
# TODO: Add initial data setup

echo "✅ Development environment setup complete!"
echo "🌐 API will be available at: http://localhost:8000"
echo "📖 API documentation: http://localhost:8000/docs"
echo "🌸 Flower (Celery monitoring): http://localhost:5555"