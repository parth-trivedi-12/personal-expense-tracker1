# 💰 Personal Expense Tracker

A comprehensive Flask-based web application for tracking personal expenses with advanced security features, budget management, and financial reporting.

## 🚀 Features

### Core Features
- **User Authentication**: Secure registration and login with password hashing
- **Expense Management**: Add, edit, delete, and view expenses with full CRUD operations
- **Budget Tracking**: Set monthly budgets and track spending against them
- **Financial Reports**: Generate detailed reports with visual charts
- **Data Export**: Export expenses to CSV and PDF formats

### Advanced Features
- **Expense Templates**: Create templates for recurring expenses
- **Quick Add**: Add expenses from templates with one click
- **User Profile**: Manage account information and view statistics
- **Category Filtering**: Filter expenses by category
- **Payment Methods**: Track different payment methods (Cash, Card, UPI, etc.)

### Security Features
- **CSRF Protection**: All forms protected against Cross-Site Request Forgery
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Parameterized queries and proper data handling
- **Secure Sessions**: Encrypted session management
- **Password Security**: Strong password requirements and secure hashing
- **Error Handling**: Comprehensive error handling and logging

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Chart.js)
- **Security**: Flask-WTF, Werkzeug Security
- **PDF Generation**: pdfkit
- **Logging**: Python logging with file rotation

## 📦 Installation

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Personal_Expense_tracker_main
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install wkhtmltopdf** (for PDF generation)
   - **Windows**: Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
   - **macOS**: `brew install wkhtmltopdf`
   - **Ubuntu/Debian**: `sudo apt-get install wkhtmltopdf`

5. **Set environment variables** (optional)
   ```bash
   # Set a custom secret key
   export SECRET_KEY="your-secure-secret-key-here"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session encryption (auto-generated if not set)

### Database
- SQLite database is automatically created as `expense.db`
- All tables are created automatically on first run
- Database includes proper foreign key constraints and data validation

### Logging
- Logs are stored in `logs/expense_tracker.log`
- Automatic log rotation (10 files, 10KB each)
- Log levels: INFO, WARNING, ERROR

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password`: Hashed password
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp
- `is_active`: Account status

### Expenses Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `title`: Expense title
- `amount`: Expense amount (positive)
- `date`: Expense date
- `category`: Expense category
- `description`: Optional description
- `payment_method`: Payment method used
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Budget Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `amount`: Budget amount
- `start_date`: Budget start date
- `end_date`: Budget end date
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Expense Templates Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `title`: Template title
- `amount`: Template amount
- `category`: Template category
- `description`: Template description
- `payment_method`: Template payment method
- `is_active`: Template status
- `created_at`: Creation timestamp

## 🔒 Security Features

### Authentication & Authorization
- Secure password hashing using Werkzeug
- Session-based authentication
- User-specific data isolation
- Login required decorator for protected routes

### Input Validation
- Email format validation
- Password strength requirements (8+ chars, uppercase, lowercase, digit)
- Amount validation (positive numbers, reasonable limits)
- Date validation (no future dates)
- Category and payment method validation

### CSRF Protection
- All forms protected with CSRF tokens
- Flask-WTF integration for automatic token generation

### SQL Injection Prevention
- Parameterized queries using SQLAlchemy ORM
- No direct SQL string concatenation
- Proper data type handling

### Error Handling
- Comprehensive try-catch blocks
- Database transaction rollback on errors
- User-friendly error messages
- Detailed error logging

## 📈 Usage Guide

### Getting Started
1. **Register**: Create a new account with email and password
2. **Login**: Access your account
3. **Set Budget**: Set your monthly budget
4. **Add Expenses**: Start tracking your expenses
5. **View Dashboard**: Monitor your spending and budget status

### Managing Expenses
- **Add Expense**: Fill out the expense form with all required details
- **Edit Expense**: Click edit on any expense to modify it
- **Delete Expense**: Remove expenses you no longer need
- **Filter by Category**: Use the category filter to view specific expenses

### Using Templates
- **Create Template**: Save common expenses as templates
- **Quick Add**: Add expenses from templates with one click
- **Manage Templates**: View and organize your expense templates

### Reports and Export
- **View Reports**: See spending summaries and category breakdowns
- **Export CSV**: Download expense data for external analysis
- **Export PDF**: Generate formatted PDF reports

## 🚨 Security Considerations

### Production Deployment
- Change the default secret key
- Use environment variables for sensitive configuration
- Enable HTTPS in production
- Set up proper database backups
- Configure firewall rules
- Use a production WSGI server (Gunicorn, uWSGI)

### Best Practices
- Regularly update dependencies
- Monitor application logs
- Implement rate limiting for production
- Use a more robust database (PostgreSQL, MySQL) for production
- Set up monitoring and alerting

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

2. **PDF Generation Issues**
   - Install wkhtmltopdf on your system
   - Check file permissions for the logs directory

3. **Database Issues**
   - Ensure the application has write permissions in the directory
   - Check if the database file is not corrupted

4. **CSRF Token Errors**
   - Clear browser cookies and try again
   - Ensure JavaScript is enabled

### Log Files
- Check `logs/expense_tracker.log` for detailed error information
- Logs include timestamps, error messages, and stack traces

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error details
- Create an issue on the repository

## 🔄 Updates and Maintenance

### Regular Maintenance
- Monitor log files for errors
- Backup database regularly
- Update dependencies periodically
- Review security configurations

### Future Enhancements
- Password reset functionality
- Email notifications
- Mobile app integration
- Advanced analytics
- Multi-currency support
- Recurring expense automation
