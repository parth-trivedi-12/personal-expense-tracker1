#!/usr/bin/env python3
"""
Deployment check script
"""

import requests
import sys
import time

def check_application_health(url="http://localhost:5001"):
    """Check if the application is running and healthy"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Application is running and healthy")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Application is not accessible: {e}")
        return False

def check_database():
    """Check database connectivity"""
    try:
        from app import db, User
        with app.app_context():
            user_count = User.query.count()
            print(f"✅ Database connected. Users: {user_count}")
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    print("🔍 Checking application deployment...")
    print("=" * 40)
    
    # Check application
    app_healthy = check_application_health()
    
    # Check database
    db_healthy = check_database()
    
    if app_healthy and db_healthy:
        print("\n✅ All checks passed! Application is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
