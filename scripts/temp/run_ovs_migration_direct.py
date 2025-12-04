#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接执行OVS数据库迁移
绕过Flask加载问题，直接使用Alembic API执行迁移
"""
import os
import sys

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置OVS数据库URL
OVS_DB_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
os.environ['DATABASE_URL'] = OVS_DB_URL

from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def get_current_revision(engine):
    """获取当前数据库的迁移版本"""
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_head_revision(alembic_cfg):
    """获取最新的迁移版本"""
    script = ScriptDirectory.from_config(alembic_cfg)
    return script.get_current_head()


def get_pending_revisions(alembic_cfg, current_rev):
    """获取待执行的迁移"""
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()

    if current_rev == head:
        return []

    # 获取从当前版本到head的所有迁移
    pending = []
    for rev in script.iterate_revisions(head, current_rev):
        if rev.revision != current_rev:
            pending.append(rev)

    return list(reversed(pending))


def main():
    print_header("🚀 OVS数据库直接迁移工具")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标数据库: OVS @ Supabase")

    # 创建数据库引擎
    print("\n📡 连接OVS数据库...")
    engine = create_engine(OVS_DB_URL)

    # 测试连接
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ 已连接到数据库: {db_name}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

    # 配置Alembic
    alembic_cfg = Config(os.path.join(project_root, 'migrations', 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', os.path.join(project_root, 'migrations'))
    alembic_cfg.set_main_option('sqlalchemy.url', OVS_DB_URL)

    # 检查当前版本
    print_header("📋 检查迁移状态")
    current_rev = get_current_revision(engine)
    head_rev = get_head_revision(alembic_cfg)

    print(f"当前版本: {current_rev or '(无)'}")
    print(f"目标版本: {head_rev}")

    if current_rev == head_rev:
        print("\n✅ 数据库已是最新版本，无需迁移")
        return True

    # 获取待执行的迁移
    pending = get_pending_revisions(alembic_cfg, current_rev)
    print(f"\n📋 待执行的迁移 ({len(pending)}个):")
    for rev in pending:
        print(f"   - {rev.revision[:12]}: {rev.doc or '无描述'}")

    # 用户确认
    print("\n" + "=" * 80)
    print("⚠️  即将执行迁移")
    print("=" * 80)
    response = input("是否继续？(yes/no): ").strip().lower()
    if response not in ['yes', 'y', '是']:
        print("\n❌ 用户取消操作")
        return False

    # 执行迁移
    print_header("🚀 执行迁移")
    try:
        command.upgrade(alembic_cfg, 'head')
        print("\n✅ 迁移执行成功！")
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 验证结果
    print_header("🔍 验证结果")
    new_rev = get_current_revision(engine)
    print(f"迁移后版本: {new_rev}")

    if new_rev == head_rev:
        print("\n✅ 版本已同步到最新！")
    else:
        print(f"\n⚠️  版本不匹配: 期望 {head_rev}, 实际 {new_rev}")

    print_header("✅ 完成")
    print("\n🎉 OVS数据库迁移完成！")

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
