@echo off
echo 🚀 Deploying to Vercel with SSL fixes...
echo.

REM Deploy to Vercel
vercel --prod

if %errorlevel% equ 0 (
    echo.
    echo ✅ Deployment successful!
    echo.
    echo 🧪 Test your deployment:
    echo 1. Health check: https://your-app.vercel.app/health
    echo 2. SSL test: https://your-app.vercel.app/test-ssl
    echo 3. Setup admin: https://your-app.vercel.app/setup-admin
    echo 4. Login: admin@expensetracker.com / admin123
    echo.
) else (
    echo ❌ Deployment failed
)

pause
