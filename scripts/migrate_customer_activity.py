#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户活跃度6级状态迁移脚本

用途: 将现有客户状态迁移到新的6级活跃度状态系统
执行前: 必须先运行 backup_customer_status.py 进行数据备份

迁移逻辑:
1. 读取所有客户
2. 根据新的活跃度规则计算每个客户的状态
3. 更新数据库中的状态字段
4. 输出迁移统计报告
"""
import sys
import os
from datetime import datetime


def get_project_root():
    """获取项目根目录"""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


# 路径修正
sys.path.insert(0, get_project_root())
os.chdir(get_project_root())


def migrate_customer_activity(dry_run=False):
    """
    迁移客户活跃度状态

    Args:
        dry_run: 如果为 True，只计算不实际更新数据库
    """
    from app import create_app, db
    from app.models.customer import Company
    from app.utils.activity_tracker import calculate_company_activity_status

    app = create_app()
    with app.app_context():
        # 查询所有未删除的客户
        customers = Company.query.filter_by(is_deleted=False).all()
        total = len(customers)

        print(f"{'[DRY RUN] ' if dry_run else ''}开始迁移客户活跃度状态...")
        print(f"总客户数: {total}")
        print("-" * 60)

        # 统计变量
        status_before = {}
        status_after = {}
        changes = []

        for i, company in enumerate(customers, 1):
            old_status = company.status or 'null'
            new_status, reason, last_activity = calculate_company_activity_status(company.id)

            # 统计旧状态
            status_before[old_status] = status_before.get(old_status, 0) + 1

            # 统计新状态
            status_after[new_status] = status_after.get(new_status, 0) + 1

            # 记录变更
            if old_status != new_status:
                changes.append({
                    'id': company.id,
                    'name': company.company_name,
                    'old': old_status,
                    'new': new_status,
                    'reason': reason
                })

                if not dry_run:
                    company.status = new_status
                    db.session.add(company)

            # 进度显示
            if i % 100 == 0:
                print(f"  处理进度: {i}/{total} ({i * 100 // total}%)")

        # 提交更改
        if not dry_run and changes:
            db.session.commit()
            print(f"\n✅ 已提交数据库更改")
        elif dry_run:
            print(f"\n[DRY RUN] 未修改数据库")

        # 输出统计报告
        print("\n" + "=" * 60)
        print("迁移统计报告")
        print("=" * 60)

        print("\n📊 迁移前状态分布:")
        for status, count in sorted(status_before.items(), key=lambda x: -x[1]):
            print(f"  {status}: {count}")

        print("\n📊 迁移后状态分布:")
        status_labels = {
            'highly_active': '高度活跃',
            'active': '活跃',
            'normal': '正常',
            'to_follow': '待跟进',
            'dormant': '休眠',
            'churned': '流失'
        }
        for status in ['highly_active', 'active', 'normal', 'to_follow', 'dormant', 'churned']:
            count = status_after.get(status, 0)
            label = status_labels.get(status, status)
            print(f"  {label} ({status}): {count}")

        print(f"\n📝 状态变更数量: {len(changes)}")

        # 显示部分变更详情
        if changes:
            print("\n📋 变更详情（前20条）:")
            for change in changes[:20]:
                print(f"  [{change['id']}] {change['name'][:20]}: {change['old']} -> {change['new']} ({change['reason']})")

            if len(changes) > 20:
                print(f"  ... 还有 {len(changes) - 20} 条变更")

        return len(changes), total


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='客户活跃度6级状态迁移脚本')
    parser.add_argument('--dry-run', action='store_true', help='只计算不实际更新数据库')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认提示')

    args = parser.parse_args()

    print("=" * 60)
    print("客户活跃度6级状态迁移脚本")
    print("=" * 60)

    if not args.dry_run and not args.yes:
        # 检查备份文件
        backup_dir = os.path.join(get_project_root(), 'data', 'backups')
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('customer_status_backup_')] if os.path.exists(backup_dir) else []

        if not backup_files:
            print("\n⚠️  警告：未检测到备份文件！")
            print("请先运行 python scripts/backup_customer_status.py 进行备份")
            confirm = input("\n确定要在没有备份的情况下继续吗？(y/N): ")
            if confirm.lower() != 'y':
                print("已取消迁移")
                return
        else:
            latest_backup = sorted(backup_files)[-1]
            print(f"\n✅ 检测到最新备份: {latest_backup}")

        confirm = input("\n确定要执行迁移吗？(y/N): ")
        if confirm.lower() != 'y':
            print("已取消迁移")
            return

    changes, total = migrate_customer_activity(dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"[DRY RUN] 迁移预览完成，预计更新 {changes}/{total} 条记录")
        print("如果确认无误，请移除 --dry-run 参数执行实际迁移")
    else:
        print(f"迁移完成，共更新 {changes}/{total} 条记录")


if __name__ == '__main__':
    main()
