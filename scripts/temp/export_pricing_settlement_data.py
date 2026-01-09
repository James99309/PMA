#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出SP8D数据库中的批价单和结算单数据到Excel
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

project_root = get_project_root()
sys.path.insert(0, project_root)

# 设置SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# SP8D数据库连接
DATABASE_URL = os.environ['DATABASE_URL']

def export_data():
    """导出批价单和结算单数据"""
    print("连接SP8D数据库...")
    engine = create_engine(DATABASE_URL)

    # 查询批价单数据
    print("查询批价单数据...")
    pricing_query = """
    SELECT
        po.order_number AS "批价单号",
        po.created_at AS "创建时间",
        u.real_name AS "负责销售",
        u.username AS "销售用户名",
        po.pricing_total_amount AS "批价金额",
        po.currency AS "货币",
        po.status AS "状态",
        p.project_name AS "关联项目"
    FROM pricing_orders po
    LEFT JOIN users u ON po.created_by = u.id
    LEFT JOIN projects p ON po.project_id = p.id
    ORDER BY po.created_at DESC
    """

    pricing_df = pd.read_sql(text(pricing_query), engine)

    # 查询结算单数据
    print("查询结算单数据...")
    settlement_query = """
    SELECT
        so.order_number AS "结算单号",
        so.created_at AS "创建时间",
        u.real_name AS "负责销售",
        u.username AS "销售用户名",
        so.total_amount AS "结算金额",
        so.currency AS "货币",
        so.status AS "审批状态",
        so.settlement_status AS "结算状态",
        p.project_name AS "关联项目"
    FROM settlement_orders so
    LEFT JOIN users u ON so.created_by = u.id
    LEFT JOIN projects p ON so.project_id = p.id
    ORDER BY so.created_at DESC
    """

    settlement_df = pd.read_sql(text(settlement_query), engine)

    # 处理日期格式
    if not pricing_df.empty:
        pricing_df['创建时间'] = pd.to_datetime(pricing_df['创建时间']).dt.strftime('%Y-%m-%d %H:%M')
        # 合并销售名称
        pricing_df['负责销售'] = pricing_df.apply(
            lambda x: x['负责销售'] if pd.notna(x['负责销售']) else x['销售用户名'], axis=1
        )
        pricing_df = pricing_df.drop(columns=['销售用户名'])
        # 状态翻译
        status_map = {'draft': '草稿', 'pending': '审批中', 'approved': '已批准', 'rejected': '已拒绝'}
        pricing_df['状态'] = pricing_df['状态'].map(lambda x: status_map.get(x, x))

    if not settlement_df.empty:
        settlement_df['创建时间'] = pd.to_datetime(settlement_df['创建时间']).dt.strftime('%Y-%m-%d %H:%M')
        # 合并销售名称
        settlement_df['负责销售'] = settlement_df.apply(
            lambda x: x['负责销售'] if pd.notna(x['负责销售']) else x['销售用户名'], axis=1
        )
        settlement_df = settlement_df.drop(columns=['销售用户名'])
        # 状态翻译
        status_map = {'draft': '草稿', 'pending': '审批中', 'approved': '已批准', 'rejected': '已拒绝'}
        settlement_status_map = {'pending': '待结算', 'partially_settled': '部分结算', 'fully_settled': '已结算'}
        settlement_df['审批状态'] = settlement_df['审批状态'].map(lambda x: status_map.get(x, x))
        settlement_df['结算状态'] = settlement_df['结算状态'].map(lambda x: settlement_status_map.get(x, x))

    # 导出到Excel
    output_file = os.path.join(project_root, 'data', 'temp', f'sp8d_批价结算单_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

    # 确保目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"\n导出数据到: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        pricing_df.to_excel(writer, sheet_name='批价单', index=False)
        settlement_df.to_excel(writer, sheet_name='结算单', index=False)

    print("\n=== 导出完成 ===")
    print(f"批价单: {len(pricing_df)} 条记录")
    print(f"结算单: {len(settlement_df)} 条记录")

    # 打印预览
    print("\n=== 批价单预览 ===")
    if not pricing_df.empty:
        print(pricing_df.to_string(index=False))
    else:
        print("无数据")

    print("\n=== 结算单预览 ===")
    if not settlement_df.empty:
        print(settlement_df.to_string(index=False))
    else:
        print("无数据")

    return output_file

if __name__ == '__main__':
    export_data()
