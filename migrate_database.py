#!/usr/bin/env python3
"""
Safe Database Migration Script for Personal Expense Tracker

This script provides safe database migration capabilities that preserve user data.
Use this instead of the automatic migration in app.py for production environments.

Usage:
    python migrate_database.py --backup    # Create backup before migration
    python migrate_database.py --migrate   # Run migration
    python migrate_database.py --restore   # Restore from backup
    python migrate_database.py --status    # Check database status
"""

import os
import sys
import json
import argparse
from datetime import datetime
from app import app, db, User, Expense, Budget, Category, AdminLog
from sqlalchemy import inspect, text

def create_backup():
    """Create a complete backup of all database data"""
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'users': [],
        'expenses': [],
        'budgets': [],
        'categories': [],
        'admin_logs': []
    }
    
    try:
        with app.app_context():
            # Backup users
            users = User.query.all()
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password': user.password,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_active': user.is_active,
                    'role': user.role,
                    'last_admin_action': user.last_admin_action.isoformat() if user.last_admin_action else None
                }
                backup_data['users'].append(user_data)
            
            # Backup expenses
            expenses = Expense.query.all()
            for expense in expenses:
                expense_data = {
                    'id': expense.id,
                    'user_id': expense.user_id,
                    'title': expense.title,
                    'amount': expense.amount,
                    'date': expense.date.isoformat(),
                    'category': expense.category,
                    'description': expense.description,
                    'payment_method': expense.payment_method,
                    'created_at': expense.created_at.isoformat() if expense.created_at else None,
                    'updated_at': expense.updated_at.isoformat() if expense.updated_at else None
                }
                backup_data['expenses'].append(expense_data)
            
            # Backup budgets
            budgets = Budget.query.all()
            for budget in budgets:
                budget_data = {
                    'id': budget.id,
                    'user_id': budget.user_id,
                    'amount': budget.amount,
                    'start_date': budget.start_date.isoformat() if budget.start_date else None,
                    'end_date': budget.end_date.isoformat() if budget.end_date else None,
                    'created_at': budget.created_at.isoformat() if budget.created_at else None,
                    'updated_at': budget.updated_at.isoformat() if budget.updated_at else None
                }
                backup_data['budgets'].append(budget_data)
            
            # Backup categories
            categories = Category.query.all()
            for category in categories:
                category_data = {
                    'id': category.id,
                    'user_id': category.user_id,
                    'name': category.name,
                    'color': category.color,
                    'icon': category.icon,
                    'created_at': category.created_at.isoformat() if category.created_at else None
                }
                backup_data['categories'].append(category_data)
            
            # Backup admin logs
            admin_logs = AdminLog.query.all()
            for log in admin_logs:
                log_data = {
                    'id': log.id,
                    'admin_id': log.admin_id,
                    'action': log.action,
                    'target_user_id': log.target_user_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                backup_data['admin_logs'].append(log_data)
            
            # Save backup to file
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup created successfully: {backup_filename}")
            print(f"   Users: {len(backup_data['users'])}")
            print(f"   Expenses: {len(backup_data['expenses'])}")
            print(f"   Budgets: {len(backup_data['budgets'])}")
            print(f"   Categories: {len(backup_data['categories'])}")
            print(f"   Admin Logs: {len(backup_data['admin_logs'])}")
            
            return backup_filename
            
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return None

def restore_backup(backup_filename):
    """Restore database from backup file"""
    try:
        with open(backup_filename, 'r') as f:
            backup_data = json.load(f)
        
        with app.app_context():
            # Clear existing data
            db.drop_all()
            db.create_all()
            
            # Restore users
            for user_data in backup_data['users']:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    created_at=datetime.fromisoformat(user_data['created_at']) if user_data['created_at'] else None,
                    last_login=datetime.fromisoformat(user_data['last_login']) if user_data['last_login'] else None,
                    is_active=user_data['is_active'],
                    role=user_data['role'],
                    last_admin_action=datetime.fromisoformat(user_data['last_admin_action']) if user_data['last_admin_action'] else None
                )
                db.session.add(user)
            
            # Restore expenses
            for expense_data in backup_data['expenses']:
                expense = Expense(
                    id=expense_data['id'],
                    user_id=expense_data['user_id'],
                    title=expense_data['title'],
                    amount=expense_data['amount'],
                    date=datetime.fromisoformat(expense_data['date']).date(),
                    category=expense_data['category'],
                    description=expense_data['description'],
                    payment_method=expense_data['payment_method'],
                    created_at=datetime.fromisoformat(expense_data['created_at']) if expense_data['created_at'] else None,
                    updated_at=datetime.fromisoformat(expense_data['updated_at']) if expense_data['updated_at'] else None
                )
                db.session.add(expense)
            
            # Restore budgets
            for budget_data in backup_data['budgets']:
                budget = Budget(
                    id=budget_data['id'],
                    user_id=budget_data['user_id'],
                    amount=budget_data['amount'],
                    start_date=datetime.fromisoformat(budget_data['start_date']).date() if budget_data['start_date'] else None,
                    end_date=datetime.fromisoformat(budget_data['end_date']).date() if budget_data['end_date'] else None,
                    created_at=datetime.fromisoformat(budget_data['created_at']) if budget_data['created_at'] else None,
                    updated_at=datetime.fromisoformat(budget_data['updated_at']) if budget_data['updated_at'] else None
                )
                db.session.add(budget)
            
            # Restore categories
            for category_data in backup_data['categories']:
                category = Category(
                    id=category_data['id'],
                    user_id=category_data['user_id'],
                    name=category_data['name'],
                    color=category_data['color'],
                    icon=category_data['icon'],
                    created_at=datetime.fromisoformat(category_data['created_at']) if category_data['created_at'] else None
                )
                db.session.add(category)
            
            # Restore admin logs
            for log_data in backup_data['admin_logs']:
                log = AdminLog(
                    id=log_data['id'],
                    admin_id=log_data['admin_id'],
                    action=log_data['action'],
                    target_user_id=log_data['target_user_id'],
                    details=log_data['details'],
                    ip_address=log_data['ip_address'],
                    created_at=datetime.fromisoformat(log_data['created_at']) if log_data['created_at'] else None
                )
                db.session.add(log)
            
            db.session.commit()
            
            print(f"✅ Database restored successfully from {backup_filename}")
            print(f"   Users: {len(backup_data['users'])}")
            print(f"   Expenses: {len(backup_data['expenses'])}")
            print(f"   Budgets: {len(backup_data['budgets'])}")
            print(f"   Categories: {len(backup_data['categories'])}")
            print(f"   Admin Logs: {len(backup_data['admin_logs'])}")
            
    except Exception as e:
        print(f"❌ Error restoring backup: {str(e)}")
        db.session.rollback()

def check_database_status():
    """Check the current status of the database"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("=" * 60)
            print("DATABASE STATUS")
            print("=" * 60)
            
            if 'user' in tables:
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                print(f"✅ User table exists with {len(user_columns)} columns")
                print(f"   Columns: {', '.join(user_columns)}")
                
                # Check for required columns
                required_columns = ['created_at', 'last_login', 'is_active', 'role']
                missing_columns = [col for col in required_columns if col not in user_columns]
                
                if missing_columns:
                    print(f"⚠️  Missing required columns: {', '.join(missing_columns)}")
                else:
                    print("✅ All required columns present")
                
                # Count records
                user_count = User.query.count()
                expense_count = Expense.query.count()
                budget_count = Budget.query.count()
                category_count = Category.query.count()
                admin_log_count = AdminLog.query.count()
                
                print(f"\nRecord counts:")
                print(f"   Users: {user_count}")
                print(f"   Expenses: {expense_count}")
                print(f"   Budgets: {budget_count}")
                print(f"   Categories: {category_count}")
                print(f"   Admin Logs: {admin_log_count}")
                
            else:
                print("❌ User table does not exist")
            
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error checking database status: {str(e)}")

def run_migration():
    """Run the safe database migration"""
    try:
        with app.app_context():
            from app import init_database
            print("🔄 Running safe database migration...")
            init_database()
            print("✅ Migration completed successfully")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Safe Database Migration Tool')
    parser.add_argument('--backup', action='store_true', help='Create database backup')
    parser.add_argument('--migrate', action='store_true', help='Run database migration')
    parser.add_argument('--restore', type=str, help='Restore from backup file')
    parser.add_argument('--status', action='store_true', help='Check database status')
    
    args = parser.parse_args()
    
    if args.backup:
        create_backup()
    elif args.migrate:
        run_migration()
    elif args.restore:
        restore_backup(args.restore)
    elif args.status:
        check_database_status()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
