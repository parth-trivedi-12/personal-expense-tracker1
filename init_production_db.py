#!/usr/bin/env python3
"""
Production database initialization script
"""

from app import app, db, User, create_admin_user
from werkzeug.security import generate_password_hash

def init_production_database():
    """Initialize database for production"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin user
            create_admin_user()
            
            print("✅ Production database initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_production_database()
