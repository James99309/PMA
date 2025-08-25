#!/usr/bin/env python3
"""
调试迁移路径查找问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migration_parser import MigrationParser

def debug_migration_graph():
    parser = MigrationParser("migrations")
    migrations = parser.parse_all_migrations()
    
    current_revision = "b2d5b2180d45"
    target_revision = "unify_performance_targets_constraints"
    
    print(f"🔍 调试迁移路径查找问题")
    print(f"起始版本: {current_revision}")
    print(f"目标版本: {target_revision}")
    print()
    
    # 检查当前版本是否存在
    print("📋 检查起始版本:")
    if current_revision in migrations:
        migration = migrations[current_revision]
        print(f"✅ 找到起始版本: {migration.filename}")
        print(f"   down_revision: {migration.down_revision}")
    else:
        print(f"❌ 起始版本不在迁移列表中")
        
    print()
    
    # 检查目标版本是否存在  
    print("📋 检查目标版本:")
    if target_revision in migrations:
        migration = migrations[target_revision]
        print(f"✅ 找到目标版本: {migration.filename}")
        print(f"   down_revision: {migration.down_revision}")
    else:
        print(f"❌ 目标版本不在迁移列表中")
        
    print()
    
    # 检查依赖图
    print("📋 检查依赖图:")
    print(f"从 {current_revision[:8]} 开始的依赖: {parser.dependency_graph.get(current_revision, [])}")
    print(f"到 {target_revision[:8]} 的反向依赖: {parser.reverse_graph.get(target_revision, [])}")
    
    print()
    
    # 查找哪些迁移依赖于当前版本
    print("📋 查找依赖于当前版本的迁移:")
    depends_on_current = []
    for revision, migration in migrations.items():
        if isinstance(migration.down_revision, str):
            if migration.down_revision == current_revision:
                depends_on_current.append((revision, migration.filename))
        elif isinstance(migration.down_revision, tuple):
            if current_revision in migration.down_revision:
                depends_on_current.append((revision, migration.filename))
                
    if depends_on_current:
        print("✅ 找到依赖于当前版本的迁移:")
        for revision, filename in depends_on_current:
            print(f"   - {revision[:8]}... ({filename})")
    else:
        print("❌ 没有找到依赖于当前版本的迁移")
        
    print()
    
    # 尝试手动构建路径
    print("📋 手动构建迁移路径:")
    path = []
    current = current_revision
    
    # 按照已知的迁移链进行手动验证
    expected_chain = [
        'fix_sp8d_approval_branch_fields',
        'unify_performance_amount_types', 
        'unify_performance_targets_constraints'
    ]
    
    print("预期迁移链:")
    for step in expected_chain:
        if step in migrations:
            migration = migrations[step]
            print(f"   ✅ {step[:20]}... -> down_revision: {migration.down_revision}")
        else:
            print(f"   ❌ {step} (未找到)")

if __name__ == "__main__":
    debug_migration_graph()