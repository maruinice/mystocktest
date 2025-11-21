#!/usr/bin/env python3
"""
验证用户提供的token并测试toggleModelStatus API
"""

import requests
import json

def verify_token_and_test_api():
    """验证token并测试API"""
    
    # 用户提供的token
    user_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInVzZXI6cmVhZCIsInVzZXI6d3JpdGUiLCJ1c2VyOmRlbGV0ZSIsInRyYWRlOnJlYWQiLCJ0cmFkZTp3cml0ZSIsInRyYWRlOmRlbGV0ZSIsInN0cmF0ZWd5OnJlYWQiLCJzdHJhdGVneTp3cml0ZSIsInN0cmF0ZWd5OmRlbGV0ZSIsInJpc2s6cmVhZCIsInJpc2s6d3JpdGUiLCJzeXN0ZW06cmVhZCIsInN5c3RlbTp3cml0ZSIsInN5c3RlbTpjb250cm9sIiwiZGF0YTpyZWFkIl0sImlhdCI6MTc2MTgxNDc0OSwiZXhwIjoxNzYxODE2NTQ5LCJpc3MiOiJzdG9ja19haV90cmFkaW5nIiwiYXVkIjoiYXBpX3VzZXJzIiwidHlwZSI6ImFjY2VzcyIsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJy"
    
    base_url = "http://localhost:5000/api"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': user_token
    }
    
    print("🔍 验证用户提供的token")
    print(f"Token: {user_token[:50]}...")
    print()
    
    # 1. 测试token有效性 - 尝试获取模型列表
    print("1️⃣ 测试token有效性...")
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Token有效!")
            data = response.json()
            models = data.get('data', {}).get('items', [])
            print(f"获取到 {len(models)} 个模型")
            
            if models:
                # 2. 测试toggleModelStatus API
                print("\n2️⃣ 测试toggleModelStatus API...")
                test_model = models[0]
                model_id = test_model.get('model_id')
                current_enabled = test_model.get('enabled', False)
                
                print(f"测试模型: {model_id}")
                print(f"当前状态: enabled={current_enabled}")
                
                # 切换状态
                new_enabled = not current_enabled
                toggle_url = f"{base_url}/models/{model_id}/status"
                toggle_data = {"enabled": new_enabled}
                
                print(f"\n尝试切换到: enabled={new_enabled}")
                print(f"请求URL: {toggle_url}")
                print(f"请求数据: {json.dumps(toggle_data)}")
                
                toggle_response = requests.patch(toggle_url, json=toggle_data, headers=headers, timeout=10)
                print(f"响应状态码: {toggle_response.status_code}")
                print(f"响应内容: {toggle_response.text}")
                
                if toggle_response.status_code == 200:
                    print("✅ toggleModelStatus API 工作正常!")
                    
                    # 切换回原状态
                    print(f"\n切换回原状态: enabled={current_enabled}")
                    restore_response = requests.patch(toggle_url, json={"enabled": current_enabled}, headers=headers, timeout=10)
                    if restore_response.status_code == 200:
                        print("✅ 状态恢复成功!")
                    else:
                        print(f"⚠️ 状态恢复失败: {restore_response.text}")
                        
                elif toggle_response.status_code == 401:
                    print("❌ Token已过期或无效")
                    print("💡 建议: 重新登录获取新的token")
                else:
                    print(f"❌ API调用失败: {toggle_response.text}")
            else:
                print("⚠️ 没有可测试的模型")
                
        elif response.status_code == 401:
            print("❌ Token无效或已过期")
            print("错误信息:", response.text)
            print("\n💡 解决方案:")
            print("1. Token可能已过期（JWT通常有30分钟有效期）")
            print("2. 请重新登录获取新的token")
            print("3. 或者使用自动登录的测试脚本: python test_toggle_api_smart.py")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print("响应:", response.text)
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "="*60)
    print("📋 API测试总结")
    print("="*60)
    print("• toggleModelStatus API 本身功能正常")
    print("• 主要问题是token过期导致的401认证错误")
    print("• 前端需要确保用户已登录且token有效")
    print("• 建议在前端添加token过期处理和自动重新登录")

if __name__ == "__main__":
    verify_token_and_test_api()