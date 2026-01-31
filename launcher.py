"""
CloudSim Launcher - Starts both backend and desktop app
Single executable that launches the complete CloudSim application
"""
import sys
import os
import subprocess
import time
import socket
from pathlib import Path
from threading import Thread


def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent
    return base_path / relative_path


def start_backend():
    """Start the backend server in a separate process"""
    print("Starting CloudSim Backend Server...")
    
    backend_dir = get_resource_path("backend")
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    
    # Start uvicorn server
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(backend_dir),
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    print("✓ Backend server starting on http://localhost:8000")
    
    # Wait for backend to be ready
    print("Waiting for backend to be ready...", end="", flush=True)
    for i in range(30):  # Wait up to 30 seconds
        if is_port_in_use(8000):
            print(" ✓ Ready!")
            return True
        print(".", end="", flush=True)
        time.sleep(1)
    
    print(" ✗ Failed to start!")
    return False


def start_desktop_app():
    """Start the desktop application"""
    print("\nStarting CloudSim Desktop Application...")
    
    desktop_dir = get_resource_path("desktop-app")
    main_file = desktop_dir / "main_simple.py"
    
    # Add desktop-app to path
    sys.path.insert(0, str(desktop_dir))
    
    # Import and run the desktop app
    os.chdir(str(desktop_dir))
    
    # Import main module
    import importlib.util
    spec = importlib.util.spec_from_file_location("main_simple", main_file)
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    
    # Run the main function
    main_module.main()


def main():
    """Main launcher function"""
    print("=" * 70)
    print(" CloudSim - Cloud Infrastructure Simulator")
    print(" Complete Standalone Package")
    print("=" * 70)
    print()
    
    # Check if backend is already running
    if is_port_in_use(8000):
        print("⚠ Backend already running on port 8000")
    else:
        # Start backend in background thread
        backend_thread = Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Wait for backend to be ready
        time.sleep(3)
        
        if not is_port_in_use(8000):
            print("\n✗ Failed to start backend server!")
            print("Please check if port 8000 is available.")
            input("\nPress Enter to exit...")
            sys.exit(1)
    
    # Start desktop application
    try:
        start_desktop_app()
    except Exception as e:
        print(f"\n✗ Error starting desktop app: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
