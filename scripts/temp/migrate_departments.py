#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门数据迁移脚本
1. 为 Department 表添加 company_name 字段
2. 将和源通信的部门从 Dictionary 迁移到 Department 表
3. 设置部门负责人
"""
import sys
import os

# 路径修正
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
from app.models.expense import Department
from app.models.dictionary import Dictionary
from sqlalchemy import text

def check_and_add_company_name_column():
    """检查并添加 company_name 字段"""
    print("\n=== 步骤1: 检查 company_name 字段 ===")

    # 检查字段是否已存在
    result = db.session.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'departments' AND column_name = 'company_name'
    """))

    if result.fetchone():
        print("✓ company_name 字段已存在")
        return True

    print("→ 添加 company_name 字段...")
    try:
        db.session.execute(text("""
            ALTER TABLE departments
            ADD COLUMN company_name VARCHAR(200)
        """))
        db.session.commit()
        print("✓ company_name 字段添加成功")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ 添加字段失败: {e}")
        return False

def migrate_heyuan_departments():
    """迁移和源通信的部门数据"""
    print("\n=== 步骤2: 迁移和源通信部门 ===")

    HEYUAN_COMPANY = "和源通信（上海）股份有限公司"

    # Dictionary 中的部门映射
    dept_mapping = {
        'sales_dep': ('销售部', 'SALES'),
        'rd_dep': ('产品和解决方案部', 'RD'),
        'service_dep': ('服务部', 'SERVICE'),
        'finance_dep': ('财务部', 'FINANCE'),
    }

    migrated = 0
    for dict_key, (name, code) in dept_mapping.items():
        # 检查是否已存在
        existing = Department.query.filter_by(name=name, company_name=HEYUAN_COMPANY).first()
        if existing:
            print(f"  - {name}: 已存在 (id={existing.id})")
            continue

        # 创建新部门
        dept = Department(
            name=name,
            code=f"{code}_{HEYUAN_COMPANY[:4]}",  # 添加公司前缀确保唯一
            company_name=HEYUAN_COMPANY,
            is_active=True
        )
        db.session.add(dept)
        migrated += 1
        print(f"  + {name}: 新建成功")

    db.session.commit()
    print(f"✓ 迁移完成，新建 {migrated} 个部门")

def set_department_managers():
    """设置部门负责人"""
    print("\n=== 步骤3: 设置部门负责人 ===")

    HEYUAN_COMPANY = "和源通信（上海）股份有限公司"

    # 获取和源通信的部门负责人
    managers = User.query.filter(
        User.is_department_manager == True,
        User.company_name == HEYUAN_COMPANY,
        User.department.isnot(None),
        User.department != ''
    ).all()

    print(f"找到 {len(managers)} 个和源通信的部门负责人:")

    updated = 0
    for manager in managers:
        # 查找对应的部门
        dept = Department.query.filter_by(
            name=manager.department,
            company_name=HEYUAN_COMPANY
        ).first()

        if not dept:
            print(f"  ! {manager.real_name} ({manager.department}): 未找到对应部门")
            continue

        if dept.manager_id == manager.id:
            print(f"  - {manager.real_name} → {dept.name}: 已设置")
            continue

        # 设置负责人
        dept.manager_id = manager.id
        updated += 1
        print(f"  + {manager.real_name} → {dept.name}: 设置成功")

    db.session.commit()
    print(f"✓ 设置完成，更新 {updated} 个部门的负责人")

def show_result():
    """显示迁移结果"""
    print("\n=== 迁移结果 ===")

    depts = Department.query.all()
    if not depts:
        print("Department 表为空")
        return

    print(f"{'部门名称':<20} {'公司':<30} {'负责人':<10} {'代码':<15}")
    print("-" * 80)
    for dept in depts:
        manager_name = dept.manager.real_name if dept.manager else "(未设置)"
        company = dept.company_name or "(未设置)"
        print(f"{dept.name:<20} {company:<30} {manager_name:<10} {dept.code:<15}")

def main():
    print("=" * 60)
    print("部门数据迁移脚本")
    print("=" * 60)

    # 步骤1: 添加 company_name 字段
    if not check_and_add_company_name_column():
        print("迁移中止")
        return

    # 步骤2: 迁移部门数据
    migrate_heyuan_departments()

    # 步骤3: 设置负责人
    set_department_managers()

    # 显示结果
    show_result()

    print("\n" + "=" * 60)
    print("迁移完成!")
    print("=" * 60)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        main()
