#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 qu202408-022 的客户关联问题"""
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

# 设置云端数据库配置 (SP8D Supabase)
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
os.environ['USE_SUPABASE'] = 'true'
os.environ['SUPABASE_DB_TYPE'] = 'sp8d'

from app import create_app, db
from app.models.quotation import Quotation
from app.models.customer import Company
from app.models.project import Project

app = create_app()

with app.app_context():
    # 查找报价单（支持大小写）
    quotation = Quotation.query.filter(
        db.func.lower(Quotation.quotation_number) == 'qu202408-022'
    ).first()

    if not quotation:
        print("未找到报价单 qu202408-022")
        # 列出所有类似的报价单号
        similar = Quotation.query.filter(
            Quotation.quotation_number.ilike('%202408%')
        ).all()
        print(f"\n类似的报价单号：")
        for q in similar:
            print(f"  - {q.quotation_number}")
    else:
        print(f"=== 报价单信息 ===")
        print(f"报价单号: {quotation.quotation_number}")
        print(f"报价单ID: {quotation.id}")
        print(f"customer_id: {quotation.customer_id}")
        print(f"project_id: {quotation.project_id}")

        # 查看关联的客户
        if quotation.customer_id:
            customer = Company.query.get(quotation.customer_id)
            if customer:
                print(f"\n=== 直接关联的客户 (customer_id={quotation.customer_id}) ===")
                print(f"客户名称: {customer.name}")
                print(f"客户ID: {customer.id}")
            else:
                print(f"\n警告: customer_id={quotation.customer_id} 对应的客户不存在！")
        else:
            print(f"\n报价单没有直接关联客户 (customer_id 为空)")

        # 查看关联的项目
        if quotation.project_id:
            project = Project.query.get(quotation.project_id)
            if project:
                print(f"\n=== 关联的项目 (project_id={quotation.project_id}) ===")
                print(f"项目名称: {project.name}")
                print(f"项目ID: {project.id}")
                print(f"项目的 customer_id: {project.customer_id}")

                # 查看项目关联的客户
                if project.customer_id:
                    project_customer = Company.query.get(project.customer_id)
                    if project_customer:
                        print(f"\n=== 项目关联的客户 (project.customer_id={project.customer_id}) ===")
                        print(f"客户名称: {project_customer.name}")
                        print(f"客户ID: {project_customer.id}")
                    else:
                        print(f"\n警告: 项目的 customer_id={project.customer_id} 对应的客户不存在！")

        # 对比两个客户
        print(f"\n=== 分析 ===")
        if quotation.customer_id and quotation.project_id:
            project = Project.query.get(quotation.project_id)
            if project and project.customer_id:
                if quotation.customer_id == project.customer_id:
                    print("✓ 报价单客户与项目客户一致")
                else:
                    print("✗ 报价单客户与项目客户不一致！")
                    print(f"  报价单客户ID: {quotation.customer_id}")
                    print(f"  项目客户ID: {project.customer_id}")

                    # 获取两个客户的详细信息
                    q_customer = Company.query.get(quotation.customer_id)
                    p_customer = Company.query.get(project.customer_id)
                    if q_customer:
                        print(f"  报价单客户名称: {q_customer.name}")
                    if p_customer:
                        print(f"  项目客户名称: {p_customer.name}")
