#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户状态备份脚本 - 迁移前执行

用途: 在执行客户活跃度6级状态迁移前，备份所有客户的当前状态数据
备份文件位置: data/backups/customer_status_backup_YYYYMMDD_HHMMSS.json
"""
import sys
import os
import json
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


def backup_customer_status():
    """备份所有客户的状态数据"""
    from app import create_app, db
    from app.models.customer import Company

    app = create_app()
    with app.app_context():
        # 查询所有客户的状态
        customers = Company.query.filter_by(is_deleted=False).all()

        backup_data = {
            'backup_time': datetime.now().isoformat(),
            'backup_purpose': '客户活跃度6级状态迁移前备份',
            'total_count': len(customers),
            'customers': []
        }

        for c in customers:
            backup_data['customers'].append({
                'id': c.id,
                'company_code': c.company_code,
                'company_name': c.company_name,
                'old_status': c.status,
                'owner_id': c.owner_id,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            })

        # 创建备份目录
        backup_dir = os.path.join(get_project_root(), 'data', 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # 保存备份文件
        backup_file = os.path.join(
            backup_dir,
            f"customer_status_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 备份完成: {backup_file}")
        print(f"   总客户数: {len(customers)}")

        # 统计当前状态分布
        status_count = {}
        for c in customers:
            status = c.status or 'null'
            status_count[status] = status_count.get(status, 0) + 1

        print(f"   当前状态分布:")
        for status, count in sorted(status_count.items(), key=lambda x: -x[1]):
            print(f"     - {status}: {count}")

        return backup_file


if __name__ == '__main__':
    print("=" * 50)
    print("客户状态备份脚本")
    print("=" * 50)
    backup_customer_status()
