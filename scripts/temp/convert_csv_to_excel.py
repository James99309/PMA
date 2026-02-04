#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将CSV转换为格式化的Excel报表"""
import pandas as pd
from datetime import datetime
import os

# 活跃度状态映射
ACTIVITY_STATUS_CN = {
    'highly_active': '高度活跃',
    'active': '活跃',
    'normal': '正常',
    'to_follow': '待跟进',
    'dormant': '休眠',
    'churned': '流失',
    '': '流失',
    None: '流失'
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

# 读取CSV
df = pd.read_csv('/Users/nijie/Documents/PMA/data/temp/customer_activity_raw.csv')

# 处理数据
df['活跃度状态'] = df['status'].apply(lambda x: ACTIVITY_STATUS_CN.get(x, '流失'))
df['活跃度状态(英文)'] = df['status'].fillna('churned')
df['_sort_order'] = df['status'].apply(lambda x: STATUS_ORDER.get(x, 6))
df['归属人'] = df['owner_name'].fillna('')

# 重命名列
df = df.rename(columns={
    'company_code': '客户编码',
    'company_name': '客户名称',
    'company_type': '客户类型',
    'industry': '行业',
    'country': '国家/地区',
    'region': '省份/州',
    'created_at': '创建时间',
    'updated_at': '更新时间'
})

# 选择需要的列并排序
result_df = df[['客户编码', '客户名称', '归属人', '活跃度状态', '活跃度状态(英文)',
                '客户类型', '行业', '国家/地区', '省份/州', '创建时间', '更新时间', '_sort_order']]
result_df = result_df.sort_values(['_sort_order', '归属人', '客户名称'])
result_df = result_df.drop(columns=['_sort_order'])

# 生成文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = f'/Users/nijie/Documents/PMA/data/temp/客户活跃度报表_NAS_{timestamp}.xlsx'

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
print(f"📊 总客户数: {len(result_df)}")

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
