#!/usr/bin/env python3
"""
最终验证脚本 - 验证完整的数据流从数据库到API的正确性
"""

import requests
import json
import os
import pymysql
from urllib.parse import urlparse

def verify_database():
    """验证数据库中的策略数据"""
    print("🔍 验证数据库中的策略数据...")
    
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/stock_trading')
    parsed = urlparse(database_url.replace('mysql+pymysql://', 'mysql://'))

    connection = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, strategy_name, strategy_type, is_system, creator_id, is_active
            FROM screening_strategies 
            WHERE is_active = TRUE
            ORDER BY is_system DESC, strategy_type, id
        """)
        strategies = cursor.fetchall()
        
        system_strategies = [s for s in strategies if s['is_system'] == 1]
        custom_strategies = [s for s in strategies if s['is_system'] == 0]
        
        print(f"  📊 数据库统计:")
        print(f"    - 总策略数: {len(strategies)}")
        print(f"    - 系统策略: {len(system_strategies)}")
        print(f"    - 自定义策略: {len(custom_strategies)}")
        
        # 按类型分组系统策略
        system_by_type = {}
        for s in system_strategies:
            strategy_type = s['strategy_type']
            if strategy_type not in system_by_type:
                system_by_type[strategy_type] = []
            system_by_type[strategy_type].append(s)
        
        print(f"  📋 系统策略按类型分组:")
        for strategy_type, strategies_list in system_by_type.items():
            print(f"    - {strategy_type}: {len(strategies_list)} 个")
        
        print(f"  📋 自定义策略:")
        for s in custom_strategies:
            print(f"    - ID: {s['id']}, 名称: {s['strategy_name']}, 创建者: {s['creator_id']}")

    connection.close()
    return len(strategies), len(system_strategies), len(custom_strategies), system_by_type

def verify_api():
    """验证API返回的数据"""
    print("\n🌐 验证API返回的数据...")
    
    base_url = "http://localhost:5000"
    
    # 登录获取token
    login_data = {
        "email": "admin@example.com",
        "password": "admin123456"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return None
    
    token = login_response.json()['data']['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取策略列表
    strategies_response = requests.get(f"{base_url}/api/screening/strategies", headers=headers)
    if strategies_response.status_code != 200:
        print(f"❌ 获取策略失败: {strategies_response.status_code}")
        return None
    
    data = strategies_response.json()['data']
    
    print(f"  📊 API返回统计:")
    print(f"    - system: {len(data['system'])} 个")
    print(f"    - fundamental: {len(data['fundamental'])} 个")
    print(f"    - technical: {len(data['technical'])} 个")
    print(f"    - mixed: {len(data['mixed'])} 个")
    print(f"    - custom: {len(data['custom'])} 个")
    
    total_api = len(data['system']) + len(data['fundamental']) + len(data['technical']) + len(data['mixed']) + len(data['custom'])
    system_api = len(data['fundamental']) + len(data['technical']) + len(data['mixed'])
    custom_api = len(data['custom'])
    
    return total_api, system_api, custom_api, data

def main():
    print("🚀 开始最终验证...")
    
    # 验证数据库
    db_total, db_system, db_custom, db_system_by_type = verify_database()
    
    # 验证API
    api_result = verify_api()
    if api_result is None:
        print("❌ API验证失败")
        return
    
    api_total, api_system, api_custom, api_data = api_result
    
    # 对比验证
    print("\n✅ 数据一致性验证:")
    print(f"  总策略数: 数据库({db_total}) vs API({api_total}) - {'✅' if db_total == api_total else '❌'}")
    print(f"  系统策略: 数据库({db_system}) vs API({api_system}) - {'✅' if db_system == api_system else '❌'}")
    print(f"  自定义策略: 数据库({db_custom}) vs API({api_custom}) - {'✅' if db_custom == api_custom else '❌'}")
    
    # 验证系统策略分组
    print(f"\n📋 系统策略分组验证:")
    for strategy_type in ['fundamental', 'technical', 'mixed']:
        db_count = len(db_system_by_type.get(strategy_type, []))
        api_count = len(api_data.get(strategy_type, []))
        print(f"  {strategy_type}: 数据库({db_count}) vs API({api_count}) - {'✅' if db_count == api_count else '❌'}")
    
    # 验证system组应该为空
    system_empty = len(api_data['system']) == 0
    print(f"  system组为空: {'✅' if system_empty else '❌'}")
    
    if (db_total == api_total and db_system == api_system and db_custom == api_custom and system_empty):
        print("\n🎉 所有验证通过！数据流完全正确！")
    else:
        print("\n⚠️ 存在数据不一致问题")

if __name__ == "__main__":
    main()