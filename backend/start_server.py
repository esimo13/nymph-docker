#!/usr/bin/env python3
"""
Backend server startup script
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

if __name__ == "__main__":
    import uvicorn
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        reload_dirs=[str(app_dir)]
    )
