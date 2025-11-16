#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量创建缺失的产品子类别
为60个无法匹配的产品创建对应的子类别
"""
import sys
import os
from datetime import datetime

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

from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

from app.models.product_code import ProductSubcategory

def main():
    print("=" * 100)
    print("批量创建产品子类别")
    print("=" * 100)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 定义30个需要创建的子类别
    subcategories_to_create = [
        # 基站类 (category_id=1)
        {'category_id': 1, 'name': '智能信道交换机', 'code_letter': 'J', 'display_order': 9},

        # 合路平台类 (category_id=2)
        {'category_id': 2, 'name': '一体化分合路矩阵', 'code_letter': 'J', 'display_order': 10},

        # 直放站类 (category_id=3)
        {'category_id': 3, 'name': '数字智能光纤远端直放站', 'code_letter': 'H', 'display_order': 10},
        {'category_id': 3, 'name': '射频中继组件 413MHz', 'code_letter': 'I', 'display_order': 11},

        # 天线类 (category_id=7)
        {'category_id': 7, 'name': '综合防爆型室内全向吸顶天线', 'code_letter': 'I', 'display_order': 9},
        {'category_id': 7, 'name': '标准L型贴墙室外天线支架', 'code_letter': 'J', 'display_order': 10},

        # 配件类 (category_id=10) - 19个，按使用频率排序
        {'category_id': 10, 'name': '同轴电缆跳接线', 'code_letter': 'A', 'display_order': 3},
        {'category_id': 10, 'name': '单模光纤跳线单芯', 'code_letter': 'B', 'display_order': 4},
        {'category_id': 10, 'name': '光纤配线架', 'code_letter': 'C', 'display_order': 5},
        {'category_id': 10, 'name': '衰减器', 'code_letter': 'D', 'display_order': 6},
        {'category_id': 10, 'name': '轻低烟无卤阻燃铠光缆', 'code_letter': 'G', 'display_order': 7},
        {'category_id': 10, 'name': '馈线接地卡', 'code_letter': 'H', 'display_order': 8},
        {'category_id': 10, 'name': '同轴电缆连接器', 'code_letter': 'I', 'display_order': 9},
        {'category_id': 10, 'name': '同轴电缆连接转换器', 'code_letter': 'J', 'display_order': 10},
        {'category_id': 10, 'name': '波纹管同轴电缆', 'code_letter': 'K', 'display_order': 11},
        {'category_id': 10, 'name': '1-5/8"漏泄同轴电缆接头', 'code_letter': 'L', 'display_order': 12},
        {'category_id': 10, 'name': '1-5/8"漏泄同轴电缆吊夹', 'code_letter': 'M', 'display_order': 13},
        {'category_id': 10, 'name': '1-5/8"漏泄同轴电缆防火吊夹', 'code_letter': 'N', 'display_order': 14},
        {'category_id': 10, 'name': '同轴避雷器', 'code_letter': 'O', 'display_order': 15},
        {'category_id': 10, 'name': '普通中心束管式光缆', 'code_letter': 'P', 'display_order': 16},
        {'category_id': 10, 'name': '漏泄同轴电缆', 'code_letter': 'Q', 'display_order': 17},
        {'category_id': 10, 'name': '直流隔断器', 'code_letter': 'R', 'display_order': 18},
        {'category_id': 10, 'name': '终端负载', 'code_letter': 'S', 'display_order': 19},
        {'category_id': 10, 'name': '超柔同轴电缆跳接线', 'code_letter': 'T', 'display_order': 20},
        {'category_id': 10, 'name': '跳线', 'code_letter': 'U', 'display_order': 21},

        # 服务类 (category_id=12)
        {'category_id': 12, 'name': '施工附件', 'code_letter': 'A', 'display_order': 1},
        {'category_id': 12, 'name': '调试开通', 'code_letter': 'B', 'display_order': 2},
        {'category_id': 12, 'name': '主站频率占用费', 'code_letter': 'C', 'display_order': 3},
        {'category_id': 12, 'name': '对讲机频率占用费', 'code_letter': 'D', 'display_order': 4},
        {'category_id': 12, 'name': '电磁环境检测及申报报告费', 'code_letter': 'E', 'display_order': 5},
    ]

    print(f"准备创建 {len(subcategories_to_create)} 个子类别\n")

    # 确认执行
    confirm = input("是否继续执行？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 用户取消执行")
        session.close()
        return

    print("\n" + "=" * 100)
    print("开始创建子类别...")
    print("=" * 100 + "\n")

    created_count = 0
    skipped_count = 0
    failed_count = 0

    category_groups = {}
    for item in subcategories_to_create:
        cat_id = item['category_id']
        if cat_id not in category_groups:
            category_groups[cat_id] = []
        category_groups[cat_id].append(item)

    for cat_id, items in sorted(category_groups.items()):
        cat_name = {
            1: '基站',
            2: '合路平台',
            3: '直放站',
            7: '天线',
            10: '配件',
            12: '服务'
        }.get(cat_id, f'分类{cat_id}')

        print(f"【{cat_name}】类别 (ID={cat_id}) - {len(items)}个子类别")
        print("-" * 100)

        for item in items:
            name = item['name']
            code = item['code_letter']
            order = item['display_order']

            # 检查是否已存在
            existing = session.query(ProductSubcategory).filter(
                ProductSubcategory.category_id == cat_id,
                ProductSubcategory.name == name
            ).first()

            if existing:
                print(f"  ⚠️  已存在: {name} (ID={existing.id}, code={existing.code_letter})")
                skipped_count += 1
                continue

            try:
                # 创建新子类别
                new_subcategory = ProductSubcategory(
                    category_id=cat_id,
                    name=name,
                    code_letter=code,
                    display_order=order,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_subcategory)
                session.flush()  # 获取ID

                print(f"  ✅ 已创建: {name} (ID={new_subcategory.id}, code={code}, order={order})")
                created_count += 1

            except Exception as e:
                print(f"  ❌ 创建失败: {name} - {e}")
                failed_count += 1

        print()

    # 提交更改
    print("=" * 100)
    print("提交数据库更改...")
    print("=" * 100)

    try:
        session.commit()
        print("✅ 所有更改已提交到数据库\n")
    except Exception as e:
        session.rollback()
        print(f"❌ 提交失败: {e}\n")
        session.close()
        return

    # 统计报告
    print("=" * 100)
    print("创建统计报告")
    print("=" * 100)
    print(f"✅ 成功创建: {created_count} 个")
    print(f"⚠️  已存在跳过: {skipped_count} 个")
    print(f"❌ 创建失败: {failed_count} 个")
    print(f"📊 总计处理: {created_count + skipped_count + failed_count} 个")
    print()

    # 验证结果
    print("=" * 100)
    print("验证创建结果")
    print("=" * 100)

    total_subcategories = session.query(ProductSubcategory).count()
    print(f"数据库中现有子类别总数: {total_subcategories}")
    print()

    if created_count > 0:
        print("🎉 子类别创建完成！现在可以运行数据迁移脚本关联产品。")
    else:
        print("ℹ️  未创建新子类别（可能已全部存在）")

    print(f"\n执行完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    session.close()

if __name__ == '__main__':
    main()
