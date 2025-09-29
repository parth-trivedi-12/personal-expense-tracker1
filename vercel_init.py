"""
Vercel Database Initialization Script
Run this to set up your Vercel database with all tables and admin user
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Initialize Flask app for Vercel
app = Flask(__name__)

# Get database URL from environment (Vercel will provide this)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///expense.db')

# Handle Vercel PostgreSQL URL format
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define models (must match app.py exactly)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')
    last_admin_action = db.Column(db.DateTime)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    payment_method = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#3b82f6')
    icon = db.Column(db.String(20), default='📁')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_category'),)

class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

def initialize_vercel_database():
    """Initialize Vercel database with all tables and admin user"""
    with app.app_context():
        try:
            print("🚀 Initializing Vercel database...")
            print(f"Database URL: {database_url[:50]}...")
            
            # Create all tables
            print("🏗️  Creating all tables...")
            db.create_all()
            
            # Check if admin user exists
            admin_email = "admin@expensetracker.com"
            admin_user = User.query.filter_by(email=admin_email).first()
            
            if admin_user:
                print("✅ Admin user already exists, updating password...")
                admin_user.password = generate_password_hash("admin123")
                admin_user.is_active = True
                admin_user.role = "admin"
                db.session.commit()
                print("✅ Admin password updated!")
            else:
                print("👤 Creating admin user...")
                admin_user = User(
                    username="admin",
                    email=admin_email,
                    password=generate_password_hash("admin123"),
                    role="admin",
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created!")
            
            # Verify admin user
            admin = User.query.filter_by(email=admin_email).first()
            if admin:
                print(f"\n🔑 Admin credentials:")
                print(f"   Email: {admin.email}")
                print(f"   Password: admin123")
                print(f"   Username: {admin.username}")
                print(f"   Role: {admin.role}")
                print(f"   Active: {admin.is_active}")
            
            # Test user creation
            print("\n🧪 Testing user creation...")
            test_user = User(
                username="testuser",
                email="test@example.com",
                password=generate_password_hash("testpass"),
                role="user",
                is_active=True
            )
            db.session.add(test_user)
            db.session.commit()
            
            # Clean up test user
            db.session.delete(test_user)
            db.session.commit()
            print("✅ User creation test passed!")
            
            print("\n🎉 Vercel database initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    initialize_vercel_database()
