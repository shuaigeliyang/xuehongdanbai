# 部署指南

## 📋 目录

- [本地开发部署](#本地开发部署)
- [生产环境部署](#生产环境部署)
- [Docker部署](#docker部署)
- [常见问题](#常见问题)

---

## 本地开发部署

### 1. 环境准备

确保已安装以下软件：

- Python 3.8+
- Node.js 16+
- Git

### 2. 克隆项目

```bash
git clone https://github.com/yourusername/FHb-Detection-System.git
cd FHb-Detection-System
```

### 3. 后端部署

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制模型文件（如果还没在backend目录）
# 确保以下文件存在：
# - 随机森林模型.pkl
# - SVM回归模型.pkl
# - 特征标准化器.pkl

# 启动后端服务
python main.py
```

后端服务将运行在 `http://localhost:8000`

### 4. 前端部署

```bash
# 打开新终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

前端服务将运行在 `http://localhost:3000`

### 5. 访问应用

打开浏览器访问: `http://localhost:3000`

---

## 生产环境部署

### 方案1: Nginx反向代理

#### 1. 构建前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/build/` 目录

#### 2. 配置Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API文档代理
    location /docs {
        proxy_pass http://localhost:8000;
    }

    location /redoc {
        proxy_pass http://localhost:8000;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000;
    }
}
```

#### 3. 使用Systemd管理后端服务

创建服务文件 `/etc/systemd/system/fhb-backend.service`:

```ini
[Unit]
Description=FHb Detection Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl start fhb-backend
sudo systemctl enable fhb-backend
```

---

### 方案2: 使用PM2管理后端

```bash
# 安装PM2
npm install -g pm2

# 启动后端
cd backend
pm2 start python --name "fhb-backend" -- main.py

# 保存PM2配置
pm2 save
pm2 startup
```

---

## Docker部署

### 1. 创建Dockerfile

#### 后端Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端Dockerfile (`frontend/Dockerfile`)

```dockerfile
FROM node:16-alpine as builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产环境
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/build /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: fhb-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./models:/app/models
    restart: always

  frontend:
    build: ./frontend
    container_name: fhb-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 云服务部署

### 部署到Heroku

#### 1. 准备Procfile

创建 `Procfile`:

```
web: uvicorn main:app --host=0.0.0.0 --port=$PORT
```

#### 2. 部署命令

```bash
# 登录Heroku
heroku login

# 创建应用
heroku create your-app-name

# 推送代码
git push heroku main

# 配置环境变量（如需要）
heroku config:set PYTHON_VERSION=3.9.0
```

### 部署到阿里云/腾讯云

参考各云平台的部署文档，主要步骤：

1. 购买云服务器
2. 配置安全组（开放80、8000端口）
3. 安装Nginx
4. 按照生产环境部署步骤操作

---

## 安全配置

### 1. 配置HTTPS（使用Let's Encrypt）

```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. 环境变量配置

创建 `.env` 文件:

```env
# 后端配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
SECRET_KEY=your-secret-key-here

# 数据库配置（如使用）
DATABASE_URL=postgresql://user:password@localhost/dbname
```

---

## 性能优化

### 1. 后端优化

- 使用Gunicorn多worker部署:

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

- 启用响应压缩:

```python
# main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 2. 前端优化

- 代码分割和懒加载
- 图片优化
- 启用CDN

### 3. 数据库优化（如果使用）

- 添加索引
- 查询优化
- 连接池配置

---

## 监控和日志

### 1. 应用监控

使用Prometheus + Grafana监控应用性能

### 2. 日志管理

```python
# 配置日志
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. 错误追踪

使用Sentry等工具追踪应用错误

---

## 常见问题

### Q1: 端口被占用

**问题**: 启动时报错 "Address already in use"

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# 杀死进程
kill -9 PID  # Linux/Mac
taskkill /PID PID /F  # Windows
```

### Q2: 模型文件未找到

**问题**: "模型文件未找到"

**解决**: 确保模型文件在backend目录下:
- 随机森林模型.pkl
- SVM回归模型.pkl
- 特征标准化器.pkl

### Q3: CORS错误

**问题**: 前端无法访问后端API

**解决**: 检查后端CORS配置，确保允许前端域名

### Q4: Docker容器无法启动

**问题**: Docker容器启动失败

**解决**:
```bash
# 查看容器日志
docker logs container-name

# 重新构建
docker-compose build --no-cache
```

---

## 更新部署

### 更新后端

```bash
cd backend
git pull
pip install -r requirements.txt --upgrade
sudo systemctl restart fhb-backend
```

### 更新前端

```bash
cd frontend
git pull
npm run build
# 复制build目录到nginx目录
sudo cp -r build/* /path/to/nginx/html/
```

---

## 备份策略

### 数据备份

```bash
# 备份数据库
pg_dump dbname > backup.sql

# 备份模型文件
tar -czf models-backup.tar.gz models/
```

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"

# 备份数据库
pg_dump dbname > $BACKUP_DIR/db_$DATE.sql

# 备份模型文件
tar -czf $BACKUP_DIR/models_$DATE.tar.gz models/

# 删除30天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

添加到crontab:

```bash
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

<div align="center">

**如有问题，请查看文档或提交Issue**

Made with ❤️ by 哈雷酱大小姐 (￣▽￣)／

</div>
