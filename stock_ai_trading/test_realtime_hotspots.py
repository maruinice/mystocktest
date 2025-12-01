#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试实时市场热点数据获取
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.market_hotspot_service import market_hotspot_service
import json

def test_realtime_hotspots():
    """测试实时热点数据获取"""
    print('=' * 60)
    print('测试获取实时涨幅榜（前5条）')
    print('=' * 60)
    
    result = market_hotspot_service.get_realtime_hotspots('gainers', 5)
    if result:
        for i, stock in enumerate(result, 1):
            print(f'{i}. {stock["code"]} {stock["name"]:6s} ¥{stock["price"]:7.2f} {stock["change_pct"]:+6.2f}%')
        print(f'\n✅ 成功获取 {len(result)} 条实时数据')
    else:
        print('❌ 获取失败')
    
    print('\n' + '=' * 60)
    print('测试完整API响应')
    print('=' * 60)
    
    api_result = market_hotspot_service.get_market_hotspots('gainers', 3)
    print(json.dumps(api_result, ensure_ascii=False, indent=2))
    
    if api_result.get('success'):
        data_source = api_result['data'].get('data_source', 'unknown')
        print(f'\n✅ API调用成功，数据来源: {data_source}')
    else:
        print('\n❌ API调用失败')

if __name__ == '__main__':
    test_realtime_hotspots()
