#!/usr/bin/env python3
"""
Installation script for Personal Expense Tracker
This script helps set up the application with all necessary dependencies.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["logs", "static/uploads"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")
    
    return True

def check_wkhtmltopdf():
    """Check if wkhtmltopdf is installed"""
    print("\n📄 Checking wkhtmltopdf installation...")
    
    try:
        result = subprocess.run("wkhtmltopdf --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ wkhtmltopdf is installed")
            return True
    except:
        pass
    
    print("❌ wkhtmltopdf is not installed")
    print("📋 Please install wkhtmltopdf:")
    
    system = platform.system().lower()
    if system == "windows":
        print("   - Download from: https://wkhtmltopdf.org/downloads.html")
        print("   - Or use chocolatey: choco install wkhtmltopdf")
    elif system == "darwin":  # macOS
        print("   - Use Homebrew: brew install wkhtmltopdf")
    elif system == "linux":
        print("   - Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
        print("   - CentOS/RHEL: sudo yum install wkhtmltopdf")
    
    return False

def create_env_file():
    """Create .env file with default configuration"""
    print("\n⚙️ Creating environment configuration...")
    
    env_content = """# Personal Expense Tracker Configuration
# Flask Configuration
SECRET_KEY=your-secure-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///expense.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/expense_tracker.log
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
    else:
        print("📁 .env file already exists")
    
    return True

def main():
    """Main installation process"""
    print("🚀 Personal Expense Tracker Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Check wkhtmltopdf
    wkhtmltopdf_installed = check_wkhtmltopdf()
    
    # Create environment file
    create_env_file()
    
    print("\n" + "=" * 50)
    print("🎉 Installation completed!")
    print("\n📋 Next steps:")
    print("1. Install wkhtmltopdf if not already installed (see instructions above)")
    print("2. Run the application: python app.py")
    print("3. Open your browser and go to: http://localhost:5000")
    print("4. Register a new account and start tracking expenses!")
    
    if not wkhtmltopdf_installed:
        print("\n⚠️  Note: PDF export will not work until wkhtmltopdf is installed")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
