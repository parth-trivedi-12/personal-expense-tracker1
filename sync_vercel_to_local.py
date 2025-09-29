"""
Script to sync Vercel users to local database
This will help you get all users from Vercel into your local database
"""

import sqlite3
import requests
import json
from datetime import datetime, timezone

def get_vercel_users():
    """Get users from Vercel deployment"""
    try:
        # Replace with your actual Vercel URL
        vercel_url = "https://personal-expense-tracker-demo.vercel.app"
        
        # Try to get users from Vercel
        response = requests.get(f"{vercel_url}/export-vercel-users", timeout=10)
        
        if response.status_code == 200:
            # Extract JSON data from the response
            content = response.text
            
            # Find the JSON data in the response
            start_marker = '<pre>'
            end_marker = '</pre>'
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker, start_idx)
            
            if start_idx != -1 and end_idx != -1:
                json_data = content[start_idx + len(start_marker):end_idx]
                users_data = json.loads(json_data)
                return users_data
            else:
                print("Could not find JSON data in response")
                return []
        else:
            print(f"Failed to get data from Vercel: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error getting Vercel users: {e}")
        return []

def sync_users_to_local(users_data):
    """Sync users to local database"""
    try:
        # Connect to local database
        conn = sqlite3.connect('expense.db')
        cursor = conn.cursor()
        
        print(f"Found {len(users_data)} users from Vercel")
        
        # Clear existing users (except admin)
        cursor.execute("DELETE FROM user WHERE role != 'admin'")
        print("Cleared existing non-admin users")
        
        # Add users from Vercel data
        added_count = 0
        for user_data in users_data:
            if user_data.get('role') != 'admin':  # Skip admin as it already exists
                try:
                    cursor.execute("""
                        INSERT INTO user (username, email, password, role, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_data['username'],
                        user_data['email'],
                        user_data['password'],
                        user_data['role'],
                        user_data['is_active'],
                        user_data.get('created_at', datetime.now(timezone.utc).isoformat())
                    ))
                    added_count += 1
                    print(f"Added user: {user_data['username']} ({user_data['email']})")
                except Exception as e:
                    print(f"Error adding user {user_data['username']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully synced {added_count} users to local database!")
        return True
        
    except Exception as e:
        print(f"Error syncing to local database: {e}")
        return False

def check_local_database():
    """Check current local database users"""
    try:
        conn = sqlite3.connect('expense.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, email, role, is_active FROM user")
        users = cursor.fetchall()
        
        print(f"\nLocal database has {user_count} users:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}, Active: {user[4]}")
        
        conn.close()
        return user_count
        
    except Exception as e:
        print(f"Error checking local database: {e}")
        return 0

def main():
    """Main function to sync Vercel users to local database"""
    print("🔄 Syncing Vercel Users to Local Database")
    print("=" * 50)
    
    # Check current local database
    print("1. Checking local database...")
    local_count = check_local_database()
    
    # Get users from Vercel
    print("\n2. Getting users from Vercel...")
    vercel_users = get_vercel_users()
    
    if not vercel_users:
        print("❌ No users found from Vercel. Make sure your Vercel deployment is running.")
        return
    
    # Sync users to local
    print("\n3. Syncing users to local database...")
    if sync_users_to_local(vercel_users):
        print("\n✅ Sync completed successfully!")
        
        # Check final state
        print("\n4. Final database state:")
        check_local_database()
    else:
        print("\n❌ Sync failed!")

if __name__ == "__main__":
    main()
