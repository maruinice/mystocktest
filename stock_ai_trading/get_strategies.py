#!/usr/bin/env python3
"""
获取可用策略列表的脚本
"""

import requests
import json

def get_strategies():
    """获取策略列表"""
    try:
        print("获取策略列表...")
        
        # 获取筛选策略
        response = requests.get("http://localhost:5000/api/screening/strategies")
        
        if response.status_code == 200:
            data = response.json()
            print("筛选策略:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"获取筛选策略失败: {response.status_code}")
            print(response.text)
            
        # 尝试获取交易策略
        print("\n尝试获取交易策略...")
        response2 = requests.get("http://localhost:5000/api/strategy")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print("交易策略:")
            print(json.dumps(data2, indent=2, ensure_ascii=False))
            return data2
        else:
            print(f"获取交易策略失败: {response2.status_code}")
            print(response2.text)
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    get_strategies()