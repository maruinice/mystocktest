#!/usr/bin/env python3
"""
股票基础信息数据导入脚本
从Tushare获取stock_basic数据并导入到数据库
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
        print(f"[INFO] 已加载环境变量文件: {env_path}")
    else:
        print("[INFO] 未找到 .env 文件，使用系统环境变量")
except Exception as e:
    print(f"[WARN] 加载 .env 失败: {e}")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# 导入项目模块
from app.services.tushare_service import tushare_service
from app.core.database import get_db
from app.config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_stock_basic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockBasicImporter:
    """股票基础信息导入器"""
    
    def __init__(self):
        """初始化导入器"""
        self.tushare = tushare_service
        self.batch_size = 100  # 减少批量插入大小
        
    def create_table_if_not_exists(self, db_session):
        """创建表（如果不存在）"""
        try:
            # 读取建表SQL
            sql_file = project_root / 'sql' / 'create_stock_basic_table.sql'
            if not sql_file.exists():
                logger.error(f"建表SQL文件不存在: {sql_file}")
                return False
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 执行建表SQL（分割多个语句）
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'ALTER', 'DROP')):
                    logger.info(f"执行SQL: {statement[:100]}...")
                    db_session.execute(text(statement))
            
            db_session.commit()
            logger.info("数据库表创建/更新成功")
            return True
            
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            db_session.rollback()
            return False
    
    async def fetch_stock_basic_data(self) -> pd.DataFrame:
        """获取股票基础信息数据"""
        try:
            logger.info("开始从Tushare获取股票基础信息...")
            
            # 获取所有正常上市的股票
            df = await self.tushare.get_stock_basic(
                exchange='',  # 全部交易所
                list_status='L'  # 仅上市股票
            )
            
            if df is None or df.empty:
                logger.error("未获取到股票基础信息数据")
                return pd.DataFrame()
            
            logger.info(f"成功获取 {len(df)} 条股票基础信息")
            return df
            
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            return pd.DataFrame()
    
    def format_data_for_db(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """格式化数据用于数据库插入"""
        if df.empty:
            return []
        
        records = []
        
        for _, row in df.iterrows():
            # 处理日期字段
            list_date = self._parse_date(row.get('list_date'))
            delist_date = self._parse_date(row.get('delist_date'))
            
            record = {
                'ts_code': row.get('ts_code'),
                'symbol': row.get('symbol'),
                'name': row.get('name'),
                'area': row.get('area'),
                'industry': row.get('industry'),
                'fullname': row.get('fullname'),
                'enname': row.get('enname'),
                'cnspell': row.get('cnspell'),
                'market': row.get('market'),
                'exchange': row.get('exchange'),
                'curr_type': row.get('curr_type'),
                'list_status': row.get('list_status'),
                'list_date': list_date,
                'delist_date': delist_date,
                'is_hs': row.get('is_hs'),
                'act_name': row.get('act_name'),
                'act_ent_type': row.get('act_ent_type'),
                'data_source': 'tushare',
                'sync_status': 'active'
            }
            
            # 过滤空值
            record = {k: v for k, v in record.items() 
                     if v is not None and v != '' and not pd.isna(v)}
            
            records.append(record)
        
        return records
    
    def _parse_date(self, date_str: Any) -> Any:
        """解析日期字符串"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            # Tushare日期格式：YYYYMMDD
            date_str = str(date_str).strip()
            if len(date_str) == 8 and date_str.isdigit():
                return datetime.strptime(date_str, '%Y%m%d').date()
            return None
        except Exception:
            return None
    
    def clear_existing_data(self, db_session):
        """清空现有数据"""
        try:
            logger.info("清空现有股票基础信息数据...")
            result = db_session.execute(text("DELETE FROM stock_basic WHERE data_source = 'tushare'"))
            db_session.commit()
            logger.info(f"已清空 {result.rowcount} 条现有数据")
        except Exception as e:
            logger.error(f"清空现有数据失败: {e}")
            db_session.rollback()
            raise
    
    def insert_data_batch(self, db_session, records: List[Dict[str, Any]]):
        """批量插入数据"""
        if not records:
            return
        
        try:
            # 构建插入SQL
            columns = list(records[0].keys())
            placeholders = ', '.join([f':{col}' for col in columns])
            sql = f"""
                INSERT INTO stock_basic ({', '.join(columns)})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                area = VALUES(area),
                industry = VALUES(industry),
                fullname = VALUES(fullname),
                enname = VALUES(enname),
                cnspell = VALUES(cnspell),
                market = VALUES(market),
                exchange = VALUES(exchange),
                curr_type = VALUES(curr_type),
                list_status = VALUES(list_status),
                list_date = VALUES(list_date),
                delist_date = VALUES(delist_date),
                is_hs = VALUES(is_hs),
                act_name = VALUES(act_name),
                act_ent_type = VALUES(act_ent_type),
                updated_at = CURRENT_TIMESTAMP
            """
            
            db_session.execute(text(sql), records)
            db_session.commit()
            logger.info(f"成功插入 {len(records)} 条数据")
            
        except Exception as e:
            logger.error(f"批量插入数据失败: {e}")
            db_session.rollback()
            raise
    
    async def import_data(self, clear_existing: bool = True):
        """导入股票基础信息数据"""
        logger.info("开始导入股票基础信息数据...")
        
        # 检查Tushare服务
        if not self.tushare.pro:
            logger.error("Tushare服务不可用，请检查TUSHARE_TOKEN配置")
            return False
        
        try:
            # 获取数据库会话
            db_gen = get_db()
            db_session = next(db_gen)
            
            try:
                # 创建表
                if not self.create_table_if_not_exists(db_session):
                    return False
                
                # 获取数据
                df = await self.fetch_stock_basic_data()
                if df.empty:
                    logger.error("未获取到数据，导入终止")
                    return False
                
                # 格式化数据
                records = self.format_data_for_db(df)
                if not records:
                    logger.error("数据格式化失败，导入终止")
                    return False
                
                # 清空现有数据（可选）
                if clear_existing:
                    self.clear_existing_data(db_session)
                
                # 批量插入数据
                total_records = len(records)
                logger.info(f"开始插入 {total_records} 条数据...")
                
                for i in range(0, total_records, self.batch_size):
                    batch = records[i:i + self.batch_size]
                    self.insert_data_batch(db_session, batch)
                    logger.info(f"已处理 {min(i + self.batch_size, total_records)}/{total_records} 条数据")
                
                logger.info("股票基础信息数据导入完成！")
                return True
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            return False
    
    def get_import_stats(self):
        """获取导入统计信息"""
        try:
            db_gen = get_db()
            db_session = next(db_gen)
            
            try:
                # 总数统计
                result = db_session.execute(text("""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(CASE WHEN list_status = 'L' THEN 1 END) as listed_count,
                        COUNT(CASE WHEN is_hs IN ('H', 'S') THEN 1 END) as hs_count,
                        COUNT(DISTINCT exchange) as exchange_count,
                        COUNT(DISTINCT industry) as industry_count,
                        MAX(updated_at) as last_update
                    FROM stock_basic 
                    WHERE data_source = 'tushare'
                """)).fetchone()
                
                if result:
                    stats = {
                        'total_stocks': result.total_count,
                        'listed_stocks': result.listed_count,
                        'hs_stocks': result.hs_count,
                        'exchanges': result.exchange_count,
                        'industries': result.industry_count,
                        'last_update': result.last_update
                    }
                    
                    logger.info("导入统计信息:")
                    for key, value in stats.items():
                        logger.info(f"  {key}: {value}")
                    
                    return stats
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return None


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("股票基础信息数据导入脚本")
    logger.info("=" * 50)
    
    # 检查环境变量
    if not os.getenv('TUSHARE_TOKEN'):
        logger.error("请设置TUSHARE_TOKEN环境变量")
        return
    
    # 创建导入器
    importer = StockBasicImporter()
    
    # 执行导入
    success = await importer.import_data(clear_existing=True)
    
    if success:
        # 显示统计信息
        importer.get_import_stats()
        logger.info("数据导入成功完成！")
    else:
        logger.error("数据导入失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())