# Vercel Deployment Guide for Personal Expense Tracker

This guide will walk you through deploying your Flask-based Personal Expense Tracker to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Database**: You have two options:
   - **PostgreSQL Database** (Recommended for production) - You'll need a cloud PostgreSQL database
   - **SQLite** (Testing only) - Data will be lost between requests in Vercel's serverless environment

## Step 1: Choose Your Database

### Option 1: PostgreSQL (Recommended for Production)

For a production app, you need a cloud PostgreSQL database. Here are recommended providers:

### Option A: Neon (Recommended - Free Tier Available)

1. Go to [neon.tech](https://neon.tech)
2. Sign up and create a new project
3. Copy the connection string (it will look like: `postgresql://username:password@host/database`)

### Option B: Supabase

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings > Database
4. Copy the connection string

### Option C: PlanetScale

1. Go to [planetscale.com](https://planetscale.com)
2. Create a new database
3. Get the connection string

### Option 2: SQLite (Testing Only)

⚠️ **IMPORTANT**: SQLite files are NOT persistent in Vercel's serverless environment. Data will be lost between requests. This is only suitable for testing.

If you want to use SQLite for testing:

1. Set `DATABASE_URL=sqlite:///expense.db` in your environment variables
2. The app will automatically use an in-memory database
3. **Data will be lost every time the function restarts**

## Step 2: Prepare Your Repository

Ensure your repository contains these files (already created for you):

- ✅ `vercel.json` - Vercel configuration
- ✅ `wsgi.py` - WSGI entry point
- ✅ `requirements.txt` - Updated with PostgreSQL support
- ✅ `env.example` - Environment variables template

## Step 3: Deploy to Vercel

### Method 1: Deploy via Vercel Dashboard (Recommended)

1. **Import Project**:

   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select your repository

2. **Configure Project**:

   - Framework Preset: Select "Other" or "Python"
   - Root Directory: Leave as `./` (root)
   - Build Command: Leave empty (Vercel will auto-detect)
   - Output Directory: Leave empty

3. **Set Environment Variables**:

   - Go to Project Settings > Environment Variables
   - Add the following variables:

   | Variable Name  | Value                                        | Description                     |
   | -------------- | -------------------------------------------- | ------------------------------- |
   | `SECRET_KEY`   | `your-secret-key-here`                       | Generate a secure random string |
   | `DATABASE_URL` | `postgresql://...` or `sqlite:///expense.db` | Database connection string      |
   | `FLASK_ENV`    | `production`                                 | Environment setting             |
   | `FLASK_APP`    | `wsgi.py`                                    | Flask app entry point           |

4. **Deploy**:
   - Click "Deploy"
   - Wait for the deployment to complete

### Method 2: Deploy via Vercel CLI

1. **Install Vercel CLI**:

   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:

   ```bash
   vercel login
   ```

3. **Deploy**:

   ```bash
   vercel
   ```

4. **Set Environment Variables**:

   ```bash
   vercel env add SECRET_KEY
   vercel env add DATABASE_URL
   vercel env add FLASK_ENV
   vercel env add FLASK_APP
   ```

5. **Redeploy**:
   ```bash
   vercel --prod
   ```

## Step 4: Initialize Database

After deployment, you need to initialize your database:

1. **Access your deployed app** (you'll get a URL like `https://your-app.vercel.app`)
2. **Visit the app** - the database will be automatically initialized on first access
3. **Create an admin account** - the app will create a default admin user:
   - Email: `admin@expensetracker.com`
   - Password: `admin123`
   - **⚠️ IMPORTANT**: Change this password immediately after first login!

## Step 5: Verify Deployment

1. **Test the application**:

   - Visit your Vercel URL
   - Register a new user account
   - Test adding expenses
   - Test all major features

2. **Check logs** (if needed):
   - Go to Vercel Dashboard > Your Project > Functions
   - Click on your function to view logs

## Step 6: Custom Domain (Optional)

1. **Add Domain**:
   - Go to Project Settings > Domains
   - Add your custom domain
   - Follow Vercel's DNS configuration instructions

## Troubleshooting

### Common Issues:

1. **Database Connection Error**:

   - Verify your `DATABASE_URL` is correct
   - Ensure your database provider allows connections from Vercel
   - Check if your database is paused (some free tiers pause after inactivity)

2. **Static Files Not Loading**:

   - Check that your `vercel.json` routes are correct
   - Ensure static files are in the `static/` directory

3. **Build Errors**:

   - Check that all dependencies are in `requirements.txt`
   - Verify Python version compatibility

4. **Function Timeout**:
   - Vercel has a 10-second timeout for hobby plans
   - Consider upgrading to Pro plan for longer timeouts
   - Optimize your database queries

### Debug Commands:

```bash
# Test locally with Vercel environment
vercel dev

# Check deployment logs
vercel logs

# Redeploy with debug info
vercel --debug
```

## Environment Variables Reference

| Variable       | Required | Description                   | Example                                                    |
| -------------- | -------- | ----------------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`   | Yes      | Flask secret key for sessions | `your-secret-key-here`                                     |
| `DATABASE_URL` | Yes      | Database connection string    | `postgresql://user:pass@host/db` or `sqlite:///expense.db` |
| `FLASK_ENV`    | Yes      | Flask environment             | `production`                                               |
| `FLASK_APP`    | Yes      | Flask app entry point         | `wsgi.py`                                                  |
| `VERCEL`       | Auto     | Set by Vercel                 | `1`                                                        |

## Security Notes

1. **Change Default Admin Password**: The default admin password is `admin123` - change it immediately!
2. **Use Strong Secret Key**: Generate a strong, random secret key
3. **Database Security**: Use connection pooling and SSL for your database
4. **Environment Variables**: Never commit sensitive data to your repository

## Performance Optimization

1. **Database Indexing**: Add indexes for frequently queried columns
2. **Connection Pooling**: Use a connection pooler like PgBouncer
3. **Caching**: Consider implementing Redis for session storage
4. **CDN**: Vercel automatically provides CDN for static assets

## Monitoring

1. **Vercel Analytics**: Enable in project settings
2. **Error Tracking**: Consider adding Sentry or similar
3. **Database Monitoring**: Use your database provider's monitoring tools

## Support

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **PostgreSQL Documentation**: [postgresql.org/docs](https://postgresql.org/docs)

---

## Quick Start Checklist

- [ ] Set up cloud PostgreSQL database
- [ ] Get database connection string
- [ ] Deploy to Vercel
- [ ] Set environment variables
- [ ] Test the application
- [ ] Change default admin password
- [ ] Verify all features work
- [ ] Set up custom domain (optional)

Your Personal Expense Tracker should now be live on Vercel! 🚀

