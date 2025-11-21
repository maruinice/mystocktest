#!/usr/bin/env python3
"""
更新admin用户密码的脚本
"""

import hashlib
import secrets
import pymysql
import sys
from datetime import datetime

def hash_password(password: str) -> str:
    """使用与系统一致的方法生成密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + password_hash.hex()

def update_admin_password():
    """更新admin用户密码"""
    
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'stock_trading',
        'charset': 'utf8mb4'
    }
    
    # 新密码
    new_password = 'admin123456'
    new_password_hash = hash_password(new_password)
    
    try:
        # 连接数据库
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            # 检查admin用户是否存在
            cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
            admin_user = cursor.fetchone()
            
            if admin_user:
                print(f"找到admin用户: ID={admin_user[0]}, 用户名={admin_user[1]}")
                
                # 更新密码
                update_sql = """
                UPDATE users 
                SET password_hash = %s, updated_at = %s 
                WHERE username = 'admin'
                """
                cursor.execute(update_sql, (new_password_hash, datetime.now()))
                connection.commit()
                
                print(f"✅ admin用户密码已更新")
                print(f"新密码: {new_password}")
                print(f"密码哈希: {new_password_hash}")
                
            else:
                print("❌ 未找到admin用户，创建新的admin用户...")
                
                # 创建admin用户
                insert_sql = """
                INSERT INTO users (username, email, password_hash, full_name, role, 
                                 initial_capital, current_capital, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_sql, (
                    'admin',
                    'admin@example.com', 
                    new_password_hash,
                    '系统管理员',
                    'admin',
                    1000000.00,
                    1000000.00,
                    'active',
                    datetime.now(),
                    datetime.now()
                ))
                connection.commit()
                
                print(f"✅ 已创建admin用户")
                print(f"用户名: admin")
                print(f"邮箱: admin@example.com")
                print(f"密码: {new_password}")
                
    except pymysql.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == "__main__":
    print("=== 更新Admin用户密码 ===")
    
    if update_admin_password():
        print("\n🎉 操作完成！")
        print("\n登录信息:")
        print("用户名: admin")
        print("密码: admin123456")
        print("邮箱: admin@example.com")
    else:
        print("\n❌ 操作失败！")
        sys.exit(1)