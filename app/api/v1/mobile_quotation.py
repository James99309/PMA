"""移动端报价单接口"""
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.quotation import Quotation, QuotationDetail
import logging

logger = logging.getLogger(__name__)


@api_v1_bp.route('/mobile/quotations/<int:quotation_id>', methods=['GET'])
@jwt_required()
def mobile_quotation_detail(quotation_id):
    """报价单详情（含明细、信头、extra_fields）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    quotation = Quotation.query.get(quotation_id)
    if not quotation:
        return api_response(success=False, code=404, message="报价单不存在")

    from app.views.quotation import can_view_quotation
    if not can_view_quotation(user, quotation):
        return api_response(success=False, code=403, message="无权查看此报价单")

    details = QuotationDetail.query\
        .filter_by(quotation_id=quotation_id)\
        .order_by(QuotationDetail.sort_order, QuotationDetail.id)\
        .all()

    owner = quotation.owner
    letterhead = getattr(owner, 'quotation_letterhead', None) or {}
    signature = getattr(owner, 'quotation_signature', None) or {}
    extra_fields = quotation.extra_fields or {}

    return api_response(success=True, data={
        'id': quotation.id,
        'quotation_number': quotation.quotation_number,
        'currency': quotation.currency or 'CNY',
        'amount': quotation.amount,
        'notes': quotation.notes,
        'created_at': quotation.created_at.strftime('%Y-%m-%d') if quotation.created_at else None,
        'customer': {
            'id': quotation.customer.id,
            'name': quotation.customer.company_name,
        } if quotation.customer else None,
        'contact': {
            'name': quotation.contact.name,
            'phone': getattr(quotation.contact, 'phone', '') or '',
        } if quotation.contact else None,
        'project': {
            'name': quotation.project.project_name,
        } if quotation.project else None,
        'extra_fields': extra_fields,
        'letterhead': letterhead,
        'signature': signature,
        'details': [
            {
                'row_type': d.row_type or 'product',
                'section_label': d.section_label or '',
                'product_mn': d.product_mn or '',
                'brand': d.brand or '',
                'product_name': d.product_name or '',
                'product_model': d.product_model or '',
                'product_desc': d.product_desc or '',
                'discount': d.discount,
                'market_price': d.market_price,
                'unit_price': d.unit_price,
                'quantity': d.quantity,
                'unit': d.unit or '',
                'total_price': d.total_price,
                'item_note': d.item_note or '',
            }
            for d in details
        ],
    })
