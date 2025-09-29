#!/usr/bin/env python3
"""
Installation script for Personal Expense Tracker
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'static/uploads', 'instance']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️  Directory already exists: {directory}")

def main():
    print("🚀 Personal Expense Tracker Installation")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if install_requirements():
        print("\n✅ Installation completed successfully!")
        print("\nTo run the application:")
        print("   python app.py")
    else:
        print("\n❌ Installation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
