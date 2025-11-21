# 启动问题与解决方案记录

## 2025-01-22 16:05:00

### 问题1: docker-compose 命令未找到
**现象**: 执行 `docker-compose version` 时提示命令未找到
**解决方案**: 安装 docker-compose
```bash
sudo apt install docker-compose
```

## 2025-01-22 16:08:00

### 问题2: 数据库表不存在
**现象**: 运行 `run_core_migration.py` 时报错 `Table 'stock_trading.trading_strategies' doesn't exist`
**原因**: 初始化SQL脚本 `init.sql` 只创建了 `users` 和 `stock_basic` 两张表
**解决方案**: 直接运行 Flask 应用，由 SQLAlchemy 自动创建所有必要的表

## 2025-01-22 16:10:00

### 问题3: Python 依赖缺失
**现象**: 运行 Flask 应用时报错 `ModuleNotFoundError: No module named 'jwt'`、`No module named 'psutil'` 等
**解决方案**: 安装缺失的 Python 包
```bash
pip install PyJWT psutil flask-jwt-extended flask-sqlalchemy flask-migrate
```

## 2025-01-22 16:12:00

### 问题4: Pydantic ValidationError
**现象**: 运行 Flask 应用时报错 `Extra inputs are not permitted`
**原因**: Pydantic BaseSettings 默认不允许额外的环境变量字段
**解决方案**: 在 `stock_ai_trading/app/config/settings.py` 中修改 Settings 类的 Config，添加 `extra = "allow"`
```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 允许额外的字段
```

## 2025-01-22 16:13:00

### 问题5: 前端端口配置不一致
**现象**: 浏览器无法访问前端服务，预期端口 5173 但实际运行在 3000
**原因**: Vite 配置可能被修改或默认端口变更
**解决方案**: 访问 `http://localhost:3000` 代替 `http://localhost:5173`

## 2025-01-22 16:14:00

### 问题6: 前端登录失败 (401 Unauthorized)
**现象**: 在前端登录页面输入 admin@example.com / admin123 后返回 401 错误
**原因**: 测试用户的密码哈希格式与 `user_db.py` 中的哈希方法不一致
**解决方案**: 重新创建测试用户，确保密码哈希格式正确
```python
import pymysql
import hashlib
import secrets

conn = pymysql.connect(host='localhost', user='root', password='123456', database='stock_trading')
cursor = conn.cursor()

# 生成密码哈希（与 user_db.py 中的格式一致）
password = 'admin123'
salt = secrets.token_hex(16)
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
full_hash = salt + password_hash.hex()

# 删除旧用户
cursor.execute('DELETE FROM users WHERE email = "admin@example.com"')

# 创建新用户
cursor.execute('''
    INSERT INTO users (username, email, password_hash, full_name, role, status)
    VALUES ('admin', 'admin@example.com', %s, 'Admin User', 'admin', 'active')
''', (full_hash,))

conn.commit()
conn.close()
```

## 2025-11-18 20:43:00

### 问题7: 数据库密码修改后连接失败
**现象**: 修改 `docker-compose.yml` 中的 MySQL 密码后，登录时报错 `Access denied for user 'root'@'172.18.0.1' (using password: YES)`
**原因**: 修改了 Docker Compose 中的 MySQL 密码，但 `.env` 文件中的 `DATABASE_URL` 仍使用旧密码
**解决方案**: 
1. 更新 `.env` 文件中的数据库连接字符串
```bash
# 如果 docker-compose.yml 中设置 MYSQL_ROOT_PASSWORD=123456
# 则 .env 中的 DATABASE_URL 也要对应修改：
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/stock_trading
```

2. 重启后端服务
```bash
pkill -f run_flask.py
pkill -f start_websocket.py

# 重新启动
cd stock_ai_trading
source /home/meiming/miniconda3/etc/profile.d/conda.sh
conda activate stock_trading
nohup python run_flask.py --host 0.0.0.0 --port 5000 > flask.log 2>&1 &
nohup python start_websocket.py > websocket.log 2>&1 &
```

3. 重新创建管理员用户（如果执行了 `docker compose down -v` 清除了数据）
```bash
python update_admin_password.py
```

**重要提醒**: 
- 修改 MySQL 密码时，需要同步修改以下配置：
  - `docker-compose.yml` 中的 `MYSQL_ROOT_PASSWORD`
  - `.env` 文件中的 `DATABASE_URL`
  - `update_admin_password.py` 中的数据库连接配置
- 使用 `docker compose down -v` 会删除所有数据卷，需重新创建用户

## 2025-01-22 16:15:00

### 验证结果
- ✅ MySQL 服务正常运行
- ✅ Redis 服务正常运行
- ✅ Flask API 服务正常运行 (http://localhost:5000)
- ✅ WebSocket 服务正常运行 (ws://localhost:8765)
- ✅ 前端服务正常运行 (http://localhost:3000)
- ✅ 用户登录功能正常
- ✅ 页面导航功能正常（仪表盘、交易中心、投资组合等）
- ✅ 所有核心功能可用

