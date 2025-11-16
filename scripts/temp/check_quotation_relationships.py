#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 QU202511-001 的父子关系"""
import sys, os

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
from app import create_app, db
from app.models.quotation import Quotation, QuotationDetail

app = create_app()
with app.app_context():
    # 查找 QU202511-001 报价单
    quotation = Quotation.query.filter_by(quotation_number='QU202511-001').first()
    if quotation:
        print(f'报价单ID: {quotation.id}')
        print(f'报价单编号: {quotation.quotation_number}')
        print(f'明细数量: {len(quotation.details)}')
        print()

        # 查询明细
        details = QuotationDetail.query.filter_by(quotation_id=quotation.id).order_by(QuotationDetail.id).all()
        print(f'{"ID":<8} {"产品名称":<30} {"is_accessory":<15} {"parent_item_id":<20} {"config_type":<25}')
        print('-' * 120)
        for d in details:
            print(f'{d.id:<8} {d.product_name:<30} {str(d.is_accessory):<15} {str(d.parent_item_id):<20} {str(d.config_type or ""):<25}')
    else:
        print('未找到报价单 QU202511-001')
