#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端数据库 pricing_orders 表结构"""
import sys, os

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
from sqlalchemy import inspect, text

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查云端 pricing_orders 表结构 ===\n")

        inspector = inspect(db.engine)

        # 获取表的所有列
        try:
            columns = inspector.get_columns('pricing_orders')

            print(f"✓ 表 pricing_orders 存在")
            print(f"✓ 总共 {len(columns)} 个字段\n")

            # 关键字段列表（与模型定义对应）
            critical_fields = {
                'pricing_total_discount_rate': 'Float - 批价单总折扣率',
                'settlement_total_discount_rate': 'Float - 结算单总折扣率',
                'is_direct_contract': 'Boolean - 厂商直签',
                'is_factory_pickup': 'Boolean - 厂家提货',
                'project_id': 'Integer - 项目ID',
                'quotation_id': 'Integer - 报价单ID',
                'dealer_id': 'Integer - 经销商ID',
                'distributor_id': 'Integer - 分销商ID',
            }

            print("=== 关键字段检查 ===\n")

            column_names = [col['name'] for col in columns]

            missing_fields = []
            for field, description in critical_fields.items():
                exists = field in column_names
                status = "✓" if exists else "❌"
                print(f"{status} {field:35} - {description}")
                if not exists:
                    missing_fields.append(field)

            if missing_fields:
                print(f"\n⚠️ 缺少 {len(missing_fields)} 个关键字段：")
                for field in missing_fields:
                    print(f"  - {field}")
                print("\n这可能导致：")
                print("  1. 审批时无法保存折扣率修改")
                print("  2. 数据收集函数获取不到字段值")
                print("  3. 分支条件评估可能受影响")

                print("\n🔧 建议执行数据库迁移：")
                print("  python3 standard_migration_upgrade.py")
            else:
                print("\n✓ 所有关键字段都存在")

            # 显示所有字段详情
            print("\n=== 完整字段列表 ===\n")
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                default = col.get('default', 'None')
                print(f"  {col['name']:35} {col_type:20} {nullable:10} default={default}")

            # 检查外键约束
            print("\n=== 外键约束检查 ===\n")
            foreign_keys = inspector.get_foreign_keys('pricing_orders')
            if foreign_keys:
                for fk in foreign_keys:
                    print(f"  {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print("  ⚠️ 未找到外键约束")

            # 测试查询一条数据
            print("\n=== 数据示例检查 ===\n")
            result = db.session.execute(
                text("SELECT id, order_number, pricing_total_discount_rate, settlement_total_discount_rate FROM pricing_orders ORDER BY created_at DESC LIMIT 1")
            ).fetchone()

            if result:
                print(f"  最新记录 ID: {result[0]}")
                print(f"  订单号: {result[1]}")
                print(f"  批价折扣率: {result[2] if len(result) > 2 else 'N/A (字段不存在)'}")
                print(f"  结算折扣率: {result[3] if len(result) > 3 else 'N/A (字段不存在)'}")
            else:
                print("  ⚠️ 表中没有数据")

        except Exception as e:
            print(f"❌ 检查失败: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
