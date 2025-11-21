#!/usr/bin/env python3
"""
筛选条件有效性分析脚本
对比前端定义的筛选条件与后端实际支持的字段，识别无效或未使用的条件
"""

import pymysql
import json
from typing import Dict, List, Set

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='stock_trading',
        charset='utf8mb4',
        autocommit=True
    )

def get_frontend_indicators() -> Dict:
    """获取前端定义的筛选指标"""
    return {
        'fundamental': {
            'profitability': [
                {'code': 'roe', 'name': '净资产收益率', 'unit': '%', 'range': [0, 50]},
                {'code': 'roa', 'name': '总资产收益率', 'unit': '%', 'range': [0, 30]},
                {'code': 'gross_margin', 'name': '毛利率', 'unit': '%', 'range': [0, 100]},
                {'code': 'net_margin', 'name': '净利率', 'unit': '%', 'range': [0, 50]}
            ],
            'growth': [
                {'code': 'revenue_growth', 'name': '营收增长率', 'unit': '%', 'range': [-50, 200]},
                {'code': 'profit_growth', 'name': '净利润增长率', 'unit': '%', 'range': [-100, 500]},
                {'code': 'eps_growth', 'name': 'EPS增长率', 'unit': '%', 'range': [-100, 500]}
            ],
            'valuation': [
                {'code': 'pe_ttm', 'name': '市盈率TTM', 'unit': '倍', 'range': [0, 100]},
                {'code': 'pb_mrq', 'name': '市净率MRQ', 'unit': '倍', 'range': [0, 20]},
                {'code': 'ps_ttm', 'name': '市销率TTM', 'unit': '倍', 'range': [0, 50]}
            ],
            'financial_health': [
                {'code': 'debt_ratio', 'name': '资产负债率', 'unit': '%', 'range': [0, 100]},
                {'code': 'current_ratio', 'name': '流动比率', 'unit': '倍', 'range': [0, 10]},
                {'code': 'quick_ratio', 'name': '速动比率', 'unit': '倍', 'range': [0, 10]}
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

def get_backend_supported_fields() -> Set[str]:
    """获取后端实际支持的字段（从数据库表结构和代码逻辑中提取）"""
    
    # 从数据库表结构获取可用字段
    db_fields = set()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查各个数据表的字段
            tables_to_check = [
                'stock_basic',
                'daily_history', 
                'daily_basic',
                'income',
                'balancesheet',
                'cashflow',
                'technical_indicators'
            ]
            
            for table in tables_to_check:
                try:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    for column in columns:
                        db_fields.add(column[0])  # column[0] is the field name
                    print(f"表 {table}: {len(columns)} 个字段")
                except Exception as e:
                    print(f"检查表 {table} 失败: {e}")
    
    except Exception as e:
        print(f"数据库连接失败: {e}")
    
    # 从后端代码逻辑中提取的支持字段
    backend_logic_fields = {
        # 基础信息
        'ts_code', 'symbol', 'name', 'industry', 'market', 'exchange', 'area',
        
        # 行情数据
        'close_price', 'change_pct', 'volume', 'amount', 'turnover_rate', 'volume_ratio',
        
        # 估值数据
        'pe', 'pb', 'ps', 'pe_ttm', 'ps_ttm', 'pcf',
        
        # 市值数据
        'market_cap', 'circ_mv',
        
        # 计算指标
        'daily_return_pct', 'price_position_pct', 'amplitude_pct',
        
        # 高级指标
        'pe_level', 'pe_score', 'pb_level', 'pb_score', 
        'market_cap_level', 'market_cap_yi',
        'liquidity_level', 'liquidity_score',
        'trend_level', 'trend_strength',
        'volume_price_match', 'technical_position',
        'fundamental_score', 'industry_relative_performance',
        'risk_level', 'risk_category',
        
        # 技术指标
        'ma5', 'ma20', 'ma60', 'rsi12', 'kdj_k', 'kdj_d',
        'macd_dif', 'macd_dea', 'macd_bar', 'kdj_j',
        'boll_upper', 'boll_mid', 'boll_lower',
        
        # 评分相关
        'composite_score', 'technical_score', 'roe_score', 'growth_score', 'health_score',
        'ma_score', 'rsi_score', 'volume_score'
    }
    
    # 合并数据库字段和逻辑字段
    all_supported_fields = db_fields.union(backend_logic_fields)
    
    print(f"数据库字段: {len(db_fields)} 个")
    print(f"后端逻辑字段: {len(backend_logic_fields)} 个")
    print(f"总支持字段: {len(all_supported_fields)} 个")
    
    return all_supported_fields

def extract_frontend_condition_codes(indicators: Dict) -> Set[str]:
    """提取前端定义的所有条件代码"""
    codes = set()
    
    for category, subcategories in indicators.items():
        for subcategory, items in subcategories.items():
            for item in items:
                codes.add(item['code'])
    
    return codes

def analyze_condition_effectiveness():
    """分析筛选条件的有效性"""
    print("=== 筛选条件有效性分析 ===\n")
    
    # 1. 获取前端定义的指标
    frontend_indicators = get_frontend_indicators()
    frontend_codes = extract_frontend_condition_codes(frontend_indicators)
    
    print(f"前端定义的筛选条件: {len(frontend_codes)} 个")
    print(f"条件列表: {sorted(frontend_codes)}\n")
    
    # 2. 获取后端支持的字段
    backend_fields = get_backend_supported_fields()
    
    print(f"后端支持的字段: {len(backend_fields)} 个\n")
    
    # 3. 分析有效性
    supported_conditions = frontend_codes.intersection(backend_fields)
    unsupported_conditions = frontend_codes - backend_fields
    unused_backend_fields = backend_fields - frontend_codes
    
    print("=== 分析结果 ===\n")
    
    print(f"✅ 有效的筛选条件 ({len(supported_conditions)} 个):")
    for condition in sorted(supported_conditions):
        print(f"  - {condition}")
    print()
    
    print(f"❌ 无效的筛选条件 ({len(unsupported_conditions)} 个):")
    for condition in sorted(unsupported_conditions):
        print(f"  - {condition}")
    print()
    
    print(f"🔍 后端支持但前端未使用的字段 ({len(unused_backend_fields)} 个):")
    # 只显示可能有用的字段，过滤掉内部字段
    useful_unused = [field for field in unused_backend_fields 
                    if not field.startswith(('id', 'created_at', 'updated_at', 'sync_', 'list_'))
                    and field not in ['ts_code', 'symbol', 'name']]
    
    for field in sorted(useful_unused)[:20]:  # 只显示前20个
        print(f"  - {field}")
    if len(useful_unused) > 20:
        print(f"  ... 还有 {len(useful_unused) - 20} 个字段")
    print()
    
    # 4. 详细分析无效条件
    if unsupported_conditions:
        print("=== 无效条件详细分析 ===\n")
        
        for condition in sorted(unsupported_conditions):
            # 查找该条件在前端的定义
            condition_info = None
            for category, subcategories in frontend_indicators.items():
                for subcategory, items in subcategories.items():
                    for item in items:
                        if item['code'] == condition:
                            condition_info = {
                                'category': category,
                                'subcategory': subcategory,
                                'name': item['name'],
                                'unit': item['unit']
                            }
                            break
                    if condition_info:
                        break
                if condition_info:
                    break
            
            if condition_info:
                print(f"条件: {condition}")
                print(f"  名称: {condition_info['name']}")
                print(f"  分类: {condition_info['category']} -> {condition_info['subcategory']}")
                print(f"  单位: {condition_info['unit']}")
                
                # 检查是否有相似的字段
                similar_fields = [field for field in backend_fields 
                                if condition.lower() in field.lower() or field.lower() in condition.lower()]
                if similar_fields:
                    print(f"  相似字段: {similar_fields}")
                print()
    
    # 5. 生成建议
    print("=== 改进建议 ===\n")
    
    effectiveness_rate = len(supported_conditions) / len(frontend_codes) * 100
    print(f"当前筛选条件有效率: {effectiveness_rate:.1f}%\n")
    
    if unsupported_conditions:
        print("🔧 需要处理的无效条件:")
        for condition in sorted(unsupported_conditions):
            print(f"  - {condition}: 建议删除或实现对应的数据获取逻辑")
        print()
    
    if useful_unused:
        print("💡 可以添加的新筛选条件:")
        priority_fields = ['roe', 'roa', 'debt_ratio', 'current_ratio', 'revenue_growth', 
                          'profit_growth', 'eps_growth', 'gross_margin', 'net_margin']
        
        for field in priority_fields:
            if field in useful_unused:
                print(f"  - {field}: 高优先级，建议添加到前端")
        
        other_useful = [f for f in sorted(useful_unused) if f not in priority_fields][:10]
        for field in other_useful:
            print(f"  - {field}: 可考虑添加")
        print()
    
    return {
        'frontend_conditions': len(frontend_codes),
        'backend_fields': len(backend_fields),
        'supported_conditions': len(supported_conditions),
        'unsupported_conditions': len(unsupported_conditions),
        'effectiveness_rate': effectiveness_rate,
        'unsupported_list': list(unsupported_conditions),
        'unused_backend_fields': list(useful_unused)
    }

if __name__ == "__main__":
    try:
        result = analyze_condition_effectiveness()
        
        print("=== 分析完成 ===")
        print(f"有效率: {result['effectiveness_rate']:.1f}%")
        print(f"需要处理的无效条件: {result['unsupported_conditions']} 个")
        print(f"可以利用的后端字段: {len(result['unused_backend_fields'])} 个")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()