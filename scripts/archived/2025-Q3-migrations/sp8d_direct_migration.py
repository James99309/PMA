#!/usr/bin/env python3
"""
SP8D数据库直接迁移脚本
直接执行迁移链而不依赖复杂的解析器
"""

import subprocess
import sys
import os
import time
from datetime import datetime

# SP8D数据库连接配置
SP8D_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def execute_flask_command(cmd, description):
    """执行Flask命令"""
    print(f"🚀 {description}...")
    
    env = os.environ.copy()
    env['DATABASE_URL'] = SP8D_URL
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        execution_time = time.time() - start_time
        
        print(f"✅ {description}成功 ({execution_time:.2f}s)")
        if result.stdout:
            print(f"输出: {result.stdout}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败")
        print(f"错误: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def main():
    print("🚀 开始SP8D数据库直接迁移...")
    print("⚠️  直接执行已知的迁移链")
    print()
    
    # 检查当前版本
    if not execute_flask_command(['flask', 'db', 'current'], "检查当前版本"):
        return False
    
    print()
    
    # 迁移链
    migrations = [
        'fix_sp8d_approval_branch_fields',
        'unify_performance_amount_types', 
        'unify_performance_targets_constraints'
    ]
    
    print(f"📋 计划执行 {len(migrations)} 个迁移:")
    for i, migration in enumerate(migrations, 1):
        print(f"   {i}. {migration}")
    print()
    
    # 逐步执行迁移
    for i, migration in enumerate(migrations, 1):
        print(f"📍 步骤 {i}/{len(migrations)}")
        
        if not execute_flask_command(['flask', 'db', 'upgrade', migration], 
                                   f"执行迁移 {migration[:20]}..."):
            print(f"\n❌ 迁移在步骤 {i} 失败")
            print("🔄 建议检查数据库状态后重试")
            return False
            
        print()
    
    # 验证最终状态
    print("🔍 验证最终状态...")
    if not execute_flask_command(['flask', 'db', 'current'], "检查最终版本"):
        return False
    
    print("\n" + "="*60)
    print("✅ SP8D数据库迁移成功完成！")
    print("🔍 所有迁移步骤已验证")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)