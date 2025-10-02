#!/usr/bin/env python3
"""
Deploy script for Vercel
"""

import subprocess
import sys
import os

def deploy_to_vercel():
    """Deploy the application to Vercel"""
    print("🚀 Deploying to Vercel...")
    
    try:
        # Check if vercel CLI is installed
        result = subprocess.run(['vercel', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Vercel CLI not found. Please install it first:")
            print("   npm install -g vercel")
            return False
        
        # Deploy to Vercel
        print("📦 Building and deploying...")
        result = subprocess.run(['vercel', '--prod'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Deployment successful!")
            print("🌐 Your app is now live on Vercel")
            print("\n📋 Next steps:")
            print("1. Test the health endpoint: https://your-app.vercel.app/health")
            print("2. Test registration: https://your-app.vercel.app/register")
            print("3. Test admin login: admin@expensetracker.com / admin123")
            return True
        else:
            print("❌ Deployment failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return False

if __name__ == "__main__":
    success = deploy_to_vercel()
    sys.exit(0 if success else 1)
