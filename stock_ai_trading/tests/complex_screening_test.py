#!/usr/bin/env python3
"""
复杂财务指标筛选测试脚本
测试多种财务指标的组合筛选功能
"""

import requests
import json
import time

def test_complex_screening():
    """测试复杂的财务指标筛选"""
    
    # 测试用例1: 多条件筛选 - 高ROE + 低PE
    print("=== 测试用例1: 高ROE + 低PE ===")
    screening_data_1 = {
        "strategy_id": 1,  # 使用数据库中存在的策略ID
        "conditions": [
            {"field": "roe", "operator": ">=", "value": 0.15},  # ROE >= 15%
            {"field": "pe", "operator": "<=", "value": 30}      # PE <= 30
        ],
        "strategy_name": "高ROE低PE策略",
        "strategy_type": "fundamental"
    }
    
    response_1 = requests.post(
        "http://localhost:5000/api/screening/execute",
        json=screening_data_1,
        headers={"Content-Type": "application/json"}
    )
    
    if response_1.status_code == 200:
        result_1 = response_1.json()
        data = result_1.get('data', {})
        print(f"筛选结果: 找到 {data.get('filtered_stocks', 0)} 只股票")
        results = data.get('results', [])
        if results:
            print("前3只股票:")
            for i, stock in enumerate(results[:3]):
                roe = stock.get('roe', 'N/A')
                pe = stock.get('pe', 'N/A')
                roe_str = f"{roe:.2f}%" if isinstance(roe, (int, float)) else str(roe)
                pe_str = f"{pe:.2f}" if isinstance(pe, (int, float)) else str(pe)
                print(f"  {i+1}. {stock.get('name', 'N/A')} - ROE: {roe_str}, PE: {pe_str}")
    else:
        print(f"请求失败: {response_1.status_code}")
        print(response_1.text)
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2: 市值筛选
    print("=== 测试用例2: 大市值股票 ===")
    screening_data_2 = {
        "strategy_id": 2,  # 使用数据库中存在的策略ID
        "conditions": [
            {"field": "market_cap", "operator": ">=", "value": 30000000}  # 市值 >= 3000万
        ],
        "strategy_name": "大市值策略",
        "strategy_type": "fundamental"
    }
    
    response_2 = requests.post(
        "http://localhost:5000/api/screening/execute",
        json=screening_data_2,
        headers={"Content-Type": "application/json"}
    )
    
    if response_2.status_code == 200:
        result_2 = response_2.json()
        data = result_2.get('data', {})
        print(f"筛选结果: 找到 {data.get('filtered_stocks', 0)} 只股票")
        results = data.get('results', [])
        if results:
            print("前3只股票:")
            for i, stock in enumerate(results[:3]):
                market_cap = stock.get('market_cap', 'N/A')
                market_cap_str = f"{market_cap:,.0f}" if isinstance(market_cap, (int, float)) else str(market_cap)
                print(f"  {i+1}. {stock.get('name', 'N/A')} - 市值: {market_cap_str}")
    else:
        print(f"请求失败: {response_2.status_code}")
        print(response_2.text)
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3: 营收增长筛选
    print("=== 测试用例3: 高营收增长 ===")
    screening_data_3 = {
        "strategy_id": 3,  # 使用数据库中存在的策略ID
        "conditions": [
            {"field": "revenue_growth", "operator": ">=", "value": 10}  # 营收增长 >= 10%
        ],
        "strategy_name": "高增长策略",
        "strategy_type": "growth"
    }
    
    response_3 = requests.post(
        "http://localhost:5000/api/screening/execute",
        json=screening_data_3,
        headers={"Content-Type": "application/json"}
    )
    
    if response_3.status_code == 200:
        result_3 = response_3.json()
        data = result_3.get('data', {})
        print(f"筛选结果: 找到 {data.get('filtered_stocks', 0)} 只股票")
        results = data.get('results', [])
        if results:
            print("前3只股票:")
            for i, stock in enumerate(results[:3]):
                revenue_growth = stock.get('revenue_growth', 'N/A')
                profit_growth = stock.get('profit_growth', 'N/A')
                revenue_str = f"{revenue_growth:.2f}%" if isinstance(revenue_growth, (int, float)) else str(revenue_growth)
                profit_str = f"{profit_growth:.2f}%" if isinstance(profit_growth, (int, float)) else str(profit_growth)
                print(f"  {i+1}. {stock.get('name', 'N/A')} - 营收增长率: {revenue_str}, 净利润增长率: {profit_str}")
    else:
        print(f"请求失败: {response_3.status_code}")
        print(response_3.text)
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例4: 综合价值筛选
    print("=== 测试用例4: 综合价值筛选 ===")
    screening_data_4 = {
        "strategy_id": 4,  # 使用数据库中存在的策略ID
        "conditions": [
            {"field": "roe", "operator": ">=", "value": 0.1},      # ROE >= 10%
            {"field": "pb", "operator": "<=", "value": 5},         # PB <= 5
            {"field": "pe", "operator": "<=", "value": 25},        # PE <= 25
            {"field": "market_cap", "operator": ">=", "value": 10000000}  # 市值 >= 1000万
        ],
        "strategy_name": "综合价值策略",
        "strategy_type": "value"
    }
    
    response_4 = requests.post(
        "http://localhost:5000/api/screening/execute",
        json=screening_data_4,
        headers={"Content-Type": "application/json"}
    )
    
    if response_4.status_code == 200:
        result_4 = response_4.json()
        data = result_4.get('data', {})
        print(f"筛选结果: 找到 {data.get('filtered_stocks', 0)} 只股票")
        results = data.get('results', [])
        if results:
            print("前3只股票:")
            for i, stock in enumerate(results[:3]):
                roe = stock.get('roe', 'N/A')
                pe = stock.get('pe', 'N/A')
                pb = stock.get('pb', 'N/A')
                market_cap = stock.get('market_cap', 'N/A')
                
                roe_str = f"{roe:.2f}%" if isinstance(roe, (int, float)) else str(roe)
                pe_str = f"{pe:.2f}" if isinstance(pe, (int, float)) else str(pe)
                pb_str = f"{pb:.2f}" if isinstance(pb, (int, float)) else str(pb)
                market_cap_str = f"{market_cap:,.0f}" if isinstance(market_cap, (int, float)) else str(market_cap)
                
                print(f"  {i+1}. {stock.get('name', 'N/A')} - ROE: {roe_str}, PE: {pe_str}, PB: {pb_str}, 市值: {market_cap_str}")
    else:
        print(f"请求失败: {response_4.status_code}")
        print(response_4.text)

if __name__ == "__main__":
    print("开始复杂财务指标筛选测试...")
    test_complex_screening()
    print("测试完成!")