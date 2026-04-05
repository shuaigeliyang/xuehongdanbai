@echo off
chcp 65001 >nul 2>&1
REM ============================================
REM Blood Plasma Free Hemoglobin Detection System
REM Version: 2.0
REM ============================================

title FHB Detection System

echo.
echo ============================================================
echo   Blood Plasma Free Hemoglobin Detection System
echo ============================================================
echo.

REM Get script directory
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Check Python
echo [1/4] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python version: %PYTHON_VERSION%

REM Check Node.js
echo [2/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo [OK] Node.js version: %NODE_VERSION%

REM Check and install backend dependencies
echo [3/4] Checking backend dependencies...
cd /d "%PROJECT_DIR%backend"

python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing backend dependencies...
    pip install fastapi uvicorn scikit-learn pandas numpy joblib python-multipart pydantic python-dotenv openpyxl pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [OK] Backend dependencies ready

REM Check and install frontend dependencies
echo [4/4] Checking frontend dependencies...
cd /d "%PROJECT_DIR%frontend"

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install --registry=https://registry.npmmirror.com
)

echo [OK] Frontend dependencies ready

echo.
echo ============================================================
echo   Starting services...
echo ============================================================
echo.

REM Start backend service
echo [INFO] Starting backend service (port: 8000)...
cd /d "%PROJECT_DIR%backend"
start "Backend Service - FHB Detection" cmd /c "python main.py"

REM Wait for backend to start
echo [INFO] Waiting for backend to start...
timeout /t 8 /nobreak >nul

REM Start frontend service
echo [INFO] Starting frontend service (port: 3000)...
cd /d "%PROJECT_DIR%frontend"
start "Frontend Service - FHB Detection" cmd /c "npm start"

REM Wait for frontend to start
echo [INFO] Waiting for frontend to start...
timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo   System started successfully!
echo ============================================================
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo ============================================================
echo   Note: Keep the two command windows open
echo   Stop:  Close the command windows to stop services
echo ============================================================
echo.

REM Open browser
echo [INFO] Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo [SUCCESS] System is ready! Please use browser to access the system.
echo.
pause
