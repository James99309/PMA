#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询报价单的确认徽章状态"""
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

from app import create_app, db
from app.models.quotation import Quotation
from app.models.user import User

app = create_app()

with app.app_context():
    # 查询 QU202510-004 报价单
    quotation = Quotation.query.filter_by(quotation_number='QU202510-004').first()

    if not quotation:
        print("❌ 未找到报价单 QU202510-004")
        sys.exit(1)

    print(f"\n📋 报价单信息: {quotation.quotation_number}")
    print(f"ID: {quotation.id}")
    print(f"项目: {quotation.project.project_name if quotation.project else '无'}")
    print(f"金额: {quotation.amount}")
    print(f"\n🎯 确认徽章状态:")
    print(f"  confirmation_badge_status: {quotation.confirmation_badge_status!r}")
    print(f"  confirmation_badge_color: {quotation.confirmation_badge_color!r}")
    print(f"  confirmed_by: {quotation.confirmed_by}")

    if quotation.confirmed_by:
        confirmer = User.query.get(quotation.confirmed_by)
        print(f"  确认人: {confirmer.real_name if confirmer else '未知'} (ID: {quotation.confirmed_by})")
    else:
        print(f"  确认人: 无")

    print(f"  confirmed_at: {quotation.confirmed_at}")
    print(f"  product_signature: {quotation.product_signature}")

    print(f"\n📊 产品明细数量: {len(quotation.details)}")

    # 检查是否应该显示徽章
    should_show_badge = quotation.confirmation_badge_status == 'confirmed'
    print(f"\n💡 是否应该显示徽章: {should_show_badge}")

    if not should_show_badge and quotation.confirmation_badge_status:
        print(f"⚠️  当前状态为 '{quotation.confirmation_badge_status}'，需要改为 'confirmed' 才能显示徽章")
