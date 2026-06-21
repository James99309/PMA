from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, timedelta
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, get_request_lang as _lang
from app.models.user import User
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.project_customer_association import ProjectCustomerAssociation
from app.utils.access_control import get_viewable_data, can_view_company
from app.utils.dictionary_helpers import format_money
from app.services.multi_currency_aggregation import MultiCurrencyAggregationService
from config import Config
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

# 客户活跃度状态 zh/en（与 app/utils/activity_tracker.ACTIVITY_STATUS 同步）
_STATUS_LABEL = {
    'highly_active': {'zh': '高度活跃', 'en': 'Highly active'},
    'active':        {'zh': '活跃',     'en': 'Active'},
    'normal':        {'zh': '正常',     'en': 'Normal'},
    'to_follow':     {'zh': '待跟进',   'en': 'To follow up'},
    'dormant':       {'zh': '休眠',     'en': 'Dormant'},
    'churned':       {'zh': '流失',     'en': 'Churned'},
    'frozen':        {'zh': '已冻结',   'en': 'Frozen'},
}
# 历史数据 status 有的存英文 key 有的存中文 → 加中文别名, 两者都能映射
_STATUS_LABEL.update({
    v['zh']: v for v in list(_STATUS_LABEL.values())
})

def _status_label(key):
    """status 可能是英文 key 或中文(历史数据), 都按 _lang 归一; 未知原样。"""
    m = _STATUS_LABEL.get(key)
    if not m:
        return key or ('正常' if _lang() == 'zh' else 'Normal')
    return m.get(_lang(), m['zh'])


def _source_label(key):
    """source 字段按请求语言映射 label（复用 PMA 主系统字典, zh/en）"""
    if not key:
        return ''
    try:
        from app.utils.dictionary_helpers import report_source_label
        return report_source_label(key, _lang())
    except Exception:
        return key


_REL_DATE = {
    'today':     {'zh': '今天', 'en': 'Today'},
    'yesterday': {'zh': '昨天', 'en': 'Yesterday'},
    'this_week': {'zh': '本周', 'en': 'This week'},
    'last_week': {'zh': '上周', 'en': 'Last week'},
    'this_month':{'zh': '本月', 'en': 'This month'},
    'last_month':{'zh': '上月', 'en': 'Last month'},
}

def _relative_date(d):
    """相对日期描述, 按 Accept-Language 出 zh/en; 超 60 天回 ISO 日期。"""
    if not d:
        return ''
    diff = (date.today() - d).days
    if diff <= 0:
        key = 'today'
    elif diff == 1:
        key = 'yesterday'
    elif diff <= 7:
        key = 'this_week'
    elif diff <= 14:
        key = 'last_week'
    elif diff <= 31:
        key = 'this_month'
    elif diff <= 60:
        key = 'last_month'
    else:
        return d.isoformat()
    return _REL_DATE[key].get(_lang(), _REL_DATE[key]['zh'])


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
    # 多选: 兼容 axios 带/不带方括号两种 array 序列化格式
    owner_names = request.args.getlist('owner_names') + request.args.getlist('owner_names[]')
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
    if owner_names:
        # 与 mobile_projects 同模式: 用 real_name 或 username 匹配, 兼容显示名
        query = query.join(User, User.id == Company.owner_id) \
                     .filter(User.real_name.in_(owner_names) | User.username.in_(owner_names))

    query = query.order_by(Company.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 累计客户价值需聚合：批量预取每家公司的项目（已签求和 + 进行中计数）
    company_ids = [c.id for c in pagination.items]
    proj_stats = {}  # company_id -> {value: float, open: int}
    if company_ids:
        base_cur = Config.DEFAULT_CURRENCY
        rows = (
            db.session.query(
                ProjectCustomerAssociation.company_id,
                Project.current_stage,
                Project.quotation_customer,
                Project.quotation_currency,
            )
            .join(Project, Project.id == ProjectCustomerAssociation.project_id)
            .filter(ProjectCustomerAssociation.company_id.in_(company_ids))
            .filter(Project.is_deleted == False)
            .all()
        )
        for cid, stage, amt, curr in rows:
            stat = proj_stats.setdefault(cid, {'value': 0.0, 'open': 0})
            # 累计价值：所有非失败/搁置项目都计入（含已签 + 在跟）
            # 跨币种用现成汇率换算到本实例默认币种(与 web 项目列表 sum_converted 同口径)
            if stage not in ('lost', 'paused'):
                stat['value'] += MultiCurrencyAggregationService.convert_single(
                    amt or 0, curr or base_cur, base_cur)
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
            'status':       _status_label(c.status),
            'value':        round(stat['value'] / 10000, 2),  # legacy 万(排序/兼容)
            'value_display': format_money(stat['value'], Config.DEFAULT_CURRENCY) if stat['value'] else '',
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


@api_v1_bp.route('/mobile/customers/owners', methods=['GET'])
@jwt_required()
def mobile_customer_owners():
    """返回当前用户可见客户的 distinct owner 列表(供筛选下拉用)。
    复用 web 端 _get_customer_owner_options, 与 web 端筛选数据口径一致。"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        from app.views.customer import _get_customer_owner_options
        return api_response(success=True, data=_get_customer_owner_options(user))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"mobile_customer_owners error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


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

    # 累计客户价值 = 所有"在飞"项目 quotation_customer 求和
    # 不含 lost/paused —— 但已签约 + 任何在跟项目都计入（反映客户业务总量+潜在价值）
    # 跨币种用现成汇率换算到本实例默认币种(与 web 项目列表 sum_converted 同口径)
    base_cur = Config.DEFAULT_CURRENCY
    value_raw = sum(
        MultiCurrencyAggregationService.convert_single(
            p.quotation_customer or 0,
            getattr(p, 'quotation_currency', base_cur) or base_cur,
            base_cur)
        for p in all_projects
        if p.current_stage not in ('lost', 'paused')
    )
    value_wan = round(value_raw / 10000, 2)
    value_display = format_money(value_raw, base_cur) if value_raw else ''

    projects_payload = []
    for p in all_projects[:10]:
        amt_raw = p.quotation_customer or 0
        p_cur = getattr(p, 'quotation_currency', base_cur) or base_cur
        projects_payload.append({
            'id': p.id,
            'name': p.project_name,
            'amount': round(amt_raw / 10000, 2) if amt_raw else 0,  # legacy 万
            'amount_display': format_money(amt_raw, p_cur) if amt_raw else '',
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
        'status':        _status_label(company.status),
        'owner_name':    company.owner.real_name or company.owner.username if company.owner else '',
        'last_touch':    _relative_date(last_action_date),
        'value':         value_wan,  # legacy 万(兼容)
        'value_display': value_display,
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
    """客户名称实时查重 — 名片扫描公司级 dup UI 用. 返回 score 及富预览
    字段: value_wan / open_count / contact_count, 用于设计稿中预览卡。
    """
    import difflib
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return api_response(success=True, data={'similar': []})

    try:
        companies = Company.query.filter(
            Company.is_deleted == False
        ).with_entities(Company.id, Company.company_name).all()

        candidates = []
        for c in companies:
            cn = c.company_name or ''
            if not cn:
                continue
            ratio = difflib.SequenceMatcher(None, name, cn).ratio()
            if ratio >= 0.6 or name in cn or cn in name:
                candidates.append((c.id, cn, ratio))
        candidates.sort(key=lambda x: x[2], reverse=True)
        candidates = candidates[:5]

        # 给前 5 个 match 带上统计 (累计金额/进行中/联系人数), 单独查询
        similar = []
        for cid, cn, ratio in candidates:
            # 项目统计 (跟 mobile_customer_detail 同口径)
            projs = (db.session.query(Project)
                     .join(ProjectCustomerAssociation,
                           ProjectCustomerAssociation.project_id == Project.id)
                     .filter(ProjectCustomerAssociation.company_id == cid)
                     .filter(Project.is_deleted == False)
                     .all())
            open_count = sum(1 for p in projs
                             if p.current_stage not in ('signed', 'lost', 'paused'))
            value_raw = sum((p.quotation_customer or 0) for p in projs
                            if p.current_stage not in ('lost', 'paused'))
            value_wan = round(value_raw / 10000, 2)
            contact_count = Contact.query.filter_by(company_id=cid).count()
            similar.append({
                'id': cid,
                'name': cn,
                'score': round(ratio * 100),
                'value_wan': value_wan,
                'open_count': open_count,
                'contact_count': contact_count,
            })
        return api_response(success=True, data={'similar': similar})
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
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    from app.services.business_card_ocr import extract_card
    from app.api.v1.utils import handle_image_ocr_upload
    success, payload, code, message = handle_image_ocr_upload(
        request.files.get('file'),
        owner_id=user_id,
        business_type='business_card',
        ocr_fn=extract_card,
        default_filename='business_card.jpg',
    )
    return api_response(success=success, code=code, message=message, data=payload)


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
            'position': c.position,
            'department': c.department,
            'phone': c.phone,
            'email': c.email,
            'company_id': c.company_id,
            'company_name': company.company_name,
            'has_business_card': bool(c.business_card_image_url),
        })

    return api_response(success=True, data={'duplicates': out})


# ─── 合并扫描结果到现有联系人 (空值才填, 总是更新名片图) ────────
@api_v1_bp.route('/mobile/contacts/<int:contact_id>/merge-from-card', methods=['POST'])
@jwt_required()
def mobile_contact_merge_from_card(contact_id):
    """把刚扫描到的字段合并进已有联系人。
    策略: 空字段才填, 不覆盖已有非空; business_card_image_url 和
    ocr_json_data 总是用最新的覆盖 (审计/留底)。
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    contact = Contact.query.get(contact_id)
    if not contact:
        return api_response(success=False, code=404, message='联系人不存在')

    company = Company.query.get(contact.company_id)
    if not company or company.is_deleted or not can_view_company(user, company):
        return api_response(success=False, code=403, message='无权操作此联系人')

    data = request.get_json() or {}

    def _fill_if_empty(field, val):
        v = (val or '').strip() if isinstance(val, str) else val
        if v and not ((getattr(contact, field) or '').strip() if isinstance(getattr(contact, field), str) else getattr(contact, field)):
            setattr(contact, field, v)

    try:
        _fill_if_empty('position',   data.get('position'))
        _fill_if_empty('department', data.get('department'))
        _fill_if_empty('phone',      data.get('phone'))
        _fill_if_empty('email',      data.get('email'))
        # 名片图 + OCR JSON 总是覆盖 (留最新一份)
        if data.get('business_card_image_url'):
            contact.business_card_image_url = data['business_card_image_url']
        if data.get('ocr_json_data'):
            contact.ocr_json_data = data['ocr_json_data']
        db.session.commit()
        return api_response(success=True, message='已合并到该联系人',
                            data={'contact': _contact_dict(contact),
                                  'company_id': contact.company_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f'merge contact from card error: {e}')
        return api_response(success=False, code=500, message='合并失败')


# ─── 单个联系人详情 ─────────────────────────────────────────────
@api_v1_bp.route('/mobile/contacts/<int:contact_id>', methods=['GET'])
@jwt_required()
def mobile_contact_detail(contact_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    contact = Contact.query.get(contact_id)
    if not contact:
        return api_response(success=False, code=404, message='联系人不存在')

    company = Company.query.get(contact.company_id)
    if not company or company.is_deleted or not can_view_company(user, company):
        return api_response(success=False, code=403, message='无权访问')

    data = _contact_dict(contact)
    data['company_name'] = company.company_name
    data['notes'] = contact.notes
    return api_response(success=True, data=data)


# ─── 编辑联系人 ─────────────────────────────────────────────────
@api_v1_bp.route('/mobile/contacts/<int:contact_id>', methods=['PUT'])
@jwt_required()
def mobile_contact_update(contact_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    contact = Contact.query.get(contact_id)
    if not contact:
        return api_response(success=False, code=404, message='联系人不存在')
    company = Company.query.get(contact.company_id)
    if not company or company.is_deleted or not can_view_company(user, company):
        return api_response(success=False, code=403, message='无权修改')

    data = request.get_json(silent=True) or {}
    allowed = ['name', 'position', 'department', 'phone', 'email', 'notes']
    try:
        for k in allowed:
            if k in data:
                v = (data[k] or '').strip() if isinstance(data[k], str) else data[k]
                setattr(contact, k, v or None)
        # name 必填
        if not (contact.name or '').strip():
            return api_response(success=False, code=400, message='姓名不能为空')
        db.session.commit()
        return api_response(success=True, message='已保存', data=_contact_dict(contact))
    except Exception as e:
        db.session.rollback()
        logger.error(f'mobile contact update error: {e}')
        return api_response(success=False, code=500, message='保存失败')


# ─── 删除联系人 ─────────────────────────────────────────────────
@api_v1_bp.route('/mobile/contacts/<int:contact_id>', methods=['DELETE'])
@jwt_required()
def mobile_contact_delete(contact_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    contact = Contact.query.get(contact_id)
    if not contact:
        return api_response(success=False, code=404, message='联系人不存在')
    company = Company.query.get(contact.company_id)
    if not company or company.is_deleted or not can_view_company(user, company):
        return api_response(success=False, code=403, message='无权删除')

    try:
        cid = contact.company_id
        db.session.delete(contact)
        db.session.commit()
        return api_response(success=True, message='已删除', data={'company_id': cid})
    except Exception as e:
        db.session.rollback()
        logger.error(f'mobile contact delete error: {e}')
        return api_response(success=False, code=500, message='删除失败')
