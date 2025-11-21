#!/usr/bin/env python3
"""
数据同步功能诊断脚本
检查所有相关配置和连接
"""
import sys
import os
import requests
import json
from datetime import datetime

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print('='*70)

# 后端基础URL
BASE_URL = "http://127.0.0.1:5000"

def check_backend_running():
    """检查后端是否运行"""
    print_section("1. 检查后端服务状态")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print_success(f"后端服务运行正常 (状态码: {response.status_code})")
            data = response.json()
            print_info(f"服务名称: {data.get('name', 'N/A')}")
            print_info(f"版本: {data.get('version', 'N/A')}")
            print_info(f"框架: {data.get('framework', 'N/A')}")
            return True
        else:
            print_error(f"后端服务响应异常 (状态码: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到后端服务！请确认服务已启动。")
        print_warning("请运行: start_services.bat")
        return False
    except Exception as e:
        print_error(f"检查后端服务时出错: {e}")
        return False

def check_blueprints():
    """检查Blueprint注册情况"""
    print_section("2. 检查Blueprint注册")
    
    # 检查是否导入了data_sync_bp
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from run_flask import app
        
        # 获取所有注册的Blueprint
        blueprints = list(app.blueprints.keys())
        print_info(f"已注册的Blueprints ({len(blueprints)}个):")
        for bp in blueprints:
            print(f"  - {bp}")
        
        if 'data_sync' in blueprints:
            print_success("data_sync Blueprint 已注册")
            return True
        else:
            print_error("data_sync Blueprint 未注册！")
            return False
            
    except Exception as e:
        print_error(f"检查Blueprint时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_routes():
    """检查路由注册情况"""
    print_section("3. 检查数据同步路由")
    
    endpoints = [
        '/api/data-sync/sync/status',
        '/api/data-sync/sync/config',
        '/api/data-sync/sync/industry',
        '/api/data-sync/sync/limit-prices',
        '/api/data-sync/sync/suspend',
        '/api/data-sync/sync/audit',
        '/api/data-sync/sync/all'
    ]
    
    all_ok = True
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print_success(f"{endpoint} - 可访问")
            elif response.status_code == 404:
                print_error(f"{endpoint} - 404 未找到")
                all_ok = False
            elif response.status_code == 401:
                print_warning(f"{endpoint} - 401 需要认证（但路由存在）")
            elif response.status_code == 405:
                print_warning(f"{endpoint} - 405 方法不允许（GET不支持，尝试POST）")
                # 尝试POST
                response = requests.post(url, json={}, timeout=5)
                if response.status_code == 200:
                    print_success(f"{endpoint} - POST可访问")
                else:
                    print_info(f"{endpoint} - POST状态码: {response.status_code}")
            else:
                print_warning(f"{endpoint} - 状态码: {response.status_code}")
                
        except Exception as e:
            print_error(f"{endpoint} - 错误: {e}")
            all_ok = False
    
    return all_ok

def test_sync_status():
    """测试同步状态接口"""
    print_section("4. 测试同步状态接口")
    
    url = f"{BASE_URL}/api/data-sync/sync/status"
    try:
        response = requests.get(url, timeout=10)
        
        print_info(f"URL: {url}")
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("同步状态接口正常")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print_error(f"接口返回错误: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def test_sync_config():
    """测试同步配置接口"""
    print_section("5. 测试同步配置接口")
    
    url = f"{BASE_URL}/api/data-sync/sync/config"
    try:
        response = requests.get(url, timeout=10)
        
        print_info(f"URL: {url}")
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("同步配置接口正常")
            
            if 'data_sources' in data:
                print_info(f"数据源数量: {len(data['data_sources'])}")
                for source in data['data_sources']:
                    print(f"  - {source['id']}: {source['name']}")
            
            return True
        else:
            print_error(f"接口返回错误: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def test_industry_sync():
    """测试行业分类同步"""
    print_section("6. 测试行业分类同步")
    
    url = f"{BASE_URL}/api/data-sync/sync/industry"
    payload = {
        "src": "SW2021",
        "level": "L1"
    }
    
    try:
        print_info(f"URL: {url}")
        print_info(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("行业分类同步成功")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print_error(f"同步失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """检查数据库连接和表"""
    print_section("7. 检查数据库")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.core.database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        
        # 检查表是否存在
        tables = [
            'industry_classification',
            'limit_prices',
            'suspend_info',
            'audit_opinions'
        ]
        
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) as count FROM {table}")).first()
                count = result.count if result else 0
                print_success(f"表 {table} 存在，记录数: {count}")
            except Exception as e:
                print_error(f"表 {table} 不存在或无法访问: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_tushare_token():
    """检查Tushare Token配置"""
    print_section("8. 检查Tushare配置")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.config.settings import settings
        
        token = settings.TUSHARE_TOKEN
        if token and len(token) > 10:
            print_success(f"Tushare Token已配置 (长度: {len(token)})")
            print_info(f"Token前缀: {token[:10]}...")
            return True
        else:
            print_error("Tushare Token未配置或无效！")
            print_warning("请在.env文件中设置 TUSHARE_TOKEN")
            return False
            
    except Exception as e:
        print_error(f"检查Tushare配置失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print(f"{Colors.BLUE}数据同步功能诊断工具{Colors.END}")
    print("="*70)
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        '后端服务': check_backend_running(),
        'Blueprint注册': check_blueprints(),
        '路由检查': check_routes(),
        '同步状态接口': test_sync_status(),
        '同步配置接口': test_sync_config(),
        '数据库检查': check_database(),
        'Tushare配置': check_tushare_token(),
        '行业分类同步': test_industry_sync()
    }
    
    # 汇总结果
    print_section("诊断结果汇总")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print_success("\n🎉 所有检查通过！数据同步功能正常。")
    else:
        print_error(f"\n⚠️  有 {total - passed} 项检查失败，请根据上述信息排查问题。")
        
        # 提供修复建议
        print_section("修复建议")
        
        if not results['后端服务']:
            print("1. 启动后端服务:")
            print("   cd d:\\code\\AIgogogo\\stock_ai_trading")
            print("   start_services.bat")
        
        if not results['Blueprint注册']:
            print("2. 检查 run_flask.py 是否正确导入和注册 data_sync_bp")
        
        if not results['Tushare配置']:
            print("3. 配置Tushare Token:")
            print("   在 .env 文件中添加: TUSHARE_TOKEN=你的token")
        
        if not results['数据库检查']:
            print("4. 检查数据库连接和表结构")
            print("   运行数据库迁移脚本")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}诊断被用户中断{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}诊断过程出错: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
