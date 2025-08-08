#!/usr/bin/env python3
"""
Launcher script for the YouTube Video Analyzer Streamlit UI
"""

import subprocess
import sys
import os
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import plotly
        import pandas
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False


def main():
    """Main launcher function."""
    print("🎬 YouTube Video Analyzer - Starting Web UI")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("streamlit_ui.py"):
        print("❌ Error: streamlit_ui.py not found")
        print("Please run this script from the project directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not found in environment")
        print("You can set it in the UI or run: export OPENAI_API_KEY='your-key-here'")
        print()
    
    print("✅ Dependencies check passed")
    print("🚀 Starting Streamlit UI...")
    print("📱 The web interface will open automatically")
    print("🔗 If it doesn't open, go to: http://localhost:8501")
    print()
    print("📋 Quick start:")
    print("1. Enter your OpenAI API key in the sidebar")
    print("2. Add YouTube URLs in the main area")
    print("3. Adjust settings if needed")
    print("4. Click 'Start Analysis'")
    print()
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_ui.py",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down UI server...")
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()