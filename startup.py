"""
Startup script for SHL Assessment Recommendation System
Runs both FastAPI backend and Chainlit frontend in parallel
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path


def print_banner():
    """Print startup banner"""
    print("=" * 50)
    print("SHL Assessment Recommendation System")
    print("=" * 50)
    print()


def check_data_exists():
    """Check if required data files exist"""
    data_file = Path("data/shl_assessments.json")
    
    if not data_file.exists():
        print("⚠️  WARNING: Assessment data not found!")
        print("Please ensure data is initialized before deployment")
        return False
    
    return True


def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
        print("✓ Created logs directory")


def get_port(default_port, env_var="PORT"):
    """Get port from environment variable or use default"""
    return int(os.environ.get(env_var, default_port))


def start_fastapi():
    """Start FastAPI backend"""
    port = get_port(8000, "FASTAPI_PORT")
    print(f"🚀 Starting FastAPI backend on port {port}...")
    process = subprocess.Popen(
        [sys.executable, "run.py"],
        env={**os.environ, "PORT": str(port)}
    )
    
    return process


def start_chainlit():
    """Start Chainlit frontend"""
    port = get_port(8001, "CHAINLIT_PORT")
    print(f"🚀 Starting Chainlit frontend on port {port}...")
    
    # Start process without capturing output (logs go to stdout)
    process = subprocess.Popen(
        [sys.executable, "run_chainlit.py"],
        env={**os.environ, "PORT": str(port)}
    )
    
    return process


def print_success_message():
    """Print success message with URLs"""
    fastapi_port = get_port(8000, "FASTAPI_PORT")
    chainlit_port = get_port(8001, "CHAINLIT_PORT")
    
    print()
    print("=" * 50)
    print("✓ Services Started Successfully!")
    print("=" * 50)
    print()
    print(f"📡 FastAPI Backend:   http://0.0.0.0:{fastapi_port}")
    print(f"📚 API Docs:          http://0.0.0.0:{fastapi_port}/docs")
    print(f"🎨 Chainlit Frontend: http://0.0.0.0:{chainlit_port}")
    print()
    print("=" * 50)
    print()


def cleanup(fastapi_process, chainlit_process):
    """Clean up processes on shutdown"""
    print()
    print("=" * 50)
    print("Shutting down services...")
    print("=" * 50)
    
    try:
        fastapi_process.terminate()
        chainlit_process.terminate()
        
        # Wait for graceful shutdown
        fastapi_process.wait(timeout=5)
        chainlit_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Force kill if not terminated
        fastapi_process.kill()
        chainlit_process.kill()
    
    print("✓ Services stopped")
    print()


def main():
    """Main startup function"""
    print_banner()
    check_data_exists()
    create_logs_directory()
    
    print()
    print("Starting services...")
    print()
    
    fastapi_process = None
    chainlit_process = None
    
    try:
        # Start FastAPI
        fastapi_process = start_fastapi()
        
        # Wait a bit for FastAPI to initialize
        print("⏳ Waiting for FastAPI to initialize...")
        time.sleep(3)
        
        # Start Chainlit
        chainlit_process = start_chainlit()
        
        # Wait a bit for Chainlit to initialize
        print("⏳ Waiting for Chainlit to initialize...")
        time.sleep(2)
        
        # Print success message
        print_success_message()
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            cleanup(fastapi_process, chainlit_process)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep the script running and monitor processes
        while True:
            # Check if processes are still running
            if fastapi_process.poll() is not None:
                print("❌ FastAPI process died unexpectedly")
                if chainlit_process:
                    chainlit_process.terminate()
                sys.exit(1)
            
            if chainlit_process.poll() is not None:
                print("❌ Chainlit process died unexpectedly")
                if fastapi_process:
                    fastapi_process.terminate()
                sys.exit(1)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        if fastapi_process and chainlit_process:
            cleanup(fastapi_process, chainlit_process)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if fastapi_process:
            fastapi_process.terminate()
        if chainlit_process:
            chainlit_process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    main()