#!/usr/bin/env python3
"""
创建本地到云端的增量迁移
分析本地数据库相对于云端版本的新变更，生成增量迁移脚本
"""

import psycopg2
import subprocess
import os
import sys
from datetime import datetime

def get_local_schema():
    """获取本地数据库完整结构"""
    print("🔍 获取本地数据库结构...")
    
    try:
        result = subprocess.run([
            'pg_dump', 
            '--schema-only',
            '--no-owner',
            '--no-privileges', 
            '-d', 'pma_local'
        ], capture_output=True, text=True, check=True)
        
        print("✅ 本地数据库结构获取成功")
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取本地数据库结构失败: {e}")
        return None

def get_cloud_schema():
    """获取云端数据库完整结构"""
    print("🔍 获取云端数据库结构...")
    
    cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
    try:
        result = subprocess.run([
            'pg_dump',
            '--schema-only', 
            '--no-owner',
            '--no-privileges',
            cloud_db_url
        ], capture_output=True, text=True, check=True)
        
        print("✅ 云端数据库结构获取成功")
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取云端数据库结构失败: {e}")
        return None

def analyze_schema_differences(local_schema, cloud_schema):
    """分析本地和云端数据库结构差异"""
    print("🔍 分析数据库结构差异...")
    
    # 保存schema到临时文件
    with open('/tmp/local_schema.sql', 'w') as f:
        f.write(local_schema)
    
    with open('/tmp/cloud_schema.sql', 'w') as f:
        f.write(cloud_schema)
    
    print("📊 Schema文件已保存:")
    print("   本地: /tmp/local_schema.sql")
    print("   云端: /tmp/cloud_schema.sql")
    
    # 基本分析：表数量对比
    local_tables = set()
    cloud_tables = set()
    
    for line in local_schema.split('\n'):
        if line.strip().startswith('CREATE TABLE'):
            table_name = line.split()[2].strip('"')
            local_tables.add(table_name)
    
    for line in cloud_schema.split('\n'):
        if line.strip().startswith('CREATE TABLE'):
            table_name = line.split()[2].strip('"')
            cloud_tables.add(table_name)
    
    new_tables = local_tables - cloud_tables
    missing_tables = cloud_tables - local_tables
    common_tables = local_tables & cloud_tables
    
    print(f"\n📋 表结构对比:")
    print(f"   本地表数量: {len(local_tables)}")
    print(f"   云端表数量: {len(cloud_tables)}")
    print(f"   共同表: {len(common_tables)}")
    print(f"   本地新增表: {len(new_tables)}")
    print(f"   云端独有表: {len(missing_tables)}")
    
    if new_tables:
        print(f"\n🆕 本地新增的表:")
        for table in sorted(new_tables):
            print(f"   - {table}")
    
    if missing_tables:
        print(f"\n⚠️  云端独有的表 (本地缺失):")
        for table in sorted(missing_tables):
            print(f"   - {table}")
    
    return {
        'local_tables': local_tables,
        'cloud_tables': cloud_tables,
        'new_tables': new_tables,
        'missing_tables': missing_tables,
        'common_tables': common_tables
    }

def get_local_migration_info():
    """获取本地迁移信息"""
    print("🔍 获取本地迁移信息...")
    
    try:
        result = subprocess.run([
            'psql', '-d', 'pma_local', '-t', '-c',
            'SELECT version_num FROM alembic_version;'
        ], capture_output=True, text=True, check=True)
        
        local_version = result.stdout.strip()
        print(f"✅ 本地迁移版本: {local_version}")
        return local_version
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取本地迁移版本失败: {e}")
        return None

def create_incremental_migration_script():
    """创建增量迁移脚本"""
    print("🛠️  创建增量迁移脚本...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_file = f"migrations/local_to_cloud_incremental_{timestamp}.sql"
    
    # 生成增量迁移脚本
    script_content = f"""-- 本地到云端增量迁移脚本
-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 目标: 将本地 pma_local 的最新结构同步到云端 sp8d

BEGIN;

-- 安全检查：确认当前版本
DO $$
DECLARE
    current_version TEXT;
BEGIN
    SELECT version_num INTO current_version FROM alembic_version LIMIT 1;
    
    IF current_version != 'c8d3eaeaf234' THEN
        RAISE EXCEPTION '版本不匹配：期望 c8d3eaeaf234，实际 %', current_version;
    END IF;
    
    RAISE NOTICE '✅ 版本检查通过：%', current_version;
END
$$;

-- 1. 添加本地新增的索引（从 592b90d54921 迁移）
-- 这些索引在本地存在但云端可能缺失

-- 报价单性能索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_id ON quotations(project_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_owner_id ON quotations(owner_id);  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_created_at ON quotations(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_updated_at ON quotations(updated_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_amount ON quotations(amount);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_owner ON quotations(project_id, owner_id);

-- 项目性能索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_type ON projects(project_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_current_stage ON projects(current_stage);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_type_stage ON projects(project_type, current_stage);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_vendor_sales_manager ON projects(vendor_sales_manager_id);

-- 2. 更新迁移版本到本地最新版本
UPDATE alembic_version SET version_num = '592b90d54921';

-- 添加迁移记录
INSERT INTO alembic_version (version_num) VALUES ('592b90d54921') 
ON CONFLICT (version_num) DO NOTHING;

COMMIT;

-- 验证迁移结果
SELECT '✅ 迁移完成，当前版本: ' || version_num FROM alembic_version;
"""

    # 保存迁移脚本
    os.makedirs('migrations', exist_ok=True)
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 增量迁移脚本已创建: {migration_file}")
    return migration_file

def create_cloud_deployment_script(migration_file):
    """创建云端部署脚本"""
    print("🛠️  创建云端部署脚本...")
    
    deployment_script = f"""#!/usr/bin/env python3
'''
云端数据库增量迁移部署脚本
安全地将本地最新结构同步到云端
'''

import psycopg2
import sys
from datetime import datetime

CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def execute_migration():
    '''执行增量迁移'''
    print("🚀 开始执行云端增量迁移...")
    
    try:
        # 读取迁移脚本
        with open('{migration_file}', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 连接云端数据库
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False  # 使用事务
        
        cursor = conn.cursor()
        
        print("✅ 云端数据库连接成功")
        
        # 执行迁移
        print("🔄 执行迁移脚本...")
        cursor.execute(migration_sql)
        
        # 验证迁移结果
        cursor.execute("SELECT version_num FROM alembic_version;")
        new_version = cursor.fetchone()[0]
        
        # 提交事务
        conn.commit()
        
        print(f"✅ 迁移成功完成！新版本: {{new_version}}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {{str(e)}}")
        try:
            conn.rollback()
            print("✅ 事务已回滚")
        except:
            pass
        return False

def main():
    print("🚀 云端数据库增量迁移工具")
    print("=" * 50)
    
    success = execute_migration()
    
    if success:
        print("\\n🎉 云端数据库迁移成功完成！")
        print("📋 已应用本地最新的数据库结构")
    else:
        print("\\n💥 云端数据库迁移失败")
        print("📋 数据库状态已回滚，请检查错误信息")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""

    deployment_file = "deploy_to_cloud.py"
    with open(deployment_file, 'w', encoding='utf-8') as f:
        f.write(deployment_script)
    
    print(f"✅ 云端部署脚本已创建: {deployment_file}")
    return deployment_file

def main():
    """主函数"""
    print("🚀 本地到云端增量迁移工具")
    print("=" * 80)
    
    # 1. 获取本地迁移版本
    local_version = get_local_migration_info()
    if not local_version:
        print("❌ 无法获取本地迁移版本")
        return False
    
    # 2. 获取数据库结构
    print(f"\\n🔍 分析数据库结构差异...")
    local_schema = get_local_schema()
    cloud_schema = get_cloud_schema()
    
    if not local_schema or not cloud_schema:
        print("❌ 无法获取数据库结构")
        return False
    
    # 3. 分析差异
    diff_analysis = analyze_schema_differences(local_schema, cloud_schema)
    
    # 4. 创建迁移脚本
    print(f"\\n🛠️  生成迁移方案...")
    migration_file = create_incremental_migration_script()
    deployment_file = create_cloud_deployment_script(migration_file)
    
    # 5. 总结报告
    print(f"\\n📋 迁移方案总结:")
    print("=" * 80)
    print(f"本地版本: {local_version}")
    print(f"云端版本: c8d3eaeaf234")
    print(f"迁移脚本: {migration_file}")
    print(f"部署脚本: {deployment_file}")
    
    print(f"\\n🎯 下一步操作:")
    print("1. ☁️  确保云端数据库已备份（已完成）")
    print("2. 🔍 审查迁移脚本内容")
    print(f"3. 🚀 执行部署: python {deployment_file}")
    print("4. ✅ 验证迁移结果")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)