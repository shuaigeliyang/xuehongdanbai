#!/bin/bash
# 简化的依赖安装脚本
# 哈雷酱大小姐 (￣▽￣)／

cd "$(dirname "$0")"

echo "========================================"
echo "  安装核心依赖包"
echo "  作者: 哈雷酱大小姐"
echo "========================================"

# 激活虚拟环境
source venv/bin/activate

# 升级pip
echo ""
echo "[1/6] 升级pip..."
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q

# 安装基础包
echo ""
echo "[2/6] 安装基础包..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q \
    python-dotenv \
    typing-extensions \
    requests

# 安装SQLAlchemy（不需要编译的版本）
echo ""
echo "[3/6] 安装SQLAlchemy..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q \
    sqlalchemy==2.0.25

# 安装MySQL相关
echo ""
echo "[4/6] 安装MySQL驱动..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q \
    pymysql \
    aiomysql

# 安装认证相关
echo ""
echo "[5/6] 安装认证包..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q \
    python-jose \
    passlib \
    bcrypt

# 安装Web框架
echo ""
echo "[6/6] 安装Web框架..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -q \
    fastapi \
    uvicorn \
    python-multipart

echo ""
echo "========================================"
echo "依赖安装完成！"
echo "========================================"
echo ""
echo "已安装的包："
pip list | grep -E "sqlalchemy|fastapi|uvicorn|aiomysql|pymysql|jose|passlib"
echo ""
echo "下一步："
echo "  启动后端: python main_complete.py"
