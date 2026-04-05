@echo off
REM ============================================
REM 血浆游离血红蛋白检测系统 - 后端启动脚本
REM 作者: 哈雷酱大小姐 (￣▽￣)／
REM ============================================

echo.
echo ============================================
echo   血浆游离血红蛋白检测系统 - 后端服务
echo   作者: 哈雷酱大小姐 (￣▽￣)／
echo ============================================
echo.

REM 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 使用Windows虚拟环境...
    call venv\Scripts\activate.bat
    python main.py
) else if exist "venv\bin\activate" (
    echo [INFO] 使用Git Bash虚拟环境...
    venv\bin\python main.py
) else (
    echo [WARNING] 未找到虚拟环境，使用系统Python...
    python main.py
)

pause
