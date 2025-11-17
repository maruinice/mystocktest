#!/usr/bin/env python3
"""
选股指标数据完整性检查脚本
检查前端配置的指标在数据库中的可用性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text
import pandas as pd

def check_database_tables():
    """检查数据库表和字段"""
    print("\n" + "="*80)
    print("数据库表和字段检查")
    print("="*80)
    
    db = next(get_db())
    
    # 1. 检查stock_basic表
    print("\n1. stock_basic 表:")
    result = db.execute(text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN list_status='L' THEN 1 END) as listed
        FROM stock_basic
    """)).fetchone()
    print(f"   总股票数: {result[0]}")
    print(f"   上市股票: {result[1]}")
    
    # 2. 检查daily_history表
    print("\n2. daily_history 表:")
    result = db.execute(text("""
        SELECT COUNT(DISTINCT ts_code) as stocks,
               COUNT(*) as records,
               MAX(trade_date) as latest_date
        FROM daily_history
    """)).fetchone()
    print(f"   有数据股票: {result[0]}")
    print(f"   总记录数: {result[1]}")
    print(f"   最新日期: {result[2]}")
    
    # 3. 检查daily_basic表
    print("\n3. daily_basic 表:")
    result = db.execute(text("""
        SELECT COUNT(DISTINCT ts_code) as stocks,
               COUNT(*) as records,
               COUNT(pe_ttm) as has_pe,
               COUNT(pb) as has_pb,
               COUNT(ps_ttm) as has_ps,
               COUNT(turnover_rate) as has_turnover,
               COUNT(volume_ratio) as has_volume_ratio,
               MAX(trade_date) as latest_date
        FROM daily_basic
    """)).fetchone()
    print(f"   有数据股票: {result[0]}")
    print(f"   总记录数: {result[1]}")
    print(f"   PE_TTM覆盖: {result[2]} ({result[2]/result[1]*100:.1f}%)")
    print(f"   PB覆盖: {result[3]} ({result[3]/result[1]*100:.1f}%)")
    print(f"   PS_TTM覆盖: {result[4]} ({result[4]/result[1]*100:.1f}%)")
    print(f"   换手率覆盖: {result[5]} ({result[5]/result[1]*100:.1f}%)")
    print(f"   量比覆盖: {result[6]} ({result[6]/result[1]*100:.1f}%)")
    print(f"   最新日期: {result[7]}")
    
    # 4. 检查financial_indicators表
    print("\n4. financial_indicators 表:")
    result = db.execute(text("""
        SELECT COUNT(DISTINCT ts_code) as stocks,
               COUNT(*) as records
        FROM financial_indicators
    """)).fetchone()
    print(f"   有数据股票: {result[0]}")
    print(f"   总记录数: {result[1]}")
    
    # 检查关键字段覆盖率
    result = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(roe) as has_roe,
            COUNT(roa) as has_roa,
            COUNT(gross_margin) as has_gross_margin,
            COUNT(netprofit_margin) as has_net_margin,
            COUNT(debt_to_assets) as has_debt_ratio,
            COUNT(current_ratio) as has_current_ratio,
            COUNT(quick_ratio) as has_quick_ratio,
            COUNT(eps) as has_eps,
            COUNT(pb_mrq) as has_pb_mrq
        FROM financial_indicators
    """)).fetchone()
    
    total = result[0]
    print(f"\n   字段覆盖率:")
    print(f"   - ROE: {result[1]} ({result[1]/total*100:.1f}%)")
    print(f"   - ROA: {result[2]} ({result[2]/total*100:.1f}%)")
    print(f"   - 毛利率: {result[3]} ({result[3]/total*100:.1f}%)")
    print(f"   - 净利率: {result[4]} ({result[4]/total*100:.1f}%)")
    print(f"   - 资产负债率: {result[5]} ({result[5]/total*100:.1f}%)")
    print(f"   - 流动比率: {result[6]} ({result[6]/total*100:.1f}%)")
    print(f"   - 速动比率: {result[7]} ({result[7]/total*100:.1f}%)")
    print(f"   - EPS: {result[8]} ({result[8]/total*100:.1f}%)")
    print(f"   - PB_MRQ: {result[9]} ({result[9]/total*100:.1f}%)")


def check_frontend_indicators():
    """检查前端配置的指标"""
    print("\n" + "="*80)
    print("前端指标配置检查")
    print("="*80)
    
    # 前端配置的指标
    indicators = {
        '基本面指标': {
            '盈利能力': ['roe', 'roa', 'gross_margin', 'net_margin', 'eps'],
            '成长性': ['revenue_growth', 'profit_growth'],
            '估值': ['pe_ttm', 'pb', 'ps_ttm', 'pb_mrq'],
            '财务健康': ['debt_ratio', 'current_ratio', 'quick_ratio']
        },
        '技术面指标': {
            '趋势': ['ma5', 'ma20', 'ma60'],
            '动量': ['rsi12', 'kdj_k', 'kdj_d']
        },
        '市场指标': {
            '基础': ['market_cap', 'change_pct', 'close_price'],
            '成交量': ['turnover_rate', 'volume_ratio']
        }
    }
    
    # 字段映射关系
    field_mapping = {
        'net_margin': 'netprofit_margin',
        'debt_ratio': 'debt_to_assets',
        'market_cap': 'total_mv',
        'change_pct': 'pct_chg',
        'close_price': 'close'
    }
    
    # 数据来源
    data_sources = {
        'roe': ('financial_indicators', 'roe', '✅'),
        'roa': ('financial_indicators', 'roa', '✅'),
        'gross_margin': ('financial_indicators', 'gross_margin', '✅'),
        'net_margin': ('financial_indicators', 'netprofit_margin', '⚠️'),
        'eps': ('financial_indicators', 'eps', '✅'),
        'revenue_growth': ('计算', '需要从历史数据计算', '❌'),
        'profit_growth': ('计算', '需要从历史数据计算', '❌'),
        'pe_ttm': ('daily_basic', 'pe_ttm', '✅'),
        'pb': ('daily_basic', 'pb', '✅'),
        'ps_ttm': ('daily_basic', 'ps_ttm', '✅'),
        'pb_mrq': ('financial_indicators', 'pb_mrq', '⚠️'),
        'debt_ratio': ('financial_indicators', 'debt_to_assets', '⚠️'),
        'current_ratio': ('financial_indicators', 'current_ratio', '✅'),
        'quick_ratio': ('financial_indicators', 'quick_ratio', '✅'),
        'ma5': ('计算', '从daily_history计算', '🔧'),
        'ma20': ('计算', '从daily_history计算', '🔧'),
        'ma60': ('计算', '从daily_history计算', '🔧'),
        'rsi12': ('计算', '从daily_history计算', '🔧'),
        'kdj_k': ('计算', '从daily_history计算', '🔧'),
        'kdj_d': ('计算', '从daily_history计算', '🔧'),
        'market_cap': ('daily_basic', 'total_mv', '✅'),
        'change_pct': ('daily_history', 'pct_chg', '✅'),
        'close_price': ('daily_history', 'close', '✅'),
        'turnover_rate': ('daily_basic', 'turnover_rate', '✅'),
        'volume_ratio': ('daily_basic', 'volume_ratio', '✅')
    }
    
    total_indicators = 0
    available_indicators = 0
    need_mapping = 0
    need_calculation = 0
    missing = 0
    
    for category, groups in indicators.items():
        print(f"\n{category}:")
        for group_name, indicator_list in groups.items():
            print(f"  {group_name}:")
            for indicator in indicator_list:
                total_indicators += 1
                source = data_sources.get(indicator, ('未知', '未知', '❌'))
                status = source[2]
                
                if status == '✅':
                    available_indicators += 1
                    status_text = "可用"
                elif status == '⚠️':
                    need_mapping += 1
                    status_text = "需映射"
                elif status == '🔧':
                    need_calculation += 1
                    status_text = "需计算"
                else:
                    missing += 1
                    status_text = "缺失"
                
                print(f"    {status} {indicator:20s} -> {source[0]:20s}.{source[1]:20s} ({status_text})")
    
    print("\n" + "-"*80)
    print("统计:")
    print(f"  总指标数: {total_indicators}")
    print(f"  ✅ 直接可用: {available_indicators} ({available_indicators/total_indicators*100:.1f}%)")
    print(f"  ⚠️  需要映射: {need_mapping} ({need_mapping/total_indicators*100:.1f}%)")
    print(f"  🔧 需要计算: {need_calculation} ({need_calculation/total_indicators*100:.1f}%)")
    print(f"  ❌ 数据缺失: {missing} ({missing/total_indicators*100:.1f}%)")
    print(f"  总体可用率: {(available_indicators+need_mapping+need_calculation)/total_indicators*100:.1f}%")


def check_field_mapping_issues():
    """检查字段映射问题"""
    print("\n" + "="*80)
    print("字段映射问题检查")
    print("="*80)
    
    issues = [
        {
            'frontend': 'net_margin',
            'backend': 'netprofit_margin',
            'table': 'financial_indicators',
            'issue': '字段名不一致',
            'fix': "将 'net_margin' 映射到 'netprofit_margin'"
        },
        {
            'frontend': 'debt_ratio',
            'backend': 'debt_to_assets',
            'table': 'financial_indicators',
            'issue': '字段名不一致',
            'fix': "将 'debt_ratio' 映射到 'debt_to_assets'"
        },
        {
            'frontend': 'market_cap',
            'backend': 'total_mv',
            'table': 'daily_basic',
            'issue': '字段名不一致',
            'fix': "将 'market_cap' 映射到 'total_mv'"
        }
    ]
    
    print("\n需要修复的字段映射:")
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['frontend']}:")
        print(f"   前端字段: {issue['frontend']}")
        print(f"   后端字段: {issue['backend']}")
        print(f"   数据表: {issue['table']}")
        print(f"   问题: {issue['issue']}")
        print(f"   修复方案: {issue['fix']}")


def generate_fix_code():
    """生成修复代码"""
    print("\n" + "="*80)
    print("修复代码生成")
    print("="*80)
    
    print("\n在 stock_screening_service.py 的 _get_base_screening_data() 方法中:")
    print("\n# 修改前:")
    print("'net_margin': float(fi_data['net_margin']) if (fi_data and fi_data.get('net_margin')) else None,")
    print("'debt_ratio': float(fi_data['debt_ratio']) if (fi_data and fi_data.get('debt_ratio')) else None,")
    
    print("\n# 修改后:")
    print("'net_margin': float(fi_data['netprofit_margin']) if (fi_data and fi_data.get('netprofit_margin')) else None,")
    print("'debt_ratio': float(fi_data['debt_to_assets']) if (fi_data and fi_data.get('debt_to_assets')) else None,")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("选股功能数据完整性检查")
    print("="*80)
    
    try:
        # 1. 检查数据库表
        check_database_tables()
        
        # 2. 检查前端指标配置
        check_frontend_indicators()
        
        # 3. 检查字段映射问题
        check_field_mapping_issues()
        
        # 4. 生成修复代码
        generate_fix_code()
        
        print("\n" + "="*80)
        print("检查完成！")
        print("="*80)
        print("\n详细分析报告请查看: STOCK_SCREENING_DATA_ANALYSIS.md")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
