"""
策略数据库服务
连接trading_strategies表进行策略管理
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import pymysql
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StrategyDatabaseService:
    """策略数据库服务"""
    
    def __init__(self):
        self.db_config = self._get_db_config()
    
    def _get_db_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        import os
        from urllib.parse import urlparse
        
        # 尝试从环境变量获取数据库URL
        database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
        
        try:
            # 解析数据库URL
            parsed = urlparse(database_url)
            return {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or 3306,
                'user': parsed.username or 'root',
                'password': parsed.password or '123456',
                'database': parsed.path.lstrip('/') or 'stock_trading',
                'charset': 'utf8mb4'
            }
        except Exception:
            # 如果解析失败，使用默认配置
            return {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '123456',
                'database': 'stock_trading',
                'charset': 'utf8mb4'
            }
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        connection = None
        try:
            connection = pymysql.connect(
                cursorclass=pymysql.cursors.DictCursor,
                **self.db_config
            )
            yield connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def get_strategies(self, user_id: int = None, page: int = 1, size: int = 20, 
                      keyword: str = '', status: str = '', category: str = '', 
                      risk_level: str = '') -> Tuple[List[Dict[str, Any]], int]:
        """获取策略列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # 构建查询条件
                where_conditions = []
                params = []
                
                if user_id:
                    where_conditions.append("user_id = %s")
                    params.append(user_id)
                
                if keyword:
                    where_conditions.append("(strategy_name LIKE %s OR description LIKE %s)")
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                
                if status:
                    where_conditions.append("status = %s")
                    params.append(status)
                
                if category:
                    where_conditions.append("category = %s")
                    params.append(category)
                
                if risk_level:
                    where_conditions.append("risk_level = %s")
                    params.append(risk_level)
                
                where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # 查询总数
                count_sql = f"SELECT COUNT(*) as total FROM trading_strategies{where_clause}"
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']
                
                # 查询数据
                offset = (page - 1) * size
                data_sql = f"""
                    SELECT 
                        id as strategy_id,
                        strategy_name as name,
                        display_name,
                        description,
                        strategy_type,
                        category,
                        risk_level,
                        author,
                        min_capital,
                        parameters,
                        indicators,
                        indicator_params,
                        buy_conditions,
                        sell_conditions,
                        code,
                        performance,
                        sharpe_ratio,
                        max_drawdown,
                        win_rate,
                        total_trades,
                        backtest_count,
                        last_backtest_date,
                        ai_generated,
                        original_prompt,
                        status,
                        created_at,
                        updated_at,
                        last_run_at
                    FROM trading_strategies
                    {where_clause}
                    ORDER BY updated_at DESC
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(data_sql, params + [size, offset])
                strategies = cursor.fetchall()
                
                # 处理JSON字段
                for strategy in strategies:
                    for json_field in ['parameters', 'indicators', 'indicator_params', 'buy_conditions', 'sell_conditions']:
                        if strategy[json_field]:
                            try:
                                strategy[json_field] = json.loads(strategy[json_field])
                            except:
                                strategy[json_field] = {}
                    
                    # 格式化日期
                    for date_field in ['created_at', 'updated_at', 'last_run_at']:
                        if strategy[date_field]:
                            strategy[date_field] = strategy[date_field].isoformat()
                    
                    if strategy['last_backtest_date']:
                        strategy['last_backtest_date'] = strategy['last_backtest_date'].strftime('%Y-%m-%d')
                
                return strategies, total
                
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            return [], 0
    
    def get_strategy_by_id(self, strategy_id: str, user_id: int = None) -> Optional[Dict[str, Any]]:
        """根据ID获取策略"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                where_clause = "id = %s"
                params = [strategy_id]
                
                if user_id:
                    where_clause += " AND user_id = %s"
                    params.append(user_id)
                
                sql = f"""
                    SELECT 
                        id as strategy_id,
                        user_id,
                        strategy_name as name,
                        display_name,
                        description,
                        strategy_type,
                        category,
                        risk_level,
                        author,
                        min_capital,
                        parameters,
                        indicators,
                        indicator_params,
                        buy_conditions,
                        sell_conditions,
                        code,
                        performance,
                        sharpe_ratio,
                        max_drawdown,
                        win_rate,
                        total_trades,
                        backtest_count,
                        last_backtest_date,
                        ai_generated,
                        original_prompt,
                        status,
                        created_at,
                        updated_at,
                        last_run_at
                    FROM trading_strategies
                    WHERE {where_clause}
                """
                
                cursor.execute(sql, params)
                strategy = cursor.fetchone()
                
                if strategy:
                    # 处理JSON字段
                    for json_field in ['parameters', 'indicators', 'indicator_params', 'buy_conditions', 'sell_conditions']:
                        if strategy[json_field]:
                            try:
                                strategy[json_field] = json.loads(strategy[json_field])
                            except:
                                strategy[json_field] = {}
                    
                    # 格式化日期
                    for date_field in ['created_at', 'updated_at', 'last_run_at']:
                        if strategy[date_field]:
                            strategy[date_field] = strategy[date_field].isoformat()
                    
                    if strategy['last_backtest_date']:
                        strategy['last_backtest_date'] = strategy['last_backtest_date'].strftime('%Y-%m-%d')
                
                return strategy
                
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return None
    
    def create_strategy(self, user_id: int, strategy_data: Dict[str, Any]) -> Optional[str]:
        """创建策略"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 准备数据
                sql = """
                    INSERT INTO trading_strategies (
                        user_id, strategy_name, display_name, description, strategy_type,
                        category, risk_level, author, min_capital, parameters,
                        indicators, indicator_params, buy_conditions, sell_conditions,
                        code, ai_generated, original_prompt, status, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                params = [
                    user_id,
                    strategy_data.get('name'),
                    strategy_data.get('display_name', strategy_data.get('name')),
                    strategy_data.get('description'),
                    strategy_data.get('strategy_type', 'custom'),
                    strategy_data.get('category', 'custom'),
                    strategy_data.get('risk_level', 'medium'),
                    strategy_data.get('author'),
                    strategy_data.get('min_capital', 100000),
                    json.dumps(strategy_data.get('parameters', {})),
                    json.dumps(strategy_data.get('indicators', [])),
                    json.dumps(strategy_data.get('indicator_params', {})),
                    json.dumps(strategy_data.get('buy_conditions', [])),
                    json.dumps(strategy_data.get('sell_conditions', [])),
                    strategy_data.get('code'),
                    strategy_data.get('ai_generated', False),
                    strategy_data.get('original_prompt'),
                    strategy_data.get('status', 'draft'),
                    datetime.now(),
                    datetime.now()
                ]
                
                cursor.execute(sql, params)
                conn.commit()
                
                return str(cursor.lastrowid)
                
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            return None
    
    def update_strategy(self, strategy_id: str, user_id: int, update_data: Dict[str, Any]) -> bool:
        """更新策略"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建更新字段
                set_clauses = []
                params = []
                
                field_mapping = {
                    'name': 'strategy_name',
                    'display_name': 'display_name',
                    'description': 'description',
                    'strategy_type': 'strategy_type',
                    'category': 'category',
                    'risk_level': 'risk_level',
                    'author': 'author',
                    'min_capital': 'min_capital',
                    'code': 'code',
                    'status': 'status'
                }
                
                for key, db_field in field_mapping.items():
                    if key in update_data:
                        set_clauses.append(f"{db_field} = %s")
                        params.append(update_data[key])
                
                # JSON字段
                json_fields = ['parameters', 'indicators', 'indicator_params', 'buy_conditions', 'sell_conditions']
                for field in json_fields:
                    if field in update_data:
                        set_clauses.append(f"{field} = %s")
                        params.append(json.dumps(update_data[field]))
                
                if not set_clauses:
                    return True
                
                set_clauses.append("updated_at = %s")
                params.append(datetime.now())
                
                params.extend([strategy_id, user_id])
                
                sql = f"""
                    UPDATE trading_strategies 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s AND user_id = %s
                """
                
                cursor.execute(sql, params)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            return False
    
    def delete_strategy(self, strategy_id: str, user_id: int) -> bool:
        """删除策略"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = "DELETE FROM trading_strategies WHERE id = %s AND user_id = %s"
                cursor.execute(sql, [strategy_id, user_id])
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            return False
    
    def save_backtest_result(self, backtest_data: Dict[str, Any]) -> Optional[str]:
        """保存回测结果"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 先尝试添加缺失的字段
                try:
                    cursor.execute("ALTER TABLE backtest_results ADD COLUMN returns_distribution JSON")
                    cursor.execute("ALTER TABLE backtest_results ADD COLUMN monthly_returns JSON")
                    conn.commit()
                except Exception:
                    pass  # 字段可能已存在
                
                sql = """
                    INSERT INTO backtest_results (
                        backtest_id, user_id, strategy_id, strategy_name,
                        start_date, end_date, initial_capital, final_capital,
                        parameters, stock_pool, benchmark,
                        total_return, annualized_return, benchmark_return, alpha, beta,
                        sharpe_ratio, sortino_ratio, max_drawdown, volatility,
                        win_rate, profit_factor, total_trades, winning_trades, losing_trades,
                        avg_win, avg_loss, largest_win, largest_loss,
                        equity_curve, trades, returns_distribution, monthly_returns,
                        status, created_at, completed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                params = [
                    backtest_data.get('backtest_id'),
                    backtest_data.get('user_id'),
                    backtest_data.get('strategy_id'),
                    backtest_data.get('strategy_name'),
                    backtest_data.get('start_date'),
                    backtest_data.get('end_date'),
                    backtest_data.get('initial_capital'),
                    backtest_data.get('final_capital'),
                    json.dumps(backtest_data.get('parameters', {})),
                    json.dumps(backtest_data.get('stock_pool', [])),
                    backtest_data.get('benchmark'),
                    backtest_data.get('total_return'),
                    backtest_data.get('annualized_return'),
                    backtest_data.get('benchmark_return'),
                    backtest_data.get('alpha'),
                    backtest_data.get('beta'),
                    backtest_data.get('sharpe_ratio'),
                    backtest_data.get('sortino_ratio'),
                    backtest_data.get('max_drawdown'),
                    backtest_data.get('volatility'),
                    backtest_data.get('win_rate'),
                    backtest_data.get('profit_factor'),
                    backtest_data.get('total_trades'),
                    backtest_data.get('winning_trades'),
                    backtest_data.get('losing_trades'),
                    backtest_data.get('avg_win'),
                    backtest_data.get('avg_loss'),
                    backtest_data.get('largest_win'),
                    backtest_data.get('largest_loss'),
                    json.dumps(backtest_data.get('equity_curve', [])),
                    json.dumps(backtest_data.get('trades', [])),
                    json.dumps(backtest_data.get('returns_distribution', [])),
                    json.dumps(backtest_data.get('monthly_returns', [])),
                    backtest_data.get('status', 'completed'),
                    datetime.now(),
                    datetime.now() if backtest_data.get('status') == 'completed' else None
                ]
                
                cursor.execute(sql, params)
                conn.commit()
                
                return backtest_data.get('backtest_id')
                
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")
            return None
    
    def get_backtest_results(self, user_id: int, strategy_id: str = None, 
                           page: int = 1, size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """获取回测结果列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                where_conditions = ["user_id = %s"]
                params = [user_id]
                
                if strategy_id:
                    where_conditions.append("strategy_id = %s")
                    params.append(strategy_id)
                
                where_clause = " WHERE " + " AND ".join(where_conditions)
                
                # 查询总数
                count_sql = f"SELECT COUNT(*) as total FROM backtest_results{where_clause}"
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']
                
                # 查询数据
                offset = (page - 1) * size
                data_sql = f"""
                    SELECT 
                        backtest_id, strategy_id, strategy_name,
                        start_date, end_date, initial_capital, final_capital,
                        total_return, sharpe_ratio, max_drawdown, win_rate,
                        total_trades, status, created_at, completed_at
                    FROM backtest_results
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(data_sql, params + [size, offset])
                results = cursor.fetchall()
                
                # 格式化日期
                for result in results:
                    for date_field in ['start_date', 'end_date']:
                        if result[date_field]:
                            result[date_field] = result[date_field].strftime('%Y-%m-%d')
                    
                    for datetime_field in ['created_at', 'completed_at']:
                        if result[datetime_field]:
                            result[datetime_field] = result[datetime_field].isoformat()
                
                return results, total
                
        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return [], 0
    
    def get_backtest_result_detail(self, backtest_id: str, user_id: int = None) -> Optional[Dict[str, Any]]:
        """获取回测结果详情"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                where_conditions = ["backtest_id = %s"]
                params = [backtest_id]
                
                if user_id:
                    where_conditions.append("user_id = %s")
                    params.append(user_id)
                
                where_clause = " WHERE " + " AND ".join(where_conditions)
                
                sql = f"""
                    SELECT * FROM backtest_results
                    {where_clause}
                """
                
                cursor.execute(sql, params)
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                # 解析JSON字段
                json_fields = ['parameters', 'stock_pool', 'equity_curve', 'trades', 'returns_distribution', 'monthly_returns']
                for field in json_fields:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except (json.JSONDecodeError, TypeError):
                            result[field] = [] if field in ['stock_pool', 'equity_curve', 'trades', 'returns_distribution', 'monthly_returns'] else {}
                
                # 格式化日期
                for date_field in ['start_date', 'end_date']:
                    if result[date_field]:
                        result[date_field] = result[date_field].strftime('%Y-%m-%d')
                
                for datetime_field in ['created_at', 'completed_at']:
                    if result[datetime_field]:
                        result[datetime_field] = result[datetime_field].isoformat()
                
                # 添加缺失的字段（兼容前端）
                if 'returns_distribution' not in result:
                    result['returns_distribution'] = []
                if 'monthly_returns' not in result:
                    result['monthly_returns'] = []
                
                return result
                
        except Exception as e:
            logger.error(f"获取回测结果详情失败: {e}")
            return None


# 创建全局实例
strategy_db_service = StrategyDatabaseService()