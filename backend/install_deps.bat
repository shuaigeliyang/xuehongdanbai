@echo off
REM ============================================
REM 血浆游离血红蛋白检测系统 - 依赖安装脚本
REM 作者: 哈雷酱大小姐 (￣▽￣)／
REM ============================================

echo.
echo ============================================
echo   安装Python依赖包
echo   作者: 哈雷酱大小姐 (￣▽￣)／
echo ============================================
echo.

REM 尝试使用虚拟环境
if exist "venv\Scripts\pip.exe" (
    echo [INFO] 使用虚拟环境的pip...
    venv\Scripts\pip.exe install --trusted-host pypi.org --trusted-host files.pythonhosted.org fastapi uvicorn pydantic pandas openpyxl scikit-learn numpy
    goto :success
)

if exist "venv\bin\pip" (
    echo [INFO] 使用Git Bash虚拟环境的pip...
    venv\bin\pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org fastapi uvicorn pydantic pandas openpyxl scikit-learn numpy
    goto :success
)

REM 如果没有虚拟环境，使用系统Python
echo [INFO] 使用系统Python安装依赖...
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org fastapi uvicorn pydantic pandas openpyxl scikit-learn numpy

:success
echo.
echo ============================================
echo   依赖安装完成！
echo ============================================
echo.
pause
