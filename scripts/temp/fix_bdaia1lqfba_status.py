#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复产品BDAIA1LQFBA的状态（从已入库改回申请入库）"""

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

os.chdir(get_project_root())
sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.dev_product import DevProduct
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 80)
    print("修复产品BDAIA1LQFBA状态")
    print("=" * 80)

    # 查找产品
    dev_product = DevProduct.query.filter_by(mn_code='BDAIA1LQFBA').first()

    if not dev_product:
        print("\n❌ 未找到产品BDAIA1LQFBA")
        sys.exit(1)

    print(f"\n📋 当前产品信息:")
    print(f"   ID: {dev_product.id}")
    print(f"   MN编号: {dev_product.mn_code}")
    print(f"   型号: {dev_product.model}")
    print(f"   当前状态: {dev_product.status}")
    print(f"   当前阶段: {dev_product.current_stage_key}")

    # 检查是否已入库
    from app.models.product import Product
    warehoused = Product.query.filter_by(source_dev_product_id=dev_product.id).first()

    if warehoused:
        print(f"\n⚠️  警告：该产品已经实际入库到产品库（Product#{warehoused.id}）")
        print(f"   如果要修复状态，建议检查数据一致性")
        response = input("\n是否继续修复状态？(y/N): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)

    # 修复状态
    old_status = dev_product.status
    old_stage_key = dev_product.current_stage_key

    # 更新为申请入库状态
    dev_product.status = '申请入库'

    # 清理阶段历史中的错误完成记录
    if dev_product.stage_history:
        # 移除已入库阶段的记录
        dev_product.stage_history = [
            record for record in dev_product.stage_history
            if record.get('stage') != 'stored'
        ]

        # 如果申请入库阶段有结束日期，清除它
        for record in reversed(dev_product.stage_history):
            if record.get('stage') == 'apply_storage' and record.get('endDate'):
                record['endDate'] = None
                break

        # 触发SQLAlchemy更新
        dev_product.stage_history = list(dev_product.stage_history)

    dev_product.updated_at = datetime.now()

    print(f"\n✅ 修复操作:")
    print(f"   状态: {old_status} → {dev_product.status}")
    print(f"   阶段: {old_stage_key} → {dev_product.current_stage_key}")

    # 提交修改
    try:
        db.session.commit()
        print("\n✅ 状态修复成功！")
        print("\n📝 现在可以从产品详情页提交入库审批了")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
