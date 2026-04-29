from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.customer import Company, Contact
from app.utils.access_control import get_viewable_data
import logging

logger = logging.getLogger(__name__)


def _company_summary(c):
    primary_contact = c.contacts[0] if c.contacts else None
    return {
        'id': c.id,
        'name': c.name,
        'industry': c.industry,
        'region': c.region,
        'primary_contact_name': primary_contact.name if primary_contact else '',
        'primary_contact_phone': primary_contact.phone if primary_contact else '',
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    }


def _contact_dict(ct):
    return {
        'id': ct.id,
        'name': ct.name,
        'title': ct.title,
        'phone': ct.phone,
        'email': ct.email,
        'department': ct.department,
        'company_id': ct.company_id,
        'company_name': ct.company.name if ct.company else '',
    }


@api_v1_bp.route('/mobile/customers', methods=['GET'])
@jwt_required()
def mobile_customer_list():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))

    query = get_viewable_data(Company, user, [Company.is_deleted == False])

    if search:
        query = query.filter(Company.name.ilike(f'%{search}%'))

    query = query.order_by(Company.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return api_response(success=True, data={
        'items': [_company_summary(c) for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages,
    })


@api_v1_bp.route('/mobile/customers/<int:company_id>', methods=['GET'])
@jwt_required()
def mobile_customer_detail(company_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return api_response(success=False, code=404, message="客户不存在")

    from app.utils.access_control import can_view_company
    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权访问此客户")

    contacts = Contact.query.filter_by(company_id=company_id).all()
    return api_response(success=True, data={
        'id': company.id,
        'name': company.name,
        'industry': company.industry,
        'region': company.region,
        'address': company.address,
        'website': company.website,
        'contacts': [_contact_dict(ct) for ct in contacts],
        'updated_at': company.updated_at.isoformat() if company.updated_at else None,
    })


@api_v1_bp.route('/mobile/contacts/search', methods=['GET'])
@jwt_required()
def mobile_contact_search():
    """按姓名或电话搜索联系人（用于拜访前快速查找）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    q = request.args.get('q', '').strip()
    if not q:
        return api_response(success=False, code=400, message="请输入搜索关键词")

    # 先获取用户可查看的公司 ID
    viewable_company_ids = [
        c.id for c in get_viewable_data(Company, user, [Company.is_deleted == False]).all()
    ]

    contacts = (
        Contact.query
        .filter(
            Contact.company_id.in_(viewable_company_ids),
            (Contact.name.ilike(f'%{q}%') | Contact.phone.ilike(f'%{q}%'))
        )
        .limit(20)
        .all()
    )

    return api_response(success=True, data={
        'items': [_contact_dict(ct) for ct in contacts],
        'total': len(contacts),
    })
