"""
Script to create admin user in Vercel production database
Run this script in your Vercel environment or locally with Vercel database connection
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Initialize Flask app for Vercel
app = Flask(__name__)

# Vercel database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///expense.db')

# Handle Vercel PostgreSQL URL format
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define models (must match your app.py)
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

def create_admin_user():
    """Create admin user in Vercel database"""
    with app.app_context():
        try:
            # Check if admin already exists
            admin_email = "admin@expensetracker.com"
            existing_admin = User.query.filter_by(email=admin_email).first()
            
            if existing_admin:
                print(f"✅ Admin user already exists: {existing_admin.username} ({existing_admin.email})")
                print(f"   Role: {existing_admin.role}, Active: {existing_admin.is_active}")
                
                # Update password to ensure it's correct
                existing_admin.password = generate_password_hash("admin123")
                existing_admin.is_active = True
                existing_admin.role = "admin"
                db.session.commit()
                print("✅ Admin password updated successfully!")
                
            else:
                # Create new admin user
                admin_password = "admin123"
                hashed_password = generate_password_hash(admin_password)
                
                admin_user = User(
                    username="admin",
                    email=admin_email,
                    password=hashed_password,
                    role="admin",
                    is_active=True
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Admin user created successfully!")
                print(f"   Email: {admin_email}")
                print(f"   Password: {admin_password}")
                print(f"   Username: admin")
            
            # Verify admin user
            admin = User.query.filter_by(email=admin_email).first()
            if admin:
                print(f"\n🔍 Verification:")
                print(f"   ID: {admin.id}")
                print(f"   Username: {admin.username}")
                print(f"   Email: {admin.email}")
                print(f"   Role: {admin.role}")
                print(f"   Active: {admin.is_active}")
                print(f"   Created: {admin.created_at}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Setting up admin user for Vercel deployment...")
    print("=" * 50)
    
    if create_admin_user():
        print("\n✅ Admin setup completed successfully!")
        print("\n🔑 Admin Login Credentials:")
        print("   Email: admin@expensetracker.com")
        print("   Password: admin123")
        print("\n🌐 You can now login to your Vercel deployment!")
    else:
        print("\n❌ Admin setup failed!")
        print("Please check your Vercel database connection and try again.")
