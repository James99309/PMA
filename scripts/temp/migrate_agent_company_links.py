#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移代理商账户关联到公司表

使用方法：
    python scripts/temp/migrate_agent_company_links.py

说明：
    此脚本查找所有角色为'dealer'的用户，尝试根据company_name
    匹配到Company表中的记录，建立linked_company_id关联。
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.user import User
from app.models.customer import Company


def migrate_agent_links():
    """迁移代理商账户到公司关联"""
    app = create_app()

    with app.app_context():
        # 查找所有代理商角色的用户
        dealers = User.query.filter_by(role='dealer').all()

        print(f"找到 {len(dealers)} 个代理商账户")
        print("-" * 60)

        linked_count = 0
        already_linked = 0
        not_found = 0
        multiple_matches = 0

        for user in dealers:
            print(f"\n处理用户: {user.username} (ID: {user.id})")
            print(f"  公司名称: {user.company_name}")

            # 检查是否已有关联
            if user.linked_company_id:
                print(f"  ✓ 已关联到公司 ID: {user.linked_company_id}")
                already_linked += 1
                continue

            if not user.company_name:
                print(f"  ✗ 未设置公司名称，跳过")
                not_found += 1
                continue

            # 尝试匹配公司
            # 1. 精确匹配
            companies = Company.query.filter(
                Company.company_name == user.company_name,
                Company.is_deleted == False
            ).all()

            # 2. 如果精确匹配失败，尝试模糊匹配
            if not companies:
                companies = Company.query.filter(
                    Company.company_name.ilike(f"%{user.company_name}%"),
                    Company.is_deleted == False
                ).all()

            if len(companies) == 0:
                print(f"  ✗ 未找到匹配的公司")
                not_found += 1
            elif len(companies) == 1:
                company = companies[0]
                user.linked_company_id = company.id
                print(f"  ✓ 关联到公司: {company.company_name} (ID: {company.id})")
                linked_count += 1
            else:
                print(f"  ⚠ 找到多个匹配的公司:")
                for c in companies:
                    print(f"    - {c.company_name} (ID: {c.id})")
                print(f"  需要手动选择，暂时跳过")
                multiple_matches += 1

        # 提交更改
        if linked_count > 0:
            db.session.commit()
            print(f"\n数据库更改已提交")

        # 打印统计
        print("\n" + "=" * 60)
        print("迁移统计:")
        print(f"  总代理商账户数: {len(dealers)}")
        print(f"  已有关联: {already_linked}")
        print(f"  新建关联: {linked_count}")
        print(f"  未找到匹配公司: {not_found}")
        print(f"  多个匹配需手动处理: {multiple_matches}")


def show_current_status():
    """显示当前代理商账户状态"""
    app = create_app()

    with app.app_context():
        dealers = User.query.filter_by(role='dealer').all()

        print("当前代理商账户状态:")
        print("-" * 80)
        print(f"{'用户名':<15} {'公司名称':<30} {'关联公司ID':<10} {'状态':<10}")
        print("-" * 80)

        for user in dealers:
            status = "已关联" if user.linked_company_id else "未关联"
            company_name = user.company_name or "(未设置)"
            linked_id = str(user.linked_company_id) if user.linked_company_id else "-"
            print(f"{user.username:<15} {company_name:<30} {linked_id:<10} {status:<10}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='迁移代理商账户关联到公司表')
    parser.add_argument('--status', action='store_true', help='仅显示当前状态，不执行迁移')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际修改数据库')

    args = parser.parse_args()

    if args.status:
        show_current_status()
    else:
        migrate_agent_links()
