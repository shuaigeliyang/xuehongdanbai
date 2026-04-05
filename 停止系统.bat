@echo off
chcp 65001 >nul 2>&1
REM ============================================
REM Blood Plasma Free Hemoglobin Detection System
REM Stop Services Script
REM Version: 2.0
REM ============================================

title Stop Services

echo.
echo ============================================================
echo   Blood Plasma Free Hemoglobin Detection System - Stop
echo ============================================================
echo.

echo [INFO] Stopping all services...

REM Stop backend service
taskkill /F /FI "WINDOWTITLE eq Backend Service*" >nul 2>&1
echo [OK] Backend service stopped

REM Stop frontend service
taskkill /F /FI "WINDOWTITLE eq Frontend Service*" >nul 2>&1
echo [OK] Frontend service stopped

echo.
echo ============================================================
echo   All services stopped
echo ============================================================
echo.
pause
