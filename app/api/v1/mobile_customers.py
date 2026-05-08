from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, timedelta
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.project_customer_association import ProjectCustomerAssociation
from app.utils.access_control import get_viewable_data, can_view_company
from app import db
import logging

logger = logging.getLogger(__name__)


# ─── 阶段 → tone 映射（与 Plan A customer-screens.jsx StageDot 对齐） ───
_STAGE_TONE = {
    'discover':   'discover',
    'embed':      'embed',
    'pre_tender': 'pre_tender',
    'tendering':  'bidding',
    'awarded':    'awarded',
    'quoted':     'quoted',
    'signed':     'won',
    'lost':       'lost',
    'paused':     'paused',
}

_STAGE_LABEL = {
    'discover':   '发现',
    'embed':      '嵌入',
    'pre_tender': '预招标',
    'tendering':  '招标中',
    'awarded':    '授权',
    'quoted':     '已报价',
    'signed':     '签约',
    'lost':       '丢单',
    'paused':     '暂停',
}

# 客户活跃度状态英文 → 中文（与 app/utils/activity_tracker.ACTIVITY_STATUS 同步）
_STATUS_LABEL = {
    'highly_active': '高度活跃',
    'active':        '活跃',
    'normal':        '正常',
    'to_follow':     '待跟进',
    'dormant':       '休眠',
    'churned':       '流失',
    'frozen':        '已冻结',
}


def _source_label(key):
    """source 字段映射到中文（复用 PMA 主系统字典）"""
    if not key:
        return ''
    try:
        from app.utils.dictionary_helpers import report_source_label
        return report_source_label(key)
    except Exception:
        return key


def _relative_date(d):
    """返回 '今天' / '昨天' / '本周' / '上周' / '本月' / '上月' 等相对描述"""
    if not d:
        return ''
    today = date.today()
    diff = (today - d).days
    if diff <= 0:
        return '今天'
    if diff == 1:
        return '昨天'
    if diff <= 7:
        return '本周'
    if diff <= 14:
        return '上周'
    if diff <= 31:
        return '本月'
    if diff <= 60:
        return '上月'
    return d.isoformat()


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
        'business_card_image_url': ct.business_card_image_url,
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
    industry = request.args.get('industry', '').strip()
    company_type = request.args.get('company_type', '').strip()
    status_f = request.args.get('status', '').strip()
    region = request.args.get('region', '').strip()
    # tier / value_min / value_max / open_bucket: 模型字段缺失或需聚合，暂未实现过滤
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))

    query = get_viewable_data(Company, user, [Company.is_deleted == False])
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    if industry:
        query = query.filter(Company.industry == industry)
    if company_type:
        query = query.filter(Company.company_type == company_type)
    if status_f:
        query = query.filter(Company.status == status_f)
    if region:
        # 命中 city 或 region 任一（LIKE 兼容 "上海" vs "上海市"）
        like = f'%{region}%'
        query = query.filter((Company.city.like(like)) | (Company.region.like(like)))

    query = query.order_by(Company.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 累计客户价值需聚合：批量预取每家公司的项目（已签求和 + 进行中计数）
    company_ids = [c.id for c in pagination.items]
    proj_stats = {}  # company_id -> {value: float, open: int}
    if company_ids:
        rows = (
            db.session.query(
                ProjectCustomerAssociation.company_id,
                Project.current_stage,
                Project.quotation_customer,
            )
            .join(Project, Project.id == ProjectCustomerAssociation.project_id)
            .filter(ProjectCustomerAssociation.company_id.in_(company_ids))
            .filter(Project.is_deleted == False)
            .all()
        )
        for cid, stage, amt in rows:
            stat = proj_stats.setdefault(cid, {'value': 0.0, 'open': 0})
            # 累计价值：所有非失败/搁置项目都计入（含已签 + 在跟）
            if stage not in ('lost', 'paused'):
                stat['value'] += (amt or 0)
            if stage not in ('signed', 'lost', 'paused'):
                stat['open'] += 1

    items = []
    for c in pagination.items:
        primary = next((ct for ct in c.contacts if ct.is_primary), None) or (c.contacts[0] if c.contacts else None)
        stat = proj_stats.get(c.id, {'value': 0.0, 'open': 0})
        items.append({
            **_company_summary(c),
            'primary_contact_name': primary.name if primary else '',
            'primary_contact_phone': primary.phone if primary else '',
            'status':       _STATUS_LABEL.get(c.status, c.status or '正常'),
            'value':        round(stat['value'] / 10000, 2),
            'open_count':   stat['open'],
            'last_touch':   _relative_date(c.updated_at.date() if c.updated_at else None),
            'company_type': c.company_type,
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

    # 联系人（主联系人优先）
    contacts = (
        Contact.query
        .filter_by(company_id=company_id)
        .order_by(Contact.is_primary.desc(), Contact.created_at.asc())
        .all()
    )

    # 跟进记录（最近20条）
    from app.models.action import Action
    actions = (
        Action.query
        .filter_by(company_id=company_id)
        .order_by(Action.date.desc(), Action.created_at.desc())
        .limit(20).all()
    )

    # 名下项目（通过 ProjectCustomerAssociation 关联）
    proj_query = (
        db.session.query(Project)
        .join(ProjectCustomerAssociation, ProjectCustomerAssociation.project_id == Project.id)
        .filter(ProjectCustomerAssociation.company_id == company_id)
        .filter(Project.is_deleted == False)
        .order_by(Project.updated_at.desc())
    )
    all_projects = proj_query.all()

    open_count = sum(1 for p in all_projects if p.current_stage not in ('signed', 'lost', 'paused'))
    won_count  = sum(1 for p in all_projects if p.current_stage == 'signed')
    lost_count = sum(1 for p in all_projects if p.current_stage == 'lost')
    total_count = len(all_projects)

    # 累计客户价值 = 所有"在飞"项目 quotation_customer 求和（万元）
    # 不含 lost/paused —— 但已签约 + 任何在跟项目都计入（反映客户业务总量+潜在价值）
    value_raw = sum(
        (p.quotation_customer or 0)
        for p in all_projects
        if p.current_stage not in ('lost', 'paused')
    )
    value_wan = round(value_raw / 10000, 2)

    projects_payload = []
    for p in all_projects[:10]:
        amt_raw = p.quotation_customer or 0
        projects_payload.append({
            'id': p.id,
            'name': p.project_name,
            'amount': round(amt_raw / 10000, 2) if amt_raw else 0,
            'stage': p.current_stage or 'discover',
            'stage_label': _STAGE_LABEL.get(p.current_stage, p.current_stage or '—'),
            'tone': _STAGE_TONE.get(p.current_stage, 'discover'),
        })

    last_action_date = actions[0].date if actions else None

    # tier / company_size / established_year 等字段 Company 模型未实现，已从设计前端隐藏
    return api_response(success=True, data={
        **_company_summary(company),
        'address':       company.address,
        'website':       getattr(company, 'website', None),
        'company_type':  company.company_type,
        'source':        _source_label(company.source) if company.source else '',
        'status':        _STATUS_LABEL.get(company.status, company.status or '正常'),
        'owner_name':    company.owner.real_name or company.owner.username if company.owner else '',
        'last_touch':    _relative_date(last_action_date),
        'value':         value_wan,
        'open_count':    open_count,
        'won_count':     won_count,
        'lost_count':    lost_count,
        'total_count':   total_count,
        'projects':      projects_payload,
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
            # 名片扫描留底 (可选, 普通新建联系人时不传)
            business_card_image_url=data.get('business_card_image_url') or None,
            ocr_json_data=data.get('ocr_json_data') or None,
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


def _search_address_amap(q):
    import requests as req
    from flask import current_app
    api_key = current_app.config.get('AMAP_SERVER_KEY')
    resp = req.get('https://restapi.amap.com/v3/assistant/inputtips', params={
        'key': api_key, 'keywords': q, 'datatype': 'all', 'output': 'json'
    }, timeout=8)
    data = resp.json()
    if data.get('status') != '1':
        return []
    results = []
    for tip in data.get('tips', [])[:8]:
        name = tip.get('name', '')
        if not name:
            continue
        loc = tip.get('location', '')
        lat = lng = None
        if loc and ',' in str(loc):
            try:
                parts = str(loc).split(',')
                lng, lat = float(parts[0]), float(parts[1])
            except Exception:
                pass
        address = tip.get('address', '')
        address = address if isinstance(address, str) else ''
        district = tip.get('district', '')
        results.append({
            'name': name,
            'district': district,
            'address': address,
            'latitude': lat,
            'longitude': lng,
        })
    return results


def _search_address_google(q):
    import requests as req
    from flask import current_app
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    resp = req.get('https://maps.googleapis.com/maps/api/place/autocomplete/json', params={
        'key': api_key, 'input': q, 'language': 'zh',
    }, timeout=8)
    data = resp.json()
    if data.get('status') not in ('OK', 'ZERO_RESULTS'):
        return []
    results = []
    for pred in data.get('predictions', [])[:8]:
        sf = pred.get('structured_formatting', {})
        name = sf.get('main_text', pred.get('description', ''))
        secondary = sf.get('secondary_text', '')
        results.append({
            'name': name,
            'district': secondary,
            'address': pred.get('description', ''),
            'place_id': pred.get('place_id', ''),
            'latitude': None,
            'longitude': None,
        })
    return results


@api_v1_bp.route('/mobile/address/search', methods=['GET'])
@jwt_required()
def mobile_address_search():
    """地址联想搜索"""
    from flask import current_app
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return api_response(success=True, data={'suggestions': []})
    map_provider = current_app.config.get('MAP_PROVIDER', 'google')
    try:
        if map_provider == 'amap':
            suggestions = _search_address_amap(q)
        else:
            suggestions = _search_address_google(q)
        return api_response(success=True, data={'suggestions': suggestions})
    except Exception as e:
        logger.error(f"address search error: {e}")
        return api_response(success=True, data={'suggestions': []})


@api_v1_bp.route('/mobile/address/detail', methods=['GET'])
@jwt_required()
def mobile_address_detail():
    """Google Place 详情（获取 lat/lng 和结构化地址）"""
    import requests as req
    from flask import current_app
    place_id = request.args.get('place_id', '').strip()
    if not place_id:
        return api_response(success=False, code=400, message='缺少 place_id')
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    try:
        resp = req.get('https://maps.googleapis.com/maps/api/place/details/json', params={
            'key': api_key, 'place_id': place_id,
            'fields': 'geometry,address_components,formatted_address,name',
            'language': 'zh',
        }, timeout=8)
        data = resp.json()
        if data.get('status') != 'OK':
            return api_response(success=False, code=500, message='获取地址详情失败')
        result = data['result']
        lat = result['geometry']['location']['lat']
        lng = result['geometry']['location']['lng']
        from app.views.customer import _reverse_geocode_google
        addr_data = _reverse_geocode_google(lat, lng)
        addr_data['latitude'] = lat
        addr_data['longitude'] = lng
        return api_response(success=True, data=addr_data)
    except Exception as e:
        logger.error(f"address detail error: {e}")
        return api_response(success=False, code=500, message=str(e))


@api_v1_bp.route('/mobile/check-name/customer', methods=['POST'])
@jwt_required()
def mobile_check_customer_name():
    """客户名称实时查重"""
    import difflib
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return api_response(success=True, data={'similar': []})

    try:
        companies = Company.query.filter(
            Company.is_deleted == False
        ).with_entities(Company.id, Company.company_name).all()

        similar = []
        for c in companies:
            cn = c.company_name or ''
            if not cn:
                continue
            ratio = difflib.SequenceMatcher(None, name, cn).ratio()
            if ratio >= 0.6 or name in cn or cn in name:
                similar.append({
                    'id': c.id,
                    'name': cn,
                    'score': round(ratio * 100),
                })
        similar.sort(key=lambda x: x['score'], reverse=True)
        return api_response(success=True, data={'similar': similar[:5]})
    except Exception as e:
        logger.error(f"mobile check customer name error: {e}")
        return api_response(success=False, code=500, message=str(e))


@api_v1_bp.route('/mobile/geocode/reverse', methods=['POST'])
@jwt_required()
def mobile_reverse_geocode():
    """反向地理编码（JWT版）"""
    import requests as req
    from flask import current_app
    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    if lat is None or lng is None:
        return api_response(success=False, code=400, message='缺少经纬度参数')

    map_provider = current_app.config.get('MAP_PROVIDER', 'google')
    try:
        if map_provider == 'amap':
            from app.views.customer import _reverse_geocode_amap
            result = _reverse_geocode_amap(lat, lng, lang='zh')
        else:
            from app.views.customer import _reverse_geocode_google
            result = _reverse_geocode_google(lat, lng, lang='zh')
        return api_response(success=True, data=result)
    except Exception as e:
        logger.error(f"mobile reverse geocode error: {e}")
        return api_response(success=False, code=500, message=f'地理编码失败: {str(e)}')


@api_v1_bp.route('/mobile/customers', methods=['POST'])
@jwt_required()
def mobile_create_customer():
    """新建客户"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return api_response(success=False, code=400, message='公司名称不能为空')

    try:
        company = Company(
            company_name=name,
            company_type=data.get('company_type') or None,
            industry=data.get('industry') or None,
            country=data.get('country') or None,
            region=data.get('region') or None,
            city=data.get('city') or None,
            address=data.get('address') or None,
            latitude=data.get('latitude') or None,
            longitude=data.get('longitude') or None,
            notes=data.get('notes') or None,
            owner_id=user_id,
        )
        db.session.add(company)
        db.session.commit()
        return api_response(success=True, message='客户已创建', data={'id': company.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile create customer error: {e}")
        return api_response(success=False, code=500, message='创建失败，请重试')


# ─── 编辑客户（PUT）──────────────────────────────────────────────
@api_v1_bp.route('/mobile/customers/<int:company_id>', methods=['PUT'])
@jwt_required()
def mobile_customer_update(company_id):
    """更新客户信息（仅创建人或管理员可操作）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return api_response(success=False, code=404, message="客户不存在")

    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权修改此客户")

    data = request.get_json(silent=True) or {}

    # 仅允许更新这些字段，其他静默忽略
    allowed = ['company_name', 'company_type', 'industry', 'country', 'region',
               'city', 'address', 'status', 'source', 'notes']
    try:
        for k in allowed:
            if k in data:
                setattr(company, k, data[k] or None)
        db.session.commit()
        return api_response(success=True, message='已保存', data={'id': company.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile update customer error: {e}")
        return api_response(success=False, code=500, message='保存失败')


# ─── 归档客户（软删除）────────────────────────────────────────────
@api_v1_bp.route('/mobile/customers/<int:company_id>', methods=['DELETE'])
@jwt_required()
def mobile_customer_archive(company_id):
    """归档客户（is_deleted=True）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return api_response(success=False, code=404, message="客户不存在")

    if not can_view_company(user, company):
        return api_response(success=False, code=403, message="无权归档此客户")

    try:
        company.is_deleted = True
        db.session.commit()
        return api_response(success=True, message='已归档')
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile archive customer error: {e}")
        return api_response(success=False, code=500, message='归档失败')


# ─── 拍名片自动录入: 上传图 + Claude vision OCR ─────────────────
@api_v1_bp.route('/mobile/customers/scan-business-card', methods=['POST'])
@jwt_required()
def mobile_scan_business_card():
    """multipart 上传裁剪后的名片图 → 存 NAS + 调 Claude vision OCR
    返回 { file_url, fields: {name, company, ...}, ocr_json: 原始字符串 }
    """
    import json as _json
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    f = request.files.get('file')
    if not f:
        return api_response(success=False, code=400, message='未提供图片')

    # 读字节 (供 OCR 用) + 复用 chat 的存储管道存到 NAS
    blob = f.read()
    try:
        f.stream.seek(0)
    except Exception:
        pass
    if not blob:
        return api_response(success=False, code=400, message='图片为空')

    # 1) 存到 NAS 的 chat 桶 (复用现有 attachment 通道)
    file_url = None
    try:
        from app.utils.smart_storage_manager import get_smart_storage
        from urllib.parse import quote
        storage = get_smart_storage()
        result = storage.upload_file(
            object_id=user_id,
            file=f.stream,
            filename=f.filename or 'business_card.jpg',
            file_type='image',
            bucket_type='chat',
            business_type='business_card',
        )
        if result and result.get('url'):
            nas_path = result.get('nas_path') or result.get('storage_path') or ''
            rel_path = nas_path.split('/', 1)[1] if '/' in nas_path else nas_path
            file_url = f'/api/v1/mobile/chat/file?path={quote(rel_path)}'
    except Exception as e:
        logger.warning(f'business card upload to NAS failed: {e}')
        # 即使存失败也继续 OCR (用户可决定是否保存)

    # 2) Claude vision OCR
    from app.services.business_card_ocr import extract_card
    ocr_result = extract_card(blob)
    if not ocr_result.get('success'):
        return api_response(success=False, code=500,
                            message=ocr_result.get('message', '识别失败'),
                            data={'file_url': file_url})

    fields = ocr_result['data']
    ocr_json_str = _json.dumps(fields, ensure_ascii=False)

    return api_response(success=True, data={
        'file_url': file_url,
        'fields': fields,
        'ocr_json': ocr_json_str,
    })


# ─── 联系人重复检测: 按 phone/email 精确命中 ────────────────────
@api_v1_bp.route('/mobile/contacts/check-duplicate', methods=['POST'])
@jwt_required()
def mobile_contact_check_duplicate():
    """检查 phone / email 是否已存在于其他联系人
    返回 { duplicates: [{contact_id, name, phone, email, company_id, company_name}, ...] }
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip().lower()
    if not phone and not email:
        return api_response(success=True, data={'duplicates': []})

    q = Contact.query
    from sqlalchemy import or_, func
    clauses = []
    if phone:
        clauses.append(Contact.phone == phone)
    if email:
        clauses.append(func.lower(Contact.email) == email)
    if not clauses:
        return api_response(success=True, data={'duplicates': []})
    matches = q.filter(or_(*clauses)).limit(10).all()

    # 仅返回当前用户能看到的客户名下的联系人 (权限过滤)
    out = []
    for c in matches:
        company = Company.query.get(c.company_id)
        if not company or company.is_deleted:
            continue
        if not can_view_company(user, company):
            continue
        out.append({
            'contact_id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email,
            'company_id': c.company_id,
            'company_name': company.company_name,
        })

    return api_response(success=True, data={'duplicates': out})
