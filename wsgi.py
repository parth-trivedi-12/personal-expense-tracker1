"""
WSGI entry point for Vercel deployment
"""
import os
import sys
from app import app, init_database

# Initialize database when the app starts
init_database()

# This is the WSGI application that Vercel will use
application = app

if __name__ == "__main__":
    # This is for local development only
    app.run(debug=True, port=5001)
