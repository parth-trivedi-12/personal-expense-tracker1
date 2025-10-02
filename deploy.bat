@echo off
echo 🚀 Deploying to Vercel...
echo.

REM Check if vercel is installed
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Vercel CLI not found. Installing...
    npm install -g vercel
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Vercel CLI
        pause
        exit /b 1
    )
)

echo ✅ Vercel CLI found
echo.

REM Deploy to Vercel
echo 📦 Deploying to production...
vercel --prod

if %errorlevel% equ 0 (
    echo.
    echo ✅ Deployment successful!
    echo.
    echo 🧪 Test your deployment:
    echo 1. Visit: https://your-app.vercel.app/health
    echo 2. Setup admin: https://your-app.vercel.app/setup-admin
    echo 3. Login: admin@expensetracker.com / admin123
    echo.
) else (
    echo ❌ Deployment failed
)

pause
