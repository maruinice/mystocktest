"""
股票选股服务
实现各种选股策略和算法
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import pandas as pd
import numpy as np

from app.services.strategy_database_service import strategy_db_service
from app.services.screening_technical_indicators import (
    screening_tech_indicators,
    batch_calculate_indicators
)

logger = logging.getLogger(__name__)


class StockScreeningService:
    """股票选股服务"""
    
    def __init__(self):
        self.db_service = strategy_db_service
    
    async def execute_screening(self, strategy_id: int, user_id: int = None, 
                              custom_conditions: Dict = None) -> Dict:
        """
        执行选股
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            custom_conditions: 自定义筛选条件
        
        Returns:
            选股结果
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 获取策略配置
            strategy = await self._get_strategy(strategy_id)
            if not strategy:
                return {'success': False, 'message': '策略不存在'}
            
            # 创建结果记录
            result_id = await self._create_result_record(task_id, strategy_id, user_id)
            
            # 更新状态为运行中
            await self._update_result_status(result_id, 'running')
            
            start_time = datetime.now()
            
            try:
                # 执行筛选
                screening_result = await self._perform_screening(strategy, custom_conditions)
                
                # 计算执行时间
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # 保存结果
                await self._save_screening_result(
                    result_id, screening_result, execution_time
                )
                
                # 更新策略使用统计
                await self._update_strategy_usage(strategy_id)
                
                return {
                    'success': True,
                    'message': '选股完成',
                    'data': {
                        'task_id': task_id,
                        'result_id': result_id,
                        'total_stocks': screening_result['total_stocks'],
                        'filtered_stocks': screening_result['filtered_stocks'],
                        'execution_time': execution_time,
                        'results': screening_result['results'][:20]  # 返回前20个结果
                    }
                }
                
            except Exception as e:
                # 更新状态为失败
                await self._update_result_status(result_id, 'failed', str(e))
                raise e
                
        except Exception as e:
            logger.error(f"执行选股失败: {e}")
            return {'success': False, 'message': f'选股失败: {str(e)}'}
    
    async def get_screening_result(self, task_id: str) -> Dict:
        """获取选股结果"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                SELECT sr.*, ss.strategy_name, ss.strategy_type
                FROM screening_results sr
                LEFT JOIN screening_strategies ss ON sr.strategy_id = ss.id
                WHERE sr.task_id = %s
                """
                
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {'success': False, 'message': '结果不存在'}
                
                # 解析JSON数据
                result_data = json.loads(result['result_data']) if result['result_data'] else {}
                summary_stats = json.loads(result['summary_stats']) if result['summary_stats'] else {}
                conditions = json.loads(result['conditions']) if result.get('conditions') else {}
                
                return {
                    'success': True,
                    'data': {
                        'task_id': result['task_id'],
                        'strategy_id': result['strategy_id'],
                        'strategy_name': result['strategy_name'],
                        'strategy_type': result['strategy_type'],
                        'screening_date': result['screening_date'].strftime('%Y-%m-%d'),
                        'status': result['status'],
                        'total_stocks': result['total_stocks'],
                        'filtered_stocks': result['filtered_stocks'],
                        'execution_time': result['execution_time'],
                        'results': result_data.get('results', []),
                        'summary': summary_stats,
                        'conditions': conditions,  # 添加筛选条件
                        'created_at': result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                
        except Exception as e:
            logger.error(f"获取选股结果失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}
    
    async def get_available_strategies(self, user_id: int = None) -> Dict:
        """获取可用的选股策略"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取系统策略和用户自定义策略
                sql = """
                SELECT id, strategy_name, strategy_code, strategy_type, description,
                       is_system, usage_count, success_rate, avg_return, created_at
                FROM screening_strategies
                WHERE is_active = TRUE
                AND (is_system = TRUE OR creator_id = %s OR creator_id IS NULL)
                ORDER BY is_system DESC, usage_count DESC
                """
                
                cursor.execute(sql, (user_id,))
                strategies = cursor.fetchall()
                
                # 按类型分组
                grouped_strategies = {
                    'system': [],
                    'fundamental': [],
                    'technical': [],
                    'mixed': [],
                    'custom': []
                }
                
                for strategy in strategies:
                    strategy_data = {
                        'id': strategy['id'],
                        'name': strategy['strategy_name'],
                        'code': strategy['strategy_code'],
                        'type': strategy['strategy_type'],
                        'description': strategy['description'],
                        'is_system': strategy['is_system'],
                        'usage_count': strategy['usage_count'],
                        'success_rate': float(strategy['success_rate']) if strategy['success_rate'] else None,
                        'avg_return': float(strategy['avg_return']) if strategy['avg_return'] else None,
                        'created_at': strategy['created_at'].strftime('%Y-%m-%d')
                    }
                    
                    if strategy['is_system']:
                        # 系统策略按照strategy_type分类
                        strategy_type = strategy['strategy_type']
                        if strategy_type in grouped_strategies:
                            grouped_strategies[strategy_type].append(strategy_data)
                        else:
                            # 如果类型不在预定义分组中，放入system分组
                            grouped_strategies['system'].append(strategy_data)
                    else:
                        # 用户自定义策略放入custom分组
                        grouped_strategies['custom'].append(strategy_data)
                
                return {
                    'success': True,
                    'data': grouped_strategies
                }
                
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}
    
    async def get_screening_indicators(self) -> Dict:
        """获取可用的筛选指标"""
        try:
            indicators = {
                'fundamental': {
                    'profitability': [
                        {'code': 'roe', 'name': '净资产收益率', 'unit': '%', 'range': [0, 50]},
                        {'code': 'roa', 'name': '总资产收益率', 'unit': '%', 'range': [0, 30]},
                        {'code': 'gross_margin', 'name': '毛利率', 'unit': '%', 'range': [0, 100]},
                        {'code': 'net_margin', 'name': '净利率', 'unit': '%', 'range': [0, 50]},
                        {'code': 'eps', 'name': '每股收益', 'unit': '元', 'range': [0, 10]}
                    ],
                    'growth': [
                        {'code': 'revenue_growth', 'name': '营收增长率', 'unit': '%', 'range': [-50, 100]},
                        {'code': 'profit_growth', 'name': '净利润增长率', 'unit': '%', 'range': [-50, 100]}
                    ],
                    'valuation': [
                        {'code': 'pe_ttm', 'name': '市盈率TTM', 'unit': '倍', 'range': [0, 100]},
                        {'code': 'pb', 'name': '市净率', 'unit': '倍', 'range': [0, 20]},
                        {'code': 'ps_ttm', 'name': '市销率TTM', 'unit': '倍', 'range': [0, 50]},
                        {'code': 'pb_mrq', 'name': '市净率MRQ', 'unit': '倍', 'range': [0, 10]}
                    ],
                    'financial_health': [
                        {'code': 'debt_ratio', 'name': '资产负债率', 'unit': '%', 'range': [0, 100]},
                        {'code': 'current_ratio', 'name': '流动比率', 'unit': '倍', 'range': [0, 5]},
                        {'code': 'quick_ratio', 'name': '速动比率', 'unit': '倍', 'range': [0, 3]}
                    ]
                },
                'technical': {
                    'trend': [
                        {'code': 'ma5', 'name': '5日均线', 'unit': '元', 'range': [0, 1000]},
                        {'code': 'ma20', 'name': '20日均线', 'unit': '元', 'range': [0, 1000]},
                        {'code': 'ma60', 'name': '60日均线', 'unit': '元', 'range': [0, 1000]}
                    ],
                    'momentum': [
                        {'code': 'rsi12', 'name': 'RSI(12)', 'unit': '', 'range': [0, 100]},
                        {'code': 'kdj_k', 'name': 'KDJ-K', 'unit': '', 'range': [0, 100]},
                        {'code': 'kdj_d', 'name': 'KDJ-D', 'unit': '', 'range': [0, 100]}
                    ],
                    'volume': [
                        {'code': 'turnover_rate', 'name': '换手率', 'unit': '%', 'range': [0, 50]},
                        {'code': 'volume_ratio', 'name': '量比', 'unit': '倍', 'range': [0, 10]}
                    ]
                },
                'market': {
                    'basic': [
                        {'code': 'market_cap', 'name': '总市值', 'unit': '万元', 'range': [0, 10000000]},
                        {'code': 'change_pct', 'name': '涨跌幅', 'unit': '%', 'range': [-20, 20]},
                        {'code': 'close_price', 'name': '收盘价', 'unit': '元', 'range': [0, 1000]}
                    ]
                }
            }
            
            return {
                'success': True,
                'data': indicators
            }
            
        except Exception as e:
            logger.error(f"获取指标列表失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}
    
    async def _get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """获取策略配置"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                SELECT * FROM screening_strategies 
                WHERE id = %s AND is_active = TRUE
                """
                
                cursor.execute(sql, (strategy_id,))
                strategy = cursor.fetchone()
                
                if strategy:
                    # 解析JSON配置
                    strategy['config'] = json.loads(strategy['config']) if strategy['config'] else {}
                    strategy['conditions'] = json.loads(strategy['conditions']) if strategy['conditions'] else {}
                    strategy['sort_rules'] = json.loads(strategy['sort_rules']) if strategy['sort_rules'] else {}
                
                return strategy
                
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return None
    
    async def _create_result_record(self, task_id: str, strategy_id: int, user_id: int = None) -> int:
        """创建结果记录"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO screening_results (
                    task_id, strategy_id, user_id, screening_date, status
                ) VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(sql, (
                    task_id, strategy_id, user_id, 
                    datetime.now().date(), 'pending'
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                return result_id
                
        except Exception as e:
            logger.error(f"创建结果记录失败: {e}")
            raise e
    
    async def _update_result_status(self, result_id: int, status: str, error_message: str = None):
        """更新结果状态"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                UPDATE screening_results 
                SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                
                cursor.execute(sql, (status, error_message, result_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新结果状态失败: {e}")
    
    async def _perform_screening(self, strategy: Dict, custom_conditions: Dict = None) -> Dict:
        """执行筛选逻辑"""
        try:
            # 写入调试文件
            with open('debug_screening.log', 'a', encoding='utf-8') as f:
                f.write(f"[DEBUG] _perform_screening 开始，custom_conditions: {custom_conditions}\n")
                f.flush()
            
            print(f"[DEBUG] _perform_screening 开始，custom_conditions: {custom_conditions}", flush=True)
            
            # 获取基础数据
            base_data = await self._get_base_screening_data()
            
            with open('debug_screening.log', 'a', encoding='utf-8') as f:
                f.write(f"[DEBUG] 获取基础数据完成，行数: {len(base_data)}\n")
                f.flush()
            
            print(f"[DEBUG] 获取基础数据完成，行数: {len(base_data)}", flush=True)
            
            if base_data.empty:
                return {
                    'total_stocks': 0,
                    'filtered_stocks': 0,
                    'results': [],
                    'summary': {}
                }
            
            total_stocks = len(base_data)
            
            # 应用筛选条件
            if custom_conditions:
                # 如果有自定义条件，正确处理不同格式
                if isinstance(custom_conditions, list):
                    # 直接是条件数组
                    conditions = custom_conditions
                elif isinstance(custom_conditions, dict) and 'conditions' in custom_conditions:
                    # 包含conditions字段的字典
                    conditions = custom_conditions['conditions']
                else:
                    # 其他格式，直接使用
                    conditions = custom_conditions
                print(f"[DEBUG] 使用自定义条件: {conditions}", flush=True)
            else:
                # 使用策略默认条件
                conditions = strategy.get('conditions', {})
                print(f"[DEBUG] 使用策略默认条件: {conditions}", flush=True)
            
            print(f"[DEBUG] 准备调用 _apply_screening_conditions", flush=True)
            filtered_data = await self._apply_screening_conditions(base_data, conditions)
            print(f"[DEBUG] _apply_screening_conditions 完成，筛选后行数: {len(filtered_data) if filtered_data is not None else 0}", flush=True)
            
            # 如果没有条件，返回默认100条；如果有条件，返回真实筛选结果（即使为0）
            if not conditions or (isinstance(conditions, dict) and not conditions):
                # 无条件时，返回默认100条
                print("[DEBUG] 无筛选条件，返回默认100条", flush=True)
                logger.info("无筛选条件，返回默认100条")
                filtered_data = base_data.head(100)
            elif filtered_data is None or len(filtered_data) == 0:
                # 有条件但筛选结果为空，返回真实的空结果
                print("[DEBUG] 有筛选条件但结果为0，返回真实空结果", flush=True)
                logger.info("筛选条件严格，结果为0条")
                filtered_data = pd.DataFrame()  # 返回空DataFrame
            # 应用排序规则
            sort_rules = strategy.get('sort_rules', {})
            sorted_data = await self._apply_sorting_rules(filtered_data, sort_rules)
            
            # 计算综合评分
            scored_data = await self._calculate_composite_score(sorted_data, strategy)
            
            # 生成结果
            results = self._format_screening_results(scored_data)
            
            
            # 生成汇总统计
            summary = self._generate_summary_stats(scored_data, strategy)
            
            return {
                'total_stocks': total_stocks,
                'filtered_stocks': len(results),
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"执行筛选失败: {e}")
            raise e
    
    async def _get_base_screening_data(self) -> pd.DataFrame:
        """获取基础筛选数据 - 使用验证成功的逻辑"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                
                # 第一步：获取股票基础信息
                cursor.execute("""
                    SELECT ts_code, symbol, name, industry, market, exchange, area
                    FROM stock_basic 
                    WHERE list_status = 'L' 
                      AND sync_status = 'active'
                      AND name NOT LIKE '模拟股票%'
                    ORDER BY RAND()
                    LIMIT 500
                """)
                stocks = cursor.fetchall()
                # 若基础表为空，回退到从daily_basic取近一年有数据的股票并关联基本信息
                if not stocks:
                    logger.warning("stock_basic筛选为空，回退到daily_basic获取候选股票")
                    cursor.execute(f"""
                        SELECT DISTINCT db.ts_code
                        FROM daily_basic db
                        WHERE db.trade_date >= '{one_year_ago}'
                        LIMIT 500
                    """)
                    ts_rows = cursor.fetchall()
                    ts_codes = [row['ts_code'] for row in ts_rows]
                    if ts_codes:
                        in_list = ",".join([f"'{c}'" for c in ts_codes])
                        cursor.execute(f"""
                            SELECT sb.ts_code, sb.symbol, sb.name, sb.industry, sb.market, sb.exchange, sb.area
                            FROM stock_basic sb
                            WHERE sb.ts_code IN ({in_list}) AND sb.name NOT LIKE '模拟股票%'
                        """)
                        stocks = cursor.fetchall()
                
                logger.info(f"获取到 {len(stocks)} 只股票基础信息")
                
                # 第二步：为每只股票获取最新数据
                screening_data = []
                
                for stock in stocks:
                    ts_code = stock['ts_code']
                    
                    # 获取最新日线数据
                    cursor.execute(f"""
                        SELECT close_price, change_pct, volume, amount, turnover_rate, volume_ratio,
                               pe, pb, ps, pcf, market_cap, circ_mv, trade_date
                        FROM daily_history 
                        WHERE ts_code = '{ts_code}' 
                        AND trade_date >= '{one_year_ago}'
                        ORDER BY trade_date DESC 
                        LIMIT 1
                    """)
                    dh_data = cursor.fetchone()
                    
                    # 获取最新基本面数据
                    cursor.execute(f"""
                        SELECT pe, pb, ps, pe_ttm, ps_ttm, total_mv, circ_mv, 
                               turnover_rate, volume_ratio, trade_date
                        FROM daily_basic 
                        WHERE ts_code = '{ts_code}' 
                        AND trade_date >= '{one_year_ago}'
                        ORDER BY trade_date DESC 
                        LIMIT 1
                    """)
                    db_data = cursor.fetchone()
                    
                    # 获取最新财务指标数据
                    cursor.execute(f"""
                        SELECT roe, roa, gross_margin, net_margin, revenue_growth, 
                               profit_growth, debt_ratio, current_ratio, eps, pb_mrq
                        FROM financial_indicators 
                        WHERE ts_code = '{ts_code}' 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """)
                    fi_data = cursor.fetchone()
                    
                    # 合并数据（放宽为任意一个来源有数据即可）
                    if dh_data or db_data:
                        stock_data = {
                            'ts_code': ts_code,
                            'symbol': stock['symbol'],
                            'name': stock['name'],
                            'industry': stock['industry'],
                            'market': stock['market'],
                            'exchange': stock['exchange'],
                            'area': stock['area'],
                            
                            # 行情数据
                            'close_price': float(dh_data['close_price']) if (dh_data and dh_data.get('close_price')) else None,
                            'change_pct': float(dh_data['change_pct']) if (dh_data and dh_data.get('change_pct')) else None,
                            'volume': float(dh_data['volume']) if (dh_data and dh_data.get('volume')) else None,
                            'amount': float(dh_data['amount']) if (dh_data and dh_data.get('amount')) else None,
                            'turnover_rate': float(dh_data['turnover_rate']) if (dh_data and dh_data.get('turnover_rate')) else None,
                            'volume_ratio': float(dh_data['volume_ratio']) if (dh_data and dh_data.get('volume_ratio')) else None,
                            
                            # 估值数据 - 优先使用daily_basic
                            'pe': float(db_data['pe']) if (db_data and db_data.get('pe')) else (float(dh_data['pe']) if (dh_data and dh_data.get('pe')) else None),
                            'pb': float(db_data['pb']) if (db_data and db_data.get('pb')) else (float(dh_data['pb']) if (dh_data and dh_data.get('pb')) else None),
                            'ps': float(db_data['ps']) if (db_data and db_data.get('ps')) else (float(dh_data['ps']) if (dh_data and dh_data.get('ps')) else None),
                            'pe_ttm': float(db_data['pe_ttm']) if (db_data and db_data.get('pe_ttm')) else None,
                            'ps_ttm': float(db_data['ps_ttm']) if (db_data and db_data.get('ps_ttm')) else None,
                            'pcf': float(dh_data['pcf']) if (dh_data and dh_data.get('pcf')) else None,
                            
                            # 市值数据
                            'market_cap': float(db_data['total_mv']) if (db_data and db_data.get('total_mv')) else (float(dh_data['market_cap']) if (dh_data and dh_data.get('market_cap')) else None),
                            'circ_mv': float(db_data['circ_mv']) if (db_data and db_data.get('circ_mv')) else (float(dh_data['circ_mv']) if (dh_data and dh_data.get('circ_mv')) else None),
                            
                            # 财务指标数据
                            'roe': float(fi_data['roe']) if (fi_data and fi_data.get('roe')) else None,
                            'roa': float(fi_data['roa']) if (fi_data and fi_data.get('roa')) else None,
                            'gross_margin': float(fi_data['gross_margin']) if (fi_data and fi_data.get('gross_margin')) else None,
                            'net_margin': float(fi_data['net_margin']) if (fi_data and fi_data.get('net_margin')) else None,
                            'revenue_growth': float(fi_data['revenue_growth']) if (fi_data and fi_data.get('revenue_growth')) else None,
                            'profit_growth': float(fi_data['profit_growth']) if (fi_data and fi_data.get('profit_growth')) else None,
                            'debt_ratio': float(fi_data['debt_ratio']) if (fi_data and fi_data.get('debt_ratio')) else None,
                            'current_ratio': float(fi_data['current_ratio']) if (fi_data and fi_data.get('current_ratio')) else None,
                            'eps': float(fi_data['eps']) if (fi_data and fi_data.get('eps')) else None,
                            'pb_mrq': float(fi_data['pb_mrq']) if (fi_data and fi_data.get('pb_mrq')) else None,
                            
                            # 计算技术指标
                            'daily_return_pct': float(dh_data['change_pct']) if (dh_data and dh_data.get('change_pct')) else 0,
                            'price_position_pct': 50,  # 默认中位
                            'amplitude_pct': 0,  # 默认值
                        }
                        
                        screening_data.append(stock_data)
                
                logger.info(f"获取到 {len(screening_data)} 条完整数据")
                
                # 转换为DataFrame
                df = pd.DataFrame(screening_data)
                
                if not df.empty:
                    # 数据质量检查
                    pe_count = df['pe'].notna().sum()
                    pb_count = df['pb'].notna().sum()
                    close_count = df['close_price'].notna().sum()
                    market_cap_count = df['market_cap'].notna().sum()
                    
                    # 财务指标数据质量检查
                    roe_count = df['roe'].notna().sum()
                    roa_count = df['roa'].notna().sum()
                    gross_margin_count = df['gross_margin'].notna().sum()
                    net_margin_count = df['net_margin'].notna().sum()
                    
                    logger.info(f"数据质量: 收盘价{close_count}条, PE数据{pe_count}条, PB数据{pb_count}条, 市值{market_cap_count}条")
                    logger.info(f"财务指标: ROE{roe_count}条, ROA{roa_count}条, 毛利率{gross_margin_count}条, 净利率{net_margin_count}条")
                    
                    # 计算衍生指标
                    df = self._calculate_advanced_indicators(df)
                
                return df
                
        except Exception as e:
            logger.error(f"获取基础数据失败: {e}")
            return pd.DataFrame()
    
    def _calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算高级技术和基本面指标"""
        try:
            # 1. 估值指标分类
            if 'pe' in df.columns:
                df['pe_level'] = pd.cut(
                    df['pe'], 
                    bins=[0, 15, 25, 50, 100, float('inf')], 
                    labels=['低估值', '合理估值', '偏高估值', '高估值', '超高估值']
                )
                # PE合理性评分 (0-100)
                df['pe_score'] = np.where(
                    df['pe'] <= 15, 100,
                    np.where(df['pe'] <= 25, 80,
                    np.where(df['pe'] <= 50, 60,
                    np.where(df['pe'] <= 100, 30, 10)))
                )
            
            if 'pb' in df.columns:
                df['pb_level'] = pd.cut(
                    df['pb'], 
                    bins=[0, 1, 2, 3, 5, float('inf')], 
                    labels=['破净', '低PB', '合理PB', '偏高PB', '高PB']
                )
                # PB合理性评分
                df['pb_score'] = np.where(
                    df['pb'] <= 1, 100,
                    np.where(df['pb'] <= 2, 80,
                    np.where(df['pb'] <= 3, 60,
                    np.where(df['pb'] <= 5, 40, 20)))
                )
            
            # 2. 市值分类
            if 'market_cap' in df.columns:
                df['market_cap_level'] = pd.cut(
                    df['market_cap'] / 10000,  # 转换为亿元
                    bins=[0, 50, 200, 1000, float('inf')], 
                    labels=['小盘股', '中小盘', '中大盘', '大盘股']
                )
                
                # 市值亿元
                df['market_cap_yi'] = df['market_cap'] / 10000
            
            # 3. 流动性指标
            if 'turnover_rate' in df.columns:
                df['liquidity_level'] = pd.cut(
                    df['turnover_rate'], 
                    bins=[0, 1, 3, 7, 15, float('inf')], 
                    labels=['低流动性', '一般', '活跃', '非常活跃', '超活跃']
                )
                
                # 流动性评分
                df['liquidity_score'] = np.where(
                    df['turnover_rate'] < 0.5, 20,
                    np.where(df['turnover_rate'] < 1, 40,
                    np.where(df['turnover_rate'] < 3, 60,
                    np.where(df['turnover_rate'] < 7, 80, 100)))
                )
            
            # 4. 涨跌幅分析
            if 'change_pct' in df.columns:
                df['trend_level'] = pd.cut(
                    df['change_pct'], 
                    bins=[-float('inf'), -7, -3, -1, 1, 3, 7, float('inf')], 
                    labels=['大跌', '下跌', '微跌', '平稳', '微涨', '上涨', '大涨']
                )
                
                # 趋势强度评分
                df['trend_strength'] = np.abs(df['change_pct'])
            
            # 5. 量价关系
            if 'volume_ratio' in df.columns and 'change_pct' in df.columns:
                # 量价配合度 (成交量放大 + 价格上涨 = 好信号)
                df['volume_price_match'] = np.where(
                    (df['volume_ratio'] > 1.5) & (df['change_pct'] > 0), 100,
                    np.where((df['volume_ratio'] > 1.2) & (df['change_pct'] > 0), 80,
                    np.where((df['volume_ratio'] < 0.8) & (df['change_pct'] < 0), 60,
                    np.where((df['volume_ratio'] > 1.5) & (df['change_pct'] < 0), 20, 50)))
                )
            
            # 6. 技术位置指标
            if 'price_position_pct' in df.columns:
                df['technical_position'] = pd.cut(
                    df['price_position_pct'], 
                    bins=[0, 20, 40, 60, 80, 100], 
                    labels=['底部', '偏低', '中位', '偏高', '顶部']
                )
            
            # 7. 综合评分计算
            score_columns = ['pe_score', 'pb_score', 'liquidity_score']
            available_scores = [col for col in score_columns if col in df.columns]
            
            if available_scores:
                df['fundamental_score'] = df[available_scores].mean(axis=1)
            
            # 8. 行业相对表现 (如果有足够数据)
            if 'industry' in df.columns and 'change_pct' in df.columns:
                industry_avg = df.groupby('industry')['change_pct'].transform('mean')
                df['industry_relative_performance'] = df['change_pct'] - industry_avg
            
            # 9. 风险等级评估
            risk_factors = []
            if 'pe' in df.columns:
                risk_factors.append(np.where(df['pe'] > 50, 1, 0))  # 高PE风险
            if 'pb' in df.columns:
                risk_factors.append(np.where(df['pb'] > 5, 1, 0))   # 高PB风险
            if 'turnover_rate' in df.columns:
                risk_factors.append(np.where(df['turnover_rate'] > 15, 1, 0))  # 高换手风险
            
            if risk_factors:
                df['risk_level'] = sum(risk_factors)
                df['risk_category'] = pd.cut(
                    df['risk_level'], 
                    bins=[-1, 0, 1, 2, 3], 
                    labels=['低风险', '中低风险', '中高风险', '高风险']
                )
            
            # 10. 添加技术指标计算
            df = self._add_technical_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"计算高级指标失败: {e}")
            return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """为每只股票添加技术指标"""
        try:
            if df.empty or 'ts_code' not in df.columns:
                return df
            
            logger.info(f"开始计算技术指标，股票数量: {len(df)}")
            
            # 批量获取历史数据并计算技术指标
            stock_data_dict = {}
            
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                for ts_code in df['ts_code'].unique():
                    try:
                        # 获取最近60个交易日的数据
                        cursor.execute("""
                            SELECT trade_date, 
                                   open_price as open, 
                                   high_price as high, 
                                   low_price as low, 
                                   close_price as close, 
                                   volume
                            FROM daily_history
                            WHERE ts_code = %s
                            ORDER BY trade_date DESC
                            LIMIT 60
                        """, (ts_code,))
                        
                        rows = cursor.fetchall()
                        
                        if rows and len(rows) >= 60:
                            # 转换为DataFrame
                            hist_df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
                            hist_df = hist_df.sort_values('trade_date').reset_index(drop=True)
                            stock_data_dict[ts_code] = hist_df
                        
                    except Exception as e:
                        logger.error(f"获取{ts_code}历史数据失败: {e}")
                        continue
            
            # 批量计算技术指标
            if stock_data_dict:
                logger.info(f"获取到{len(stock_data_dict)}只股票的历史数据，开始计算技术指标")
                tech_indicators = batch_calculate_indicators(stock_data_dict)
                
                # 将技术指标合并到主DataFrame
                for ts_code, indicators in tech_indicators.items():
                    mask = df['ts_code'] == ts_code
                    for indicator_name, value in indicators.items():
                        df.loc[mask, indicator_name] = value
                
                logger.info(f"技术指标计算完成")
            else:
                logger.warning("没有获取到足够的历史数据来计算技术指标")
            
            return df
            
        except Exception as e:
            logger.error(f"添加技术指标失败: {e}")
            return df
    
    async def _apply_screening_conditions(self, df: pd.DataFrame, conditions) -> pd.DataFrame:
        """应用筛选条件"""
        try:
            print(f"[DEBUG] 开始应用筛选条件，输入数据行数: {len(df)}", flush=True)
            print(f"[DEBUG] 条件类型: {type(conditions)}, 条件内容: {conditions}", flush=True)
            
            # 文件调试
            with open('debug_screening.log', 'a', encoding='utf-8') as f:
                f.write(f"[DEBUG] _apply_screening_conditions 开始，输入数据行数: {len(df)}\n")
                f.write(f"[DEBUG] 条件类型: {type(conditions)}, 条件内容: {conditions}\n")
            
            logger.info(f"开始应用筛选条件，输入数据行数: {len(df)}")
            logger.info(f"条件类型: {type(conditions)}, 条件内容: {conditions}")
            
            filtered_df = df.copy()
            
            # 处理条件数组格式：[{"field": "roe", "operator": ">=", "value": 0.1}]
            if isinstance(conditions, list):
                condition_list = conditions
                print(f"[DEBUG] 使用条件数组格式，条件数量: {len(condition_list)}", flush=True)
                logger.info(f"使用条件数组格式，条件数量: {len(condition_list)}")
                
                # 文件调试
                with open('debug_screening.log', 'a', encoding='utf-8') as f:
                    f.write(f"[DEBUG] 使用条件数组格式，条件数量: {len(condition_list)}\n")
                
                for condition in condition_list:
                    field = condition.get('field')
                    operator = condition.get('operator')
                    value = condition.get('value')
                    
                    print(f"[DEBUG] 处理条件: {field} {operator} {value}", flush=True)
                    logger.info(f"处理条件: {field} {operator} {value}")
                    
                    # 文件调试
                    with open('debug_screening.log', 'a', encoding='utf-8') as f:
                        f.write(f"[DEBUG] 处理条件: {field} {operator} {value}\n")
                    
                    if not field or field not in df.columns:
                        print(f"[DEBUG] 字段 {field} 不存在于数据中，可用字段: {list(df.columns)}", flush=True)
                        logger.warning(f"字段 {field} 不存在于数据中，可用字段: {list(df.columns)}")
                        
                        # 文件调试
                        with open('debug_screening.log', 'a', encoding='utf-8') as f:
                            f.write(f"[DEBUG] 字段 {field} 不存在于数据中，可用字段: {list(df.columns)}\n")
                        continue
                    
                    # 检查字段数据
                    field_data = df[field]
                    non_null_count = field_data.notna().sum()
                    print(f"[DEBUG] 字段 {field} 非空值数量: {non_null_count}/{len(df)}", flush=True)
                    logger.info(f"字段 {field} 非空值数量: {non_null_count}/{len(df)}")
                    
                    # 文件调试
                    with open('debug_screening.log', 'a', encoding='utf-8') as f:
                        f.write(f"[DEBUG] 字段 {field} 非空值数量: {non_null_count}/{len(df)}\n")
                    
                    # 应用操作符
                    if operator == '>=':
                        before_count = len(filtered_df)
                        filtered_df = filtered_df[filtered_df[field] >= value]
                        after_count = len(filtered_df)
                        print(f"[DEBUG] 应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}", flush=True)
                        logger.info(f"应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}")
                        
                        # 文件调试
                        with open('debug_screening.log', 'a', encoding='utf-8') as f:
                            f.write(f"[DEBUG] 应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}\n")
                    elif operator == '<=':
                        filtered_df = filtered_df[filtered_df[field] <= value]
                    elif operator == '>':
                        filtered_df = filtered_df[filtered_df[field] > value]
                    elif operator == '<':
                        filtered_df = filtered_df[filtered_df[field] < value]
                    elif operator == '==':
                        filtered_df = filtered_df[filtered_df[field] == value]
                    elif operator == '!=':
                        filtered_df = filtered_df[filtered_df[field] != value]
                    elif operator == 'in':
                        if isinstance(value, (list, tuple)):
                            filtered_df = filtered_df[filtered_df[field].isin(value)]
                    elif operator == 'not_in':
                        if isinstance(value, (list, tuple)):
                            filtered_df = filtered_df[~filtered_df[field].isin(value)]
                    
                    logger.info(f"应用条件 {field} {operator} {value}，剩余股票数: {len(filtered_df)}")
            
            # 处理新的条件格式：{"conditions": [{"field": "roe", "operator": ">=", "value": 0.1}]}
            elif isinstance(conditions, dict) and 'conditions' in conditions:
                condition_list = conditions['conditions']
                print(f"[DEBUG] 使用新格式条件，条件数量: {len(condition_list)}", flush=True)
                logger.info(f"使用新格式条件，条件数量: {len(condition_list)}")
                
                # 文件调试
                with open('debug_screening.log', 'a', encoding='utf-8') as f:
                    f.write(f"[DEBUG] 使用新格式条件，条件数量: {len(condition_list)}\n")
                
                for condition in condition_list:
                    field = condition.get('field')
                    operator = condition.get('operator')
                    value = condition.get('value')
                    
                    print(f"[DEBUG] 处理条件: {field} {operator} {value}", flush=True)
                    logger.info(f"处理条件: {field} {operator} {value}")
                    
                    # 文件调试
                    with open('debug_screening.log', 'a', encoding='utf-8') as f:
                        f.write(f"[DEBUG] 处理条件: {field} {operator} {value}\n")
                    
                    if not field or field not in df.columns:
                        print(f"[DEBUG] 字段 {field} 不存在于数据中，可用字段: {list(df.columns)}", flush=True)
                        logger.warning(f"字段 {field} 不存在于数据中，可用字段: {list(df.columns)}")
                        
                        # 文件调试
                        with open('debug_screening.log', 'a', encoding='utf-8') as f:
                            f.write(f"[DEBUG] 字段 {field} 不存在于数据中，可用字段: {list(df.columns)}\n")
                        continue
                    
                    # 检查字段数据
                    field_data = df[field]
                    non_null_count = field_data.notna().sum()
                    print(f"[DEBUG] 字段 {field} 非空值数量: {non_null_count}/{len(df)}", flush=True)
                    logger.info(f"字段 {field} 非空值数量: {non_null_count}/{len(df)}")
                    
                    # 文件调试
                    with open('debug_screening.log', 'a', encoding='utf-8') as f:
                        f.write(f"[DEBUG] 字段 {field} 非空值数量: {non_null_count}/{len(df)}\n")
                    
                    # 应用操作符
                    if operator == '>=':
                        before_count = len(filtered_df)
                        filtered_df = filtered_df[filtered_df[field] >= value]
                        after_count = len(filtered_df)
                        print(f"[DEBUG] 应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}", flush=True)
                        logger.info(f"应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}")
                        
                        # 文件调试
                        with open('debug_screening.log', 'a', encoding='utf-8') as f:
                            f.write(f"[DEBUG] 应用 {field} >= {value}，筛选前: {before_count}，筛选后: {after_count}\n")
                    elif operator == '<=':
                        filtered_df = filtered_df[filtered_df[field] <= value]
                    elif operator == '>':
                        filtered_df = filtered_df[filtered_df[field] > value]
                    elif operator == '<':
                        filtered_df = filtered_df[filtered_df[field] < value]
                    elif operator == '==':
                        filtered_df = filtered_df[filtered_df[field] == value]
                    elif operator == '!=':
                        filtered_df = filtered_df[filtered_df[field] != value]
                    elif operator == 'in':
                        if isinstance(value, (list, tuple)):
                            filtered_df = filtered_df[filtered_df[field].isin(value)]
                    elif operator == 'not_in':
                        if isinstance(value, (list, tuple)):
                            filtered_df = filtered_df[~filtered_df[field].isin(value)]
                    
                    logger.info(f"应用条件 {field} {operator} {value}，剩余股票数: {len(filtered_df)}")
            
            # 处理旧的条件格式：直接的字段-值映射
            else:
                for field, condition in conditions.items():
                    if field not in df.columns:
                        print(f"[DEBUG] 字段 {field} 不在数据列中，跳过", flush=True)
                        logger.warning(f"字段 {field} 不在数据列中，跳过")
                        continue

                    if isinstance(condition, dict):
                        # 范围条件
                        min_val = condition.get('min')
                        max_val = condition.get('max')

                        before_count = len(filtered_df)
                        if min_val is not None:
                            filtered_df = filtered_df[filtered_df[field] >= min_val]
                            print(f"[DEBUG] 应用 {field} >= {min_val}，筛选前: {before_count}，筛选后: {len(filtered_df)}", flush=True)
                            logger.info(f"应用 {field} >= {min_val}，筛选前: {before_count}，筛选后: {len(filtered_df)}")

                        before_count = len(filtered_df)
                        if max_val is not None:
                            filtered_df = filtered_df[filtered_df[field] <= max_val]
                            print(f"[DEBUG] 应用 {field} <= {max_val}，筛选前: {before_count}，筛选后: {len(filtered_df)}", flush=True)
                            logger.info(f"应用 {field} <= {max_val}，筛选前: {before_count}，筛选后: {len(filtered_df)}")
                    
                    elif isinstance(condition, (list, tuple)):
                        # 枚举条件
                        filtered_df = filtered_df[filtered_df[field].isin(condition)]
                    
                    elif isinstance(condition, bool):
                        # 布尔条件
                        if condition:
                            filtered_df = filtered_df[filtered_df[field].notna()]
                        else:
                            filtered_df = filtered_df[filtered_df[field].isna()]
            
            return filtered_df

        except Exception as e:
            logger.error(f"应用筛选条件失败: {e}")
            # 如果筛选过程出错，返回空DataFrame而不是原始数据
            return pd.DataFrame()
    
    async def _apply_sorting_rules(self, df: pd.DataFrame, sort_rules: Dict) -> pd.DataFrame:
        """应用排序规则"""
        try:
            if not sort_rules or df.empty:
                return df
            
            sort_columns = []
            sort_ascending = []
            
            for field, direction in sort_rules.items():
                if field in df.columns:
                    sort_columns.append(field)
                    sort_ascending.append(direction.lower() == 'asc')
            
            if sort_columns:
                df = df.sort_values(sort_columns, ascending=sort_ascending)
            
            return df
            
        except Exception as e:
            logger.error(f"应用排序规则失败: {e}")
            return df
    
    async def _calculate_composite_score(self, df: pd.DataFrame, strategy: Dict) -> pd.DataFrame:
        """计算综合评分"""
        try:
            if df.empty:
                return df
            
            config = strategy.get('config', {})
            strategy_type = strategy.get('strategy_type', 'mixed')
            
            # 初始化评分
            df['composite_score'] = 0.0
            
            if strategy_type == 'fundamental':
                # 基本面评分
                df = self._calculate_fundamental_score(df, config)
            
            elif strategy_type == 'technical':
                # 技术面评分
                df = self._calculate_technical_score(df, config)
            
            elif strategy_type == 'mixed':
                # 综合评分
                fundamental_weight = config.get('fundamental_weight', 0.6)
                technical_weight = config.get('technical_weight', 0.4)
                
                df = self._calculate_fundamental_score(df, config)
                df = self._calculate_technical_score(df, config)
                
                df['composite_score'] = (
                    df.get('fundamental_score', 0) * fundamental_weight +
                    df.get('technical_score', 0) * technical_weight
                )
            
            # 按评分排序
            df = df.sort_values('composite_score', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"计算综合评分失败: {e}")
            return df
    
    def _calculate_fundamental_score(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """计算基本面评分"""
        try:
            df['fundamental_score'] = 0.0
            
            # ROE评分 (0-30分)
            if 'roe' in df.columns:
                roe_weight = config.get('weight_roe', 0.3)
                df['roe_score'] = np.where(
                    df['roe'].notna(),
                    np.clip(df['roe'] / 20 * 30, 0, 30),
                    0
                )
                df['fundamental_score'] += df['roe_score'] * roe_weight
            
            # PE评分 (0-25分，越低越好)
            if 'pe_ttm' in df.columns:
                pe_weight = config.get('weight_pe', 0.2)
                df['pe_score'] = np.where(
                    (df['pe_ttm'].notna()) & (df['pe_ttm'] > 0),
                    np.clip(25 - df['pe_ttm'] / 2, 0, 25),
                    0
                )
                df['fundamental_score'] += df['pe_score'] * pe_weight
            
            # 成长性评分 (0-25分)
            if 'revenue_growth' in df.columns:
                growth_weight = config.get('weight_growth', 0.3)
                df['growth_score'] = np.where(
                    df['revenue_growth'].notna(),
                    np.clip(df['revenue_growth'] / 2, 0, 25),
                    0
                )
                df['fundamental_score'] += df['growth_score'] * growth_weight
            
            # 财务健康评分 (0-20分)
            if 'debt_ratio' in df.columns:
                health_weight = config.get('weight_health', 0.2)
                df['health_score'] = np.where(
                    df['debt_ratio'].notna(),
                    np.clip(20 - df['debt_ratio'] / 5, 0, 20),
                    0
                )
                df['fundamental_score'] += df['health_score'] * health_weight
            
            return df
            
        except Exception as e:
            logger.error(f"计算基本面评分失败: {e}")
            return df
    
    def _calculate_technical_score(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """计算技术面评分"""
        try:
            df['technical_score'] = 0.0
            
            # 趋势评分 (0-40分)
            if all(col in df.columns for col in ['close_price', 'ma5', 'ma20']):
                trend_weight = config.get('weight_trend', 0.4)
                
                # 价格相对均线位置
                df['ma_score'] = np.where(
                    (df['close_price'].notna()) & (df['ma5'].notna()) & (df['ma20'].notna()),
                    np.where(df['close_price'] > df['ma5'], 20, 0) +
                    np.where(df['close_price'] > df['ma20'], 20, 0),
                    0
                )
                df['technical_score'] += df['ma_score'] * trend_weight
            
            # 动量评分 (0-30分)
            if 'rsi12' in df.columns:
                momentum_weight = config.get('weight_momentum', 0.3)
                df['rsi_score'] = np.where(
                    df['rsi12'].notna(),
                    np.where(
                        (df['rsi12'] >= 30) & (df['rsi12'] <= 70), 30,
                        np.where(df['rsi12'] < 30, 20, 10)
                    ),
                    0
                )
                df['technical_score'] += df['rsi_score'] * momentum_weight
            
            # 成交量评分 (0-30分)
            if 'turnover_rate' in df.columns:
                volume_weight = config.get('weight_volume', 0.3)
                df['volume_score'] = np.where(
                    df['turnover_rate'].notna(),
                    np.clip(df['turnover_rate'] * 3, 0, 30),
                    0
                )
                df['technical_score'] += df['volume_score'] * volume_weight
            
            return df
            
        except Exception as e:
            logger.error(f"计算技术面评分失败: {e}")
            return df
    
    def _format_screening_results(self, df: pd.DataFrame) -> List[Dict]:
        """格式化筛选结果"""
        try:
            results = []
            
            for _, row in df.head(100).iterrows():  # 限制返回100个结果
                result = {
                    'ts_code': row.get('ts_code'),
                    'symbol': row.get('symbol'),
                    'name': row.get('name'),
                    'industry': row.get('industry'),
                    'market': row.get('market'),
                    'close_price': float(row['close_price']) if pd.notna(row.get('close_price')) else None,
                    'change_pct': float(row['change_pct']) if pd.notna(row.get('change_pct')) else None,
                    'turnover_rate': float(row['turnover_rate']) if pd.notna(row.get('turnover_rate')) else None,
                    'pe': float(row['pe']) if pd.notna(row.get('pe')) else None,
                    'pb': float(row['pb']) if pd.notna(row.get('pb')) else None,
                    'market_cap': float(row['market_cap']) if pd.notna(row.get('market_cap')) else None,
                    'roe': float(row['roe']) if pd.notna(row.get('roe')) else None,
                    'revenue_growth': float(row['revenue_growth']) if pd.notna(row.get('revenue_growth')) else None,
                    # 新增财务指标
                    'profit_growth': float(row['profit_growth']) if pd.notna(row.get('profit_growth')) else None,
                    'debt_ratio': float(row['debt_ratio']) if pd.notna(row.get('debt_ratio')) else None,
                    'current_ratio': float(row['current_ratio']) if pd.notna(row.get('current_ratio')) else None,
                    'quick_ratio': float(row['quick_ratio']) if pd.notna(row.get('quick_ratio')) else None,
                    'gross_margin': float(row['gross_margin']) if pd.notna(row.get('gross_margin')) else None,
                    'net_margin': float(row['net_margin']) if pd.notna(row.get('net_margin')) else None,
                    'roa': float(row['roa']) if pd.notna(row.get('roa')) else None,
                    'composite_score': float(row['composite_score']) if pd.notna(row.get('composite_score')) else 0,
                    'rank': len(results) + 1
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"格式化结果失败: {e}")
            return []
    
    def _generate_summary_stats(self, df: pd.DataFrame, strategy: Dict) -> Dict:
        """生成汇总统计"""
        try:
            if df.empty:
                return {}
            
            summary = {
                'total_count': len(df),
                'avg_score': float(df['composite_score'].mean()) if 'composite_score' in df.columns else 0,
                'industry_distribution': df['industry'].value_counts().head(10).to_dict() if 'industry' in df.columns else {},
                'market_distribution': df['market'].value_counts().to_dict() if 'market' in df.columns else {},
                'score_distribution': {
                    'excellent': len(df[df.get('composite_score', 0) >= 80]),
                    'good': len(df[(df.get('composite_score', 0) >= 60) & (df.get('composite_score', 0) < 80)]),
                    'average': len(df[(df.get('composite_score', 0) >= 40) & (df.get('composite_score', 0) < 60)]),
                    'poor': len(df[df.get('composite_score', 0) < 40])
                }
            }
            
            # 添加关键指标统计
            if 'roe' in df.columns:
                summary['avg_roe'] = float(df['roe'].mean()) if df['roe'].notna().any() else None
            
            if 'pe' in df.columns:
                summary['avg_pe'] = float(df['pe'].mean()) if df['pe'].notna().any() else None
            
            if 'market_cap' in df.columns:
                summary['avg_market_cap'] = float(df['market_cap'].mean()) if df['market_cap'].notna().any() else None
            
            return summary
            
        except Exception as e:
            logger.error(f"生成汇总统计失败: {e}")
            return {}
    
    async def _save_screening_result(self, result_id: int, screening_result: Dict, execution_time: int):
        """保存筛选结果"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                UPDATE screening_results 
                SET total_stocks = %s, filtered_stocks = %s, result_data = %s,
                    summary_stats = %s, execution_time = %s, status = 'completed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                
                cursor.execute(sql, (
                    screening_result['total_stocks'],
                    screening_result['filtered_stocks'],
                    json.dumps(screening_result, ensure_ascii=False),
                    json.dumps(screening_result['summary'], ensure_ascii=False),
                    execution_time,
                    result_id
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"保存筛选结果失败: {e}")
    
    async def _update_strategy_usage(self, strategy_id: int):
        """更新策略使用统计"""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                UPDATE screening_strategies 
                SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                
                cursor.execute(sql, (strategy_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新策略统计失败: {e}")


# 创建全局实例
stock_screening_service = StockScreeningService()