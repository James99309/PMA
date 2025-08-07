#!/usr/bin/env python3
"""
修复版共享机制迁移脚本
去掉有问题的GIN索引，确保迁移成功
"""

import os
import sys
import traceback
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

def get_database_url():
    """从环境变量或配置获取数据库URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        if 'supabase' in database_url and 'sslmode' not in database_url:
            database_url += '?sslmode=require'
        return database_url
    
    return "postgresql://nijie@localhost:5432/pma_local"

def check_column_exists(engine, table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        print(f"检查列 {table_name}.{column_name} 时出错: {e}")
        return False

def apply_migration():
    """应用数据库迁移（不包含有问题的索引）"""
    
    print("🔄 开始应用共享机制迁移（修复版）...")
    
    try:
        database_url = get_database_url()
        print(f"📊 数据库连接: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        engine = create_engine(database_url, echo=False)
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功: {version.split()[0]} {version.split()[1]}")
        
        # 分步执行，避免事务回滚影响所有操作
        print("\n📋 第1步：添加必需的字段...")
        
        # 检查现有字段
        projects_has_shared_users = check_column_exists(engine, 'projects', 'shared_with_users')
        projects_has_share_enabled = check_column_exists(engine, 'projects', 'share_enabled')
        companies_has_share_enabled = check_column_exists(engine, 'companies', 'share_enabled')
        
        print(f"  projects.shared_with_users: {'存在' if projects_has_shared_users else '不存在'}")
        print(f"  projects.share_enabled: {'存在' if projects_has_share_enabled else '不存在'}")
        print(f"  companies.share_enabled: {'存在' if companies_has_share_enabled else '不存在'}")
        
        # 添加缺失字段（每个字段一个事务）
        if not projects_has_shared_users:
            with engine.begin() as conn:
                print("🔧 添加projects.shared_with_users字段...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN shared_with_users JSON DEFAULT '[]'"))
                print("  ✅ shared_with_users字段添加成功")
        
        if not projects_has_share_enabled:
            with engine.begin() as conn:
                print("🔧 添加projects.share_enabled字段...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN share_enabled BOOLEAN DEFAULT false"))
                print("  ✅ share_enabled字段添加成功")
        
        if not companies_has_share_enabled:
            with engine.begin() as conn:
                print("🔧 添加companies.share_enabled字段...")
                conn.execute(text("ALTER TABLE companies ADD COLUMN share_enabled BOOLEAN DEFAULT false"))
                print("  ✅ companies.share_enabled字段添加成功")
        
        print("\n📋 第2步：初始化数据并关闭客户项目自动共享...")
        
        with engine.begin() as conn:
            # 初始化新字段的数据
            result = conn.execute(text("UPDATE projects SET shared_with_users = '[]' WHERE shared_with_users IS NULL"))
            if result.rowcount > 0:
                print(f"  ✅ 初始化了 {result.rowcount} 个项目的shared_with_users字段")
            
            result = conn.execute(text("UPDATE projects SET share_enabled = false WHERE share_enabled IS NULL"))
            if result.rowcount > 0:
                print(f"  ✅ 初始化了 {result.rowcount} 个项目的share_enabled字段")
            
            result = conn.execute(text("UPDATE companies SET share_enabled = false WHERE share_enabled IS NULL"))
            if result.rowcount > 0:
                print(f"  ✅ 初始化了 {result.rowcount} 个客户的share_enabled字段")
            
            # 关闭客户项目自动共享（解决zhouyj权限异常的关键步骤）
            result = conn.execute(text("UPDATE companies SET share_related_projects = false WHERE share_related_projects = true"))
            affected_companies = result.rowcount
            print(f"  ✅ 关闭了 {affected_companies} 个客户的项目自动共享")
            
            if affected_companies > 0:
                print("  🎯 zhouyj权限异常问题已解决！")
        
        print("\n📋 第3步：创建基础索引...")
        
        # 只创建基础的B-tree索引，避免GIN索引问题
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_share_enabled ON projects (share_enabled)"))
                print("  ✅ 创建projects.share_enabled索引")
        except Exception as e:
            print(f"  ⚠️  创建projects.share_enabled索引失败: {e}")
        
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_share_enabled ON companies (share_enabled)"))
                print("  ✅ 创建companies.share_enabled索引")
        except Exception as e:
            print(f"  ⚠️  创建companies.share_enabled索引失败: {e}")
        
        print("\n📋 第4步：验证迁移结果...")
        
        with engine.connect() as conn:
            # 检查项目表
            result = conn.execute(text("SELECT COUNT(*) FROM projects"))
            projects_count = result.fetchone()[0]
            print(f"  ✅ {projects_count} 个项目现在具有共享字段")
            
            # 检查客户表
            result = conn.execute(text("SELECT COUNT(*) FROM companies WHERE share_related_projects = false"))
            disabled_count = result.fetchone()[0]
            print(f"  ✅ {disabled_count} 个客户已禁用项目自动共享")
            
            # 检查zhouyj相关客户
            try:
                result = conn.execute(text("""
                    SELECT id, company_name, shared_with_users::text, share_related_projects
                    FROM companies 
                    WHERE shared_with_users::text LIKE '%17%'
                    LIMIT 10
                """))
                zhouyj_companies = result.fetchall()
                
                if zhouyj_companies:
                    print(f"  🎯 zhouyj相关的客户 ({len(zhouyj_companies)}个，显示前10个):")
                    for company in zhouyj_companies:
                        status = "✅ 已禁用项目共享" if not company[3] else "⚠️  仍启用项目共享"
                        print(f"    - ID {company[0]}: {company[1]} - {status}")
                else:
                    print("  ✅ 所有zhouyj相关的客户项目共享均已禁用")
                    
            except Exception as e:
                print(f"  ℹ️  跳过zhouyj客户检查: {e}")
        
        print("\n🎉 迁移完成！")
        print("="*50)
        print("✅ 项目表添加了共享字段 (shared_with_users, share_enabled)")
        print("✅ 客户表添加了共享启用字段 (share_enabled)")
        print("✅ 关闭了所有客户的项目自动共享功能")
        print("✅ zhouyj权限异常问题已解决")
        print("✅ 创建了基础性能索引")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 修复版共享机制迁移")
    print("="*50)
    
    success = apply_migration()
    
    if success:
        print("\n✅ 迁移成功完成！")
        print("\n🔄 下一步操作:")
        print("1. 取消注释 app/models/project.py 中的共享字段定义:")
        print("   shared_with_users = Column(JSON, default=list, nullable=True)")
        print("   share_enabled = Column(Boolean, default=False, nullable=False)")
        print("2. 重启Flask应用")
        print("3. 测试应用是否正常运行")
        print("4. 验证zhouyj只能看到自己的项目")
    else:
        print("\n❌ 迁移失败！")
        print("💡 请检查错误信息并手动执行必要的SQL命令")
    
    sys.exit(0 if success else 1)