"""
Script to run Chainlit frontend

Usage:
    python run_chainlit.py
"""

import os
import subprocess
import sys

# Set environment variables
os.environ.setdefault('CHAINLIT_HOST', '0.0.0.0')
os.environ.setdefault('CHAINLIT_PORT', '8001')

if __name__ == "__main__":
    print("=" * 60)
    print("Starting SHL Assessment Recommendation System - Chainlit UI")
    print("=" * 60)
    print(f"Host: {os.environ.get('CHAINLIT_HOST', '0.0.0.0')}")
    print(f"Port: {os.environ.get('CHAINLIT_PORT', '8001')}")
    print("=" * 60)
    
    # Run chainlit
    try:
        subprocess.run([
            sys.executable, "-m", "chainlit", "run",
            "chainlit_app/app.py",
            "--host", os.environ.get('CHAINLIT_HOST', '0.0.0.0'),
            "--port", os.environ.get('CHAINLIT_PORT', '8001')
        ])
    except KeyboardInterrupt:
        print("\n\nShutting down Chainlit...")
        sys.exit(0)