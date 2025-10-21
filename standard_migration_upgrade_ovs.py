#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS数据库标准迁移升级工具
使用Flask-Migrate标准流程升级云端OVS数据库到最新版本

功能:
- 自动检查迁移状态
- 自动备份数据库
- 执行Flask-Migrate标准升级
- 验证升级结果

使用方法:
    python3 standard_migration_upgrade_ovs.py
"""

import os
import sys
import subprocess
from datetime import datetime

# OVS数据库连接信息
OVS_DB_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_command(cmd, description, timeout=300):
    """执行命令并返回结果"""
    print(f"\n🔧 {description}...")
    print(f"命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'DATABASE_URL': OVS_DB_URL}
        )

        # 打印输出
        if result.stdout:
            print(result.stdout)

        return True, result.stdout

    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败！")
        print(f"返回码: {e.returncode}")
        if e.stdout:
            print(f"标准输出:\n{e.stdout}")
        if e.stderr:
            print(f"错误输出:\n{e.stderr}")
        return False, e.stderr

    except subprocess.TimeoutExpired:
        print(f"❌ 命令执行超时！")
        return False, "超时"

    except Exception as e:
        print(f"❌ 发生异常: {e}")
        return False, str(e)


def backup_database():
    """备份OVS数据库"""
    print_header("步骤1: 备份OVS数据库")

    print("⚠️  升级前自动备份数据库...")
    success, output = run_command(
        ['python3', 'simple_ovs_backup.py'],
        "执行OVS数据库备份",
        timeout=120
    )

    if not success:
        print("❌ 数据库备份失败！")
        print("   为安全起见，终止升级流程")
        return False

    print("✅ 数据库备份完成")
    return True


def check_current_status():
    """检查当前迁移状态"""
    print_header("步骤2: 检查当前迁移状态")

    success, output = run_command(
        ['flask', 'db', 'current'],
        "查询OVS当前迁移版本",
        timeout=30
    )

    if success and output:
        print(f"✅ 查询成功")
        return True
    else:
        print("⚠️  无法查询迁移状态，将继续升级流程")
        return True  # 继续执行，不中断


def show_pending_migrations():
    """显示待应用的迁移"""
    print_header("步骤3: 检查待应用的迁移")

    # 尝试运行检查脚本
    print("📋 运行迁移状态检查脚本...")
    subprocess.run(
        ['python3', 'scripts/temp/check_ovs_migration_status.py'],
        env={**os.environ, 'DATABASE_URL': OVS_DB_URL}
    )

    print("\n✅ 迁移检查完成，继续执行升级流程...")


def execute_upgrade():
    """执行数据库升级"""
    print_header("步骤4: 执行数据库升级")

    print("🚀 开始执行Flask-Migrate升级...")
    success, output = run_command(
        ['flask', 'db', 'upgrade'],
        "执行 flask db upgrade",
        timeout=600
    )

    if not success:
        print("\n❌ 升级失败！")
        print("\n可能的原因:")
        print("   1. 迁移文件有错误")
        print("   2. 数据库结构冲突")
        print("   3. 网络连接问题")
        print("\n建议:")
        print("   1. 检查错误输出")
        print("   2. 查看最新的备份文件")
        print("   3. 如需回滚，使用备份恢复数据库")
        return False

    print("\n✅ 升级成功！")
    return True


def verify_result():
    """验证升级结果"""
    print_header("步骤5: 验证升级结果")

    # 检查最终版本
    print("🔍 检查升级后的迁移版本...")
    success, output = run_command(
        ['flask', 'db', 'current'],
        "查询升级后版本",
        timeout=30
    )

    if success:
        print("✅ 版本查询成功")

    # 运行Schema对比
    print("\n🔍 运行Schema对比验证...")
    subprocess.run(
        ['python3', 'scripts/temp/compare_local_ovs_schemas.py'],
        env={**os.environ, 'DATABASE_URL': OVS_DB_URL}
    )

    return True


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 OVS数据库标准迁移升级工具")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标数据库: pma_db_ovs @ Supabase")

    # 用户确认
    print("\n" + "=" * 80)
    print("⚠️  重要提醒")
    print("=" * 80)
    print("本工具将:")
    print("   1. 自动备份OVS数据库")
    print("   2. 检查当前迁移状态")
    print("   3. 显示待应用的迁移列表")
    print("   4. 执行Flask-Migrate升级到最新版本")
    print("   5. 验证升级结果")
    print("\n注意:")
    print("   - 升级期间请勿操作数据库")
    print("   - 如遇问题可使用备份恢复")

    response = input("\n是否继续？(yes/no): ").strip().lower()
    if response not in ['yes', 'y', '是']:
        print("\n❌ 用户取消操作")
        return

    # 执行升级流程
    try:
        # 步骤1: 备份数据库
        if not backup_database():
            print("\n❌ 升级流程终止")
            return

        # 步骤2: 检查当前状态
        check_current_status()

        # 步骤3: 显示待应用的迁移
        show_pending_migrations()

        # 步骤4: 执行升级
        if not execute_upgrade():
            print("\n❌ 升级流程失败")
            return

        # 步骤5: 验证结果
        verify_result()

        # 完成
        print_header("✅ 升级完成")
        print("\n🎉 OVS数据库已成功升级到最新版本！")
        print("\n下一步:")
        print("   1. 检查应用运行是否正常")
        print("   2. 验证数据完整性")
        print("   3. 如有问题，使用备份文件恢复")

        # 显示最新备份
        print("\n📁 最新备份文件:")
        subprocess.run(['ls', '-lht', 'cloud_db_backups/', '|', 'grep', 'ovs', '|', 'head', '-3'], shell=True)

    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
        return

    except Exception as e:
        print(f"\n\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == '__main__':
    main()
