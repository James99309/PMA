#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON报告查看工具 - 友好格式化显示
"""
import json
import sys

def view_json_report(file_path):
    """查看和显示JSON报告"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n" + "=" * 80)
        print("📊 批价分析报告 - JSON数据")
        print("=" * 80)

        # 显示时间戳
        print(f"\n⏰ 生成时间: {data.get('timestamp', 'N/A')}")

        # 显示汇总数据
        print("\n" + "-" * 80)
        print("📋 员工成绩汇总")
        print("-" * 80)

        summary = data.get('summary', {})
        for username, info in summary.items():
            print(f"\n{username} - {info.get('real_name', 'N/A')}")
            print(f"  ├─ 线上批价单: {info.get('online_quotations', 0)} 个")
            print(f"  ├─ 线上金额: ¥{info.get('online_total_amount', 0):,.0f}")
            print(f"  ├─ 线下记录: {info.get('offline_records', 0)} 条")
            print(f"  ├─ 线下金额: ¥{info.get('offline_total_amount', 0):,.0f}")
            print(f"  └─ 合计金额: ¥{info.get('combined_total', 0):,.0f}")

        # 显示总体统计
        print("\n" + "-" * 80)
        print("📈 总体统计")
        print("-" * 80)

        totals = data.get('totals', {})
        print(f"线上总额: ¥{totals.get('online_total', 0):,.0f}")
        print(f"线下总额: ¥{totals.get('offline_total', 0):,.0f}")
        print(f"合计: ¥{totals.get('combined_total', 0):,.0f}")
        print(f"线上批价单总数: {totals.get('online_quotations', 0)} 个")
        print(f"线下记录总数: {totals.get('offline_records', 0)} 条")

        # 显示详细批价单
        print("\n" + "-" * 80)
        print("🔍 详细批价单列表")
        print("-" * 80)

        details = data.get('details', {})
        for username, user_data in details.items():
            online_quotations = user_data.get('online', {}).get('quotations', [])

            if online_quotations:
                real_name = user_data.get('online', {}).get('real_name', username)
                print(f"\n{username} ({real_name}) - {len(online_quotations)} 个批价单:")

                for q in online_quotations:
                    print(f"  • {q.get('quotation_number', 'N/A'):20} | ¥{q.get('amount', 0):>12,.0f}")

        print("\n" + "=" * 80)
        print("✅ 报告查看完成")
        print("=" * 80 + "\n")

    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # 使用最新的分析报告文件
    file_path = '/Users/nijie/Documents/PMA/data/quotation_analysis_final_report.json'

    # 如果文件不存在，尝试其他文件
    import os
    if not os.path.exists(file_path):
        file_path = '/Users/nijie/Documents/PMA/data/quotation_performance_analysis_final.json'

    print(f"📂 正在读取: {file_path}")
    view_json_report(file_path)
