#!/usr/bin/env python3
"""
详细分析财务数据表的结构和数据
"""

import pymysql
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    parsed = urlparse(database_url.replace('mysql+pymysql://', 'mysql://'))
    
    return pymysql.connect(
        host=parsed.hostname,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:],  # 去掉开头的 '/'
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def analyze_table(table_name: str):
    """详细分析表结构和数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print(f"📊 分析 {table_name.upper()} 表:")
        
        # 获取表结构
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        print(f"  🔍 表结构 ({len(columns)} 个字段):")
        for col in columns:
            print(f"    - {col['Field']:<20} {col['Type']:<20} {col['Null']:<5} {col['Key']:<5} {col['Default'] or ''}")
        
        # 获取数据统计
        cursor.execute(f"SELECT COUNT(*) as total_count FROM {table_name}")
        total_count = cursor.fetchone()['total_count']
        
        print(f"\n  📈 数据统计:")
        print(f"    总记录数: {total_count:,}")
        
        if total_count > 0:
            # 获取股票数量
            cursor.execute(f"SELECT COUNT(DISTINCT ts_code) as stock_count FROM {table_name}")
            stock_count = cursor.fetchone()['stock_count']
            print(f"    股票数量: {stock_count:,}")
            
            # 获取时间范围
            if 'ann_date' in [col['Field'] for col in columns]:
                cursor.execute(f"SELECT MIN(ann_date) as min_date, MAX(ann_date) as max_date FROM {table_name} WHERE ann_date IS NOT NULL")
                date_range = cursor.fetchone()
                if date_range['min_date'] and date_range['max_date']:
                    print(f"    时间范围: {date_range['min_date']} ~ {date_range['max_date']}")
            
            # 获取样本数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()
            
            print(f"\n  📋 样本数据:")
            for i, row in enumerate(sample_data, 1):
                print(f"    样本 {i}:")
                for key, value in row.items():
                    if value is not None:
                        print(f"      {key}: {value}")
                print()
        else:
            print("    ❌ 表中无数据")
        
        # 分析财务指标字段的数据完整性
        financial_fields = []
        for col in columns:
            field_name = col['Field'].lower()
            if any(keyword in field_name for keyword in ['roe', 'roa', 'margin', 'ratio', 'revenue', 'profit', 'assets', 'equity', 'debt', 'eps']):
                financial_fields.append(col['Field'])
        
        if financial_fields and total_count > 0:
            print(f"  💰 财务指标字段数据完整性:")
            for field in financial_fields:
                cursor.execute(f"SELECT COUNT(*) as non_null_count FROM {table_name} WHERE {field} IS NOT NULL AND {field} != 0")
                non_null_count = cursor.fetchone()['non_null_count']
                completeness = (non_null_count / total_count * 100) if total_count > 0 else 0
                print(f"    {field:<20}: {non_null_count:>6}/{total_count:<6} ({completeness:5.1f}%)")
        
        return columns, total_count
        
    except Exception as e:
        print(f"❌ 分析表 {table_name} 时出错: {e}")
        return [], 0
    finally:
        cursor.close()
        conn.close()

def suggest_screening_indicators():
    """基于实际数据建议可用的筛选指标"""
    
    print("\n💡 基于实际数据的筛选指标建议:")
    
    # 检查financial_indicators表的可用指标
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM financial_indicators")
        count = cursor.fetchone()['count']
        
        if count > 0:
            # 获取有数据的字段
            cursor.execute("DESCRIBE financial_indicators")
            columns = cursor.fetchall()
            
            available_indicators = []
            
            for col in columns:
                field = col['Field']
                if field in ['id', 'ts_code', 'ann_date', 'end_date', 'report_type']:
                    continue
                    
                # 检查字段数据完整性
                cursor.execute(f"SELECT COUNT(*) as non_null_count FROM financial_indicators WHERE {field} IS NOT NULL AND {field} != 0")
                non_null_count = cursor.fetchone()['non_null_count']
                
                if non_null_count > 0:
                    completeness = (non_null_count / count * 100)
                    available_indicators.append({
                        'field': field,
                        'count': non_null_count,
                        'completeness': completeness
                    })
            
            # 按完整性排序
            available_indicators.sort(key=lambda x: x['completeness'], reverse=True)
            
            print("  📊 financial_indicators 表可用指标 (按数据完整性排序):")
            for indicator in available_indicators:
                print(f"    {indicator['field']:<20}: {indicator['count']:>4} 条数据 ({indicator['completeness']:5.1f}%)")
            
            # 建议高质量指标
            high_quality_indicators = [ind for ind in available_indicators if ind['completeness'] >= 50]
            
            if high_quality_indicators:
                print(f"\n  ✅ 建议添加的高质量指标 (完整性 >= 50%):")
                
                indicator_mapping = {
                    'roe': {'name': 'ROE净资产收益率', 'unit': '%', 'range': [0, 50]},
                    'roa': {'name': 'ROA总资产收益率', 'unit': '%', 'range': [0, 20]},
                    'roic': {'name': 'ROIC投入资本回报率', 'unit': '%', 'range': [0, 30]},
                    'gross_margin': {'name': '毛利率', 'unit': '%', 'range': [0, 100]},
                    'net_margin': {'name': '净利率', 'unit': '%', 'range': [0, 50]},
                    'debt_ratio': {'name': '资产负债率', 'unit': '%', 'range': [0, 100]},
                    'current_ratio': {'name': '流动比率', 'unit': '倍', 'range': [0, 10]},
                    'quick_ratio': {'name': '速动比率', 'unit': '倍', 'range': [0, 5]},
                    'eps': {'name': '每股收益', 'unit': '元', 'range': [-10, 50]},
                    'bps': {'name': '每股净资产', 'unit': '元', 'range': [0, 100]},
                    'revenue_growth': {'name': '营收增长率', 'unit': '%', 'range': [-100, 500]},
                    'profit_growth': {'name': '净利润增长率', 'unit': '%', 'range': [-100, 1000]}
                }
                
                for indicator in high_quality_indicators:
                    field = indicator['field']
                    if field in indicator_mapping:
                        info = indicator_mapping[field]
                        print(f"    📈 {field}: {info['name']} ({info['unit']}) - 完整性 {indicator['completeness']:.1f}%")
        
    except Exception as e:
        print(f"❌ 分析指标建议时出错: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 开始详细分析财务数据表...\n")
    
    try:
        # 分析两个财务表
        tables = ['financial_data', 'financial_indicators']
        
        for table in tables:
            analyze_table(table)
            print("\n" + "="*80 + "\n")
        
        # 建议可用的筛选指标
        suggest_screening_indicators()
        
        print("\n✅ 财务数据表分析完成！")
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")