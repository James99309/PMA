from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.customer import Company, Contact
from app.utils.access_control import get_viewable_data, can_view_company
from app import db
import logging

logger = logging.getLogger(__name__)


def _contact_dict(ct):
    return {
        'id': ct.id,
        'name': ct.name,
        'position': ct.position,   # 职位字段名是 position，不是 title
        'phone': ct.phone,
        'email': ct.email,
        'department': ct.department,
        'is_primary': ct.is_primary,
        'company_id': ct.company_id,
    }


def _company_summary(c):
    return {
        'id': c.id,
        'name': c.company_name,
        'industry': c.industry,
        'region': c.region,
        'city': c.city,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
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
        query = query.filter(Company.company_name.ilike(f'%{search}%'))

    query = query.order_by(Company.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for c in pagination.items:
        primary = c.contacts[0] if c.contacts else None
        items.append({
            **_company_summary(c),
            'primary_contact_name': primary.name if primary else '',
            'primary_contact_phone': primary.phone if primary else '',
        })

    return api_response(success=True, data={
        'items': items,
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

    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权访问此客户")

    # 联系人
    contacts = Contact.query.filter_by(company_id=company_id).all()

    # 跟进记录（最近20条）
    from app.models.action import Action
    actions = (
        Action.query
        .filter_by(company_id=company_id)
        .order_by(Action.date.desc(), Action.created_at.desc())
        .limit(20).all()
    )

    return api_response(success=True, data={
        **_company_summary(company),
        'address': company.address,
        'website': getattr(company, 'website', None),
        'contacts': [_contact_dict(ct) for ct in contacts],
        'actions': [
            {
                'id': a.id,
                'date': a.date.isoformat() if a.date else None,
                'communication': a.communication,
                'owner_name': a.owner.real_name or a.owner.username if a.owner else '',
            }
            for a in actions
        ],
    })


@api_v1_bp.route('/mobile/customers/<int:company_id>/notes', methods=['POST'])
@jwt_required()
def mobile_customer_add_note(company_id):
    """添加客户跟进记录"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return api_response(success=False, code=404, message="客户不存在")

    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权访问此客户")

    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return api_response(success=False, code=400, message="跟进内容不能为空")

    try:
        from datetime import date
        from app.models.action import Action
        action = Action(
            date=date.today(),
            company_id=company_id,
            communication=content,
            owner_id=user_id,
            is_shared=True,
        )
        db.session.add(action)
        db.session.commit()
        return api_response(success=True, message="跟进记录已添加")
    except Exception as e:
        db.session.rollback()
        logger.error(f"customer add note error: {e}")
        return api_response(success=False, code=500, message="添加失败，请重试")


@api_v1_bp.route('/mobile/customers/<int:company_id>/contacts', methods=['POST'])
@jwt_required()
def mobile_customer_add_contact(company_id):
    """新增联系人"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return api_response(success=False, code=404, message="客户不存在")

    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权访问此客户")

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return api_response(success=False, code=400, message="联系人姓名不能为空")

    try:
        contact = Contact(
            name=name,
            position=data.get('position', '').strip() or None,
            phone=data.get('phone', '').strip() or None,
            email=data.get('email', '').strip() or None,
            department=data.get('department', '').strip() or None,
            company_id=company_id,
            owner_id=user_id,
        )
        db.session.add(contact)
        db.session.commit()
        return api_response(success=True, message="联系人已添加", data=_contact_dict(contact))
    except Exception as e:
        db.session.rollback()
        logger.error(f"add contact error: {e}")
        return api_response(success=False, code=500, message="添加失败，请重试")


@api_v1_bp.route('/mobile/contacts/search', methods=['GET'])
@jwt_required()
def mobile_contact_search():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    q = request.args.get('q', '').strip()
    if not q:
        return api_response(success=False, code=400, message="请输入搜索关键词")

    viewable_ids = [
        c.id for c in get_viewable_data(Company, user, [Company.is_deleted == False]).all()
    ]
    contacts = (
        Contact.query
        .filter(
            Contact.company_id.in_(viewable_ids),
            (Contact.name.ilike(f'%{q}%') | Contact.phone.ilike(f'%{q}%'))
        )
        .limit(20).all()
    )
    return api_response(success=True, data={
        'items': [_contact_dict(ct) for ct in contacts],
        'total': len(contacts),
    })
