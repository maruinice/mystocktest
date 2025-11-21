#!/usr/bin/env python3
"""
选股数据初始化脚本
确保选股功能有足够的数据进行筛选
"""

import asyncio
import requests
import time
from datetime import datetime

# 配置
API_BASE = "http://localhost:5000/api/screening"

async def init_screening_data():
    """初始化选股数据"""
    print("🚀 开始初始化选股数据...")
    print("=" * 60)
    
    steps = [
        {
            'name': '同步股票基础信息',
            'url': f'{API_BASE}/data/sync-stock-basic',
            'method': 'POST',
            'data': {},
            'timeout': 60
        },
        {
            'name': '同步日线行情数据',
            'url': f'{API_BASE}/data/sync-quotes',
            'method': 'POST',
            'data': {},
            'timeout': 60
        },
        {
            'name': '同步财务指标数据',
            'url': f'{API_BASE}/data/sync-financial',
            'method': 'POST',
            'data': {},
            'timeout': 60
        },
        {
            'name': '计算技术指标',
            'url': f'{API_BASE}/data/calculate-technical',
            'method': 'POST',
            'data': {},
            'timeout': 120
        }
    ]
    
    success_count = 0
    
    for i, step in enumerate(steps, 1):
        print(f"\n📋 步骤 {i}: {step['name']}")
        print(f"   URL: {step['url']}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                step['url'], 
                json=step['data'], 
                timeout=step['timeout']
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ 成功: {result.get('message', '操作完成')}")
                    if 'data' in result:
                        data = result['data']
                        for key, value in data.items():
                            print(f"      {key}: {value}")
                    print(f"   ⏱️  耗时: {elapsed_time:.2f}秒")
                    success_count += 1
                else:
                    print(f"   ❌ 失败: {result.get('message', '未知错误')}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print(f"      响应: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 超时: 操作超过{step['timeout']}秒")
        except Exception as e:
            print(f"   ❌ 异常: {str(e)[:100]}")
        
        # 步骤间等待
        if i < len(steps):
            print("   ⏳ 等待2秒...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("📊 数据初始化结果汇总")
    print("=" * 60)
    
    success_rate = success_count / len(steps) * 100
    print(f"✅ 成功步骤: {success_count}/{len(steps)} ({success_rate:.1f}%)")
    
    if success_count == len(steps):
        print("🎉 所有数据初始化完成！现在可以进行选股了。")
        
        # 测试选股功能
        print("\n🎯 测试选股功能...")
        await test_screening()
        
    elif success_count >= 2:
        print("⚠️  部分数据初始化完成，选股功能可能受限。")
        print("💡 建议检查失败的步骤并重新执行。")
    else:
        print("❌ 数据初始化失败，选股功能无法正常使用。")
        print("💡 请检查后端服务状态和数据库连接。")

async def test_screening():
    """测试选股功能"""
    try:
        print("📋 获取策略列表...")
        response = requests.get(f'{API_BASE}/strategies', timeout=30)
        
        if response.status_code != 200:
            print("   ❌ 获取策略列表失败")
            return
        
        strategies_data = response.json()
        if not strategies_data.get('success'):
            print("   ❌ 策略列表返回失败")
            return
        
        system_strategies = strategies_data['data']['system']
        if not system_strategies:
            print("   ❌ 没有可用的系统策略")
            return
        
        strategy_id = system_strategies[0]['id']
        strategy_name = system_strategies[0]['name']
        print(f"   ✅ 选择策略: {strategy_name} (ID: {strategy_id})")
        
        print("📋 执行选股测试...")
        screening_data = {
            'strategy_id': strategy_id,
            'conditions': {
                'pe': {'min': 0, 'max': 100},
                'pb': {'min': 0, 'max': 20}
            }
        }
        
        response = requests.post(f'{API_BASE}/execute', json=screening_data, timeout=60)
        
        if response.status_code != 200:
            print("   ❌ 选股执行失败")
            return
        
        execution_result = response.json()
        if not execution_result.get('success'):
            print(f"   ❌ 选股执行失败: {execution_result.get('message')}")
            return
        
        filtered_count = execution_result['data']['filtered_stocks']
        execution_time = execution_result['data']['execution_time']
        
        print(f"   ✅ 选股测试成功!")
        print(f"      筛选结果: {filtered_count}只股票")
        print(f"      执行时间: {execution_time}ms")
        
        if filtered_count > 0:
            print("🎊 选股功能正常！数据初始化成功！")
        else:
            print("⚠️  选股功能正常，但当前条件下没有筛选出股票。")
            print("💡 可以尝试调整筛选条件或检查数据质量。")
            
    except Exception as e:
        print(f"   ❌ 选股测试失败: {e}")

def main():
    """主函数"""
    print("🎯 选股数据初始化工具")
    print(f"⏰ 开始时间: {datetime.now()}")
    print(f"🔗 API地址: {API_BASE}")
    
    # 检查后端服务
    print("\n🔍 检查后端服务状态...")
    try:
        response = requests.get(f'{API_BASE}/strategies', timeout=10)
        if response.status_code == 200:
            print("   ✅ 后端服务正常")
        else:
            print(f"   ❌ 后端服务异常: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 无法连接后端服务: {e}")
        print("   💡 请确保后端服务已启动: python run_flask.py --port 5000")
        return
    
    # 运行初始化
    asyncio.run(init_screening_data())
    
    print(f"\n⏰ 完成时间: {datetime.now()}")
    print("🔗 访问选股功能: http://localhost:3000/#/admin/screening")

if __name__ == "__main__":
    main()