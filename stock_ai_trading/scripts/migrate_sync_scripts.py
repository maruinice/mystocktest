"""
迁移同步脚本到统一文件夹
将根目录的同步脚本整合到 app/services/sync_services/
"""

import os
import shutil

# 需要迁移的同步脚本
SYNC_SCRIPTS_TO_MIGRATE = [
    'sync_financial_indicators.py',
    'sync_audit_opinions.py',
    'sync_industry_classification.py',
]

# 需要删除的测试和临时文件
FILES_TO_DELETE = [
    # 测试文件
    'test_ai_final.py',
    'test_ai_generation.py',
    'test_api_call.py',
    'test_code_parser.py',
    'test_code_quality.py',
    'test_data_sync.py',
    'test_enhanced_prompt.py',
    'test_full_flow.py',
    'test_full_response.py',
    'test_import.py',
    'test_llm_gateway.py',
    'test_performance.py',
    'test_prompt_enhancement.py',
    'test_quick.py',
    'test_save_strategy.py',
    'test_sync_direct.py',
    # 临时同步脚本
    'sync_complete_apis.py',
    'sync_stock_basic_simple.py',
    'sync_stock_basic_tables.py',
    'sync_suspend_only.py',
]

# 需要保留的文件（移到 scripts/ 文件夹）
FILES_TO_KEEP_IN_SCRIPTS = [
    'test_sync_system.py',  # 系统测试脚本
    'migrate_sync_scripts.py',  # 本脚本
]

def main():
    print("\n" + "="*70)
    print("同步脚本迁移工具")
    print("="*70)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sync_services_dir = os.path.join(base_dir, 'app', 'services', 'sync_services')
    scripts_dir = os.path.join(base_dir, 'scripts')
    
    # 创建 scripts 目录
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
        print(f"\n✅ 创建目录: {scripts_dir}")
    
    # 1. 迁移同步脚本到 app/services/sync_services/
    print("\n" + "-"*70)
    print("步骤1: 迁移同步脚本")
    print("-"*70)
    
    for script in SYNC_SCRIPTS_TO_MIGRATE:
        src = os.path.join(base_dir, script)
        if os.path.exists(src):
            # 重命名为 _original.py 保留原始文件作为参考
            dst = os.path.join(sync_services_dir, script.replace('.py', '_original.py'))
            shutil.copy2(src, dst)
            print(f"✅ 复制 {script} -> sync_services/{os.path.basename(dst)}")
        else:
            print(f"⚠️  文件不存在: {script}")
    
    # 2. 移动保留的脚本到 scripts/
    print("\n" + "-"*70)
    print("步骤2: 移动保留的脚本到 scripts/")
    print("-"*70)
    
    for script in FILES_TO_KEEP_IN_SCRIPTS:
        src = os.path.join(base_dir, script)
        if os.path.exists(src):
            dst = os.path.join(scripts_dir, script)
            shutil.move(src, dst)
            print(f"✅ 移动 {script} -> scripts/{script}")
    
    # 3. 删除临时文件
    print("\n" + "-"*70)
    print("步骤3: 清理临时文件")
    print("-"*70)
    
    for file in FILES_TO_DELETE:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ 删除 {file}")
        else:
            print(f"⚠️  文件不存在: {file}")
    
    # 4. 删除原始同步脚本
    print("\n" + "-"*70)
    print("步骤4: 删除原始同步脚本")
    print("-"*70)
    
    for script in SYNC_SCRIPTS_TO_MIGRATE:
        file_path = os.path.join(base_dir, script)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ 删除 {script}")
    
    print("\n" + "="*70)
    print("迁移完成！")
    print("="*70)
    print("\n说明:")
    print("1. 原始同步脚本已复制到 app/services/sync_services/ 作为参考")
    print("2. 测试脚本已移动到 scripts/ 文件夹")
    print("3. 临时文件已删除")
    print("4. 根目录已清理")
    print("\n下一步:")
    print("- 基于原始脚本创建对应的 SyncService 类")
    print("- 在 sync_manager.py 中注册所有服务")
    print("- 测试所有同步功能")

if __name__ == '__main__':
    main()
