@echo off
chcp 65001 >nul
title Insurance Claims Management System - Production Server

echo.
echo ========================================
echo  نظام إدارة مطالبات التأمين
echo  Insurance Claims Management System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app" (
    echo ❌ Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Install/update requirements
echo 🔧 Checking dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Some dependencies might be missing, but continuing...
)

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "LOCAL_IP=%%a"
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo 🚀 Starting server...
echo 🌐 Your local IP: %LOCAL_IP%
echo.

REM Start the production server
python run_production.py

echo.
echo 🛑 Server stopped
pause
