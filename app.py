from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import secrets
import logging
from logging.handlers import RotatingFileHandler
import re
from functools import wraps

app = Flask(__name__)

# Generate secure secret key
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24 hours session timeout
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS attacks
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Initialize CSRF protection
csrf = CSRFProtect(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration for different environments
database_url = os.environ.get('DATABASE_URL')
app.logger.info(f"DATABASE_URL: {database_url}")

if database_url:
    # Use provided DATABASE_URL (Supabase, Neon.tech, or other PostgreSQL)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if database_url.startswith('postgresql://') or database_url.startswith('postgresql+pg8000://'):
        # PostgreSQL configuration (Supabase, Neon.tech, etc.)
        # For pg8000 driver, we need to use ssl_context instead of sslmode parameter
        if database_url.startswith('postgresql+pg8000://'):
            # Convert to standard postgresql:// for pg8000 with SSL
            database_url = database_url.replace('postgresql+pg8000://', 'postgresql://', 1)
        
        # Add SSL requirement for cloud PostgreSQL providers
        # Check if sslmode is already present to avoid duplication
        if 'sslmode=' not in database_url:
            if '?' in database_url:
                # URL already has parameters, add sslmode
                database_url += '&sslmode=require'
            else:
                # URL has no parameters, add sslmode
                database_url += '?sslmode=require'
        
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.logger.info("✅ Using PostgreSQL database (Supabase/Neon.tech) with SSL")
    elif database_url.startswith('sqlite:///'):
        # SQLite configuration
        if database_url == 'sqlite:///expense.db' and os.environ.get('VERCEL'):
            # Use persistent SQLite file for Vercel (better than in-memory)
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join("/tmp", "expense.db")
            app.logger.info("✅ Using persistent SQLite database file on Vercel")
            app.logger.warning("⚠️  NOTE: File system is ephemeral on Vercel - data may be lost during deployments")
            app.logger.info("💡 RECOMMENDATION: For production, use PostgreSQL or cloud SQLite (Turso/LibSQL)")
        else:
            app.config["SQLALCHEMY_DATABASE_URI"] = database_url
            app.logger.info("✅ Using SQLite database")
    else:
        # Fallback to in-memory SQLite
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.logger.warning("⚠️  WARNING: Using in-memory SQLite database. Data will be lost between requests!")
else:
    # Local development environment - default to SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "expense.db")
    app.logger.info("✅ Using local SQLite database for development")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure logging
if not app.debug:
    if os.environ.get('VERCEL'):
        # In Vercel, use console logging only
        app.logger.setLevel(logging.INFO)
        app.logger.info('Expense Tracker startup on Vercel')
    else:
        # Local development - use file logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        try:
            file_handler = RotatingFileHandler('logs/expense_tracker.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Expense Tracker startup')
        except (PermissionError, OSError) as e:
            # If logging fails, just use console logging
            print(f"Warning: Could not set up file logging: {e}")
            app.logger.setLevel(logging.INFO)

# Input validation functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

def validate_amount(amount_str):
    """Validate and convert amount to float"""
    try:
        amount = float(amount_str)
        if amount < 0:
            return False, None, "Amount cannot be negative"
        if amount > 999999.99:
            return False, None, "Amount too large"
        return True, amount, "Valid amount"
    except ValueError:
        return False, None, "Invalid amount format"

def validate_date(date_str):
    """Validate date format"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date > datetime.now().date():
            return False, None, "Date cannot be in the future"
        return True, date, "Valid date"
    except ValueError:
        return False, None, "Invalid date format"

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        
        # Verify user still exists in database
        user = User.query.get(session["user_id"])
        if not user or not user.is_active:
            session.clear()
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        
        # Refresh session to prevent timeout during active use
        session.permanent = True
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        
        user = User.query.get(session["user_id"])
        if not user or not user.is_active:
            session.clear()
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        
        if user.role != 'admin':
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for("dashboard"))
        
        return f(*args, **kwargs)
    return decorated_function

def user_only(f):
    """Decorator to restrict access to regular users only (not admins)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        
        user = User.query.get(session["user_id"])
        if not user or not user.is_active:
            session.clear()
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        
        if user.role == 'admin':
            flash("Access denied. This page is for regular users only.", "danger")
            return redirect(url_for("admin_dashboard"))
        
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action, target_user_id=None, details=None):
    """Log admin actions"""
    if "user_id" in session:
        admin_log = AdminLog(
            admin_id=session["user_id"],
            action=action,
            target_user_id=target_user_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(admin_log)
        db.session.commit()

# ----------------- Models -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    last_admin_action = db.Column(db.DateTime)
    
    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')

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
    
    # Add constraints (commented out to avoid SQLite issues)
    # __table_args__ = (
    #     db.CheckConstraint('amount > 0', name='check_amount_positive'),
    #     db.CheckConstraint('length(title) > 0', name='check_title_not_empty'),
    # )

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Add constraints (commented out to avoid SQLite issues)
    # __table_args__ = (
    #     db.CheckConstraint('amount >= 0', name='check_budget_positive'),
    # )

class Category(db.Model):
    """User-defined expense categories"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#3b82f6')  # Hex color code
    icon = db.Column(db.String(20), default='📁')  # Emoji icon
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Ensure unique category names per user
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_category'),)

    def __repr__(self):
        return f"<Category {self.name}>"

class AdminLog(db.Model):
    """Track admin actions"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_actions')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='admin_targeted_actions')


# ----------------- Routes -----------------
@app.route("/")
def home():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user and user.role == 'admin':
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("dashboard"))
    return render_template("index.html", app=app)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            # Validate input
            if not username or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if len(username) < 3 or len(username) > 50:
                flash("Username must be between 3 and 50 characters.", "danger")
                return render_template("register.html")

            if not validate_email(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, "danger")
                return render_template("register.html")

            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                flash("Username or Email already exists.", "danger")
                return render_template("register.html")

            # Create new user
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            app.logger.info(f"New user registered: {username} ({email})")
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            
            # Provide more specific error messages
            error_message = str(e)
            if "UNIQUE constraint failed" in error_message:
                if "username" in error_message:
                    flash("Username already exists. Please choose a different username.", "danger")
                elif "email" in error_message:
                    flash("Email already exists. Please use a different email address.", "danger")
                else:
                    flash("Username or Email already exists. Please use different credentials.", "danger")
            elif "NOT NULL constraint failed" in error_message:
                flash("Please fill in all required fields.", "danger")
            else:
                flash(f"Registration failed: {error_message}", "danger")
            
            return render_template("register.html")
    
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        try:
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")

            if not validate_email(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("login.html")

            user = User.query.filter_by(email=email, is_active=True).first()
            
            if user and check_password_hash(user.password, password):
                # Update last login
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()
                
                # Set session
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = user.role
                session.permanent = True  # Make session permanent (24 hours)
                
                app.logger.info(f"User logged in: {user.username} ({email}) - Role: {user.role}")
                flash("Login successful!", "success")
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("dashboard"))
            else:
                app.logger.warning(f"Failed login attempt for email: {email}")
                flash("Invalid credentials. Try again.", "danger")
                return render_template("login.html")
                
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash("An error occurred during login. Please try again.", "danger")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user_id" in session:
        app.logger.info(f"User logged out: {session.get('username', 'Unknown')}")
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# ----------------- Dashboard -----------------
@app.route("/dashboard")
@user_only
def dashboard():
    user_id = session["user_id"]

    expenses = Expense.query.filter_by(user_id=user_id).all()
    total_expenses = sum([e.amount for e in expenses])
    budget = Budget.query.filter_by(user_id=user_id).first()
    budget_amount = budget.amount if budget else 0
    remaining = budget_amount - total_expenses
    overspending_alert = "No Alerts 🎉" if remaining>=0 else "Overspending! ⚠️"

    # Expenses by category
    categories = ["Food", "Travel", "Shopping", "Utilities", "Other"]
    expenses_by_category = {cat: 0 for cat in categories}
    for e in expenses:
        if e.category in expenses_by_category:
            expenses_by_category[e.category] += e.amount

    return render_template("dashboard.html",
                           name=session["username"],
                           total_expenses=total_expenses,
                           budget_amount=budget_amount,
                           remaining=remaining,
                           overspending_alert=overspending_alert,
                           expenses_by_category=expenses_by_category)

# ----------------- Expenses CRUD -----------------
@app.route("/expenses", methods=["GET", "POST"])
@user_only
def expenses():
    user_id = session["user_id"]

    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            amount_str = request.form.get("amount", "")
            date_str = request.form.get("date", "")
            category = request.form.get("category", "")
            description = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "")

            # Validate input
            if not title or not amount_str or not date_str or not category or not payment_method:
                flash("All required fields must be filled.", "danger")
                return redirect(url_for("expenses"))

            if len(title) > 200:
                flash("Title is too long (maximum 200 characters).", "danger")
                return redirect(url_for("expenses"))

            # Validate amount
            is_valid, amount, error_msg = validate_amount(amount_str)
            if not is_valid:
                flash(error_msg, "danger")
                return redirect(url_for("expenses"))

            # Validate date
            is_valid, date, error_msg = validate_date(date_str)
            if not is_valid:
                flash(error_msg, "danger")
                return redirect(url_for("expenses"))

            # Validate category - check if it exists in user's categories
            user_categories = [cat.name for cat in Category.query.filter_by(user_id=user_id).all()]
            if category not in user_categories:
                flash("Invalid category selected.", "danger")
                return redirect(url_for("expenses"))

            # Validate payment method
            valid_payment_methods = ["Cash", "Card", "UPI", "Other"]
            if payment_method not in valid_payment_methods:
                flash("Invalid payment method selected.", "danger")
                return redirect(url_for("expenses"))

            # Create expense
            new_expense = Expense(
                user_id=user_id,
                title=title,
                amount=amount,
                date=date,
                category=category,
                description=description,
                payment_method=payment_method
            )
            
            db.session.add(new_expense)
            db.session.commit()
            
            app.logger.info(f"Expense added by user {user_id}: {title} - ₹{amount}")
            flash("Expense added successfully!", "success")
            return redirect(url_for("expenses"))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding expense: {str(e)}")
            flash("An error occurred while adding the expense. Please try again.", "danger")
            return redirect(url_for("expenses"))

    # Get user's categories
    user_categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
    
    # If user has no categories, create default ones
    if not user_categories:
        default_categories = [
            {"name": "Food", "color": "#ef4444", "icon": "🍕"},
            {"name": "Travel", "color": "#3b82f6", "icon": "🚗"},
            {"name": "Shopping", "color": "#22c55e", "icon": "🛍️"},
            {"name": "Utilities", "color": "#f59e0b", "icon": "⚡"},
            {"name": "Other", "color": "#8b5cf6", "icon": "📁"}
        ]
        
        for cat_data in default_categories:
            category = Category(
                user_id=user_id,
                name=cat_data["name"],
                color=cat_data["color"],
                icon=cat_data["icon"]
            )
            db.session.add(category)
        
        db.session.commit()
        user_categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()

    filter_category = request.args.get("category", "All")
    search_term = request.args.get("search", "").strip()
    
    # Build query
    query = Expense.query.filter_by(user_id=user_id)
    
    # Apply category filter
    if filter_category != "All":
        query = query.filter(Expense.category == filter_category)
    
    # Apply search filter
    if search_term:
        query = query.filter(
            db.or_(
                Expense.title.ilike(f"%{search_term}%"),
                Expense.description.ilike(f"%{search_term}%"),
                Expense.category.ilike(f"%{search_term}%")
            )
        )
    
    user_expenses = query.order_by(Expense.date.desc()).all()

    # Calculate expenses by category
    expenses_by_category = {}
    for category in user_categories:
        expenses_by_category[category.name] = 0
    
    for e in Expense.query.filter_by(user_id=user_id).all():
        if e.category in expenses_by_category:
            expenses_by_category[e.category] += e.amount

    return render_template(
        "expense.html",
        expenses=user_expenses,
        selected_category=filter_category,
        search_term=search_term,
        expenses_by_category=expenses_by_category,
        user_categories=user_categories
    )

@app.route("/expenses/view/<int:id>")
@user_only
def view_expense(id):
    expense = Expense.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()
    return render_template("view_expense.html", expense=expense)

@app.route("/expenses/edit/<int:id>", methods=["GET","POST"])
@user_only
def edit_expense(id):
    expense = Expense.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()
    user_id = session["user_id"]

    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            amount_str = request.form.get("amount", "")
            date_str = request.form.get("date", "")
            category = request.form.get("category", "")
            description = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "")

            # Get user's categories
            user_categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
            
            # Validate input
            if not title or not amount_str or not date_str or not category or not payment_method:
                flash("All required fields must be filled.", "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            if len(title) > 200:
                flash("Title is too long (maximum 200 characters).", "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            # Validate amount
            is_valid, amount, error_msg = validate_amount(amount_str)
            if not is_valid:
                flash(error_msg, "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            # Validate date
            is_valid, date, error_msg = validate_date(date_str)
            if not is_valid:
                flash(error_msg, "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            # Validate category
            valid_categories = ["Food", "Travel", "Shopping", "Utilities", "Other"]
            if category not in valid_categories:
                flash("Invalid category selected.", "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            # Validate payment method
            valid_payment_methods = ["Cash", "Card", "UPI", "Other"]
            if payment_method not in valid_payment_methods:
                flash("Invalid payment method selected.", "danger")
                return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

            # Update expense
            expense.title = title
            expense.amount = amount
            expense.date = date
            expense.category = category
            expense.description = description
            expense.payment_method = payment_method
            expense.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            app.logger.info(f"Expense updated by user {session['user_id']}: {title} - ₹{amount}")
            flash("Expense updated successfully!", "success")
            return redirect(url_for("expenses"))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating expense: {str(e)}")
            flash("An error occurred while updating the expense. Please try again.", "danger")
            # Get user's categories for error case
            user_categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
            return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

    # Get user's categories for GET request
    user_categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
    return render_template("edit_expense.html", expense=expense, user_categories=user_categories)

@app.route("/expenses/delete/<int:id>", methods=["POST"])
@user_only
def delete_expense(id):
    try:
        expense = Expense.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()
        title = expense.title
        amount = expense.amount
        
        db.session.delete(expense)
        db.session.commit()
        
        app.logger.info(f"Expense deleted by user {session['user_id']}: {title} - ₹{amount}")
        flash("Expense deleted successfully!", "success")
        return redirect(url_for("expenses"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting expense: {str(e)}")
        flash("An error occurred while deleting the expense. Please try again.", "danger")
        return redirect(url_for("expenses"))

# ----------------- Category Management -----------------
@app.route("/categories", methods=["GET", "POST"])
@user_only
def categories():
    user_id = session["user_id"]
    
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            color = request.form.get("color", "#3b82f6")
            icon = request.form.get("icon", "📁")
            
            if not name:
                flash("Category name is required.", "danger")
                return redirect(url_for("categories"))
            
            if len(name) > 50:
                flash("Category name is too long (maximum 50 characters).", "danger")
                return redirect(url_for("categories"))
            
            # Check if category already exists
            existing_category = Category.query.filter_by(user_id=user_id, name=name).first()
            if existing_category:
                flash("Category already exists.", "danger")
                return redirect(url_for("categories"))
            
            category = Category(
                user_id=user_id,
                name=name,
                color=color,
                icon=icon
            )
            
            db.session.add(category)
            db.session.commit()
            
            app.logger.info(f"Category '{name}' created by user {user_id}")
            flash("Category created successfully!", "success")
            return redirect(url_for("categories"))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating category: {str(e)}")
            flash("An error occurred while creating the category. Please try again.", "danger")
            return redirect(url_for("categories"))
    
    # Get user's categories
    categories = Category.query.filter_by(user_id=user_id).order_by(Category.name).all()
    return render_template("categories.html", categories=categories)

@app.route("/categories/delete/<int:id>", methods=["POST"])
@user_only
def delete_category(id):
    try:
        category = Category.query.filter_by(id=id, user_id=session["user_id"]).first_or_404()
        name = category.name
        
        # Check if category is being used by any expenses
        expense_count = Expense.query.filter_by(user_id=session["user_id"], category=name).count()
        if expense_count > 0:
            flash(f"Cannot delete category '{name}' because it has {expense_count} expense(s). Please reassign or delete those expenses first.", "danger")
            return redirect(url_for("categories"))
        
        db.session.delete(category)
        db.session.commit()
        
        app.logger.info(f"Category '{name}' deleted by user {session['user_id']}")
        flash("Category deleted successfully!", "success")
        return redirect(url_for("categories"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting category: {str(e)}")
        flash("An error occurred while deleting the category. Please try again.", "danger")
        return redirect(url_for("categories"))

# ----------------- Budget -----------------
@app.route("/budget", methods=["GET","POST"])
@user_only
def budget():
    user_id = session["user_id"]
    budget = Budget.query.filter_by(user_id=user_id).first()
    
    # Calculate current month expenses
    current_month = datetime.now().replace(day=1)
    expenses = Expense.query.filter_by(user_id=user_id).filter(
        Expense.date >= current_month
    ).all()
    total_expenses = sum([e.amount for e in expenses])
    
    budget_amount = budget.amount if budget else 0
    remaining = budget_amount - total_expenses
    
    if request.method == "POST":
        try:
            amount_str = request.form.get("budget", "")
            
            if not amount_str:
                flash("Budget amount is required.", "danger")
                return render_template("budget.html", 
                                     budget=budget_amount, 
                                     total_expenses=total_expenses, 
                                     remaining=remaining)
            
            # Validate amount
            is_valid, amount, error_msg = validate_amount(amount_str)
            if not is_valid:
                flash(error_msg, "danger")
                return render_template("budget.html", 
                                     budget=budget_amount, 
                                     total_expenses=total_expenses, 
                                     remaining=remaining)
            
            if not budget:
                budget = Budget(user_id=user_id, amount=amount)
                db.session.add(budget)
            else:
                budget.amount = amount
                budget.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            app.logger.info(f"Budget updated by user {user_id}: ₹{amount}")
            flash("Budget updated successfully!", "success")
            return redirect(url_for("budget"))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating budget: {str(e)}")
            flash("An error occurred while updating the budget. Please try again.", "danger")
            return render_template("budget.html", 
                                 budget=budget_amount, 
                                 total_expenses=total_expenses, 
                                 remaining=remaining)
    
    return render_template("budget.html", 
                         budget=budget_amount, 
                         total_expenses=total_expenses, 
                         remaining=remaining)

# ----------------- Reports -----------------
@app.route("/reports")
@user_only
def reports():
    user_id = session["user_id"]
    
    try:
        expenses = Expense.query.filter_by(user_id=user_id).all()
        total_expenses = sum([e.amount for e in expenses])
        budget = Budget.query.filter_by(user_id=user_id).first()
        budget_amount = budget.amount if budget else 0
        remaining = budget_amount - total_expenses
        
        # Calculate expenses by category
        categories = ["Food", "Travel", "Shopping", "Utilities", "Other"]
        expenses_by_category = {cat: 0 for cat in categories}
        for e in expenses:
            if e.category in expenses_by_category:
                expenses_by_category[e.category] += e.amount
        
        return render_template("reports.html", 
                             total_expenses=total_expenses,
                             budget_amount=budget_amount, 
                             remaining=remaining,
                             expenses_by_category=expenses_by_category)
                             
    except Exception as e:
        app.logger.error(f"Error generating reports: {str(e)}")
        flash("An error occurred while generating reports. Please try again.", "danger")
        return redirect(url_for("dashboard"))

# ----------------- Export CSV -----------------
@app.route("/export/csv")
@user_only
def export_csv():
    try:
        user_id = session["user_id"]
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()

        def generate():
            yield "Title,Amount,Date,Category,Payment Method,Description,Created At\n"
            for e in expenses:
                yield f'"{e.title}",{e.amount},{e.date},{e.category},{e.payment_method},"{e.description}",{e.created_at}\n'

        app.logger.info(f"CSV export requested by user {user_id}")
        return Response(generate(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=expenses.csv"})
                        
    except Exception as e:
        app.logger.error(f"Error exporting CSV: {str(e)}")
        flash("An error occurred while exporting data. Please try again.", "danger")
        return redirect(url_for("reports"))

# ----------------- Export PDF -----------------
@app.route("/export/pdf")
@user_only
def export_pdf():
    try:
        user_id = session["user_id"]
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
        
        # Calculate summary data
        total_expenses = sum([e.amount for e in expenses])
        budget = Budget.query.filter_by(user_id=user_id).first()
        budget_amount = budget.amount if budget else 0
        remaining = budget_amount - total_expenses
        
        # Calculate expenses by category
        categories = ["Food", "Travel", "Shopping", "Utilities", "Other"]
        expenses_by_category = {cat: 0 for cat in categories}
        for e in expenses:
            if e.category in expenses_by_category:
                expenses_by_category[e.category] += e.amount
        
        # Create PDF using reportlab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Expense Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Financial Summary", heading_style))
        
        # Summary data
        summary_data = [
            ["Total Expenses", f"₹{total_expenses:.2f}"],
            ["Budget Amount", f"₹{budget_amount:.2f}"],
            ["Remaining", f"₹{remaining:.2f}"],
            ["Budget Utilization", f"{(total_expenses/budget_amount*100):.1f}%" if budget_amount > 0 else "N/A"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Category breakdown
        story.append(Paragraph("Expenses by Category", heading_style))
        
        category_data = [["Category", "Amount (₹)", "Percentage"]]
        for category, amount in expenses_by_category.items():
            if amount > 0:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                category_data.append([category, f"₹{amount:.2f}", f"{percentage:.1f}%"])
        
        if len(category_data) > 1:
            category_table = Table(category_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(category_table)
        else:
            story.append(Paragraph("No expenses found in any category.", summary_style))
        
        story.append(Spacer(1, 20))
        
        # Detailed expenses table
        story.append(Paragraph("Detailed Expenses", heading_style))
        
        if expenses:
            # Prepare table data
            table_data = [["Title", "Amount (₹)", "Date", "Category", "Description"]]
            
            for expense in expenses:
                # Truncate description if too long
                description = expense.description[:50] + "..." if len(expense.description) > 50 else expense.description
                table_data.append([
                    expense.title,
                    f"₹{expense.amount:.2f}",
                    expense.date.strftime("%Y-%m-%d"),
                    expense.category,
                    description
                ])
            
            # Create table
            expenses_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 2*inch])
            expenses_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(expenses_table)
        else:
            story.append(Paragraph("No expenses found.", summary_style))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_content)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        app.logger.info(f"PDF export completed successfully for user {user_id}")
        return response
        
    except Exception as e:
        app.logger.error(f"Error in PDF export: {str(e)}")
        flash("An error occurred while generating the PDF report.", "danger")
        return redirect(url_for("reports"))

# ----------------- New Advanced Features -----------------


# User Profile
@app.route("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    try:
        user = User.query.get(session["user_id"])
        new_username = request.form.get("username", "").strip()
        new_email = request.form.get("email", "").strip()
        
        if not new_username or not new_email:
            flash("All fields are required.", "danger")
            return redirect(url_for("profile"))
        
        if not validate_email(new_email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("profile"))
        
        # Check if email/username already exists (excluding current user)
        existing_user = User.query.filter(
            (User.username == new_username) | (User.email == new_email)
        ).filter(User.id != user.id).first()
        
        if existing_user:
            flash("Username or Email already exists.", "danger")
            return redirect(url_for("profile"))
        
        user.username = new_username
        user.email = new_email
        db.session.commit()
        
        session["username"] = new_username
        app.logger.info(f"Profile updated by user {user.id}")
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating profile: {str(e)}")
        flash("An error occurred while updating profile. Please try again.", "danger")
        return redirect(url_for("profile"))

@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    try:
        user = User.query.get(session["user_id"])
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("profile"))
        
        # Verify current password
        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("profile"))
        
        # Validate new password
        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "danger")
            return redirect(url_for("profile"))
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("profile"))
        
        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        # Clear session for security - user must login again
        session.clear()
        
        app.logger.info(f"Password changed by user {user.id} - session cleared")
        flash("Password changed successfully! Please login again.", "success")
        return redirect(url_for("login"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error changing password: {str(e)}")
        flash("An error occurred while changing password. Please try again.", "danger")
        return redirect(url_for("profile"))

@app.route("/profile/delete-account", methods=["POST"])
@login_required
def delete_account():
    try:
        user = User.query.get(session["user_id"])
        confirm_text = request.form.get("confirm_text", "").strip()
        password = request.form.get("password", "").strip()
        
        if confirm_text != "DELETE":
            flash("Please type 'DELETE' to confirm account deletion.", "danger")
            return redirect(url_for("profile"))
        
        if not password:
            flash("Please enter your password to confirm account deletion.", "danger")
            return redirect(url_for("profile"))
        
        # Verify password
        if not check_password_hash(user.password, password):
            flash("Incorrect password. Account deletion cancelled.", "danger")
            return redirect(url_for("profile"))
        
        # Delete all user data
        user_id = user.id
        username = user.username
        email = user.email
        
        # Get counts for logging
        expense_count = Expense.query.filter_by(user_id=user_id).count()
        category_count = Category.query.filter_by(user_id=user_id).count()
        budget_count = Budget.query.filter_by(user_id=user_id).count()
        
        # Delete user's expenses
        Expense.query.filter_by(user_id=user_id).delete()
        
        # Delete user's categories
        Category.query.filter_by(user_id=user_id).delete()
        
        # Delete user's budgets
        Budget.query.filter_by(user_id=user_id).delete()
        
        # Delete user account
        db.session.delete(user)
        db.session.commit()
        
        # Verify all data is deleted
        remaining_expenses = Expense.query.filter_by(user_id=user_id).count()
        remaining_categories = Category.query.filter_by(user_id=user_id).count()
        remaining_budgets = Budget.query.filter_by(user_id=user_id).count()
        
        if remaining_expenses > 0 or remaining_categories > 0 or remaining_budgets > 0:
            app.logger.error(f"Data deletion incomplete for user {user_id}: {remaining_expenses} expenses, {remaining_categories} categories, {remaining_budgets} budgets still exist")
        else:
            app.logger.info(f"Account completely deleted: {username} ({email}) - Successfully removed {expense_count} expenses, {category_count} categories, {budget_count} budgets")
        
        # Clear session
        session.clear()
        flash("Your account has been permanently deleted.", "success")
        return redirect(url_for("login"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting account: {str(e)}")
        flash("An error occurred while deleting account. Please try again.", "danger")
        return redirect(url_for("profile"))


# ----------------- Admin Routes -----------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    """Admin dashboard with system statistics"""
    try:
        # Get system statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
        total_expense_count = Expense.query.count()
        
        # Recent users (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        
        # Recent expenses (last 7 days)
        recent_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.created_at >= week_ago
        ).scalar() or 0
        
        # Top spending users
        top_users = db.session.query(
            User.username, 
            db.func.sum(Expense.amount).label('total_spent')
        ).join(Expense).group_by(User.id).order_by(
            db.func.sum(Expense.amount).desc()
        ).limit(5).all()
        
        # Expenses by category (all users)
        category_stats = db.session.query(
            Expense.category,
            db.func.count(Expense.id).label('count'),
            db.func.sum(Expense.amount).label('total')
        ).group_by(Expense.category).order_by(
            db.func.sum(Expense.amount).desc()
        ).all()
        
        return render_template("admin/dashboard.html",
                             total_users=total_users,
                             active_users=active_users,
                             total_expenses=total_expenses,
                             total_expense_count=total_expense_count,
                             recent_users=recent_users,
                             recent_expenses=recent_expenses,
                             top_users=top_users,
                             category_stats=category_stats)
                             
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {str(e)}")
        flash("An error occurred while loading the admin dashboard.", "danger")
        return redirect(url_for("dashboard"))

@app.route("/admin/users")
@admin_required
def admin_users():
    """Manage all users"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        role_filter = request.args.get('role', 'all', type=str)
        status_filter = request.args.get('status', 'all', type=str)
        
        # Build query
        query = User.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        if role_filter != 'all':
            query = query.filter(User.role == role_filter)
            
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Paginate results
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        return render_template("admin/users.html", users=users, 
                             search=search, role_filter=role_filter, status_filter=status_filter)
                             
    except Exception as e:
        app.logger.error(f"Error in admin users: {str(e)}")
        flash("An error occurred while loading users.", "danger")
        return redirect(url_for("admin_dashboard"))

@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    """View detailed user information"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user statistics
        user_expenses = Expense.query.filter_by(user_id=user_id).all()
        total_spent = sum([e.amount for e in user_expenses])
        expense_count = len(user_expenses)
        
        # Recent expenses
        recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(
            Expense.created_at.desc()
        ).limit(10).all()
        
        # Expenses by category
        category_stats = db.session.query(
            Expense.category,
            db.func.count(Expense.id).label('count'),
            db.func.sum(Expense.amount).label('total')
        ).filter_by(user_id=user_id).group_by(Expense.category).all()
        
        return render_template("admin/user_detail.html",
                             user=user,
                             total_spent=total_spent,
                             expense_count=expense_count,
                             recent_expenses=recent_expenses,
                             category_stats=category_stats)
                             
    except Exception as e:
        app.logger.error(f"Error in admin user detail: {str(e)}")
        flash("An error occurred while loading user details.", "danger")
        return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    """Delete a user and all their data"""
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        email = user.email
        
        # Get counts for logging
        expense_count = Expense.query.filter_by(user_id=user_id).count()
        category_count = Category.query.filter_by(user_id=user_id).count()
        budget_count = Budget.query.filter_by(user_id=user_id).count()
        
        # Delete user's data
        Expense.query.filter_by(user_id=user_id).delete()
        Category.query.filter_by(user_id=user_id).delete()
        Budget.query.filter_by(user_id=user_id).delete()
        AdminLog.query.filter_by(admin_id=user_id).delete()
        AdminLog.query.filter_by(target_user_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        log_admin_action(f"User deleted", None, f"Deleted user {username} ({email}) with {expense_count} expenses, {category_count} categories, {budget_count} budgets")
        
        flash(f"User {username} and all their data have been permanently deleted.", "success")
        return redirect(url_for("admin_users"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting user: {str(e)}")
        flash("An error occurred while deleting the user.", "danger")
        return redirect(url_for("admin_users"))



# ----------------- Error Handlers -----------------
@app.errorhandler(400)
def bad_request(error):
    return render_template('errors/400.html'), 400

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

# ----------------- Initialize DB -----------------
def create_admin_user():
    """Create default admin user if it doesn't exist"""
    try:
        admin_email = "admin@expensetracker.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            admin_password = "admin123"  # Default password - should be changed
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
            
            app.logger.info(f"Default admin user created - Email: {admin_email}, Password: admin123")
            print("✅ Default admin user created!")
            print(f"   Email: {admin_email}")
            print("   Password: admin123")
            print("   ⚠️  Please change the admin password after first login!")
        else:
            app.logger.info("Admin user already exists")
            
    except Exception as e:
        app.logger.error(f"Error creating admin user: {str(e)}")
        print(f"❌ Error creating admin user: {str(e)}")

def safe_add_column(table_name, column_name, column_type, default_value=None):
    """Safely add a column to an existing table without losing data"""
    try:
        inspector = db.inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in existing_columns:
            app.logger.info(f"Adding column {column_name} to table {table_name}")
            
            # Use raw SQL to add column safely
            if default_value is not None:
                if isinstance(default_value, str):
                    db.session.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'")
                else:
                    db.session.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
            else:
                db.session.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            
            db.session.commit()
            app.logger.info(f"Successfully added column {column_name} to {table_name}")
            return True
        else:
            app.logger.info(f"Column {column_name} already exists in {table_name}")
            return False
    except Exception as e:
        app.logger.error(f"Error adding column {column_name} to {table_name}: {str(e)}")
        db.session.rollback()
        return False

def backup_user_data():
    """Create a backup of user data before any destructive operations"""
    try:
        users = User.query.all()
        backup_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password': user.password,
                'created_at': getattr(user, 'created_at', None),
                'last_login': getattr(user, 'last_login', None),
                'is_active': getattr(user, 'is_active', True),
                'role': getattr(user, 'role', 'user')
            }
            backup_data.append(user_data)
        
        app.logger.info(f"Backed up {len(backup_data)} users")
        return backup_data
    except Exception as e:
        app.logger.error(f"Error creating user backup: {str(e)}")
        return []

def restore_user_data(backup_data):
    """Restore user data from backup"""
    try:
        for user_data in backup_data:
            # Check if user already exists
            existing_user = User.query.get(user_data['id'])
            if not existing_user:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                # Add new columns if they exist in backup
                if 'created_at' in user_data and user_data['created_at']:
                    user.created_at = user_data['created_at']
                if 'last_login' in user_data and user_data['last_login']:
                    user.last_login = user_data['last_login']
                if 'is_active' in user_data:
                    user.is_active = user_data['is_active']
                if 'role' in user_data:
                    user.role = user_data['role']
                
                db.session.add(user)
        
        db.session.commit()
        app.logger.info(f"Restored {len(backup_data)} users from backup")
        return True
    except Exception as e:
        app.logger.error(f"Error restoring user data: {str(e)}")
        db.session.rollback()
        return False

def init_database():
    """Initialize database with safe migration that preserves data"""
    with app.app_context():
        try:
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user' in existing_tables:
                # Check if new columns exist
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                
                # Check if we need to add any missing columns
                missing_columns = []
                if 'created_at' not in user_columns:
                    missing_columns.append(('created_at', 'DATETIME', 'CURRENT_TIMESTAMP'))
                if 'last_login' not in user_columns:
                    missing_columns.append(('last_login', 'DATETIME', None))
                if 'is_active' not in user_columns:
                    missing_columns.append(('is_active', 'BOOLEAN', True))
                if 'role' not in user_columns:
                    missing_columns.append(('role', 'VARCHAR(20)', "'user'"))
                
                if missing_columns:
                    app.logger.info(f"Database schema needs updates. Adding {len(missing_columns)} missing columns...")
                    
                    # Create backup before making changes
                    backup_data = backup_user_data()
                    
                    # Add missing columns safely
                    for column_name, column_type, default_value in missing_columns:
                        safe_add_column('user', column_name, column_type, default_value)
                    
                    # Update existing users with default values for new columns
                    if missing_columns:
                        users = User.query.all()
                        for user in users:
                            updated = False
                            if 'created_at' not in user_columns and not hasattr(user, 'created_at'):
                                user.created_at = datetime.now(timezone.utc)
                                updated = True
                            if 'is_active' not in user_columns and not hasattr(user, 'is_active'):
                                user.is_active = True
                                updated = True
                            if 'role' not in user_columns and not hasattr(user, 'role'):
                                user.role = 'user'
                                updated = True
                            
                            if updated:
                                db.session.add(user)
                        
                        db.session.commit()
                        app.logger.info("Updated existing users with default values for new columns")
                    
                    app.logger.info("Database schema updated successfully while preserving all data")
                else:
                    app.logger.info("Database schema is up to date")
            else:
                # Create all tables for first time
                db.create_all()
                app.logger.info("Database created successfully")
            
            # Create admin user
            create_admin_user()
                
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            print(f"Database initialization failed: {str(e)}")
            
            # Only as a last resort, try to recreate database
            # But first warn the user about data loss
            print("⚠️  WARNING: Database initialization failed. Attempting to recreate database...")
            print("⚠️  This will result in DATA LOSS if there was existing data!")
            
            try:
                # Check if there are any users before dropping
                try:
                    user_count = User.query.count()
                    if user_count > 0:
                        print(f"⚠️  WARNING: Found {user_count} existing users. Data will be lost!")
                        response = input("Do you want to continue? This will DELETE ALL DATA! (yes/no): ")
                        if response.lower() != 'yes':
                            print("Database recreation cancelled.")
                            return
                except:
                    pass  # If we can't check, proceed with recreation
                
                db.drop_all()
                db.create_all()
                app.logger.info("Database recreated after error")
                create_admin_user()
                print("✅ Database recreated successfully")
            except Exception as e2:
                app.logger.error(f"Database recreation failed: {str(e2)}")
                print(f"❌ Database recreation failed: {str(e2)}")

if __name__=="__main__":
    init_database()
    app.run(debug=True, port=5001)
