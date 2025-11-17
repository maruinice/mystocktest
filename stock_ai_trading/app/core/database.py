"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:123456@localhost:3306/stock_trading"
)

# Create database engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise

def drop_tables():
    """删除所有表"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("数据库表删除成功")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise

# 数据库事件监听器
@event.listens_for(engine, "connect")
def set_mysql_pragma(dbapi_connection, connection_record):
    """设置数据库连接参数"""
    if "mysql" in DATABASE_URL:
        # MySQL连接参数
        cursor = dbapi_connection.cursor()
        cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
        cursor.execute("SET SESSION time_zone='+08:00'")
        cursor.close()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
    
    def execute_raw_sql(self, sql: str, params: dict = None):
        """执行原生SQL"""
        with self.get_session() as session:
            try:
                result = session.execute(sql, params or {})
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                logger.error(f"执行SQL失败: {sql}, 错误: {e}")
                raise
    
    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> dict:
        """获取表信息"""
        try:
            with self.get_session() as session:
                # 获取表结构信息
                result = session.execute(f"DESCRIBE {table_name}")
                columns = result.fetchall()
                
                # 获取表统计信息
                result = session.execute(f"SELECT COUNT(*) as row_count FROM {table_name}")
                row_count = result.fetchone()[0]
                
                return {
                    'table_name': table_name,
                    'columns': [dict(row) for row in columns],
                    'row_count': row_count
                }
        except Exception as e:
            logger.error(f"获取表信息失败: {table_name}, 错误: {e}")
            return {}
    
    def optimize_table(self, table_name: str):
        """优化表"""
        try:
            with self.get_session() as session:
                session.execute(f"OPTIMIZE TABLE {table_name}")
                session.commit()
                logger.info(f"表优化完成: {table_name}")
        except Exception as e:
            logger.error(f"表优化失败: {table_name}, 错误: {e}")
            raise

# 全局数据库管理器实例
db_manager = DatabaseManager()