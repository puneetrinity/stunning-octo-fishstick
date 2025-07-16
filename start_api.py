#!/usr/bin/env python3
"""
Quick startup script to test the ChatSEO API
"""
import uvicorn
from main import app
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting ChatSEO Platform API...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔐 Debug mode: {settings.debug}")
    print(f"🌐 API will be available at: http://localhost:8000")
    print(f"📖 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )