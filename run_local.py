#!/usr/bin/env python3
"""
Local runner for Personal Expense Tracker
This script ensures the app runs locally without SSL issues
"""

import os
import sys
from app import app, db

def init_local_database():
    """Initialize local database"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if admin user exists
            from app import User
            admin = User.query.filter_by(email="admin@expensetracker.com").first()
            
            if not admin:
                # Create admin user
                from werkzeug.security import generate_password_hash
                admin = User(
                    username="admin",
                    email="admin@expensetracker.com",
                    password=generate_password_hash("admin123"),
                    role="admin",
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created: admin@expensetracker.com / admin123")
            else:
                print("✅ Admin user already exists")
                
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Personal Expense Tracker locally...")
    
    # Initialize database
    init_local_database()
    
    # Run the app
    print("🌐 App running at: http://localhost:5000")
    print("👤 Admin login: admin@expensetracker.com / admin123")
    print("🛑 Press Ctrl+C to stop")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        ssl_context=None  # Disable SSL for local development
    )
