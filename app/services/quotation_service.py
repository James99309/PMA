# -*- coding: utf-8 -*-
"""
Quotation Service — 报价单业务服务层

抽自 system_diagram.api_create_quotation_from_bom 的核心逻辑。
两个调用方共享:
  1. 系统图(views/system_diagram.py) — 通过 diagram_id 反查 project,网页 session 鉴权
  2. MCP server(routes/internal_api.py) — skill 直接传 project_id,internal token 鉴权
"""
from __future__ import annotations

import hashlib
import json as json_lib
import logging
from datetime import datetime
from typing import Optional

from app import db
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from config import Config

logger = logging.getLogger(__name__)


def create_quotation_from_bom(
    user,
    project: Project,
    items: list,
    *,
    customer_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    currency: Optional[str] = None,
    notes: str = '',
    inherit_customer_from_history: bool = True,
) -> Quotation:
    """从 BOM items 创建 Quotation + 一组 QuotationDetail。

    参数:
        user: 当前用户(owner_id)
        project: 已加载的 Project 对象(必传,不接受 None)
        items: BOM 列表,每项 dict 含 product_name/model/mn/desc/brand/unit/
               quantity/market_price/unit_price[/discount/total_price]
        customer_id: 可选,显式指定客户 id;不传时根据
                     inherit_customer_from_history 决定是否继承
        contact_id: 可选,联系人 id
        currency: 可选,默认 Config.DEFAULT_CURRENCY
        notes: 报价单备注
        inherit_customer_from_history: 不传 customer_id 时,是否从同项目最新
                                       quotation 继承 customer_id(默认 True,
                                       与原 system_diagram 行为一致)

    返回:
        已 commit 的 Quotation 对象(含 id, quotation_number, amount 等)

    异常:
        ValueError — items 为空 / 无效;Project 不存在
        其他异常会触发 db.session.rollback() 后再抛出
    """
    if not project:
        raise ValueError('project 不能为空')
    if not isinstance(items, list) or len(items) == 0:
        raise ValueError('报价单必须包含至少一个明细项')

    # 自动继承 customer_id(若未显式指定)
    if customer_id is None and inherit_customer_from_history:
        existing_q = (
            Quotation.query
            .filter_by(project_id=project.id)
            .order_by(Quotation.id.desc())
            .first()
        )
        if existing_q and existing_q.customer_id:
            customer_id = existing_q.customer_id

    quote_currency = currency or Config.DEFAULT_CURRENCY

    try:
        quotation = Quotation(
            project_id=project.id,
            customer_id=customer_id,
            contact_id=contact_id,
            amount=0,
            project_stage=project.current_stage or '',
            project_type=project.project_type or '',
            currency=quote_currency,
            owner_id=user.id,
            notes=notes or '',
        )
        db.session.add(quotation)

        total_amount = 0.0
        for item in items:
            if not isinstance(item, dict):
                continue
            product_name = (item.get('product_name') or '').strip()
            if not product_name:
                continue

            quantity = max(1, int(item.get('quantity', 1) or 1))
            market_price = float(item.get('market_price', 0) or 0)
            unit_price   = float(item.get('unit_price', 0) or 0)
            discount     = float(item.get('discount', 1.0) or 1.0)
            # 优先用传入的 total_price,否则按 unit * qty 算
            total_price  = float(item.get('total_price') or (unit_price * quantity))

            detail = QuotationDetail(
                product_name=product_name,
                product_model=item.get('product_model', ''),
                product_mn=item.get('product_mn') or item.get('mn', ''),
                product_desc=item.get('product_desc', ''),
                brand=item.get('brand', ''),
                unit=item.get('unit', ''),
                quantity=quantity,
                discount=discount,
                market_price=market_price,
                unit_price=unit_price,
                total_price=total_price,
                currency=quote_currency,
            )
            quotation.details.append(detail)
            total_amount += total_price

        quotation.amount = total_amount
        quotation.calculate_implant_total_amount()

        # 产品签名(用于幂等 / 重复检测)
        sig_data = [{
            'product_name': d.product_name,
            'product_model': d.product_model,
            'quantity': d.quantity,
            'unit_price': d.unit_price,
        } for d in quotation.details]
        quotation.product_signature = hashlib.md5(
            json_lib.dumps(sig_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        quotation.updated_at = datetime.now()

        db.session.commit()

        # 项目活跃度刷新(失败不影响主流程)
        try:
            from app.utils.activity_tracker import update_active_status
            update_active_status(project)
        except Exception as _e:
            logger.debug(f'活跃度刷新跳过: {_e}')

        logger.info(
            f'[quotation_service] 创建报价单 {quotation.quotation_number} '
            f'(project={project.id}, owner={user.id}, items={len(items)}, '
            f'amount={total_amount})'
        )
        return quotation

    except Exception as e:
        db.session.rollback()
        logger.exception(f'[quotation_service] 从 BOM 创建报价单失败: {e}')
        raise
