"""
CloudSim Backend Launcher
Starts the FastAPI backend server
"""
import sys
import uvicorn
from pathlib import Path

def main():
    """Launch the backend server"""
    print("=" * 70)
    print("CloudSim Backend Server")
    print("=" * 70)
    print("Starting on http://localhost:8000")
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Run uvicorn server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()
