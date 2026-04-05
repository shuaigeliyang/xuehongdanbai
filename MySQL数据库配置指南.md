# MySQL数据库配置完整指南

**作者：** 哈雷酱大小姐 (￣▽￣)／
**更新时间：** 2026-03-16
**版本：** 1.0

---

## ✅ 已完成的配置

### 1. MySQL数据库已创建 ✓

数据库信息：
- **数据库名**：fhb_detection
- **字符集**：utf8mb4
- **排序规则**：utf8mb4_unicode_ci
- **主机**：localhost
- **端口**：3306
- **用户**：root
- **密码**：root

### 2. Python配置文件已更新 ✓

已修改的文件：
- `backend/db_config.py` - 数据库连接配置
- `backend/.env` - 环境变量配置
- `backend/requirements.txt` - 依赖包列表

### 3. MySQL驱动已安装 ✓

- aiomysql==0.3.2
- pymysql==1.1.2
- mysql-connector-python==9.6.0

---

## 🚀 启动系统

### 方法1: 使用现有后端（推荐）

如果你的后端之前能正常运行，只需要：

1. **确保MySQL服务正在运行**
2. **启动后端**：
```bash
cd backend
python main_complete.py
```

3. **查看启动日志**：
   - 如果看到"数据库初始化完成"，说明MySQL连接成功
   - 如果看到错误，检查下面的故障排除部分

### 方法2: 重新安装依赖

如果遇到依赖问题：

```bash
cd backend

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装核心依赖（按顺序）
pip install sqlalchemy==2.0.25
pip install fastapi uvicorn
pip install python-jose passlib python-multipart
pip install python-dotenv
pip install aiomysql pymysql

# 启动后端
python main_complete.py
```

---

## 🔍 验证MySQL连接

### 检查数据库是否可用

```bash
# 方法1: 使用MySQL命令行
mysql -uroot -proot -e "USE fhb_detection; SHOW TABLES;"

# 方法2: 使用Python测试
cd backend
python test_mysql_connection.py
```

### 预期结果

如果连接成功，你应该看到：
```
[OK] 成功连接到MySQL
[INFO] MySQL版本: 8.0.44
[INFO] 当前数据库: fhb_detection
[OK] 创建了 X 个表
```

---

## 📋 数据库表结构

系统启动时会自动创建以下表：

1. **users** - 用户表
   - 用户信息、认证数据

2. **predictions** - 预测记录表
   - 吸光度数据
   - 预测结果
   - 样本信息

3. **calibrations** - 校准记录表
   - 校准数据
   - 性能指标

4. **system_logs** - 系统日志表
   - 日志记录
   - 系统事件

5. **audit_logs** - 审计日志表
   - 用户操作记录
   - 安全审计

---

## 🛠️ 故障排除

### 问题1: 连接MySQL失败

**错误信息**：`Can't connect to MySQL server`

**解决方案**：
1. 检查MySQL服务是否运行
2. 检查用户名密码是否正确 (root/root)
3. 检查端口是否正确 (3306)

```bash
# 检查MySQL服务状态
# Windows:
net start | findstr MySQL

# Linux:
sudo systemctl status mysql
```

### 问题2: 数据库不存在

**错误信息**：`Unknown database 'fhb_detection'`

**解决方案**：
```bash
cd backend
python create_mysql_database.py
```

### 问题3: 权限问题

**错误信息**：`Access denied for user 'root'`

**解决方案**：
```sql
-- 在MySQL中执行
GRANT ALL PRIVILEGES ON fhb_detection.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 问题4: 字符集问题

**错误信息**：字符编码错误

**解决方案**：
```sql
-- 修改数据库字符集
ALTER DATABASE fhb_detection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题5: 依赖包问题

**错误信息**：`ModuleNotFoundError: No module named 'sqlalchemy'`

**解决方案**：
```bash
# 单独安装SQLAlchemy
pip install sqlalchemy==2.0.25

# 如果还有问题，重新创建虚拟环境
cd backend
 deactivate  # 退出当前虚拟环境
rm -rf venv  # 删除虚拟环境
python -m venv venv  # 创建新的虚拟环境
venv\Scripts\activate  # 激活虚拟环境
pip install -r requirements.txt  # 安装依赖
```

---

## 💾 数据管理

### 查看数据

```bash
# 连接到MySQL
mysql -uroot -proot

# 使用数据库
USE fhb_detection;

# 查看表
SHOW TABLES;

# 查看预测记录
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;

# 查看统计信息
SELECT COUNT(*) as total FROM predictions;
SELECT model_type, COUNT(*) as count FROM predictions GROUP BY model_type;
```

### 备份数据

```bash
# 方法1: 使用mysqldump
mysqldump -uroot -proot fhb_detection > backup_$(date +%Y%m%d).sql

# 方法2: 使用Python脚本
python backup_mysql.py
```

### 恢复数据

```bash
# 恢复备份
mysql -uroot -proot fhb_detection < backup_20260316.sql
```

### 清空数据

```sql
-- 清空预测记录
TRUNCATE TABLE predictions;

-- 清空所有表
TRUNCATE TABLE predictions;
TRUNCATE TABLE users;
TRUNCATE TABLE calibrations;
TRUNCATE TABLE system_logs;
TRUNCATE TABLE audit_logs;
```

---

## 🎯 性能优化

### MySQL配置优化

编辑 `my.ini` (Windows) 或 `my.cnf` (Linux)：

```ini
[mysqld]
# 连接配置
max_connections = 200
connect_timeout = 10

# 缓冲区配置
innodb_buffer_pool_size = 256M
key_buffer_size = 16M

# 查询缓存
query_cache_size = 32M
query_cache_type = 1

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

### 应用层优化

1. **使用连接池**：
   - 已在 `db_config.py` 中配置
   - pool_size=5, max_overflow=10

2. **批量操作**：
   - 避免频繁的数据库写入
   - 使用批量查询

3. **索引优化**：
   - 为常用查询字段添加索引
   - 定期分析和优化慢查询

---

## 📊 监控与维护

### 查看MySQL状态

```sql
-- 查看连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看查询统计
SHOW STATUS LIKE 'Questions';

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';

-- 查看表大小
SELECT
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'fhb_detection'
ORDER BY size_mb DESC;
```

### 定期维护任务

```sql
-- 优化表
OPTIMIZE TABLE predictions;
OPTIMIZE TABLE users;

-- 分析表
ANALYZE TABLE predictions;
ANALYZE TABLE users;

-- 修复表
REPAIR TABLE predictions;
```

---

## 🔐 安全建议

### 生产环境配置

1. **创建专用数据库用户**：
```sql
CREATE USER 'fhb_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT SELECT, INSERT, UPDATE, DELETE ON fhb_detection.* TO 'fhb_user'@'localhost';
FLUSH PRIVILEGES;
```

2. **修改.env配置**：
```
DATABASE_URL=mysql+aiomysql://fhb_user:strong_password_here@localhost:3306/fhb_detection
```

3. **启用SSL连接**（如果需要）：
```
DATABASE_URL=mysql+aiomysql://fhb_user:password@localhost:3306/fhb_detection?ssl=true
```

4. **定期备份**：
   - 设置自动备份任务
   - 保留多个备份版本
   - 测试备份恢复流程

---

## 📞 快速参考

### 常用命令

```bash
# 启动MySQL
# Windows:
net start MySQL80
# Linux:
sudo systemctl start mysql

# 停止MySQL
# Windows:
net stop MySQL80
# Linux:
sudo systemctl stop mysql

# 重启MySQL
# Windows:
net restart MySQL80
# Linux:
sudo systemctl restart mysql

# 连接MySQL
mysql -uroot -proot

# 查看数据库
mysql -uroot -proot -e "SHOW DATABASES;"

# 查看表
mysql -uroot -proot fhb_detection -e "SHOW TABLES;"

# 备份数据库
mysqldump -uroot -proot fhb_detection > backup.sql

# 恢复数据库
mysql -uroot -proot fhb_detection < backup.sql
```

### 配置文件位置

- **数据库配置**：`backend/db_config.py`
- **环境变量**：`backend/.env`
- **依赖列表**：`backend/requirements.txt`
- **测试脚本**：`backend/test_mysql_connection.py`
- **创建脚本**：`backend/create_mysql_database.py`

---

## 🎉 总结

现在你的系统已经配置好了MySQL数据库！(￣▽￣)／

**已完成的工作：**
- ✅ MySQL数据库创建
- ✅ Python配置更新
- ✅ MySQL驱动安装
- ✅ 完整配置文档

**下一步：**
1. 启动后端服务：`python main_complete.py`
2. 启动前端服务：`npm start`
3. 进行预测操作
4. 查看MySQL中的数据

**数据持久化验证：**
1. 进行几次预测
2. 在MySQL中查看数据：
   ```sql
   USE fhb_detection;
   SELECT * FROM predictions ORDER BY created_at DESC;
   ```
3. 重启系统，验证数据依然存在

---

**常见问题：**
- 如果启动失败，检查上面的故障排除部分
- 如果有权限问题，确保MySQL用户有足够权限
- 如果有连接问题，确保MySQL服务正在运行

哼，本小姐的配置可是完美的！有问题就查文档！(￣▽￣)ゞ

---

*作者：哈雷酱大小姐*
*版本：1.0*
*日期：2026-03-16*
