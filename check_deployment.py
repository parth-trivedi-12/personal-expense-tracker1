#!/usr/bin/env python3
"""
Script to check if the deployment is working correctly
"""

import requests
import sys
import os

def check_deployment(url):
    """Check if the deployment is working"""
    print(f"🔍 Checking deployment at: {url}")
    
    try:
        # Test main page
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page returned status code: {response.status_code}")
            return False
            
        # Test static files
        static_url = f"{url}/static/css/style.css"
        static_response = requests.get(static_url, timeout=10)
        if static_response.status_code == 200:
            print("✅ Static files are loading correctly")
        else:
            print(f"❌ Static files returned status code: {static_response.status_code}")
            
        # Test login page
        login_url = f"{url}/login"
        login_response = requests.get(login_url, timeout=10)
        if login_response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page returned status code: {login_response.status_code}")
            
        print("🎉 Deployment check completed!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking deployment: {str(e)}")
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python check_deployment.py <your-vercel-url>")
        print("Example: python check_deployment.py https://your-app.vercel.app")
        sys.exit(1)
        
    url = sys.argv[1]
    if not url.startswith('http'):
        url = f"https://{url}"
        
    success = check_deployment(url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
