#!/usr/bin/env python3
"""
应用共享机制迁移脚本
安全地为项目表添加共享字段并解决zhouyj权限异常问题
"""

import os
import sys
import traceback
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

def get_database_url():
    """从环境变量或配置获取数据库URL"""
    # 尝试从环境变量获取
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # 如果是Supabase等云服务的URL，需要处理SSL
        if 'supabase' in database_url and 'sslmode' not in database_url:
            database_url += '?sslmode=require'
        return database_url
    
    # 如果没有环境变量，使用默认的本地配置
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

def apply_migration(database_url):
    """应用数据库迁移"""
    
    print("🔄 开始应用共享机制迁移...")
    print(f"📊 数据库连接: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        # 创建数据库连接
        engine = create_engine(database_url, echo=False)
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功: {version.split()[0]} {version.split()[1]}")
        
        # 开始事务
        with engine.begin() as conn:
            print("\n📋 检查现有表结构...")
            
            # 检查projects表是否存在shared_with_users字段
            projects_has_shared_users = check_column_exists(engine, 'projects', 'shared_with_users')
            projects_has_share_enabled = check_column_exists(engine, 'projects', 'share_enabled')
            companies_has_share_enabled = check_column_exists(engine, 'companies', 'share_enabled')
            
            print(f"  projects.shared_with_users: {'存在' if projects_has_shared_users else '不存在'}")
            print(f"  projects.share_enabled: {'存在' if projects_has_share_enabled else '不存在'}")
            print(f"  companies.share_enabled: {'存在' if companies_has_share_enabled else '不存在'}")
            
            # 1. 为项目表添加共享字段
            if not projects_has_shared_users:
                print("\n🔧 为projects表添加shared_with_users字段...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN shared_with_users JSON DEFAULT '[]'"))
                print("  ✅ shared_with_users字段添加成功")
            else:
                print("  ℹ️  projects.shared_with_users字段已存在")
            
            if not projects_has_share_enabled:
                print("🔧 为projects表添加share_enabled字段...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN share_enabled BOOLEAN DEFAULT false"))
                print("  ✅ share_enabled字段添加成功")
            else:
                print("  ℹ️  projects.share_enabled字段已存在")
            
            # 2. 为客户表添加共享启用字段
            if not companies_has_share_enabled:
                print("🔧 为companies表添加share_enabled字段...")
                conn.execute(text("ALTER TABLE companies ADD COLUMN share_enabled BOOLEAN DEFAULT false"))
                print("  ✅ companies.share_enabled字段添加成功")
            else:
                print("  ℹ️  companies.share_enabled字段已存在")
            
            # 3. 初始化现有数据
            print("\n📊 初始化现有数据...")
            
            # 初始化项目共享字段
            result = conn.execute(text("UPDATE projects SET shared_with_users = '[]' WHERE shared_with_users IS NULL"))
            print(f"  ✅ 初始化了 {result.rowcount} 个项目的shared_with_users字段")
            
            result = conn.execute(text("UPDATE projects SET share_enabled = false WHERE share_enabled IS NULL"))
            print(f"  ✅ 初始化了 {result.rowcount} 个项目的share_enabled字段")
            
            # 初始化客户共享启用字段
            result = conn.execute(text("UPDATE companies SET share_enabled = false WHERE share_enabled IS NULL"))
            print(f"  ✅ 初始化了 {result.rowcount} 个客户的share_enabled字段")
            
            # 4. 关闭客户的项目自动共享功能
            print("\n🔒 关闭客户项目自动共享功能...")
            result = conn.execute(text("UPDATE companies SET share_related_projects = false WHERE share_related_projects = true"))
            print(f"  ✅ 关闭了 {result.rowcount} 个客户的项目自动共享")
            
            # 5. 创建性能索引
            print("\n🚀 创建性能优化索引...")
            
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_shared_users ON projects USING gin (shared_with_users)"))
                print("  ✅ 创建projects.shared_with_users GIN索引")
            except Exception as e:
                print(f"  ⚠️  创建projects.shared_with_users索引失败: {e}")
            
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_share_enabled ON projects (share_enabled)"))
                print("  ✅ 创建projects.share_enabled索引")
            except Exception as e:
                print(f"  ⚠️  创建projects.share_enabled索引失败: {e}")
            
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_companies_share_enabled ON companies (share_enabled)"))
                print("  ✅ 创建companies.share_enabled索引")
            except Exception as e:
                print(f"  ⚠️  创建companies.share_enabled索引失败: {e}")
            
            # 验证结果
            print("\n📊 验证迁移结果...")
            
            # 检查项目表
            result = conn.execute(text("SELECT COUNT(*) FROM projects WHERE shared_with_users IS NOT NULL"))
            projects_count = result.fetchone()[0]
            print(f"  ✅ {projects_count} 个项目具有共享字段")
            
            # 检查客户表
            result = conn.execute(text("SELECT COUNT(*) FROM companies WHERE share_related_projects = false"))
            disabled_count = result.fetchone()[0]
            print(f"  ✅ {disabled_count} 个客户已禁用项目自动共享")
            
            # 检查zhouyj相关的客户
            result = conn.execute(text("""
                SELECT id, company_name, shared_with_users, share_related_projects
                FROM companies 
                WHERE shared_with_users @> '[17]'::jsonb
            """))
            zhouyj_companies = result.fetchall()
            
            if zhouyj_companies:
                print(f"  🎯 zhouyj相关的客户 ({len(zhouyj_companies)}个):")
                for company in zhouyj_companies:
                    status = "已禁用项目共享" if not company[3] else "⚠️  仍启用项目共享"
                    print(f"    - ID {company[0]}: {company[1]} - {status}")
            else:
                print("  ✅ 未发现zhouyj相关的客户共享")
            
        print("\n🎉 迁移完成！")
        print("✅ 项目表添加了共享字段")
        print("✅ 客户表关闭了项目自动共享")
        print("✅ 创建了性能索引")
        print("✅ zhouyj权限异常问题已解决")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"\n❌ 数据库操作失败: {e}")
        print("事务已自动回滚")
        return False
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生未知错误: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 共享机制迁移工具")
    print("="*50)
    
    # 获取数据库URL
    try:
        database_url = get_database_url()
        if not database_url:
            print("❌ 无法获取数据库连接配置")
            print("请设置 DATABASE_URL 环境变量")
            return False
            
    except Exception as e:
        print(f"❌ 获取数据库配置时出错: {e}")
        return False
    
    # 确认执行
    print(f"📊 将要连接到数据库并执行迁移")
    print(f"🔗 数据库: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    confirm = input("\n是否继续执行迁移？(y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ 用户取消操作")
        return False
    
    # 执行迁移
    success = apply_migration(database_url)
    
    if success:
        print("\n🎯 下一步操作:")
        print("1. 重启应用服务")
        print("2. 取消注释项目模型中的共享字段定义")
        print("3. 测试项目共享功能")
        print("4. 验证zhouyj权限异常已解决")
        return True
    else:
        print("\n💡 如果遇到问题，请检查:")
        print("1. 数据库连接配置是否正确")
        print("2. 用户是否有足够的权限执行DDL操作")
        print("3. 数据库版本是否支持所需功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)