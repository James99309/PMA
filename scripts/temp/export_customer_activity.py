#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出客户活跃度报表
生成包含客户、归属人、活跃度状态的Excel表格供HR筛选
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

# 设置环境变量以避免 WeasyPrint 问题
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib'

from app import create_app, db
from app.models.customer import Company
from app.models.user import User
from datetime import datetime
import pandas as pd

# 活跃度状态映射
ACTIVITY_STATUS_CN = {
    'highly_active': '高度活跃',
    'active': '活跃',
    'normal': '正常',
    'to_follow': '待跟进',
    'dormant': '休眠',
    'churned': '流失'
}

# 状态排序优先级（用于排序）
STATUS_ORDER = {
    'highly_active': 1,
    'active': 2,
    'normal': 3,
    'to_follow': 4,
    'dormant': 5,
    'churned': 6
}

def export_customer_activity():
    """导出客户活跃度报表"""
    app = create_app()

    with app.app_context():
        # 查询所有未删除的客户
        companies = Company.query.filter_by(is_deleted=False).all()

        data = []
        for company in companies:
            # 获取归属人信息
            owner_name = ''
            if company.owner:
                owner_name = company.owner.real_name or company.owner.username

            # 获取活跃度状态
            status = company.status or 'churned'
            status_cn = ACTIVITY_STATUS_CN.get(status, status)

            data.append({
                '客户编码': company.company_code,
                '客户名称': company.company_name,
                '归属人': owner_name,
                '活跃度状态': status_cn,
                '活跃度状态(英文)': status,
                '客户类型': company.company_type or '',
                '行业': company.industry or '',
                '国家/地区': company.country or '',
                '省份/州': company.region or '',
                '创建时间': company.created_at.strftime('%Y-%m-%d') if company.created_at else '',
                '更新时间': company.updated_at.strftime('%Y-%m-%d') if company.updated_at else '',
                '_sort_order': STATUS_ORDER.get(status, 99)
            })

        # 创建 DataFrame
        df = pd.DataFrame(data)

        # 按活跃度状态和归属人排序
        df = df.sort_values(['_sort_order', '归属人', '客户名称'])

        # 删除排序辅助列
        df = df.drop(columns=['_sort_order'])

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(get_project_root(), 'data', 'temp', f'客户活跃度报表_{timestamp}.xlsx')

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 导出到 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='客户活跃度', index=False)

            # 获取工作表
            worksheet = writer.sheets['客户活跃度']

            # 调整列宽
            column_widths = {
                'A': 12,  # 客户编码
                'B': 35,  # 客户名称
                'C': 12,  # 归属人
                'D': 12,  # 活跃度状态
                'E': 15,  # 活跃度状态(英文)
                'F': 15,  # 客户类型
                'G': 15,  # 行业
                'H': 12,  # 国家/地区
                'I': 12,  # 省份/州
                'J': 12,  # 创建时间
                'K': 12,  # 更新时间
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        print(f"\n✅ 导出成功!")
        print(f"📄 文件路径: {output_path}")
        print(f"📊 总客户数: {len(data)}")

        # 打印统计信息
        print("\n📈 活跃度统计:")
        status_stats = df['活跃度状态'].value_counts()
        for status in ['高度活跃', '活跃', '正常', '待跟进', '休眠', '流失']:
            count = status_stats.get(status, 0)
            print(f"   {status}: {count}")

        # 打印归属人统计
        print("\n👥 归属人统计:")
        owner_stats = df['归属人'].value_counts()
        for owner, count in owner_stats.head(10).items():
            owner_display = owner if owner else '(未分配)'
            print(f"   {owner_display}: {count}")

        return output_path


if __name__ == '__main__':
    export_customer_activity()
