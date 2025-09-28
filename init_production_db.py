#!/usr/bin/env python3
"""
Script to initialize the production database
Run this after setting up your PostgreSQL database
"""

import os
import sys
from app import app, init_database

def main():
    """Initialize the production database"""
    print("🚀 Initializing production database...")
    
    # Set environment variables for production
    os.environ['VERCEL'] = '1'
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        with app.app_context():
            init_database()
            print("✅ Database initialized successfully!")
            print("📝 Default admin credentials:")
            print("   Email: admin@expensetracker.com")
            print("   Password: admin123")
            print("   ⚠️  Please change the admin password after first login!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
