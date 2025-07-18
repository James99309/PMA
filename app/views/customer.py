from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import gettext as _, ngettext
from app.models.customer import Company, Contact, COMPANY_TYPES
from app.models.user import User
from app import db
from app.permissions import permission_required
from app.models.project import Project
from app.models.action import Action
from sqlalchemy import or_, func, desc, text
from datetime import datetime
import difflib
import json
import re
from app.utils.dictionary_helpers import get_company_type_options, get_industry_options, get_status_options, get_country_options, COMPANY_TYPE_LABELS, INDUSTRY_LABELS, STATUS_LABELS, COUNTRY_LABELS
from app.utils.access_control import (
    get_viewable_data, can_edit_data, 
    can_view_company, can_edit_company_info, can_edit_company_sharing, can_delete_company,
    can_view_contact, can_edit_contact, can_delete_contact, can_change_company_owner
)
from app.utils.notification_helpers import trigger_event_notification
from app.utils.user_helpers import generate_user_tree_data
from app.utils.activity_tracker import check_company_activity, update_active_status
from zoneinfo import ZoneInfo
from app.utils.change_tracker import ChangeTracker
# 添加审批相关函数导入
from app.helpers.approval_helpers import get_object_approval_instance, get_available_templates
from app.utils.access_control import can_start_approval
from app.utils.country_names import get_country_names


customer = Blueprint('customer', __name__)

@customer.route('/api/countries-regions')
@login_required
def get_countries_regions():
    """获取语言感知的国家和地区数据"""
    from app.utils.i18n import get_current_language
    from app.utils.country_names import get_country_names
    
    lang = get_current_language()
    country_names = get_country_names(lang)
    
    # 地区数据映射（扩展支持多语言）
    region_data = {
        "CN": {
            "zh": ["北京市", "上海市", "天津市", "重庆市", "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省", 
                   "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省", "河南省", "湖北省", "湖南省", 
                   "广东省", "海南省", "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省", "台湾省",
                   "内蒙古自治区", "广西壮族自治区", "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区",
                   "香港特别行政区", "澳门特别行政区"],
            "en": ["Beijing", "Shanghai", "Tianjin", "Chongqing", "Hebei Province", "Shanxi Province", 
                   "Liaoning Province", "Jilin Province", "Heilongjiang Province", "Jiangsu Province", 
                   "Zhejiang Province", "Anhui Province", "Fujian Province", "Jiangxi Province", 
                   "Shandong Province", "Henan Province", "Hubei Province", "Hunan Province", 
                   "Guangdong Province", "Hainan Province", "Sichuan Province", "Guizhou Province", 
                   "Yunnan Province", "Shaanxi Province", "Gansu Province", "Qinghai Province", 
                   "Taiwan Province", "Inner Mongolia Autonomous Region", "Guangxi Zhuang Autonomous Region", 
                   "Tibet Autonomous Region", "Ningxia Hui Autonomous Region", "Xinjiang Uyghur Autonomous Region",
                   "Hong Kong Special Administrative Region", "Macao Special Administrative Region"]
        },
        "US": {
            "zh": ["阿拉巴马州", "阿拉斯加州", "亚利桑那州", "阿肯色州", "加利福尼亚州", "科罗拉多州", "康涅狄格州",
                   "特拉华州", "佛罗里达州", "乔治亚州", "夏威夷州", "爱达荷州", "伊利诺伊州", "印第安纳州",
                   "爱荷华州", "堪萨斯州", "肯塔基州", "路易斯安那州", "缅因州", "马里兰州", "马萨诸塞州",
                   "密歇根州", "明尼苏达州", "密西西比州", "密苏里州", "蒙大拿州", "内布拉斯加州",
                   "内华达州", "新罕布什尔州", "新泽西州", "新墨西哥州", "纽约州", "北卡罗来纳州",
                   "北达科他州", "俄亥俄州", "俄克拉荷马州", "俄勒冈州", "宾夕法尼亚州", "罗得岛州",
                   "南卡罗来纳州", "南达科他州", "田纳西州", "德克萨斯州", "犹他州", "佛蒙特州",
                   "弗吉尼亚州", "华盛顿州", "西弗吉尼亚州", "威斯康星州", "怀俄明州", "华盛顿特区"],
            "en": ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
                   "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", 
                   "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", 
                   "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", 
                   "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", 
                   "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", 
                   "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
                   "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"]
        },
        "JP": {
            "zh": ["东京都", "大阪府", "神奈川县", "爱知县", "埼玉县", "千叶县", "兵库县", "北海道", "福冈县", 
                   "静冈县", "茨城县", "广岛县", "京都府", "新潟县", "宫城县", "长野县", "岐阜县", "群马县", 
                   "栃木县", "冈山县", "三重县", "熊本县", "鹿儿岛县", "山口县", "爱媛县", "长崎县", 
                   "滋贺县", "奈良县", "青森县", "岩手县", "福岛县", "福井县", "山梨县", "和歌山县", 
                   "佐贺县", "山形县", "香川县", "大分县", "富山县", "石川县", "宫崎县", "秋田县", 
                   "德岛县", "高知县", "岛根县", "鸟取县", "冲绳县"],
            "en": ["Tokyo", "Osaka", "Kanagawa", "Aichi", "Saitama", "Chiba", "Hyogo", "Hokkaido", "Fukuoka", 
                   "Shizuoka", "Ibaraki", "Hiroshima", "Kyoto", "Niigata", "Miyagi", "Nagano", "Gifu", "Gunma", 
                   "Tochigi", "Okayama", "Mie", "Kumamoto", "Kagoshima", "Yamaguchi", "Ehime", "Nagasaki", 
                   "Shiga", "Nara", "Aomori", "Iwate", "Fukushima", "Fukui", "Yamanashi", "Wakayama", 
                   "Saga", "Yamagata", "Kagawa", "Oita", "Toyama", "Ishikawa", "Miyazaki", "Akita", 
                   "Tokushima", "Kochi", "Shimane", "Tottori", "Okinawa"]
        },
        "MY": {
            "zh": ["柔佛州", "吉打州", "吉兰丹州", "马六甲州", "森美兰州", "彭亨州", "槟城州", "霹雳州", 
                   "玻璃市州", "雪兰莪州", "丁加奴州", "沙巴州", "砂拉越州", "吉隆坡联邦直辖区", "布城联邦直辖区", "纳闽联邦直辖区"],
            "en": ["Johor", "Kedah", "Kelantan", "Malacca", "Negeri Sembilan", "Pahang", "Penang", "Perak", 
                   "Perlis", "Selangor", "Terengganu", "Sabah", "Sarawak", "Kuala Lumpur", "Putrajaya", "Labuan"]
        },
        "ID": {
            "zh": ["雅加达特区", "万丹省", "西爪哇省", "中爪哇省", "日惹特区", "东爪哇省", "巴厘省", "西努沙登加拉省", 
                   "东努沙登加拉省", "西加里曼丹省", "中加里曼丹省", "东加里曼丹省", "南加里曼丹省", "北加里曼丹省",
                   "北苏门答腊省", "西苏门答腊省", "廖内省", "廖内群岛省", "占碑省", "南苏门答腊省", "明古鲁省", 
                   "楠榜省", "邦加-勿里洞省", "北苏拉威西省", "中苏拉威西省", "南苏拉威西省", "东南苏拉威西省", 
                   "哥伦打洛省", "西苏拉威西省", "马鲁古省", "北马鲁古省", "巴布亚省", "西巴布亚省"],
            "en": ["Jakarta", "Banten", "West Java", "Central Java", "Yogyakarta", "East Java", "Bali", "West Nusa Tenggara", 
                   "East Nusa Tenggara", "West Kalimantan", "Central Kalimantan", "East Kalimantan", "South Kalimantan", "North Kalimantan",
                   "North Sumatra", "West Sumatra", "Riau", "Riau Islands", "Jambi", "South Sumatra", "Bengkulu", 
                   "Lampung", "Bangka Belitung", "North Sulawesi", "Central Sulawesi", "South Sulawesi", "Southeast Sulawesi", 
                   "Gorontalo", "West Sulawesi", "Maluku", "North Maluku", "Papua", "West Papua"]
        },
        "VN": {
            "zh": ["河内市", "胡志明市", "海防市", "岘港市", "芹苴市", "安江省", "北江省", "北干省", "北宁省", 
                   "薄辽省", "槟椥省", "平定省", "平阳省", "平福省", "平顺省", "金瓯省", "高平省", "多乐省", 
                   "得农省", "奠边省", "同奈省", "同塔省", "嘉莱省", "河江省", "河南省", "河静省", "后江省", 
                   "兴安省", "和平省", "胡志明市", "承天顺化省", "兴安省", "坚江省", "昆嵩省", "莱州省", 
                   "林同省", "老街省", "隆安省", "南定省", "义安省", "宁平省", "宁顺省", "富寿省", "富安省", 
                   "富国岛", "广平省", "广义省", "广南省", "广宁省", "朔庄省", "山罗省", "西宁省", "太原省", 
                   "太平省", "清化省", "承天顺化省", "茶荣省", "图元省", "永隆省", "永福省", "安沛省"],
            "en": ["Hanoi", "Ho Chi Minh City", "Hai Phong", "Da Nang", "Can Tho", "An Giang", "Bac Giang", "Bac Kan", "Bac Ninh", 
                   "Ba Ria-Vung Tau", "Ben Tre", "Binh Dinh", "Binh Duong", "Binh Phuoc", "Binh Thuan", "Ca Mau", "Cao Bang", "Dak Lak", 
                   "Dak Nong", "Dien Bien", "Dong Nai", "Dong Thap", "Gia Lai", "Ha Giang", "Ha Nam", "Ha Tinh", "Hau Giang", 
                   "Hung Yen", "Hoa Binh", "Ho Chi Minh City", "Thua Thien Hue", "Hau Giang", "Kien Giang", "Kon Tum", "Lai Chau", 
                   "Lam Dong", "Lao Cai", "Long An", "Nam Dinh", "Nghe An", "Ninh Binh", "Ninh Thuan", "Phu Tho", "Phu Yen", 
                   "Phu Quoc", "Quang Binh", "Quang Ngai", "Quang Nam", "Quang Ninh", "Soc Trang", "Son La", "Tay Ninh", "Thai Nguyen", 
                   "Thai Binh", "Thanh Hoa", "Thua Thien Hue", "Tra Vinh", "Tuyen Quang", "Vinh Long", "Vinh Phuc", "Yen Bai"]
        },
        "TH": {
            "zh": ["曼谷", "春武里府", "北榄府", "暖武里府", "巴吞他尼府", "龙仔厝府", "北碧府", "猜也奔府", 
                   "彰化府", "清莱府", "清迈府", "春蓬府", "甘烹碧府", "华富里府", "来兴府", "南奔府", 
                   "南邦府", "廊开府", "洛坤府", "洛武里府", "湄宏顺府", "马哈沙拉堪府", "莫达汉府", 
                   "那空那育府", "那空拍侬府", "那空叻差是玛府", "那空沙旺府", "那空是贪玛叻府", 
                   "楠府", "呵叻府", "廊曼府", "巴真府", "北大年府", "攀牙府", "博他仑府", "碧武里府", 
                   "佛丕府", "佛统府", "普吉府", "叻丕府", "罗勇府", "沙缴府", "桑卡府", "沙敦府",
                   "信武里府", "四色菊府", "素可泰府", "素林府", "素叻府", "达府", "董里府", "陶公府", 
                   "程逸府", "乌隆府", "乌泰他尼府", "惹拉府", "也拉府", "益梭通府"],
            "en": ["Bangkok", "Chonburi", "Samut Prakan", "Nonthaburi", "Pathum Thani", "Samut Sakhon", "Kanchanaburi", "Chachoengsao", 
                   "Chanthaburi", "Chiang Rai", "Chiang Mai", "Chumphon", "Kamphaeng Phet", "Lopburi", "Loei", "Lamphun", 
                   "Lampang", "Nong Khai", "Nakhon Si Thammarat", "Lopburi", "Mae Hong Son", "Maha Sarakham", "Mukdahan", 
                   "Nakhon Nayok", "Nakhon Phanom", "Nakhon Ratchasima", "Nakhon Sawan", "Nakhon Si Thammarat", 
                   "Nan", "Nong Bua Lamphu", "Nong Khai", "Prachinburi", "Pattani", "Phang Nga", "Phatthalung", "Phetchaburi", 
                   "Phetchabun", "Nakhon Pathom", "Phuket", "Ratchaburi", "Rayong", "Sa Kaeo", "Sakon Nakhon", "Satun", 
                   "Sing Buri", "Sisaket", "Sukhothai", "Surin", "Surat Thani", "Tak", "Trang", "Trat", 
                   "Ubon Ratchathani", "Udon Thani", "Uthai Thani", "Yala", "Yala", "Yasothon"]
        }
    }
    
    # 构建返回数据 - 保持地区排序
    countries = []
    for code, name in country_names.items():
        countries.append({"code": code, "name": name})
    
    # 构建地区数据
    regions = {}
    for country_code, region_langs in region_data.items():
        regions[country_code] = region_langs.get(lang, region_langs.get('zh', []))
    
    return jsonify({
        "countries": countries,
        "regions": regions
    })

def get_existing_filter_options(all_viewable_companies):
    """
    基于实际存在的公司数据生成筛选器选项
    """
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    
    # 获取实际存在的企业类型
    existing_company_types = {c.company_type for c in all_viewable_companies if c.company_type}
    company_type_options = [(key, COMPANY_TYPE_LABELS.get(key, {}).get(lang_code, key)) 
                           for key in existing_company_types]
    
    # 获取实际存在的行业
    existing_industries = {c.industry for c in all_viewable_companies if c.industry}  
    industry_options = [(key, INDUSTRY_LABELS.get(key, {}).get(lang_code, key))
                       for key in existing_industries]
    
    # 获取实际存在的状态
    existing_statuses = {c.status for c in all_viewable_companies if c.status}
    status_options = [(key, STATUS_LABELS.get(key, {}).get(lang_code, key))
                     for key in existing_statuses]
    
    # 获取实际存在的国家
    existing_countries = {c.country for c in all_viewable_companies if c.country}
    country_options = [(key, COUNTRY_LABELS.get(key, {}).get(lang_code, key))
                      for key in existing_countries]
    
    return company_type_options, industry_options, status_options, country_options

@customer.route('/')
@permission_required('customer', 'view')
def list_companies():
    search = request.args.get('search', '')
    
    # 滚动加载参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 限制每次加载数量的范围
    if limit not in [10, 20, 30, 50]:
        limit = 20
    
    # 初始化查询：使用权限控制
    query = get_viewable_data(Company, current_user)
    
    # 搜索过滤
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    
    # 筛选条件
    owner_filter = request.args.get('owner_filter')
    company_type_filter = request.args.get('company_type')
    industry_filter = request.args.get('industry')
    country_filter = request.args.get('country')
    status_filter = request.args.get('status_filter')
    
    if owner_filter:
        query = query.filter(Company.owner_id == owner_filter)
    if company_type_filter:
        query = query.filter(Company.company_type == company_type_filter)
    if industry_filter:
        query = query.filter(Company.industry == industry_filter)
    if country_filter:
        query = query.filter(Company.country == country_filter)
    if status_filter:
        query = query.filter(Company.status == status_filter)
    
    # 获取排序参数
    sort_field = request.args.get('sort', 'updated_at')
    sort_order = request.args.get('order', 'desc')
    
    # 验证排序字段是否有效
    valid_sort_fields = ['company_code', 'company_name', 'company_type', 'industry',
                         'country', 'region', 'address', 'status', 'owner_id',
                         'updated_at', 'created_at']

    if sort_field not in valid_sort_fields:
        sort_field = 'updated_at'

    # 添加排序
    if hasattr(Company, sort_field):
        order_attr = getattr(Company, sort_field)
        if sort_order == 'desc':
            query = query.order_by(order_attr.desc())
        else:
            query = query.order_by(order_attr.asc())

    # 获取总记录数
    total_count = query.count()
    
    # 滚动加载查询
    companies = query.offset(offset).limit(limit).all()
    
    # 计算是否还有更多数据
    has_more = (offset + limit) < total_count
    
    # 预加载所有企业的所有者信息（优化：只加载当前页的数据）
    owner_ids = [company.owner_id for company in companies if company.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for company in companies:
            if company.owner_id and company.owner_id in owners:
                company.owner = owners[company.owner_id]
    
    # 为每个公司添加联系人创建者ID列表（优化：只处理当前页的数据）
    company_ids = [company.id for company in companies]
    company_contact_owners = {}
    if company_ids:
        contact_owners = db.session.query(Contact.company_id, Contact.owner_id).filter(
            Contact.company_id.in_(company_ids)
        ).distinct().all()
        
        for company_id, owner_id in contact_owners:
            if company_id not in company_contact_owners:
                company_contact_owners[company_id] = []
            company_contact_owners[company_id].append(owner_id)
    
    # 将映射添加到公司对象
    for company in companies:
        company.contact_owner_ids = company_contact_owners.get(company.id, [])
    
    # 获取国际化的国家名称映射
    from app.utils.i18n import get_current_language
    country_code_to_name = get_country_names(get_current_language())
    
    # 获取所有用户和唯一的owner_ids用于筛选
    all_users = User.query.filter(User._is_active == True).order_by(User.real_name, User.username).all()
    
    # 获取当前用户可见的所有公司数据（用于生成筛选器选项）
    all_viewable_companies = get_viewable_data(Company, current_user).all()
    unique_owner_ids = {c.owner_id for c in all_viewable_companies if c.owner_id}
    
    # 获取实际存在的筛选器选项（基于当前可见数据）
    company_type_options, industry_options, status_options, country_options = get_existing_filter_options(all_viewable_companies)
    
    return render_template('customer/list.html', 
                          companies=companies, 
                          total_count=total_count,
                          has_more=has_more,
                          offset=offset,
                          limit=limit,
                          search_term=search, 
                          sort_field=sort_field, 
                          sort_order=sort_order,
                          owner_filter=owner_filter,
                          all_users=all_users,
                          unique_owner_ids=unique_owner_ids,
                          country_code_to_name=country_code_to_name,
                          COMPANY_TYPE_OPTIONS=company_type_options,
                          INDUSTRY_OPTIONS=industry_options,
                          STATUS_OPTIONS=status_options,
                          COUNTRY_OPTIONS=country_options)

@customer.route('/api/load-more', methods=['GET'])
@permission_required('customer', 'view')
def load_more_companies():
    """为滚动加载提供的API端点"""
    # 使用与list_companies相同的逻辑，但返回JSON
    search = request.args.get('search', '')
    
    # 滚动加载参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 限制每次加载数量的范围
    if limit not in [10, 20, 30, 50]:
        limit = 20
    
    # 初始化查询：使用权限控制
    query = get_viewable_data(Company, current_user)
    
    # 搜索过滤
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    
    # 筛选条件
    owner_filter = request.args.get('owner_filter')
    company_type_filter = request.args.get('company_type')
    industry_filter = request.args.get('industry')
    country_filter = request.args.get('country')
    status_filter = request.args.get('status_filter')
    
    if owner_filter:
        query = query.filter(Company.owner_id == owner_filter)
    if company_type_filter:
        query = query.filter(Company.company_type == company_type_filter)
    if industry_filter:
        query = query.filter(Company.industry == industry_filter)
    if country_filter:
        query = query.filter(Company.country == country_filter)
    if status_filter:
        query = query.filter(Company.status == status_filter)
    
    # 获取排序参数
    sort_field = request.args.get('sort', 'updated_at')
    sort_order = request.args.get('order', 'desc')
    
    # 验证排序字段是否有效
    valid_sort_fields = ['company_code', 'company_name', 'company_type', 'industry',
                         'country', 'region', 'address', 'status', 'owner_id',
                         'updated_at', 'created_at']

    if sort_field not in valid_sort_fields:
        sort_field = 'updated_at'

    # 添加排序
    if hasattr(Company, sort_field):
        order_attr = getattr(Company, sort_field)
        if sort_order == 'desc':
            query = query.order_by(order_attr.desc())
        else:
            query = query.order_by(order_attr.asc())

    # 获取总记录数
    total_count = query.count()
    
    # 滚动加载查询
    companies = query.offset(offset).limit(limit).all()
    
    # 计算是否还有更多数据
    has_more = (offset + limit) < total_count
    
    # 预加载所有企业的所有者信息
    owner_ids = [company.owner_id for company in companies if company.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for company in companies:
            if company.owner_id and company.owner_id in owners:
                company.owner = owners[company.owner_id]
    
    # 为每个公司添加联系人创建者ID列表
    company_ids = [company.id for company in companies]
    company_contact_owners = {}
    if company_ids:
        contact_owners = db.session.query(Contact.company_id, Contact.owner_id).filter(
            Contact.company_id.in_(company_ids)
        ).distinct().all()
        
        for company_id, owner_id in contact_owners:
            if company_id not in company_contact_owners:
                company_contact_owners[company_id] = []
            company_contact_owners[company_id].append(owner_id)
    
    # 将映射添加到公司对象
    for company in companies:
        company.contact_owner_ids = company_contact_owners.get(company.id, [])
    
    # 获取国际化的国家名称映射
    from app.utils.i18n import get_current_language
    country_code_to_name = get_country_names(get_current_language())
    
    # 渲染HTML片段
    html = render_template('customer/company_rows.html', 
                          companies=companies,
                          owner_filter=owner_filter,
                          country_code_to_name=country_code_to_name,
                          COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options(),
                          COUNTRY_OPTIONS=get_country_options())
    
    return jsonify({
        'html': html,
        'has_more': has_more,
        'total_count': total_count,
        'loaded_count': offset + len(companies)
    })

@customer.route('/search', methods=['GET'])
@permission_required('customer', 'view')
def search_companies():
    search = request.args.get('search', '')
    if not search:
        return redirect(url_for('customer.list_companies'))
    
    # 使用数据访问控制
    query = get_viewable_data(Company, current_user)
    
    # 添加搜索条件
    query = query.filter(Company.company_name.ilike(f'%{search}%'))
    companies = query.all()
    
    # 预加载所有企业的所有者信息
    owner_ids = [company.owner_id for company in companies if company.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for company in companies:
            if company.owner_id and company.owner_id in owners:
                company.owner = owners[company.owner_id]
    
    # 为每个公司添加联系人创建者ID列表
    company_ids = [company.id for company in companies]
    contact_owners = db.session.query(Contact.company_id, Contact.owner_id).filter(
        Contact.company_id.in_(company_ids)
    ).distinct().all()
    
    # 创建公司ID到联系人创建者ID列表的映射
    company_contact_owners = {}
    for company_id, owner_id in contact_owners:
        if company_id not in company_contact_owners:
            company_contact_owners[company_id] = []
        company_contact_owners[company_id].append(owner_id)
    
    # 将映射添加到公司对象
    for company in companies:
        company.contact_owner_ids = company_contact_owners.get(company.id, [])
    
    # 获取排序参数，提供默认值
    sort_field = request.args.get('sort', 'company_name')
    sort_order = request.args.get('order', 'asc')
    
    # 获取国际化的国家名称映射
    country_code_to_name = get_country_names(get_current_language())
    
    # 为搜索结果生成筛选器选项（基于当前可见的所有数据，不仅仅是搜索结果）
    all_viewable_companies = get_viewable_data(Company, current_user).all()
    company_type_options, industry_options, status_options, country_options = get_existing_filter_options(all_viewable_companies)
    
    # 获取用户信息用于筛选器
    all_users = User.query.filter(User._is_active == True).order_by(User.real_name, User.username).all()
    unique_owner_ids = {c.owner_id for c in all_viewable_companies if c.owner_id}
    
    return render_template('customer/list.html', 
                          companies=companies, 
                          search_term=search, 
                          sort_field=sort_field, 
                          sort_order=sort_order,
                          country_code_to_name=country_code_to_name,
                          all_users=all_users,
                          unique_owner_ids=unique_owner_ids,
                          COMPANY_TYPE_OPTIONS=company_type_options,
                          INDUSTRY_OPTIONS=industry_options,
                          STATUS_OPTIONS=status_options,
                          COUNTRY_OPTIONS=country_options)

@customer.route('/search_contacts', methods=['GET'])
@permission_required('customer', 'view')
def search_contacts():
    search = request.args.get('search', '')
    
    if not search:
        return redirect(url_for('customer.list_companies'))
    
    # 使用数据访问控制
    query = get_viewable_data(Contact, current_user)
    
    if search:
        # 搜索联系人
        contacts = query.filter(Contact.name.ilike(f'%{search}%')).all()
    else:
        contacts = query.limit(50).all()  # 限制结果数量
    
    # 获取联系人所属的公司信息
    company_ids = set(contact.company_id for contact in contacts if contact.company_id)
    companies = {company.id: company for company in Company.query.filter(Company.id.in_(company_ids), Company.is_deleted == False).all()}
    
    # 为每个联系人添加company属性
    for contact in contacts:
        if contact.company_id and contact.company_id in companies:
            contact.company = companies[contact.company_id]
    
    # 返回搜索结果专用模板，不使用contacts.html
    return render_template('customer/search_results.html', contacts=contacts, search_term=search,
                          COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options(),
                          COUNTRY_OPTIONS=get_country_options())

@customer.route('/<int:company_id>/view')
@permission_required('customer', 'view')
def view_company(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    
    # 检查当前用户是否有权限查看此企业
    if not can_view_company(current_user, company):
        flash(_('您没有权限查看此客户信息'), 'danger')
        return redirect(url_for('customer.list_companies'))
    
    # 所有联系人
    all_contacts = Contact.query.filter_by(company_id=company_id).all()
    
    # 获取用户有权限查看的联系人
    viewable_contacts = [c for c in all_contacts if can_view_contact(current_user, c)]
    
    # 预加载所有联系人的所有者信息
    owner_ids = [contact.owner_id for contact in all_contacts if contact.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for contact in all_contacts:
            if contact.owner_id and contact.owner_id in owners:
                contact.owner = owners[contact.owner_id]
    
    # 如果需要，确保公司的动作记录已正确加载并按日期排序
    if hasattr(company, 'actions') and company.actions:
        company.actions.sort(key=lambda x: x.date, reverse=True)
    
    # 查询与该企业相关的所有项目
    projects = Project.query.filter(
        or_(
            Project.end_user == company.company_name,
            Project.design_issues.like(f'%{company.company_name}%'),
            Project.contractor == company.company_name,
            Project.system_integrator == company.company_name,
            Project.dealer == company.company_name
        )
    ).all()
    
    # 筛选用户有权限查看的项目
    viewable_project_ids = [p.id for p in get_viewable_data(Project, current_user).all()]
    viewable_projects = [p for p in projects if p.id in viewable_project_ids]
    
    # 获取公司的行动记录
    page = request.args.get('page', 1, type=int)
    query = Action.query.filter_by(company_id=company_id)
    pagination = query.order_by(Action.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    actions = pagination.items
    
    # 筛选出用户有权限查看的联系人的行动记录
    viewable_contact_ids = [c.id for c in viewable_contacts]
    viewable_actions = [a for a in actions if a.contact_id in viewable_contact_ids or a.owner_id == current_user.id]
    
    # 提前加载行动记录所有者信息，避免N+1查询
    action_user_ids = [action.owner_id for action in actions if action.owner_id]
    users = User.query.filter(User.id.in_(set(action_user_ids))).all()
    user_map = {user.id: user for user in users}
    for action in actions:
        if action.owner_id and action.owner_id in user_map:
            action.owner = user_map[action.owner_id]
    
    # 获取所有可选用户列表（用于共享设置）
    # 修复：直接使用_is_active字段会漏掉管理员用户，需要改用属性方法判断
    # 通过SQL表达式实现：管理员用户或_is_active=True的用户
    all_users = User.query.filter(
        or_(
            User.role == 'admin',  # 管理员用户
            User._is_active == True  # 活跃用户
        )
    ).all()
    
    # 获取国际化的国家名称映射
    from app.utils.i18n import get_current_language
    country_code_to_name = get_country_names(get_current_language())
    
    # 查询可选新拥有人
    if can_change_company_owner(current_user, company):
        if current_user.role == 'admin':
            # 管理员可以看到所有用户
            all_users = User.query.all()
        elif getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director':
            # 部门负责人只能选择本部门的活跃用户和管理员
            all_users = User.query.filter(
                or_(User.role == 'admin', User._is_active == True),
                User.department == current_user.department
            ).all()
        else:
            # 其他情况，至少包含当前用户和当前拥有者
            all_users = User.query.filter(User.id.in_([current_user.id, company.owner_id])).all()
        # 保险：如果all_users为空，至少包含当前用户和当前拥有者
        if not all_users:
            all_users = User.query.filter(User.id.in_([current_user.id, company.owner_id])).all()
    
    # 生成用户树状数据
    user_tree_data = None
    if can_change_company_owner(current_user, company):
        filter_by_dept = current_user.role != 'admin'
        user_tree_data = generate_user_tree_data(filter_by_department=filter_by_dept)
    
    return render_template('customer/view.html', 
                          company=company, 
                          contacts=viewable_contacts, 
                          all_contacts=all_contacts,  # 用于查重
                          actions=actions, 
                          viewable_actions=viewable_actions,
                          pagination=pagination,
                          projects=projects,
                          viewable_projects=viewable_projects,
                          country_code_to_name=country_code_to_name,
                          all_users=all_users,
                          COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options(),
                          user_tree_data=user_tree_data,
                          # 添加审批相关函数
                          get_object_approval_instance=get_object_approval_instance,
                          get_available_templates=get_available_templates,
                          can_start_approval=can_start_approval)

@customer.route('/add', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_company():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            # 移除csrf_token和所有非Company字段
            for key in ['csrf_token', 'contact_name', 'contact_department', 'contact_position', 'contact_phone', 'contact_email', 'contact_notes']:
                data.pop(key, None)
            # 强制写入活跃状态
            data['status'] = 'active'
            # 设置客户归属人为当前用户
            data['owner_id'] = current_user.id
            company = Company(**data)
            db.session.add(company)
            db.session.commit()
            
            # 记录创建历史
            try:
                ChangeTracker.log_create(company)
            except Exception as track_err:
                logger.warning(f"记录客户创建历史失败: {str(track_err)}")
            
            # 新增：每次添加客户后自动刷新活跃度和更新时间
            company.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            update_active_status(company)
            db.session.commit()
            # 通知新客户创建
            from app.services.event_dispatcher import notify_customer_created
            notify_customer_created(company, current_user)
            flash(_('客户创建成功！'), 'success')
            return redirect(url_for('customer.list_companies'))
        except Exception as e:
            db.session.rollback()
            import traceback
            # 增强日志输出，包含表单内容和traceback
            flash('保存失败：' + str(e) + '<br>表单内容：' + str(dict(request.form)) + '<br>' + traceback.format_exc(), 'danger')
    
    return render_template('customer/add.html', COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options())

@customer.route('/edit/<int:company_id>', methods=['GET', 'POST'])
@permission_required('customer', 'edit')
def edit_company(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    
    # 检查编辑权限
    if not can_edit_company_info(current_user, company):
        flash(_('您没有权限编辑此企业信息'), 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))

    if request.method == 'POST':
        try:
            # 导入历史记录跟踪器
            from app.utils.change_tracker import ChangeTracker
            
            # 捕获修改前的值
            old_values = ChangeTracker.capture_old_values(company)
            
            data = request.form.to_dict()
            # 移除status字段，禁止编辑
            data.pop('status', None)
            for key, value in data.items():
                setattr(company, key, value)
            db.session.commit()
            
            # 记录变更历史
            try:
                new_values = ChangeTracker.get_new_values(company, old_values.keys())
                ChangeTracker.log_update(company, old_values, new_values)
            except Exception as track_err:
                logger.warning(f"记录客户变更历史失败: {str(track_err)}")
            
            # 更新客户活跃状态
            check_company_activity(company_id=company_id, days_threshold=1)
            flash(_('客户信息已更新！'), 'success')
            return redirect(url_for('customer.view_company', company_id=company.id))
        except Exception as e:
            db.session.rollback()
            flash('保存失败：' + str(e), 'danger')

    return render_template('customer/edit.html', company=company, COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options())

@customer.route('/api/delete-confirm/<int:company_id>')
@permission_required('customer', 'delete') 
def api_delete_confirm(company_id):
    """API端点 - 获取删除确认数据"""
    try:
        company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
        
        # 检查删除权限
        if not can_edit_data(company, current_user):
            return jsonify({'error': '您没有权限删除此企业'}), 403

        # 分析关联数据
        impact_data = analyze_company_dependencies(company)
        
        return jsonify({
            'company': {
                'id': company.id,
                'name': company.company_name,
                'type': company.company_type,
                'industry': company.industry
            },
            'impact_data': impact_data
        })
    except Exception as e:
        current_app.logger.error(f"删除确认API出错 (企业ID: {company_id}): {str(e)}")
        return jsonify({'error': f'获取删除确认信息失败: {str(e)}'}), 500

@customer.route('/api/batch-delete-confirm', methods=['POST'])
@permission_required('customer', 'delete')
def api_batch_delete_confirm():
    """API端点 - 获取批量删除确认数据"""
    try:
        if not request.is_json:
            return jsonify({'error': '请求必须是JSON格式'}), 400
            
        data = request.json
        company_ids = data.get('company_ids', [])
        
        if not company_ids or not isinstance(company_ids, list):
            return jsonify({'error': '缺少要删除的企业ID列表'}), 400
        
        try:
            company_ids = [int(id) for id in company_ids]
        except ValueError:
            return jsonify({'error': '企业ID必须是整数'}), 400
        
        # 获取企业列表并检查权限
        companies = Company.query.filter(Company.id.in_(company_ids), Company.is_deleted == False).all()
    except Exception as e:
        current_app.logger.error(f"批量删除确认API出错: {str(e)}")
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500
    
    try:
        companies_data = []
        for company in companies:
            if can_edit_data(company, current_user):
                try:
                    impact_data = analyze_company_dependencies(company)
                    companies_data.append({
                        'company': {
                            'id': company.id,
                            'name': company.company_name,
                            'type': company.company_type,
                            'industry': company.industry
                        },
                        'impact_data': impact_data
                    })
                except Exception as e:
                    current_app.logger.error(f"分析企业 {company.id} 依赖关系时出错: {str(e)}")
                    return jsonify({'error': f'分析企业依赖关系失败: {str(e)}'}), 500
        
        return jsonify({
            'companies': companies_data,
            'total_count': len(companies_data)
        })
    except Exception as e:
        current_app.logger.error(f"批量删除确认数据处理出错: {str(e)}")
        return jsonify({'error': f'数据处理失败: {str(e)}'}), 500

def analyze_company_dependencies(company):
    """分析企业的关联数据依赖"""
    try:
        impact_data = {
            'contacts': [],
            'projects': [],
            'inventories': [],
            'settlements': [],
            'pricing_orders': [],
            'settlement_orders': [],
            'purchase_orders': [],
            'actions': [],
            'total_affected': 0
        }
    
        # 检查联系人
        try:
            existing_contacts = Contact.query.filter_by(company_id=company.id).all()
            if existing_contacts:
                impact_data['contacts'] = [{'name': c.name, 'owner': c.owner.username if c.owner else 'N/A'} for c in existing_contacts]
        except Exception as e:
            current_app.logger.error(f"分析联系人失败: {str(e)}")
            impact_data['contacts'] = []
    
        # 检查项目引用
        try:
            from app.models.project import Project
            related_projects = Project.query.filter(
                db.or_(
                    Project.end_user == company.company_name,
                    Project.design_issues == company.company_name,
                    Project.contractor == company.company_name,
                    Project.system_integrator == company.company_name,
                    Project.dealer == company.company_name
                )
            ).all()
            if related_projects:
                impact_data['projects'] = [{'name': p.project_name, 'status': p.status} for p in related_projects]
        except (ImportError, AttributeError) as e:
            current_app.logger.warning(f"项目模块不可用: {str(e)}")
            impact_data['projects'] = []
        except Exception as e:
            current_app.logger.error(f"分析项目引用失败: {str(e)}")
            impact_data['projects'] = []
    
        # 检查库存相关数据
        try:
            from app.models.inventory import Inventory, Settlement, PurchaseOrder
            inventories = Inventory.query.filter_by(company_id=company.id).all()
            if inventories:
                impact_data['inventories'] = [{'product': i.product.product_name if i.product else 'N/A', 'quantity': i.quantity} for i in inventories]
            
            settlements = Settlement.query.filter_by(company_id=company.id).all()
            if settlements:
                impact_data['settlements'] = [{'number': s.settlement_number, 'status': s.status} for s in settlements]
            
            purchase_orders = PurchaseOrder.query.filter_by(company_id=company.id).all()
            if purchase_orders:
                impact_data['purchase_orders'] = [{'number': po.order_number, 'status': po.status} for po in purchase_orders]
        except (ImportError, AttributeError) as e:
            current_app.logger.warning(f"库存模块不可用: {str(e)}")
            impact_data['inventories'] = []
            impact_data['settlements'] = []
            impact_data['purchase_orders'] = []
        except Exception as e:
            current_app.logger.error(f"分析库存相关数据失败: {str(e)}")
            impact_data['inventories'] = []
            impact_data['settlements'] = []
            impact_data['purchase_orders'] = []
    
        # 检查批价单和结算单
        try:
            from app.models.pricing_order import PricingOrder, SettlementOrder
            pricing_orders = PricingOrder.query.filter(
                db.or_(
                    PricingOrder.dealer_id == company.id,
                    PricingOrder.distributor_id == company.id
                )
            ).all()
            if pricing_orders:
                impact_data['pricing_orders'] = [{'number': po.order_number, 'status': po.status, 'role': 'dealer' if po.dealer_id == company.id else 'distributor'} for po in pricing_orders]
            
            settlement_orders = SettlementOrder.query.filter(
                db.or_(
                    SettlementOrder.distributor_id == company.id,
                    SettlementOrder.dealer_id == company.id
                )
            ).all()
            if settlement_orders:
                impact_data['settlement_orders'] = [{'number': so.order_number, 'status': so.status, 'role': 'distributor' if so.distributor_id == company.id else 'dealer'} for so in settlement_orders]
        except (ImportError, AttributeError) as e:
            current_app.logger.warning(f"批价单模块不可用: {str(e)}")
            impact_data['pricing_orders'] = []
            impact_data['settlement_orders'] = []
        except Exception as e:
            current_app.logger.error(f"分析批价单和结算单失败: {str(e)}")
            impact_data['pricing_orders'] = []
            impact_data['settlement_orders'] = []
    
        # 检查行动记录
        try:
            related_actions = Action.query.filter_by(company_id=company.id).all()
            if related_actions:
                impact_data['actions'] = [{'date': a.date, 'content': a.content[:50] + '...' if len(a.content) > 50 else a.content} for a in related_actions]
        except Exception as e:
            current_app.logger.error(f"分析行动记录失败: {str(e)}")
            impact_data['actions'] = []
        
        # 计算总影响数量
        try:
            impact_data['total_affected'] = (
                len(impact_data['contacts']) + 
                len(impact_data['projects']) + 
                len(impact_data['inventories']) + 
                len(impact_data['settlements']) + 
                len(impact_data['pricing_orders']) + 
                len(impact_data['settlement_orders']) + 
                len(impact_data['purchase_orders']) + 
                len(impact_data['actions'])
            )
        except Exception as e:
            current_app.logger.error(f"计算总影响数量失败: {str(e)}")
            impact_data['total_affected'] = 0
        
        return impact_data
    except Exception as e:
        current_app.logger.error(f"分析企业依赖关系完全失败: {str(e)}")
        # 返回空的影响数据
        return {
            'contacts': [],
            'projects': [],
            'inventories': [],
            'settlements': [],
            'pricing_orders': [],
            'settlement_orders': [],
            'purchase_orders': [],
            'actions': [],
            'total_affected': 0
        }

@customer.route('/delete/<int:company_id>', methods=['POST'])
@permission_required('customer', 'delete')
def delete_company(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    
    # 检查删除权限
    if not can_edit_data(company, current_user):
        flash('您没有权限删除此企业', 'danger')
        return redirect(url_for('customer.list_companies'))

    # 检查是否强制删除
    force_delete = request.form.get('force_delete') == 'true'
    if not force_delete:
        # 如果不是强制删除，重定向到确认页面
        return redirect(url_for('customer.delete_confirm', company_id=company_id))


    try:
        # 记录删除历史
        try:
            ChangeTracker.log_delete(company)
        except Exception as track_err:
            current_app.logger.warning(f"记录客户删除历史失败: {str(track_err)}")
        
        # === 新增：删除客户审批实例和相关审批记录 ===
        from app.models.approval import ApprovalInstance, ApprovalRecord
        customer_approvals = ApprovalInstance.query.filter_by(
            object_type='customer', 
            object_id=company_id
        ).all()
        
        if customer_approvals:
            approval_record_count = 0
            for approval in customer_approvals:
                # 删除审批记录
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                for record in records:
                    db.session.delete(record)
                # 删除审批实例
                db.session.delete(approval)
            
            current_app.logger.info(f"已删除 {len(customer_approvals)} 个客户审批实例和 {approval_record_count} 个审批记录")
        
        # 找到与此公司相关的所有行动记录
        related_actions = Action.query.filter_by(company_id=company.id).all()
        
        # 删除所有相关的行动记录（包括其回复，通过级联删除）
        for action in related_actions:
            db.session.delete(action)
        
        # === 新增：处理inventory相关记录 ===
        from app.models.inventory import Inventory, InventoryTransaction, Settlement, SettlementDetail, PurchaseOrder
        
        # 删除库存变动记录
        inventories = Inventory.query.filter_by(company_id=company.id).all()
        for inventory in inventories:
            # 删除库存变动记录
            InventoryTransaction.query.filter_by(inventory_id=inventory.id).delete()
            # 删除结算明细记录
            SettlementDetail.query.filter_by(inventory_id=inventory.id).delete()
            # 删除库存记录
            db.session.delete(inventory)
        
        # 删除结算记录
        Settlement.query.filter_by(company_id=company.id).delete()
        
        # 删除订货单记录
        PurchaseOrder.query.filter_by(company_id=company.id).delete()
        
        # === 新增：处理pricing和settlement相关记录 ===
        from app.models.pricing_order import PricingOrder, SettlementOrder, PricingOrderDetail, SettlementOrderDetail, PricingOrderApprovalRecord
        
        # 删除批价单相关记录
        pricing_orders = PricingOrder.query.filter(
            db.or_(
                PricingOrder.dealer_id == company.id,
                PricingOrder.distributor_id == company.id
            )
        ).all()
        for po in pricing_orders:
            # 删除批价单明细
            PricingOrderDetail.query.filter_by(pricing_order_id=po.id).delete()
            # 删除结算单明细
            SettlementOrderDetail.query.filter_by(pricing_order_id=po.id).delete()
            # 删除审批记录
            PricingOrderApprovalRecord.query.filter_by(pricing_order_id=po.id).delete()
            # 删除批价单
            db.session.delete(po)
        
        # 删除结算单记录
        settlement_orders = SettlementOrder.query.filter(
            db.or_(
                SettlementOrder.distributor_id == company.id,
                SettlementOrder.dealer_id == company.id
            )
        ).all()
        for so in settlement_orders:
            db.session.delete(so)
            
        # 然后删除公司 (这将级联删除联系人，因为在模型中设置了cascade='all, delete-orphan')
        db.session.delete(company)
        db.session.commit()
        flash('企业删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除失败：' + str(e), 'danger')

    return redirect(url_for('customer.list_companies'))

@customer.route('/<int:company_id>/contacts')
@permission_required('customer', 'view')
def list_contacts(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    
    # 预加载所有联系人的所有者信息
    owner_ids = [contact.owner_id for contact in company.contacts if contact.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for contact in company.contacts:
            if contact.owner_id and contact.owner_id in owners:
                contact.owner = owners[contact.owner_id]
    
    return render_template('customer/contacts.html', company=company, COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options())

@customer.route('/<int:company_id>/contacts/add', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_contact(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    # 允许所有人添加联系人，但只显示自己创建的联系人
    if request.method == 'POST':
        name = request.form['name']
        # 查重：同公司下所有联系人（不论owner）
        duplicate = Contact.query.filter_by(company_id=company_id, name=name).first()
        if duplicate:
            # 如果当前用户不可见，提示不可见
            if duplicate.owner_id != current_user.id:
                flash('该客户已有同名联系人（不可见）', 'danger')
                return redirect(url_for('customer.view_company', company_id=company_id))
            else:
                flash('该客户已有同名联系人', 'danger')
                return redirect(url_for('customer.view_company', company_id=company_id))
        
        # 创建新联系人
        contact = Contact(
            company_id=company_id,
            name=name,
            department=request.form['department'],
            position=request.form['position'],
            phone=request.form['phone'],
            email=request.form['email'],
            notes=request.form['notes'],
            owner_id=current_user.id,
            # 处理共享控制字段
            override_share='override_share' in request.form,
            shared_disabled='shared_disabled' in request.form
        )
        
        # 添加到数据库
        db.session.add(contact)
        db.session.commit()
        
        # 记录创建历史
        try:
            ChangeTracker.log_create(contact)
        except Exception as track_err:
            logger.warning(f"记录联系人创建历史失败: {str(track_err)}")
        
        # 新增：每次添加联系人后自动刷新客户活跃度和更新时间
        company.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        update_active_status(company)
        db.session.commit()
        
        # 设置为主要联系人（如果勾选）
        if request.form.get('is_primary'):
            contact.set_as_primary()
        
        flash('联系人添加成功！', 'success')
        # 修改为添加后跳转客户详情页
        return redirect(url_for('customer.view_company', company_id=company_id))
    return render_template('customer/add_contact.html', company=company, COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options())

@customer.route('/<int:company_id>/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@permission_required('customer', 'edit')
def edit_contact(company_id, contact_id):
    contact = Contact.query.get_or_404(contact_id)
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    
    # 检查编辑权限
    if not can_edit_contact(current_user, contact):
        flash('您没有权限编辑此联系人', 'danger')
        return redirect(url_for('customer.list_contacts', company_id=company_id))

    if request.method == 'POST':
        # 捕获修改前的值
        old_values = ChangeTracker.capture_old_values(contact)
        
        contact.name = request.form['name']
        contact.department = request.form['department']
        contact.position = request.form['position']
        contact.phone = request.form['phone']
        contact.email = request.form['email']
        contact.notes = request.form['notes']
        
        # 处理主要联系人状态
        if request.form.get('is_primary'):
            contact.set_as_primary()
        elif contact.is_primary:  # 如果之前是主要联系人，现在取消了
            contact.is_primary = False
            
        # 处理共享控制设置
        contact.override_share = 'override_share' in request.form
        contact.shared_disabled = 'shared_disabled' in request.form
            
        db.session.commit()
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(contact, old_values.keys())
            ChangeTracker.log_update(contact, old_values, new_values)
        except Exception as track_err:
            logger.warning(f"记录联系人变更历史失败: {str(track_err)}")
        
        flash('联系人信息更新成功！', 'success')
        return redirect(url_for('customer.list_contacts', company_id=contact.company_id))
    return render_template('customer/edit_contact.html', contact=contact, COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options())

@customer.route('/<int:company_id>/contacts/<int:contact_id>/delete', methods=['POST'])
@permission_required('customer', 'delete')
def delete_contact(company_id, contact_id):
    contact = Contact.query.get_or_404(contact_id);
    # 检查删除权限
    if not can_delete_contact(current_user, contact):
        flash('您没有权限删除此联系人，只有联系人的创建者或管理员才能删除', 'danger')
        return redirect(url_for('customer.list_contacts', company_id=company_id))
    
    # 记录删除历史
    try:
        ChangeTracker.log_delete(contact)
    except Exception as track_err:
        logger.warning(f"记录联系人删除历史失败: {str(track_err)}")
    
    db.session.delete(contact)
    db.session.commit()
    flash('联系人删除成功！', 'success')
    # 修改为删除后跳转客户详情页
    return redirect(url_for('customer.view_company', company_id=company_id))

@customer.route('/api/contacts/<int:contact_id>/add_action', methods=['POST'])
@permission_required('customer', 'create')
def add_action_api(contact_id):
    """通过API添加行动记录"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        company = contact.company
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        data = request.json
        # 验证必填字段
        if not data.get('communication'):
            return jsonify({'success': False, 'message': '沟通情况不能为空'}), 400
        if not data.get('date'):
            return jsonify({'success': False, 'message': '日期不能为空'}), 400
        # 获取项目ID，如果未选择则设为None
        project_id = data.get('project_id') or None
        try:
            # 解析日期，支持ISO格式
            action_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00')).date()
        except ValueError:
            # 尝试标准格式
            action_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        action = Action(
            date=action_date,
            contact_id=contact.id,
            company_id=company.id,
            project_id=project_id,
            communication=data['communication'],
            owner_id=current_user.id
        )
        db.session.add(action)
        db.session.commit()
        # 返回成功信息和新创建的行动记录信息
        return jsonify({
            'success': True, 
            'message': '行动记录添加成功',
            'data': {
                'id': action.id,
                'date': action.date.isoformat(),
                'contact_name': contact.name,
                'contact_id': contact.id,
                'company_name': company.company_name,
                'company_id': company.id,
                'project_id': action.project_id,
                'communication': action.communication,
                'owner_id': action.owner_id
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback_str = traceback.format_exc()
        print(f"添加行动记录出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/companies/<company_type>')
@permission_required('customer', 'view')
def api_companies_by_type(company_type):
    """API端点 - 根据类型获取企业列表"""
    try:
        # 获取用户可查看的企业
        query = get_viewable_data(Company, current_user)
        query = query.filter(Company.is_deleted == False)
        
        # 根据类型筛选企业
        type_mapping = {
            'user': ['end_user', 'customer'],
            'designer': ['design_institute', 'consultant'],
            'contractor': ['contractor', 'general_contractor'],
            'integrator': ['system_integrator', 'integrator'],
            'dealer': ['dealer', 'distributor']
        }
        
        if company_type in type_mapping:
            company_types = type_mapping[company_type]
            query = query.filter(Company.company_type.in_(company_types))
        
        companies = query.order_by(Company.company_name).all()
        
        # 格式化返回数据
        result = []
        for company in companies:
            result.append({
                'id': company.id,
                'name': company.company_name,
                'type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else '未指定',
                'is_readable': can_view_company(current_user, company)
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"获取企业列表失败: {str(e)}")
        return jsonify([])

@customer.route('/api/company/search')
@permission_required('customer', 'view')
def search_company_api():
    keyword = request.args.get('keyword', '').strip()
    if not keyword or len(keyword) < 1:
        return jsonify({'results': []})
    
    # 优化搜索查询，提高中文单字符匹配效率
    # 使用or_条件组合多个搜索条件，支持任意位置匹配
    from sqlalchemy import or_
    
    # 判断是否为单个中文字符（完整中文字符范围判断）
    is_single_chinese = len(keyword) == 1 and '\u4e00' <= keyword <= '\u9fff'
    
    # 构建搜索条件
    if is_single_chinese:
        # 中文单字符使用包含匹配
        search_condition = Company.company_name.contains(keyword)
    else:
        # 其他情况使用前缀匹配，效率更高
        search_condition = Company.company_name.ilike(f"%{keyword}%")
    
    # 执行查询
    all_matches = Company.query.filter(search_condition, Company.is_deleted == False).limit(15).all()
    
    # 获取用户有权限查看的公司
    user_authorized_companies = get_viewable_data(Company, current_user).all()
    authorized_ids = {c.id for c in user_authorized_companies}
    
    # 预加载所有公司拥有者信息，避免N+1查询问题
    owner_ids = [c.owner_id for c in all_matches if c.owner_id is not None]
    owners = {}
    if owner_ids:
        for user in User.query.filter(User.id.in_(owner_ids)).all():
            owners[user.id] = user
    
    results = []
    for c in all_matches:
        # 准备地区显示文本
        location = []
        if c.country:
            location.append(c.country)
        if c.region:
            location.append(c.region)
        location_text = " ".join(location)
        
        # 判断用户是否有权限查看/编辑该公司
        has_permission = c.id in authorized_ids
        
        # 获取拥有者信息
        owner_name = "未指定"
        if c.owner_id and c.owner_id in owners:
            owner = owners[c.owner_id]
            owner_name = owner.real_name or owner.username
        
        # 构建紧凑格式的显示文本：企业名称 | 国家 城市 | 拥有者真实姓名
        display_text = c.company_name
        if location_text:
            display_text += f" | {location_text}"
        display_text += f" | {owner_name}"
        
        result = {
            'id': c.id,
            'name': c.company_name,
            'display': display_text,
            'has_permission': has_permission,
            'region': c.region,
            'owner_name': owner_name
        }
        
        # 只有当用户有权限时才返回详细信息
        if has_permission:
            result.update({
                'country': c.country,
                'region': c.region,
                'address': c.address,
                'industry': c.industry,
                'company_type': c.company_type,
                'status': c.status or 'active',
                'notes': c.notes,
                'owner_id': c.owner_id
            })
        
        results.append(result)
    
    return jsonify({'results': results})

@customer.route('/api/contacts/search_by_name')
@permission_required('customer', 'view')
def search_contact_api():
    keyword = request.args.get('keyword', '').strip()
    if not keyword or len(keyword) < 1:
        return jsonify({'results': []})
    
    # 判断是否为单个中文字符（完整中文字符范围判断）
    is_single_chinese = len(keyword) == 1 and '\u4e00' <= keyword <= '\u9fff'
    
    # 构建搜索条件
    if is_single_chinese:
        # 中文单字符使用包含匹配
        search_condition = Contact.name.contains(keyword)
    else:
        # 其他情况使用模糊匹配
        search_condition = Contact.name.ilike(f"%{keyword}%")
    
    # 执行查询
    all_matches = Contact.query.filter(search_condition).limit(15).all()
    
    # 获取用户有权限查看的公司ID
    user_authorized_companies = get_viewable_data(Company, current_user).all()
    authorized_company_ids = {c.id for c in user_authorized_companies}
    
    results = []
    for contact in all_matches:
        # 预加载公司信息，避免N+1查询
        company = Company.query.filter_by(id=contact.company_id, is_deleted=False).first()
        if not company:
            continue
            
        # 判断用户是否有权限查看该联系人所属的公司
        can_view_enterprise = contact.company_id in authorized_company_ids
        
        # 获取地区信息用于显示
        location = []
        if company.region:
            location.append(company.region)
        location_text = ", ".join(location)
        
        result = {
            'id': contact.id,
            'name': contact.name,
            'company_id': company.id,
            'company_name': company.company_name,
            'display': f"{contact.name} ({company.company_name})",
            'position': contact.position or '',
            'department': contact.department or '',
            'can_view_enterprise': can_view_enterprise
        }
        
        results.append(result)
    
    return jsonify({'results': results})

@customer.route('/api/check-duplicates', methods=['POST'])
@permission_required('customer', 'create')
def check_duplicates():
    """检查企业名称重复"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 打印请求内容，帮助调试
        print(f"收到check-duplicates请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        company_names = data.get('company_names', [])
        
        # 确保company_names是一个列表
        if not isinstance(company_names, list):
            print(f"company_names不是列表: {company_names}")
            return jsonify({'success': False, 'message': 'company_names必须是列表'}), 400
        
        if not company_names:
            return jsonify({'success': False, 'message': '没有提供企业名称'}), 400
        
        # 检查列表中的每个元素是否为字符串
        for i, name in enumerate(company_names):
            if not isinstance(name, str):
                print(f"company_names中的元素[{i}]不是字符串: {name}")
                # 尝试转换为字符串
                try:
                    company_names[i] = str(name)
                except:
                    # 如果转换失败，则移除该元素
                    print(f"无法将元素[{i}]转换为字符串，已移除")
                    company_names[i] = ""
        
        # 过滤掉空字符串
        company_names = [name for name in company_names if name]
        
        if not company_names:
            return jsonify({'success': False, 'message': '没有有效的企业名称'}), 400
        
        print(f"过滤后的企业名称列表: {company_names}")
        
        # 获取所有现有企业名称
        existing_companies = Company.query.with_entities(Company.id, Company.company_name).filter(Company.is_deleted == False).all()
        existing_names = {company.company_name: company.id for company in existing_companies}
        
        conflicts = []
        for import_name in company_names:
            # 如果名称完全匹配
            if import_name in existing_names:
                conflicts.append({
                    'import_name': import_name,
                    'existing_name': import_name,
                    'existing_id': existing_names[import_name],
                    'similarity': 1.0
                })
                continue
            
            # 模糊匹配
            for existing_name, existing_id in existing_names.items():
                # 对于中文名称，使用较高的相似度阈值以减少错误匹配
                similarity = difflib.SequenceMatcher(None, import_name, existing_name).ratio()
                
                # 提高阈值，只有较高相似度或完全包含才判定为冲突
                if len(import_name) >= 3 and len(existing_name) >= 3:
                    # 提取相似部分，判断是否有连续的中文字符
                    blocks = difflib.SequenceMatcher(None, import_name, existing_name).get_matching_blocks()
                    
                    # 判断是否有从左到右的前缀匹配（优先考虑公司名称开头部分）
                    left_to_right_match = False
                    for block in blocks:
                        # 检查是否为左侧开始的匹配（import_name的起始位置或existing_name的起始位置）
                        if (block.a == 0 or block.b == 0) and block.size >= 3:
                            left_to_right_match = True
                            break
                    
                    # 找到连续的中文字符匹配
                    continuous_match = False
                    longest_match_size = 0
                    for block in blocks:
                        if block.size > longest_match_size:
                            longest_match_size = block.size
                        
                        # 对于4个以上的中文字符匹配，需要进一步判断
                        if block.size >= 4:
                            # 提取匹配部分的文本
                            import_substr = import_name[block.a:block.a+block.size]
                            existing_substr = existing_name[block.b:block.b+block.size]
                            
                            # 检查提取的子串是否含有常见的公司名称后缀（如"有限公司"、"股份"等）
                            common_suffixes = ["有限公司", "股份", "科技", "集团", "公司"]
                            contains_common_suffix = any(suffix in import_substr for suffix in common_suffixes) or \
                                                    any(suffix in existing_substr for suffix in common_suffixes)
                            
                            # 如果不包含常见后缀，则更可能是实质性匹配
                            if not contains_common_suffix:
                                continuous_match = True
                                break
                        
                        # 对于3个字符的匹配，只有在从左到右或相似度很高的情况下才考虑
                        elif block.size == 3 and (left_to_right_match or similarity > 0.75):
                            continuous_match = True
                            break
                    
                    # 检查是否一方完全包含另一方（处理简称情况），但忽略常见后缀
                    def normalize_for_import(name):
                        # 去除常见的公司后缀
                        suffixes = ["有限公司", "有限责任公司", "股份有限公司", "股份公司", "公司"]
                        normalized = name
                        for suffix in suffixes:
                            normalized = normalized.replace(suffix, "")
                        return normalized.strip()
                    
                    norm_import = normalize_for_import(import_name)
                    norm_existing = normalize_for_import(existing_name)
                    
                    name_contains = (norm_import in norm_existing or norm_existing in norm_import) and \
                                    min(len(norm_import), len(norm_existing)) >= 2  # 确保有意义的匹配
                    
                    # 或者整体相似度较高(提高到超过0.8)
                    high_similarity = similarity > 0.8
                    
                    # 前缀匹配给予更高权重
                    prefix_match = import_name.startswith(existing_name[:3]) or existing_name.startswith(import_name[:3])
                    
                    # 综合判断是否构成冲突
                    is_conflict = (continuous_match and (left_to_right_match or longest_match_size >= 4)) or \
                                  (name_contains and similarity > 0.6) or \
                                  high_similarity or \
                                  (prefix_match and similarity > 0.65)
                    
                    if is_conflict:
                        print(f"发现潜在冲突: '{import_name}' vs '{existing_name}', " 
                              f"相似度={similarity:.2f}, 连续匹配长度={longest_match_size}, "
                              f"从左到右匹配={left_to_right_match}, 名称包含={name_contains}")
                        
                        conflicts.append({
                            'import_name': import_name,
                            'existing_name': existing_name,
                            'existing_id': existing_id,
                            'similarity': similarity
                        })
        
        # 对于每个导入名称，只保留相似度最高的匹配项
        filtered_conflicts = {}
        for conflict in conflicts:
            import_name = conflict['import_name']
            if import_name not in filtered_conflicts or conflict['similarity'] > filtered_conflicts[import_name]['similarity']:
                filtered_conflicts[import_name] = conflict
        
        # 添加推荐操作字段
        for import_name, conflict in filtered_conflicts.items():
            # 根据相似度添加推荐操作：≥0.8推荐跳过，<0.8推荐添加为新用户
            if conflict['similarity'] >= 0.8:
                conflict['recommended_action'] = 'ignore'  # 建议跳过
            else:
                conflict['recommended_action'] = 'keep'    # 建议添加为新用户
        
        result = {
            'success': True,
            'conflicts': list(filtered_conflicts.values())
        }
        
        print(f"检查重复完成，返回结果: {len(filtered_conflicts)}条冲突")
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"检查重复出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/check-contact-duplicates', methods=['POST'])
@permission_required('customer', 'create')
def check_contact_duplicates():
    """检查联系人导入冲突"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        contacts = data.get('contacts', [])
        company_names = data.get('company_names', [])
        
        # 检查格式
        if not isinstance(contacts, list):
            return jsonify({'success': False, 'message': 'contacts必须是列表'}), 400
            
        if not isinstance(company_names, list):
            return jsonify({'success': False, 'message': 'company_names必须是列表'}), 400
        
        # 1. 检查公司是否存在
        company_not_found = []
        company_map = {}  # 公司名称到ID的映射
        
        # 查询所有公司
        all_companies = Company.query.filter_by(is_deleted=False).all()
        all_company_names = {company.company_name: company.id for company in all_companies}
        
        # 检查每个公司名称是否存在
        for company_name in company_names:
            if not company_name:
                continue
                
            if company_name not in all_company_names:
                # 记录未找到的公司
                not_found_contacts = [c for c in contacts if c.get('company_name') == company_name]
                for contact in not_found_contacts:
                    company_not_found.append({
                        'company_name': company_name,
                        'name': contact.get('name', '')
                    })
            else:
                # 记录公司ID映射，方便后续使用
                company_map[company_name] = all_company_names[company_name]
        
        # 2. 检查联系人冲突
        conflicts = []
        
        # 按公司分组
        for company_name, company_id in company_map.items():
            # 查询该公司的所有联系人
            existing_contacts = Contact.query.filter_by(company_id=company_id).all()
            existing_contacts_names = {contact.name.lower(): contact for contact in existing_contacts}
            
            # 检查导入联系人是否与已有联系人冲突
            for contact in contacts:
                if contact.get('company_name') != company_name or not contact.get('name'):
                    continue
                    
                contact_name = contact.get('name').lower()
                if contact_name in existing_contacts_names:
                    # 生成联系人冲突的唯一标识
                    contact_key = f"{company_id}_{contact_name}"
                    
                    # 记录冲突信息
                    conflict = {
                        'contact_key': contact_key,
                        'import_contact': contact,
                        'existing_contact': {
                            'id': existing_contacts_names[contact_name].id,
                            'name': existing_contacts_names[contact_name].name,
                            'company_id': company_id,
                            'company_name': company_name
                        }
                    }
                    conflicts.append(conflict)
        
        return jsonify({
            'success': True,
            'company_not_found': company_not_found,
            'conflicts': conflicts
        })
        
    except Exception as e:
        print(f"检查联系人冲突出错: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/import-contacts', methods=['POST'])
@permission_required('customer', 'create')
def import_contacts():
    """导入联系人数据"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        print(f"收到联系人导入请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
            
        contacts = data.get('contacts', [])
        conflict_actions = data.get('conflict_actions', {})
        owner_id = data.get('owner_id')
        action_records = data.get('action_records', [])
        
        # 确保contacts是列表
        if not isinstance(contacts, list):
            print(f"contacts不是列表: {contacts}")
            return jsonify({'success': False, 'message': 'contacts必须是列表'}), 400
        
        # 确保conflict_actions是字典
        if not isinstance(conflict_actions, dict):
            print(f"conflict_actions不是字典: {conflict_actions}")
            return jsonify({'success': False, 'message': 'conflict_actions必须是字典'}), 400
        
        # 验证归属账户是否存在
        owner = User.query.get(owner_id)
        if not owner:
            return jsonify({'success': False, 'message': '指定的归属账户不存在'}), 400
        
        # 取得所有公司信息，用于匹配
        companies = {company.company_name: company.id for company in Company.query.filter_by(is_deleted=False).all()}
        
        # 取得所有联系人信息，用于检查冲突
        all_contacts = {}
        for company_id in set(companies.values()):
            all_contacts[company_id] = {
                contact.name.lower(): contact
                for contact in Contact.query.filter_by(company_id=company_id).all()
            }
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []  # 添加错误详情列表
        contact_name_map = {}  # (name, company) -> contact_id
        for contact_data in contacts:
            company_name = contact_data.get('company_name', '')
            contact_name = contact_data.get('name', '')
            
            if not company_name or not contact_name:
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': '公司名称或联系人姓名为空'
                })
                continue
            
            # 查找公司ID
            if company_name not in companies:
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': f'公司"{company_name}"不存在于系统中'
                })
                continue
                
            company_id = companies[company_name]
            
            try:
                # 检查是否存在冲突
                contact_key = f"{company_id}_{contact_name.lower()}"
                if company_id in all_contacts and contact_name.lower() in all_contacts[company_id]:
                    # 有冲突的情况
                    action = conflict_actions.get(contact_key, 'keep')
                    
                    if action == 'keep':
                        # 跳过此联系人
                        skipped_count += 1
                        continue
                    
                    # 覆盖现有联系人
                    existing_contact = all_contacts[company_id][contact_name.lower()]
                    existing_contact.department = contact_data.get('department', '')
                    existing_contact.position = contact_data.get('position', '')
                    existing_contact.phone = contact_data.get('phone', '')
                    existing_contact.email = contact_data.get('email', '')
                    existing_contact.owner_id = owner_id  # 更新所有者
                    
                    # 处理创建时间
                    if 'created_at' in contact_data and contact_data['created_at']:
                        try:
                            created_at = datetime.fromisoformat(contact_data['created_at'].replace('Z', '+00:00'))
                            existing_contact.created_at = created_at
                        except (ValueError, TypeError):
                            pass
                            
                    # 更新时间设置为当前时间（导入时间）
                    existing_contact.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                    updated_count += 1
                    contact_name_map[(contact_name, company_name)] = existing_contact.id
                else:
                    # 新建联系人
                    new_contact = Contact(
                        company_id=company_id,
                        name=contact_name,
                        department=contact_data.get('department', ''),
                        position=contact_data.get('position', ''),
                        phone=contact_data.get('phone', ''),
                        email=contact_data.get('email', ''),
                        is_primary=False,  # 默认不是主要联系人
                        owner_id=owner_id
                    )
                    
                    # 处理创建时间
                    if 'created_at' in contact_data and contact_data['created_at']:
                        try:
                            created_at = datetime.fromisoformat(contact_data['created_at'].replace('Z', '+00:00'))
                            new_contact.created_at = created_at
                        except (ValueError, TypeError):
                            pass
                            
                    # 更新时间设置为当前时间（导入时间）
                    new_contact.updated_at = datetime.utcnow()
                    
                    db.session.add(new_contact)
                    db.session.commit()
                    imported_count += 1
                    contact_name_map[(contact_name, company_name)] = new_contact.id
                    
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': str(e)
                })
                print(f"导入联系人 {contact_name} 出错: {str(e)}")
                
        # 同步导入行动记录
        action_success = 0
        action_failed = 0
        for action in action_records:
            contact_name = action.get('contact_name', '')
            company_name = action.get('company_name', '')
            key = (contact_name, company_name)
            contact_id = contact_name_map.get(key)
            if not contact_id:
                action_failed += 1
                continue
            # 匹配公司ID
            company_id = companies.get(company_name)
            if not company_id:
                action_failed += 1
                continue
            # 匹配项目ID
            project_id = None
            if action.get('project_name'):
                project = Project.query.filter_by(project_name=action['project_name']).first()
                if project:
                    project_id = project.id
            # 匹配owner_id
            owner_id_action = owner_id
            if action.get('owner_name'):
                user = User.query.filter((User.real_name == action['owner_name']) | (User.username == action['owner_name'])).first()
                if user:
                    owner_id_action = user.id
            # 解析日期
            try:
                action_date = None
                if action.get('date'):
                    try:
                        action_date = datetime.fromisoformat(str(action['date']).replace('Z', '+00:00')).date()
                    except Exception:
                        action_date = datetime.strptime(str(action['date']), '%Y-%m-%d').date()
                else:
                    action_date = datetime.utcnow().date()
            except Exception:
                action_date = datetime.utcnow().date()
            try:
                new_action = Action(
                    date=action_date,
                    contact_id=contact_id,
                    company_id=company_id,
                    project_id=project_id,
                    communication=action.get('communication', ''),
                    owner_id=owner_id_action,
                    created_at=datetime.combine(action_date, datetime.min.time())
                )
                db.session.add(new_action)
                db.session.commit()
                # 新增：每次添加行动记录后自动刷新客户活跃度和更新时间
                company.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
                update_active_status(company)
                db.session.commit()
                action_success += 1
            except Exception as e:
                db.session.rollback()
                action_failed += 1
                
        # 记录导入日志
        import_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'user_name': current_user.username,
            'owner_id': owner_id,
            'owner_name': owner.username,
            'total': len(contacts),
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'error': error_count,
            'notFoundCount': len([c for c in contacts if c.get('company_name', '') not in companies]),
            'error_details': error_details
        }
        
        return jsonify({
            'success': True,
            'message': f'导入完成，新增: {imported_count}，更新: {updated_count}，跳过: {skipped_count}，错误: {error_count}',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'error': error_count,
                'notFoundCount': import_log['notFoundCount'],
                'total': len(contacts),
                'log': import_log,
                'error_details': error_details,
                'action_import_result': {
                    'success': action_success,
                    'failed': action_failed
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"导入联系人数据出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/import', methods=['POST'])
@permission_required('customer', 'create')
def import_customers():
    """导入客户数据"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        print(f"收到导入请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
            
        customers = data.get('customers', [])
        conflict_actions = data.get('conflict_actions', {})
        owner_id = data.get('owner_id')
        
        # 确保customers是列表
        if not isinstance(customers, list):
            print(f"customers不是列表: {customers}")
            return jsonify({'success': False, 'message': 'customers必须是列表'}), 400
        
        # 确保conflict_actions是字典
        if not isinstance(conflict_actions, dict):
            print(f"conflict_actions不是字典: {conflict_actions}")
            return jsonify({'success': False, 'message': 'conflict_actions必须是字典'}), 400
            
        # 对导入数据进行去重，确保每个公司名称只出现一次
        import_name_set = set()
        unique_customers = []
        
        for customer in customers:
            if isinstance(customer, dict) and customer.get('company_name'):
                company_name = customer['company_name'].strip()
                if company_name and company_name not in import_name_set:
                    import_name_set.add(company_name)
                    unique_customers.append(customer)
                else:
                    print(f"忽略重复的企业名称: {company_name}")
        
        print(f"去重后的导入数据: {len(unique_customers)}/{len(customers)} 条记录")
        
        # 使用去重后的数据
        customers = unique_customers
        
        # 清理和验证客户数据
        valid_customers = []
        invalid_customers = []  # 存储无效的客户数据及原因
        for i, customer in enumerate(customers):
            if not isinstance(customer, dict):
                print(f"客户数据[{i}]不是字典: {customer}")
                invalid_customers.append({
                    'record': {'index': i, 'data': str(customer)[:100]},  # 截取前100个字符避免过长
                    'reason': '数据格式错误，不是有效的对象'
                })
                continue
                
            # 确保必要字段存在且类型正确
            if 'company_name' not in customer or not customer['company_name']:
                print(f"客户数据[{i}]缺少company_name字段")
                invalid_customers.append({
                    'record': customer,
                    'reason': '缺少企业名称字段或企业名称为空'
                })
                continue
                
            # 确保所有字符串字段的值都是字符串，并且不是'none'
            for field in ['company_name', 'country', 'region', 'address', 'company_type', 'status']:
                if field in customer and customer[field] is not None:
                    if not isinstance(customer[field], str):
                        try:
                            customer[field] = str(customer[field])
                        except:
                            customer[field] = ""
                            invalid_customers.append({
                                'record': {'company_name': customer.get('company_name', '未知'), 'field': field},
                                'reason': f'字段 {field} 无法转换为字符串'
                            })
                    
                    # 如果值是'none'或'None'，则设置为空字符串
                    if customer[field].lower() == 'none':
                        customer[field] = ""
            
            # 处理创建时间
            if 'created_at' in customer and customer['created_at']:
                if isinstance(customer['created_at'], str):
                    try:
                        print(f"尝试解析创建时间: {customer['created_at']}")
                        # 处理ISO 8601格式的日期字符串，去掉Z后添加时区信息
                        if customer['created_at'].endswith('Z'):
                            customer['created_at'] = customer['created_at'].replace('Z', '+00:00')
                        
                        # 尝试从ISO格式解析
                        try:
                            customer['created_at'] = datetime.fromisoformat(customer['created_at'])
                            print(f"成功从ISO格式解析: {customer['created_at']}")
                        except ValueError:
                            # 如果fromisoformat失败，尝试strptime
                            formats = [
                                '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO 8601 with microseconds and timezone
                                '%Y-%m-%d %H:%M:%S',       # Standard datetime
                                '%Y-%m-%d',                # Just date
                                '%d/%m/%Y',                # DD/MM/YYYY
                                '%m/%d/%Y',                # MM/DD/YYYY
                            ]
                            
                            parsed = False
                            for fmt in formats:
                                try:
                                    customer['created_at'] = datetime.strptime(customer['created_at'], fmt)
                                    print(f"使用格式 {fmt} 成功解析: {customer['created_at']}")
                                    parsed = True
                                    break
                                except ValueError:
                                    continue
                            
                            if not parsed:
                                print(f"无法解析创建时间: {customer['created_at']}，使用当前时间")
                                customer['created_at'] = datetime.utcnow()
                                invalid_customers.append({
                                    'record': {'company_name': customer.get('company_name', '未知')},
                                    'reason': '创建时间格式不正确'
                                })
                    except Exception as e:
                        print(f"创建时间解析异常: {e}")
                        customer['created_at'] = datetime.utcnow()
                        invalid_customers.append({
                            'record': {'company_name': customer.get('company_name', '未知')},
                            'reason': f'创建时间格式错误: {str(e)}'
                        })
                elif not isinstance(customer['created_at'], datetime):
                    print(f"创建时间不是字符串也不是datetime对象: {type(customer['created_at'])}")
                    customer['created_at'] = datetime.utcnow()
                    invalid_customers.append({
                        'record': {'company_name': customer.get('company_name', '未知')},
                        'reason': '创建时间格式不正确'
                    })
            else:
                print("未提供创建时间，使用当前时间")
                customer['created_at'] = datetime.utcnow()
                
            valid_customers.append(customer)
        
        if not valid_customers:
            return jsonify({
                'success': False, 
                'message': '没有有效的客户数据', 
                'data': {'error_details': invalid_customers}
            }), 400
            
        print(f"有效客户数据: {len(valid_customers)}条")
        
        if not owner_id:
            return jsonify({
                'success': False, 
                'message': '没有提供归属账户', 
                'data': {'error_details': invalid_customers}
            }), 400
        
        # 验证归属账户是否存在
        owner = User.query.get(owner_id)
        if not owner:
            return jsonify({
                'success': False, 
                'message': '指定的归属账户不存在', 
                'data': {'error_details': invalid_customers}
            }), 400
        
        # 获取现有企业列表(用于检查重复)
        existing_companies = {c.company_name: c for c in Company.query.filter(Company.is_deleted == False).all()}
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []  # 添加错误详情列表
        
        # 合并前面验证阶段的错误信息
        error_details.extend(invalid_customers)
        
        for customer_data in valid_customers:
            company_name = customer_data.get('company_name')
            if not company_name:
                error_count += 1
                error_details.append({
                    'record': customer_data,
                    'reason': '企业名称为空'
                })
                continue
            
            try:
                # 检查是否存在冲突处理决策
                action = conflict_actions.get(company_name, 'keep')
                
                # 如果存在同名企业
                if company_name in existing_companies:
                    if action == 'ignore':
                        # 忽略该条数据
                        skipped_count += 1
                        print(f"忽略已存在的企业: {company_name}")
                        continue
                    elif action == 'override':
                        # 更新现有企业
                        company = existing_companies[company_name]
                        
                        # 确保更新值不是'none'或'None'，使用None而不是空字符串
                        if 'country' in customer_data:
                            if customer_data['country'] and customer_data['country'].lower() != 'none':
                                company.country = customer_data['country']
                            elif customer_data['country'] == '' or customer_data['country'].lower() == 'none':
                                company.country = None
                        
                        # 导入表中的城市映射到省份
                        if 'region' in customer_data:
                            if customer_data['region'] and customer_data['region'].lower() != 'none':
                                company.region = customer_data['region']
                            elif customer_data['region'] == '' or customer_data['region'].lower() == 'none':
                                company.region = None
                        
                        if 'address' in customer_data:
                            if customer_data['address'] and customer_data['address'].lower() != 'none':
                                company.address = customer_data['address']
                            elif customer_data['address'] == '' or customer_data['address'].lower() == 'none':
                                company.address = None
                        
                        if 'company_type' in customer_data:
                            if customer_data['company_type'] and customer_data['company_type'].lower() != 'none':
                                company.company_type = customer_data['company_type']
                            elif customer_data['company_type'] == '' or customer_data['company_type'].lower() == 'none':
                                company.company_type = None
                        
                        # 处理备注字段
                        if 'notes' in customer_data:
                            if not customer_data['notes'] or customer_data['notes'].lower() == 'none':
                                company.notes = None
                            else:
                                company.notes = customer_data['notes']
                        
                        # 保留原始创建时间（如果Excel中有指定且有效，则使用；否则保留数据库中现有的）
                        if 'created_at' in customer_data and customer_data['created_at'] and isinstance(customer_data['created_at'], datetime):
                            print(f"覆盖记录 - 设置创建时间: {customer_data['created_at']}")
                            company.created_at = customer_data['created_at']
                        
                        # 更新时间设置为当前时间（导入时间）
                        company.updated_at = datetime.utcnow()
                        print(f"覆盖记录 - 设置更新时间: {company.updated_at}")
                        
                        company.owner_id = owner_id  # 更新所有者
                        db.session.commit()
                        updated_count += 1
                        
                        # 标记此企业已处理，防止重复导入
                        existing_companies.pop(company_name, None)
                        continue
                    else:  # action == 'keep'
                        # 克隆为新记录，但使用不同名称
                        company_name = f"{company_name}_导入_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        print(f"发现同名企业，重命名为: {company_name}")
                
                # 创建新企业(action == 'keep'或不存在冲突)
                company = Company(
                    company_name=company_name,
                    country=customer_data.get('country', '') if customer_data.get('country') and customer_data.get('country').lower() != 'none' else None,
                    region=customer_data.get('region', '') if customer_data.get('region') and customer_data.get('region').lower() != 'none' else None,  # 导入表中的城市映射到省份
                    address=customer_data.get('address', '') if customer_data.get('address') and customer_data.get('address').lower() != 'none' else None,
                    company_type=customer_data.get('company_type', '') if customer_data.get('company_type') and customer_data.get('company_type').lower() != 'none' else None,
                    status=customer_data.get('status', '活跃') if customer_data.get('status') and customer_data.get('status').lower() != 'none' else '活跃',
                    owner_id=owner_id  # 设置所有者
                )
                
                # 处理备注字段 - 如果是"none"或"None"则设为空字符串
                notes = customer_data.get('notes', '')
                if not notes or notes.lower() == 'none':
                    notes = None
                company.notes = notes
                
                # 设置创建时间和更新时间
                # 保留原始创建时间
                if 'created_at' in customer_data and customer_data['created_at']:
                    print(f"设置创建时间: {customer_data['created_at']}")
                    company.created_at = customer_data['created_at']
                
                # 更新时间设置为当前时间（导入时间）
                company.updated_at = datetime.utcnow()
                print(f"设置更新时间: {company.updated_at}")
                
                db.session.add(company)
                db.session.commit()
                imported_count += 1
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_message = str(e)
                print(f"导入企业 {company_name} 时出错: {error_message}")
                error_details.append({
                    'record': {'company_name': company_name},
                    'reason': error_message
                })
        
        # 记录导入日志
        import_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'user_name': current_user.username,
            'owner_id': owner_id,
            'owner_name': owner.username,
            'total': len(valid_customers),
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'error': error_count,
            'error_details': error_details  # 添加错误详情
        }
        
        # 这里可以实现导入日志的保存逻辑
        # 例如保存到数据库或日志文件
        
        return jsonify({
            'success': True,
            'message': f'导入完成，新增: {imported_count}，更新: {updated_count}，跳过: {skipped_count}，错误: {error_count}',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'error': error_count,
                'log': import_log,
                'error_details': error_details  # 添加错误详情
            }
        })
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"导入客户数据出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/batch-delete', methods=['POST'])
@permission_required('customer', 'delete')
def batch_delete_companies():
    """批量删除企业API"""
    try:
        # 只要有customer.delete权限即可批量删除，但只能删除自己有权限的企业
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        company_ids = data.get('company_ids', [])
        
        if not company_ids or not isinstance(company_ids, list):
            return jsonify({'success': False, 'message': '缺少要删除的企业ID列表'}), 400
        
        # 转换为整数列表
        try:
            company_ids = [int(id) for id in company_ids]
        except ValueError:
            return jsonify({'success': False, 'message': '企业ID必须是整数'}), 400
        
        # 获取要删除的企业记录
        companies = Company.query.filter(Company.id.in_(company_ids), Company.is_deleted == False).all()
        
        # 检查操作人是否有权限删除这些企业，未授权的企业自动跳过
        unauthorized_companies = []
        deletable_companies = []
        companies_with_contacts = []  # === 新增：记录有联系人的客户 ===
        companies_with_projects = []  # === 新增：记录被项目引用的客户 ===
        
        for company in companies:
            if can_edit_data(company, current_user):
                # === 新增：检查是否存在关联的联系人 ===
                existing_contacts = Contact.query.filter_by(company_id=company.id).all()
                if existing_contacts:
                    contact_names = [contact.name for contact in existing_contacts]
                    companies_with_contacts.append(f"{company.company_name}({len(existing_contacts)}个联系人)")
                    continue
                
                # === 新增：检查是否有项目引用该客户 ===
                from app.models.project import Project
                related_projects = Project.query.filter(
                    db.or_(
                        Project.end_user == company.company_name,
                        Project.design_issues == company.company_name,
                        Project.contractor == company.company_name,
                        Project.system_integrator == company.company_name,
                        Project.dealer == company.company_name
                    )
                ).all()
                
                if related_projects:
                    companies_with_projects.append(f"{company.company_name}({len(related_projects)}个项目)")
                    continue
                
                # 如果通过所有检查，添加到可删除列表
                deletable_companies.append(company)
            else:
                unauthorized_companies.append(company.company_name)
                
        if not deletable_companies and (companies_with_contacts or companies_with_projects):
            error_messages = []
            if companies_with_contacts:
                error_messages.append(f'以下客户存在联系人：{", ".join(companies_with_contacts)}')
            if companies_with_projects:
                error_messages.append(f'以下客户被项目引用：{", ".join(companies_with_projects)}')
            
            return jsonify({
                'success': False, 
                'message': f'批量删除失败：{"; ".join(error_messages)}。请先处理相关数据后再删除。'
            }), 400
        
        deleted_count = 0
        errors = []
        
        # 开始事务
        try:
            for company in deletable_companies:
                # === 新增：删除客户审批实例和相关审批记录 ===
                from app.models.approval import ApprovalInstance, ApprovalRecord
                customer_approvals = ApprovalInstance.query.filter_by(
                    object_type='customer', 
                    object_id=company.id
                ).all()
                
                if customer_approvals:
                    for approval in customer_approvals:
                        # 删除审批记录
                        records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                        for record in records:
                            db.session.delete(record)
                        # 删除审批实例
                        db.session.delete(approval)
                
                # 找到与企业相关的所有行动记录
                related_actions = Action.query.filter_by(company_id=company.id).all()
                
                # 删除所有相关的行动记录（包括其回复，通过级联删除）
                for action in related_actions:
                    db.session.delete(action)
                
                # === 新增：处理inventory相关记录 ===
                from app.models.inventory import Inventory, InventoryTransaction, Settlement, SettlementDetail, PurchaseOrder
                
                # 删除库存变动记录
                inventories = Inventory.query.filter_by(company_id=company.id).all()
                for inventory in inventories:
                    # 删除库存变动记录
                    InventoryTransaction.query.filter_by(inventory_id=inventory.id).delete()
                    # 删除结算明细记录
                    SettlementDetail.query.filter_by(inventory_id=inventory.id).delete()
                    # 删除库存记录
                    db.session.delete(inventory)
                
                # 删除结算记录
                Settlement.query.filter_by(company_id=company.id).delete()
                
                # 删除订货单记录
                PurchaseOrder.query.filter_by(company_id=company.id).delete()
                
                # === 新增：处理pricing和settlement相关记录 ===
                from app.models.pricing_order import PricingOrder, SettlementOrder, PricingOrderDetail, SettlementOrderDetail, PricingOrderApprovalRecord
                
                # 删除批价单相关记录
                pricing_orders = PricingOrder.query.filter(
                    db.or_(
                        PricingOrder.dealer_id == company.id,
                        PricingOrder.distributor_id == company.id
                    )
                ).all()
                for po in pricing_orders:
                    # 删除批价单明细
                    PricingOrderDetail.query.filter_by(pricing_order_id=po.id).delete()
                    # 删除结算单明细
                    SettlementOrderDetail.query.filter_by(pricing_order_id=po.id).delete()
                    # 删除审批记录
                    PricingOrderApprovalRecord.query.filter_by(pricing_order_id=po.id).delete()
                    # 删除批价单
                    db.session.delete(po)
                
                # 删除结算单记录
                settlement_orders = SettlementOrder.query.filter(
                    db.or_(
                        SettlementOrder.distributor_id == company.id,
                        SettlementOrder.dealer_id == company.id
                    )
                ).all()
                for so in settlement_orders:
                    db.session.delete(so)
                
                # 删除企业（会级联删除联系人）
                db.session.delete(company)
                deleted_count += 1
            
            # 提交事务
            db.session.commit()
            msg = f'成功删除{deleted_count}个企业'
            if unauthorized_companies:
                msg += f'，无权删除: {", ".join(unauthorized_companies)}'
            if companies_with_contacts:
                msg += f'，跳过有联系人的企业: {", ".join(companies_with_contacts)}'
            if companies_with_projects:
                msg += f'，跳过被项目引用的企业: {", ".join(companies_with_projects)}'
            return jsonify({
                'success': True,
                'deleted_count': deleted_count,
                'message': msg
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'删除过程中出错: {str(e)}'
            }), 500
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"批量删除企业出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/actions/<int:action_id>/delete', methods=['POST'])
@permission_required('customer', 'delete')
def delete_action_api(action_id):
    """通过API删除行动记录"""
    current_app.logger.info(f"开始删除行动记录，ID: {action_id}")
    try:
        action = Action.query.get_or_404(action_id)
        
        # 检查权限：只有行动记录的创建者和管理员可以删除
        if action.owner_id != current_user.id and current_user.role != 'admin':
            current_app.logger.warning(f"用户 {current_user.id} 尝试删除不属于他的行动记录 {action_id}")
            return jsonify({
                'success': False, 
                'message': '您没有权限删除此行动记录'
            }), 403
        
        # 记录相关信息用于返回
        contact_id = action.contact_id
        company_id = action.company_id
        
        # 删除行动记录
        db.session.delete(action)
        db.session.commit()
        
        current_app.logger.info(f"行动记录 {action_id} 已成功删除")
        
        # 返回简单的成功响应
        response = jsonify({
            'success': True,
            'message': '行动记录已成功删除',
            'data': {
                'contact_id': contact_id,
                'company_id': company_id
            }
        })
        
        # 添加必要的响应头
        response.headers['Content-Type'] = 'application/json'
        return response, 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback_str = traceback.format_exc()
        current_app.logger.error(f"删除行动记录出错: {str(e)}\n{traceback_str}")
        return jsonify({
            'success': False, 
            'message': f'服务器处理请求时出错: {str(e)}'
        }), 500

@customer.route('/contacts/<int:contact_id>/view')
@permission_required('customer', 'view')
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if not can_view_contact(current_user, contact):
        flash('您没有权限查看此联系人信息', 'danger')
        return redirect(url_for('customer.list_companies'))
    company = contact.company
    actions = Action.query.filter_by(contact_id=contact.id).order_by(Action.created_at.desc()).all()
    owner_ids = [action.owner_id for action in actions if action.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for action in actions:
            if action.owner_id and action.owner_id in owners:
                action.owner = owners[action.owner_id]
    # 传递可选新拥有人
    all_users = []
    if current_user.role == 'admin':
        all_users = User.query.all()
    elif getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director':
        all_users = User.query.filter(
            or_(User.role == 'admin', User._is_active == True),
            User.department == current_user.department
        ).all()
    else:
        all_users = User.query.filter(User.id.in_([current_user.id, contact.owner_id])).all()
    if not all_users:
        all_users = User.query.filter(User.id.in_([current_user.id, contact.owner_id])).all()
    # 计算是否有权限显示修改按钮
    has_change_owner_permission = False
    if current_user.role == 'admin':
        has_change_owner_permission = True
    elif (getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director') and contact.owner and hasattr(contact.owner, 'department') and contact.owner.department == current_user.department:
        has_change_owner_permission = True
    
    # 生成用户树状数据
    from app.utils.user_helpers import generate_user_tree_data
    user_tree_data = None
    if has_change_owner_permission:
        filter_by_dept = current_user.role != 'admin'
        user_tree_data = generate_user_tree_data(filter_by_department=filter_by_dept)
    
    return render_template('customer/contact_view.html', contact=contact, company=company, actions=actions,
                          all_users=all_users,
                          has_change_owner_permission=has_change_owner_permission,
                          user_tree_data=user_tree_data,
                          COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options(),
                          COUNTRY_OPTIONS=get_country_options())

@customer.route('/<int:company_id>/add_action', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_action_for_company(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    # 允许为所有有权限的联系人添加行动记录
    all_contacts = Contact.query.filter_by(company_id=company_id).all()
    contacts = [c for c in all_contacts if can_view_contact(current_user, c)]
    projects = Project.query.filter(
        or_(
            Project.end_user == company.company_name,
            Project.design_issues.like(f'%{company.company_name}%'),
            Project.contractor == company.company_name,
            Project.system_integrator == company.company_name,
            Project.dealer == company.company_name
        )
    ).all()
    selected_contact = None
    contact_actions = []
    contact_id = request.args.get('contact_id') if request.method == 'GET' else request.form.get('contact_id')
    if request.method == 'POST':
        # 只能为有权限的联系人添加
        if contact_id:
            contact = Contact.query.get(contact_id)
            if not contact or not can_view_contact(current_user, contact):
                flash('您没有权限为该联系人添加跟进记录', 'danger')
                return redirect(url_for('customer.view_company', company_id=company_id))
        project_id = request.form.get('project_id') or None
        communication = request.form.get('communication')
        date = request.form.get('date')
        if not communication or not date:
            flash('请填写所有必填项', 'danger')
        else:
            action = Action(
                date=datetime.strptime(date, '%Y-%m-%d'),
                contact_id=contact_id if contact_id else None,
                company_id=company_id,
                project_id=project_id,
                communication=communication,
                owner_id=current_user.id
            )
            db.session.add(action)
            db.session.commit()
            # 新增：每次添加行动记录后自动刷新客户活跃度和更新时间
            company.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            update_active_status(company)
            db.session.commit()
            flash('行动记录添加成功！', 'success')
            return redirect(url_for('customer.view_company', company_id=company_id))
    if contact_id:
        selected_contact = Contact.query.get(contact_id)
        contact_actions = Action.query.filter_by(contact_id=contact_id).order_by(Action.created_at.desc()).all()
    return render_template('customer/add_action_for_company.html', company=company, contacts=contacts, projects=projects, selected_contact=selected_contact, contact_actions=contact_actions,
                          COMPANY_TYPE_OPTIONS=get_company_type_options(),
                          INDUSTRY_OPTIONS=get_industry_options(),
                          STATUS_OPTIONS=get_status_options(),
                          COUNTRY_OPTIONS=get_country_options()) 
@customer.route('/<int:company_id>/update_sharing', methods=['POST'])
@permission_required('customer', 'edit')
def update_company_sharing(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    if not can_edit_company_sharing(current_user, company):
        flash('您没有权限编辑此客户的共享设置', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    shared_with_users = request.form.get('shared_with_users', '')
    if isinstance(shared_with_users, str):
        shared_with_users = [uid for uid in shared_with_users.split(',') if uid.strip()]
    # 兼容老的getlist方式
    if not shared_with_users:
        shared_with_users = request.form.getlist('shared_with_users')
    share_contacts = 'share_contacts' in request.form
    company.shared_with_users = [int(uid) for uid in shared_with_users]
    company.share_contacts = share_contacts
    db.session.commit()
    flash('客户共享设置已更新', 'success')
    return redirect(url_for('customer.view_company', company_id=company_id))

@customer.route('/<int:company_id>/change_owner', methods=['POST'])
@permission_required('customer', 'edit')
def change_company_owner(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
    if not can_change_company_owner(current_user, company):
        flash('您没有权限修改该客户的拥有人', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash('请选择新的拥有人', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    from app.models.user import User
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash('新拥有人不存在', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    company.owner_id = new_owner_id
    # 同步更新该客户下所有联系人的owner_id为新拥有人
    contacts = company.contacts
    for contact in contacts:
        contact.owner_id = new_owner_id
    db.session.commit()
    flash('客户拥有人及所有联系人拥有人已更新', 'success')
    return redirect(url_for('customer.view_company', company_id=company_id))

@customer.route('/contacts/<int:contact_id>/change_owner', methods=['POST'])
@permission_required('customer', 'edit')
def change_contact_owner(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    company = contact.company
    # 权限判断：管理员或本部门负责人可操作
    if not (current_user.role == 'admin' or (getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director') and contact.owner and hasattr(contact.owner, 'department') and contact.owner.department == current_user.department):
        flash('您没有权限修改该联系人的拥有人', 'danger')
        return redirect(url_for('customer.view_contact', contact_id=contact_id))
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash('请选择新的拥有人', 'danger')
        return redirect(url_for('customer.view_contact', contact_id=contact_id))
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash('新拥有人不存在', 'danger')
        return redirect(url_for('customer.view_contact', contact_id=contact_id))
    contact.owner_id = new_owner_id
    db.session.commit()
    flash('联系人拥有人已更新', 'success')
    return redirect(url_for('customer.view_contact', contact_id=contact_id))

# 获取行动记录的所有回复（树形结构）
@customer.route('/action/<int:action_id>/replies')
@login_required
@permission_required('customer', 'view')
def get_action_replies(action_id):
    """通过API获取行动记录的所有回复（树形结构）"""
    action = Action.query.get_or_404(action_id)
    from app.models.action import ActionReply
    
    replies = ActionReply.query.filter_by(action_id=action_id, parent_reply_id=None).order_by(ActionReply.created_at.asc()).all()
    def build_tree(reply):
        return {
            'id': reply.id,
            'content': reply.content,
            'owner': reply.owner.real_name or reply.owner.username,
            'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            'can_delete': (current_user.id == reply.owner_id or current_user.role == 'admin'),
            'children': [build_tree(child) for child in reply.children]
        }
    return jsonify([build_tree(r) for r in replies])

# 添加回复
@customer.route('/action/<int:action_id>/reply', methods=['POST'])
@login_required
@permission_required('customer', 'create')
def add_action_reply(action_id):
    """通过API添加行动记录回复"""
    action = Action.query.get_or_404(action_id)
    from app.models.action import ActionReply
    
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_reply_id = data.get('parent_reply_id')
    if not content:
        return jsonify({'success': False, 'message': '回复内容不能为空'}), 400
    
    reply = ActionReply(
        action_id=action_id,
        parent_reply_id=parent_reply_id,
        content=content,
        owner_id=current_user.id
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({'success': True})

# 删除回复
@customer.route('/action/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
@permission_required('customer', 'delete')
def delete_action_reply(reply_id):
    """通过API删除行动记录回复"""
    from app.models.action import ActionReply
    reply = ActionReply.query.get_or_404(reply_id)
    if reply.owner_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'message': '无权删除此回复'}), 403
    db.session.delete(reply)
    db.session.commit()
    return jsonify({'success': True})

@customer.route('/i18n-demo')
@login_required
@permission_required('customer', 'view')
def i18n_demo():
    """国际化演示页面"""
    from app.utils.i18n import get_current_language
    from app.utils.country_names import get_country_names
    
    # 获取当前语言
    current_language = get_current_language()
    
    # 获取国家名称映射
    country_names = get_country_names()
    
    # 示例客户数据
    sample_customer = {
        'company_name': 'ABC科技有限公司',
        'industry': 'technology',
        'status': 'active',
        'country': 'CN',
        'created_at': datetime.now()
    }
    
    return render_template('customer/i18n_demo.html', 
                         current_language=current_language,
                         country_names=country_names,
                         sample_customer=sample_customer,
                         INDUSTRY_OPTIONS=get_industry_options(),
                         STATUS_OPTIONS=get_status_options())

@customer.route('/api/available_accounts', methods=['GET'])
@login_required
@permission_required('customer', 'view')
def get_available_accounts_api():
    """获取可用于客户筛选的账户列表"""
    try:
        from app.models.user import User
        
        # 获取当前用户可以查看的用户ID列表
        viewable_user_ids = current_user.get_viewable_user_ids()
        
        # 查询这些用户的信息
        users = User.query.filter(User.id.in_(viewable_user_ids)).all()
        
        accounts = []
        for user in users:
            accounts.append({
                'id': user.id,
                'name': user.real_name or user.username,
                'is_current_user': user.id == current_user.id
            })
        
        # 按是否为当前用户排序，当前用户排在前面
        accounts.sort(key=lambda x: (not x['is_current_user'], x['name']))
        
        return jsonify({
            'success': True,
            'data': accounts
        })
        
    except Exception as e:
        current_app.logger.error(f"获取可用账户列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取可用账户列表失败: {str(e)}'
        }), 500

# ==================== 客户合并功能 ====================

@customer.route('/merge-tool')
@login_required
@permission_required('customer', 'create')
def customer_merge_tool():
    """智能客户合并工具页面（仅管理员可访问）"""
    if current_user.role != 'admin':
        flash(_('只有管理员可以使用客户合并工具'), 'error')
        return redirect(url_for('customer.list_companies'))
    
    return render_template('customer/merge_tool_optimized.html')

@customer.route('/api/debug-normalize', methods=['GET'])
@login_required
@permission_required('customer', 'create')
def debug_normalize():
    """调试名称标准化 - 检查特定客户名称的标准化结果"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
    
    try:
        search_name = request.args.get('name', '')
        if not search_name:
            return jsonify({'success': False, 'message': '请提供要检查的客户名称'}), 400
        
        # 查找包含该名称的所有客户
        companies = Company.query.filter(
            Company.company_name.ilike(f'%{search_name}%'),
            Company.is_deleted == False
        ).all()
        
        debug_results = []
        normalized_groups = {}
        
        for company in companies:
            normalized = normalize_company_name(company.company_name)
            debug_results.append({
                'id': company.id,
                'original_name': company.company_name,
                'normalized_name': normalized,
                'name_length': len(company.company_name),
                'normalized_length': len(normalized),
                'owner': company.owner.real_name if company.owner else None,
                'created_at': company.created_at.strftime('%Y-%m-%d') if company.created_at else None,
                'char_codes': [ord(c) for c in company.company_name],
                'is_deleted': company.is_deleted
            })
            
            # 按标准化名称分组
            if normalized not in normalized_groups:
                normalized_groups[normalized] = []
            normalized_groups[normalized].append(company)
        
        # 找出重复的标准化名称
        duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}
        
        # 特别测试相似度计算
        similarity_tests = []
        if len(companies) > 1:
            for i, company1 in enumerate(companies):
                for j, company2 in enumerate(companies):
                    if i >= j:
                        continue
                    
                    norm1 = normalize_company_name(company1.company_name)
                    norm2 = normalize_company_name(company2.company_name)
                    
                    # 计算相似度（使用与find_similar_companies相同的逻辑）
                    if norm1 == norm2:
                        similarity = 1.0
                    elif len(norm1) < 3 or len(norm2) < 3:
                        similarity = 0
                    else:
                        similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
                    
                    similarity_tests.append({
                        'company1_id': company1.id,
                        'company1_name': company1.company_name,
                        'company2_id': company2.id,
                        'company2_name': company2.company_name,
                        'normalized1': norm1,
                        'normalized2': norm2,
                        'similarity': similarity,
                        'would_match': similarity > 0.85
                    })
        
        return jsonify({
            'success': True,
            'search_name': search_name,
            'total_found': len(companies),
            'companies': debug_results,
            'duplicates': {
                k: [{'id': c.id, 'name': c.company_name} for c in v] 
                for k, v in duplicates.items()
            },
            'similarity_tests': similarity_tests,
            'matching_threshold': 0.85
        })
        
    except Exception as e:
        current_app.logger.error(f"调试标准化失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'调试失败: {str(e)}'
        }), 500

@customer.route('/api/detect-duplicates', methods=['GET'])
@login_required
@permission_required('customer', 'create')
def detect_duplicates():
    """检测重复客户"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
    
    # 检查是否请求进度信息
    check_progress = request.args.get('progress') == 'true'
    if check_progress:
        return detect_duplicates_with_progress()
    
    # 原有的快速检测逻辑（保持向后兼容）
    return detect_duplicates_simple()

def detect_duplicates_simple():
    """简单的重复检测（原有逻辑）"""
    
    try:
        current_app.logger.info("开始检测重复客户...")
        
        # 获取所有公司
        companies = Company.query.filter_by(is_deleted=False).all()
        current_app.logger.info(f"检测重复客户: 找到 {len(companies)} 个未删除的公司")
        
        if not companies:
            return jsonify({
                'success': True,
                'data': []
            })
        
        # 按名称分组检测重复
        name_groups = {}
        for company in companies:
            normalized_name = normalize_company_name(company.company_name)
            if normalized_name not in name_groups:
                name_groups[normalized_name] = []
            name_groups[normalized_name].append(company)
        
        # 重新设计的重复检测逻辑 - 支持按匹配度排序和提供重复可能性建议
        duplicate_suggestions = []
        processed_companies = set()
        
        # 特别检查包含"瑞康"的公司
        ruikang_companies = [c for c in companies if '瑞康' in c.company_name]
        if ruikang_companies:
            current_app.logger.info(f"发现 {len(ruikang_companies)} 个包含'瑞康'的公司:")
            for rc in ruikang_companies:
                current_app.logger.info(f"  - ID {rc.id}: '{rc.company_name}' (标准化: '{normalize_company_name(rc.company_name)}')")
        
        for company in companies:
            if company.id in processed_companies:
                continue
                
            try:
                similar_companies_data = find_similar_companies(company, companies)
            except Exception as e:
                current_app.logger.error(f"查找相似公司失败 - 公司ID {company.id}: {str(e)}")
                continue
            
            # 去掉"至少2个重复"的限制，只要有相似公司就提供建议
            if similar_companies_data:
                processed_companies.add(company.id)
                
                # 构建目标公司信息
                try:
                    target_contact_count = Contact.query.filter_by(company_id=company.id).count()
                    target_action_count = Action.query.filter_by(company_id=company.id).count()
                    target_project_count = db.session.query(Project).filter(
                        Project.end_user == company.company_name
                    ).count()
                except Exception as e:
                    current_app.logger.error(f"收集目标公司数据失败 - 公司ID {company.id}: {str(e)}")
                    target_contact_count = target_action_count = target_project_count = 0
                
                target_data = {
                    'id': company.id,
                    'company_name': company.company_name,
                    'company_code': company.company_code or '',
                    'owner_name': (company.owner.real_name if company.owner and hasattr(company.owner, 'real_name') else None) or 
                                 (company.owner.username if company.owner and hasattr(company.owner, 'username') else None) or '无所有者',
                    'created_at': company.created_at.strftime('%Y-%m-%d') if company.created_at else None,
                    'contact_count': target_contact_count,
                    'action_count': target_action_count,
                    'project_count': target_project_count,
                    'is_target': True
                }
                
                # 构建相似公司列表（按匹配度排序）
                similar_companies_list = []
                for similar_data in similar_companies_data:
                    similar_company = similar_data['company']
                    if similar_company.id not in processed_companies:
                        processed_companies.add(similar_company.id)
                        
                        # 统计关联数据
                        try:
                            contact_count = Contact.query.filter_by(company_id=similar_company.id).count()
                            action_count = Action.query.filter_by(company_id=similar_company.id).count()
                            project_count = db.session.query(Project).filter(
                                Project.end_user == similar_company.company_name
                            ).count()
                        except Exception as e:
                            current_app.logger.error(f"收集相似公司数据失败 - 公司ID {similar_company.id}: {str(e)}")
                            contact_count = action_count = project_count = 0
                        
                        similar_companies_list.append({
                            'id': similar_company.id,
                            'company_name': similar_company.company_name,
                            'company_code': similar_company.company_code or '',
                            'owner_name': (similar_company.owner.real_name if similar_company.owner and hasattr(similar_company.owner, 'real_name') else None) or 
                                         (similar_company.owner.username if similar_company.owner and hasattr(similar_company.owner, 'username') else None) or '无所有者',
                            'created_at': similar_company.created_at.strftime('%Y-%m-%d') if similar_company.created_at else None,
                            'contact_count': contact_count,
                            'action_count': action_count,
                            'project_count': project_count,
                            'similarity': similar_data['similarity'],
                            'match_type': similar_data['match_type'],
                            'is_target': False
                        })
                
                if similar_companies_list:
                    duplicate_suggestions.append({
                        'group_id': f"group_{company.id}",
                        'target_company': target_data,
                        'similar_companies': similar_companies_list,
                        'max_similarity': max(s['similarity'] for s in similar_companies_list),
                        'total_companies': 1 + len(similar_companies_list)
                    })
        
        # 按最高匹配度排序重复建议组
        duplicate_suggestions.sort(key=lambda x: x['max_similarity'], reverse=True)
        
        current_app.logger.info(f"重复检测完成: 找到 {len(duplicate_suggestions)} 个重复组")
        for i, suggestion in enumerate(duplicate_suggestions):
            current_app.logger.info(f"  重复组 {i+1}: 目标 '{suggestion['target_company']['company_name']}', 相似公司 {len(suggestion['similar_companies'])} 个, 最高匹配度 {suggestion['max_similarity']:.3f}")
        
        return jsonify({
            'success': True,
            'data': duplicate_suggestions
        })
        
    except Exception as e:
        current_app.logger.error(f"检测重复客户失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        }), 500

@customer.route('/api/merge-preview', methods=['POST'])
@login_required
@permission_required('customer', 'create')
def get_merge_preview():
    """获取详细的合并预览数据，包括重复联系人检测"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
    
    try:
        data = request.json
        target_company_id = data.get('target_company_id')
        source_company_ids = data.get('source_company_ids', [])
        
        if not target_company_id or not source_company_ids:
            return jsonify({'success': False, 'message': '参数错误'}), 400
        
        # 获取目标公司
        target_company = Company.query.filter_by(id=target_company_id, is_deleted=False).first()
        if not target_company:
            return jsonify({'success': False, 'message': '目标客户不存在'}), 404
        
        # 获取目标公司的现有联系人
        target_contacts = Contact.query.filter_by(company_id=target_company_id).all()
        target_contact_keys = set()
        for tc in target_contacts:
            key = f"{tc.name}|{tc.email or ''}|{tc.phone or ''}"
            target_contact_keys.add(key)
        
        # 获取所有源公司的联系人
        contacts = Contact.query.filter(Contact.company_id.in_(source_company_ids)).all()
        contacts_data = []
        duplicate_contacts = []
        
        for contact in contacts:
            contact_key = f"{contact.name}|{contact.email or ''}|{contact.phone or ''}"
            contact_info = {
                'name': contact.name,
                'company_name': contact.company.company_name,
                'position': contact.position or '',
                'phone': contact.phone or '',
                'email': contact.email or ''
            }
            
            if contact_key in target_contact_keys:
                duplicate_contacts.append(contact_info)
            else:
                contacts_data.append(contact_info)
                target_contact_keys.add(contact_key)
        
        # 获取所有源公司的行动记录
        actions = Action.query.filter(Action.company_id.in_(source_company_ids)).order_by(Action.date.desc()).all()
        actions_data = []
        for action in actions:
            actions_data.append({
                'date': action.date.strftime('%Y-%m-%d') if action.date else '',
                'communication': action.communication[:100],
                'company_name': action.company.company_name if action.company else ''
            })
        
        # 获取关联的项目（通过end_user字段）
        source_companies = Company.query.filter(Company.id.in_(source_company_ids), Company.is_deleted == False).all()
        source_company_names = [c.company_name for c in source_companies]
        
        projects = db.session.query(Project).filter(
            Project.end_user.in_(source_company_names)
        ).all()
        projects_data = []
        for project in projects:
            projects_data.append({
                'project_name': project.project_name,
                'end_user': project.end_user
            })
        
        # 获取目标企业的现有数据
        target_actions = Action.query.filter_by(company_id=target_company_id).order_by(Action.date.desc()).all()
        target_actions_data = []
        for action in target_actions:
            target_actions_data.append({
                'date': action.date.strftime('%Y-%m-%d') if action.date else '',
                'communication': action.communication[:100],
                'company_name': action.company.company_name if action.company else ''
            })
        
        # 获取目标企业的现有联系人数据
        target_contacts_data = []
        for contact in target_contacts:
            target_contacts_data.append({
                'name': contact.name,
                'company_name': contact.company.company_name,
                'position': contact.position or '',
                'phone': contact.phone or '',
                'email': contact.email or ''
            })
        
        # 获取目标企业的项目
        target_projects = db.session.query(Project).filter(
            Project.end_user == target_company.company_name
        ).all()
        target_projects_data = []
        for project in target_projects:
            target_projects_data.append({
                'project_name': project.project_name,
                'end_user': project.end_user
            })
        
        return jsonify({
            'success': True,
            'data': {
                'contacts': contacts_data,
                'duplicate_contacts': duplicate_contacts,
                'actions': actions_data,
                'projects': projects_data,
                'target': {
                    'company_name': target_company.company_name,
                    'contacts': target_contacts_data,
                    'actions': target_actions_data,
                    'projects': target_projects_data
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取合并预览失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取预览失败: {str(e)}'
        }), 500

@customer.route('/api/execute-merge', methods=['POST'])
@login_required
@permission_required('customer', 'create')
def execute_merge():
    """执行客户合并"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
    
    try:
        data = request.json
        target_company_id = data.get('target_company_id')
        source_company_ids = data.get('source_company_ids', [])
        final_company_name = data.get('final_company_name', '')
        
        if not target_company_id or not source_company_ids:
            return jsonify({'success': False, 'message': '参数错误'}), 400
        
        # 获取目标公司
        target_company = Company.query.filter_by(id=target_company_id, is_deleted=False).first()
        if not target_company:
            db.session.rollback()
            return jsonify({'success': False, 'message': '目标客户不存在'}), 404
        
        # 获取源公司列表
        source_companies = Company.query.filter(Company.id.in_(source_company_ids), Company.is_deleted == False).all()
        if len(source_companies) != len(source_company_ids):
            db.session.rollback()
            return jsonify({'success': False, 'message': '部分源客户不存在'}), 404
        
        # 确保目标公司不在源公司列表中
        if target_company_id in source_company_ids:
            db.session.rollback()
            return jsonify({'success': False, 'message': '目标客户不能在被合并的客户列表中'}), 400
        
        merge_summary = {
            'merged_contacts': 0,
            'merged_duplicate_contacts': 0,
            'merged_contact_fields': 0,
            'merged_actions': 0,
            'updated_projects': 0,
            'deleted_companies': 0,
            'added_shared_users': 0
        }
        
        # 添加详细日志
        current_app.logger.info(f"开始合并客户: 目标={target_company_id}, 源={source_company_ids}")
        
        # 1. 智能合并联系人 - 支持字段级别的合并
        target_contacts = Contact.query.filter_by(company_id=target_company_id).all()
        target_contact_dict = {}
        
        # 建立目标联系人的姓名索引
        for tc in target_contacts:
            target_contact_dict[tc.name] = tc
        
        for source_company in source_companies:
            contacts = Contact.query.filter_by(company_id=source_company.id).all()
            for contact in contacts:
                # 检查是否存在同名联系人
                if contact.name in target_contact_dict:
                    # 同名联系人：合并字段信息
                    target_contact = target_contact_dict[contact.name]
                    
                    # 字段级别合并：目标联系人字段为空时，使用源联系人的字段
                    fields_to_merge = ['department', 'position', 'phone', 'email', 'notes']
                    updated_fields = []
                    
                    for field in fields_to_merge:
                        target_value = getattr(target_contact, field)
                        source_value = getattr(contact, field)
                        
                        # 如果目标字段为空且源字段有值，则合并
                        if (not target_value or target_value.strip() == '') and source_value and source_value.strip():
                            setattr(target_contact, field, source_value)
                            updated_fields.append(field)
                    
                    # 如果源联系人是主要联系人，且目标联系人不是，则更新主要联系人标识
                    if contact.is_primary and not target_contact.is_primary:
                        target_contact.is_primary = True
                        updated_fields.append('is_primary')
                    
                    # 更新时间戳
                    target_contact.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
                    
                    # 记录合并信息
                    if updated_fields:
                        current_app.logger.info(f"合并同名联系人 '{contact.name}' 的字段: {updated_fields}")
                        merge_summary['merged_contact_fields'] += len(updated_fields)
                    
                    # 转移源联系人的行动记录到目标联系人
                    contact_actions = Action.query.filter_by(contact_id=contact.id).all()
                    for action in contact_actions:
                        action.contact_id = target_contact.id
                        action.company_id = target_company_id
                    
                    # 删除源联系人
                    db.session.delete(contact)
                    merge_summary['merged_duplicate_contacts'] += 1
                else:
                    # 不同名的联系人：直接转移
                    contact.company_id = target_company_id
                    merge_summary['merged_contacts'] += 1
                    target_contact_dict[contact.name] = contact
        
        # 2. 合并行动记录
        for source_company in source_companies:
            actions = Action.query.filter_by(company_id=source_company.id).all()
            for action in actions:
                action.company_id = target_company_id
                # 保持行动记录的原有所有者不变
                merge_summary['merged_actions'] += 1
        
        # 3. 更新项目的end_user字段
        for source_company in source_companies:
            projects = db.session.query(Project).filter(
                Project.end_user == source_company.company_name
            ).all()
            for project in projects:
                project.end_user = target_company.company_name
                # 项目的归属不变，只更新end_user字段
                merge_summary['updated_projects'] += 1
        
        # 4. 合并共享信息，确保被合并客户的所有者能访问目标客户
        original_shared_users = set(target_company.shared_with_users or [])
        target_shared_users = set(target_company.shared_with_users or [])
        
        # 添加所有源公司的共享用户
        for source_company in source_companies:
            if source_company.shared_with_users:
                target_shared_users.update(source_company.shared_with_users)
            
            # 重要：将被合并客户的所有者添加到目标客户的共享列表中
            if source_company.owner_id and source_company.owner_id != target_company.owner_id:
                target_shared_users.add(source_company.owner_id)
                current_app.logger.info(f"将被合并客户 {source_company.company_name} 的所有者(ID: {source_company.owner_id})添加到目标客户的共享列表")
        
        # 确保目标客户的所有者不在共享列表中（所有者默认有完全访问权限）
        if target_company.owner_id and target_company.owner_id in target_shared_users:
            target_shared_users.remove(target_company.owner_id)
        
        # 统计新增的共享用户数量
        merge_summary['added_shared_users'] = len(target_shared_users - original_shared_users)
        
        target_company.shared_with_users = list(target_shared_users)
        
        # 5. 删除源公司（标记为删除）
        for source_company in source_companies:
            source_company.is_deleted = True
            merge_summary['deleted_companies'] += 1
        
        # 6. 更新目标公司名称（如果提供了新名称）
        if final_company_name and final_company_name.strip():
            old_name = target_company.company_name
            target_company.company_name = final_company_name.strip()
            # 同时更新项目中的end_user字段
            projects_to_update_name = db.session.query(Project).filter(
                Project.end_user == old_name
            ).all()
            for project in projects_to_update_name:
                project.end_user = final_company_name.strip()
        
        # 7. 更新目标公司的更新时间
        target_company.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        
        # 提交事务
        db.session.commit()
        
        # 记录操作日志
        current_app.logger.info(f"管理员 {current_user.username} 执行客户合并: "
                              f"目标客户 {target_company.company_name} (ID: {target_company_id}), "
                              f"合并客户 {[c.company_name for c in source_companies]}, "
                              f"合并统计: {merge_summary}")
        
        return jsonify({
            'success': True,
            'message': '客户合并成功',
            'data': merge_summary
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"执行客户合并失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'合并失败: {str(e)}'
        }), 500

def normalize_company_name(name):
    """标准化公司名称，用于重复检测 - 更精确的匹配逻辑"""
    if not name:
        return ""
    
    import re
    
    # 1. 清理不可见字符和额外空格
    normalized = re.sub(r'\s+', '', name.strip())  # 去除所有空白字符
    normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', normalized)  # 只保留字母、数字和中文
    
    # 2. 去除地名前缀（更精确的地名识别）
    location_prefixes = [
        # 直辖市
        "北京市", "上海市", "天津市", "重庆市",
        "北京", "上海", "天津", "重庆",
        # 常见省份简称
        "广东省", "浙江省", "江苏省", "山东省", "河南省", "四川省", "湖北省", "湖南省",
        "广东", "浙江", "江苏", "山东", "河南", "四川", "湖北", "湖南",
        "福建", "安徽", "江西", "云南", "贵州", "山西", "陕西", "甘肃",
        "青海", "海南", "台湾", "香港", "澳门",
        # 常见城市
        "深圳市", "广州市", "杭州市", "南京市", "苏州市", "无锡市", "常州市",
        "深圳", "广州", "杭州", "南京", "苏州", "无锡", "常州",
        "宁波", "温州", "东莞", "佛山", "中山", "珠海", "厦门",
        "青岛", "大连", "沈阳", "长春", "哈尔滨", "西安", "成都",
        "武汉", "长沙", "郑州", "济南", "石家庄", "太原", "呼和浩特",
        # 开发区等
        "经济技术开发区", "高新技术开发区", "工业园区", "科技园区",
        "开发区", "高新区", "工业区", "科技园"
    ]
    
    # 按长度排序，先匹配长的地名
    location_prefixes.sort(key=len, reverse=True)
    
    for prefix in location_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    
    # 3. 去除公司类型后缀（只保留核心业务相关的后缀）
    business_suffixes = [
        # 标准公司类型
        "有限责任公司", "股份有限公司", "有限公司", "股份公司",
        # 特殊组织形式
        "集团有限公司", "控股有限公司", "投资有限公司",
        "集团股份有限公司", "控股股份有限公司",
        # 简化形式
        "有限", "股份", "集团", "控股", "投资",
        # 英文后缀
        "Co.,Ltd", "Co.Ltd", "Ltd", "Inc", "Corp", "LLC",
        "Company", "Corporation", "Limited", "Incorporated"
    ]
    
    # 按长度排序，先匹配长的后缀
    business_suffixes.sort(key=len, reverse=True)
    
    for suffix in business_suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break  # 只删除一个后缀
    
    # 4. 再次清理可能的空格
    normalized = re.sub(r'\s+', '', normalized)
    
    result = normalized.lower()
    
    # 调试日志
    if name != result:
        current_app.logger.debug(f"精确标准化: '{name}' -> '{result}'")
    
    return result

def find_similar_companies(target_company, all_companies):
    """查找相似的公司，返回带匹配度的结果"""
    similar_companies = []
    target_normalized = normalize_company_name(target_company.company_name)
    
    # 添加调试日志
    current_app.logger.debug(f"查找相似公司: 目标公司 '{target_company.company_name}' -> 标准化后: '{target_normalized}'")
    
    for company in all_companies:
        if company.id == target_company.id:
            continue
            
        company_normalized = normalize_company_name(company.company_name)
        
        # 更严格的相似度计算逻辑
        # 1. 首先检查原始名称的完全匹配（处理空格后）
        target_cleaned = re.sub(r'\s+', '', target_company.company_name.strip())
        company_cleaned = re.sub(r'\s+', '', company.company_name.strip())
        
        if target_cleaned == company_cleaned:
            final_score = 1.0
            current_app.logger.info(f"发现原始名称完全匹配: '{target_company.company_name}' vs '{company.company_name}'")
        else:
            # 2. 检查标准化后的名称匹配
            if target_normalized == company_normalized:
                # 标准化后相同，但原始名称不同（前缀或后缀差异）
                final_score = 0.95  # 高匹配度但不是100%
                current_app.logger.info(f"发现标准化后匹配: '{target_company.company_name}' vs '{company.company_name}' (标准化后都是: '{target_normalized}')")
            else:
                # 3. 检查核心企业名称的长度，太短的不作为匹配候选
                if len(target_normalized) < 3 or len(company_normalized) < 3:
                    final_score = 0  # 跳过太短的名称
                else:
                    # 4. 计算基础相似度
                    similarity = difflib.SequenceMatcher(None, target_normalized, company_normalized).ratio()
                    
                    # 5. 更严格的包含关系检查
                    containment_bonus = 0
                    if len(target_normalized) >= 4 and len(company_normalized) >= 4:
                        # 只有当名称足够长时才考虑包含关系
                        if target_normalized in company_normalized or company_normalized in target_normalized:
                            # 计算包含关系的权重，避免过度匹配
                            shorter_len = min(len(target_normalized), len(company_normalized))
                            longer_len = max(len(target_normalized), len(company_normalized))
                            length_ratio = shorter_len / longer_len
                            
                            # 只有当长度比例合理时才给予包含关系加权
                            if length_ratio > 0.8:  # 提高长度比例要求
                                containment_bonus = 0.1 * length_ratio  # 降低加权
                    
                    final_score = min(1.0, similarity + containment_bonus)
        
        # 调试高匹配度的情况
        if final_score > 0.8:
            current_app.logger.info(f"高匹配度 {final_score:.3f}: '{target_company.company_name}' vs '{company.company_name}'")
            current_app.logger.info(f"  标准化: '{target_normalized}' vs '{company_normalized}'")
            current_app.logger.info(f"  长度: {len(target_normalized)} vs {len(company_normalized)}")
        
        # 提高匹配度阈值，减少误匹配
        if final_score > 0.85:  # 从0.4提高到0.85，更严格的匹配
            similar_companies.append({
                'company': company,
                'similarity': final_score,
                'match_type': 'high' if final_score > 0.8 else 'medium' if final_score > 0.6 else 'low'
            })
    
    # 按匹配度降序排序
    similar_companies.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similar_companies
