"""
交易功能测试脚本
测试买入、卖出、T+1规则等功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

def test_get_account():
    """测试获取账户信息"""
    print("\n=== 测试获取账户信息 ===")
    response = requests.get(f"{BASE_URL}/trade/account")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_get_positions():
    """测试获取持仓列表"""
    print("\n=== 测试获取持仓列表 ===")
    response = requests.get(f"{BASE_URL}/trade/positions")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_place_buy_order(symbol="600000.SH", quantity=100, price=10.50):
    """测试下买单"""
    print(f"\n=== 测试下买单: {symbol} ===")
    order_data = {
        "symbol": symbol,
        "side": "buy",
        "order_type": "limit",
        "quantity": quantity,
        "price": price
    }
    response = requests.post(f"{BASE_URL}/trade/order", json=order_data)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data.get('data', {}).get('order_id')
    else:
        print(f"错误: {response.text}")
        return None

def test_place_sell_order(symbol="600000.SH", quantity=100, price=10.50):
    """测试下卖单"""
    print(f"\n=== 测试下卖单: {symbol} ===")
    order_data = {
        "symbol": symbol,
        "side": "sell",
        "order_type": "limit",
        "quantity": quantity,
        "price": price
    }
    response = requests.post(f"{BASE_URL}/trade/order", json=order_data)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data.get('data', {}).get('order_id')
    else:
        print(f"错误: {response.text}")
        return None

def test_get_orders():
    """测试获取订单列表"""
    print("\n=== 测试获取订单列表 ===")
    response = requests.get(f"{BASE_URL}/trade/orders")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_cancel_order(order_id):
    """测试撤单"""
    print(f"\n=== 测试撤单: {order_id} ===")
    response = requests.delete(f"{BASE_URL}/trade/order/{order_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def main():
    """主测试流程"""
    print("=" * 60)
    print("交易功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 查看账户信息
    test_get_account()
    
    # 2. 查看持仓
    test_get_positions()
    
    # 3. 测试买入（使用一个真实存在的股票代码）
    order_id = test_place_buy_order("600000.SH", 100, 10.50)
    
    # 4. 查看订单列表
    test_get_orders()
    
    # 5. 等待几秒让订单撮合
    print("\n等待5秒让订单撮合...")
    import time
    time.sleep(5)
    
    # 6. 再次查看账户和持仓
    test_get_account()
    test_get_positions()
    
    # 7. 测试卖出（应该失败，因为T+1）
    print("\n注意：以下卖出操作应该失败（T+1规则）")
    test_place_sell_order("600000.SH", 100, 10.60)
    
    # 8. 查看最终状态
    test_get_orders()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
