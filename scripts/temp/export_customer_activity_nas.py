#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出NAS生产环境客户活跃度报表
通过SSH隧道连接中国NAS的PostgreSQL数据库
"""
import os
import sys
from datetime import datetime

# 需要先建立SSH隧道:
# cloudflared access tcp --hostname ssh.jamesgpone.win --url localhost:2222 &
# ssh -p 2222 -L 15432:pma-postgres:5432 james.sh@localhost

import psycopg2
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

# 状态排序优先级
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
    # 连接NAS数据库（通过SSH隧道）
    conn = psycopg2.connect(
        host='localhost',
        port=15432,
        database='pma',
        user='pma',
        password='pma123'
    )

    # 查询客户和归属人数据
    query = """
    SELECT
        c.company_code,
        c.company_name,
        u.real_name as owner_name,
        u.username as owner_username,
        c.status,
        c.company_type,
        c.industry,
        c.country,
        c.region,
        c.created_at,
        c.updated_at
    FROM companies c
    LEFT JOIN users u ON c.owner_id = u.id
    WHERE c.is_deleted = false
    ORDER BY c.updated_at DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()

    # 处理数据
    data = []
    for _, row in df.iterrows():
        owner_name = row['owner_name'] or row['owner_username'] or ''
        status = row['status'] or 'churned'
        status_cn = ACTIVITY_STATUS_CN.get(status, status)

        data.append({
            '客户编码': row['company_code'],
            '客户名称': row['company_name'],
            '归属人': owner_name,
            '活跃度状态': status_cn,
            '活跃度状态(英文)': status,
            '客户类型': row['company_type'] or '',
            '行业': row['industry'] or '',
            '国家/地区': row['country'] or '',
            '省份/州': row['region'] or '',
            '创建时间': row['created_at'].strftime('%Y-%m-%d') if row['created_at'] else '',
            '更新时间': row['updated_at'].strftime('%Y-%m-%d') if row['updated_at'] else '',
            '_sort_order': STATUS_ORDER.get(status, 99)
        })

    # 创建 DataFrame
    result_df = pd.DataFrame(data)

    # 按活跃度状态和归属人排序
    result_df = result_df.sort_values(['_sort_order', '归属人', '客户名称'])

    # 删除排序辅助列
    result_df = result_df.drop(columns=['_sort_order'])

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'/Users/nijie/Documents/PMA/data/temp/客户活跃度报表_NAS_{timestamp}.xlsx'

    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 导出到 Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name='客户活跃度', index=False)

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
    status_stats = result_df['活跃度状态'].value_counts()
    for status in ['高度活跃', '活跃', '正常', '待跟进', '休眠', '流失']:
        count = status_stats.get(status, 0)
        print(f"   {status}: {count}")

    # 打印归属人统计
    print("\n👥 归属人统计:")
    owner_stats = result_df['归属人'].value_counts()
    for owner, count in owner_stats.head(10).items():
        owner_display = owner if owner else '(未分配)'
        print(f"   {owner_display}: {count}")

    return output_path


if __name__ == '__main__':
    export_customer_activity()
