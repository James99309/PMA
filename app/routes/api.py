import logging
import json
from flask import Blueprint, jsonify, request, current_app, session, g
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.customer import Company
from app.models.project import Project
from app.models.product import Product
from app.permissions import permission_required
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz  # 用于计算字符串相似度
import re
from app.models.quotation import Quotation, QuotationDetail
from app.utils.dictionary_helpers import company_type_label, COMPANY_TYPE_LABELS
from app.utils.access_control import get_viewable_data
from app.utils.role_mappings import get_role_display_name

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# 行业分类映射
INDUSTRY_LABELS = {
    'manufacturing': {'zh': '制造业', 'en': 'Manufacturing'},
    'real_estate': {'zh': '商业地产', 'en': 'Real Estate'},
    'energy': {'zh': '石油能源', 'en': 'Energy'},
    'chemical': {'zh': '化工医药', 'en': 'Chemicals & Pharma'},
    'health': {'zh': '医疗卫生', 'en': 'Healthcare'},
    'transport': {'zh': '交通运输', 'en': 'Transportation'},
    'government': {'zh': '政府机构', 'en': 'Government'},
    'education': {'zh': '教育', 'en': 'Education'},
    'other': {'zh': '其他选择', 'en': 'Other'}
}

def get_role_display_name(role_key):
    """获取角色的中文显示名"""
    from app.models.dictionary import Dictionary
    role_dict = Dictionary.query.filter_by(type='role', key=role_key, is_active=True).first()
    return role_dict.value if role_dict else role_key

@api_bp.route('/companies/<string:company_type>', methods=['GET'])
@login_required
def get_companies_by_type(company_type):
    """
    获取指定类型的公司列表
    company_type可以是：user（直接用户）, designer（设计院）, contractor（总承包）, 
    integrator（系统集成商）, dealer（经销商）
    """
    if company_type not in COMPANY_TYPE_LABELS:
        return jsonify({'error': '无效的公司类型'}), 400

    query = get_viewable_data(Company, current_user)
    companies = query.filter_by(company_type=company_type).order_by(Company.company_name).all()

    # 直接返回数组，兼容前端
    return jsonify([{'id': c.id, 'name': c.company_name} for c in companies])

@api_bp.route('/products/categories', methods=['GET'])
def get_product_categories():
    """获取去重后的产品类别列表"""
    try:
        logger.debug('正在获取产品类别列表...')
        # 使用 distinct 获取唯一的类别列表
        categories = db.session.query(Product.category).distinct().filter(
            Product.is_discontinued == False,
            Product.category.isnot(None)
        ).all()
        
        # 将结果转换为列表
        category_list = [category[0] for category in categories if category[0]]
        category_list.sort()  # 按字母顺序排序
        
        logger.debug(f'找到 {len(category_list)} 个类别')
        return jsonify(category_list)
        
    except Exception as e:
        logger.error(f'获取产品类别列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类别列表失败',
            'message': str(e)
        }), 500

@api_bp.route('/products/by-category', methods=['GET'])
def get_products_by_category():
    """获取指定类别的产品列表 - 已迁移到product_route模块"""
    # 为了保持向后兼容，重定向到product_route中的版本
    from app.routes.product import get_products_by_category as product_route_get_products
    return product_route_get_products()

@api_bp.route('/product/stats', methods=['GET'])
@login_required
def get_product_stats():
    """
    获取产品统计信息，包括：
    - 总产品数
    - 最近更新数量
    - 按状态分类
    - 按类型分类
    """
    try:
        # 总产品数
        total_count = Product.query.count()
        
        # 最近一周更新的产品数
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_updates = Product.query.filter(Product.updated_at >= one_week_ago).count()
        
        # 按状态统计 - 使用status字段，支持三种状态
        status_counts = {
            'active': Product.query.filter(Product.status == 'active').count(),
            'discontinued': Product.query.filter(Product.status == 'discontinued').count(),
            'upcoming': Product.query.filter(Product.status == 'upcoming').count()
        }
        
        # 按类型统计 - 使用实际的type值
        type_counts = {}
        # 获取所有不同类型的产品
        product_types = db.session.query(Product.type).distinct().all()
        for pt in product_types:
            type_name = pt[0]
            if type_name:
                count = Product.query.filter(Product.type == type_name).count()
                type_counts[type_name] = count
        
        return jsonify({
            'total': total_count,
            'recent_updates': recent_updates,
            'status': status_counts,
            'type': type_counts
        })
    except Exception as e:
        current_app.logger.error(f"获取产品统计信息出错: {str(e)}")
        return jsonify({'error': '获取产品统计信息失败'}), 500

@api_bp.route('/users', methods=['GET'])
@login_required
def get_all_users():
    """获取系统所有用户，仅管理员可用"""
    if current_user.role != 'admin':
        return jsonify({'error': '权限不足', 'message': '仅管理员可获取用户列表'}), 403
    
    users = User.query.all()
    users_data = [{
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'role': user.role
    } for user in users]
    
    return jsonify(users_data)

@api_bp.route('/users/hierarchical', methods=['GET'])
@login_required
def get_hierarchical_users():
    """获取层级结构的用户数据（按公司分组）"""
    users = User.query.all()
    companies = {}
    
    # 按公司分组用户
    for user in users:
        company_name = user.company_name or '未分配公司'
        if company_name not in companies:
            companies[company_name] = {
                'name': company_name,
                'is_vendor': user.is_vendor_user(),  # 添加厂商标识
                'users': []
            }
        
        # 获取真实姓名，如果没有则使用用户名
        display_name = user.real_name if hasattr(user, 'real_name') and user.real_name else (user.name if hasattr(user, 'name') else user.username)
        # 获取角色的中文显示名
        role_display = get_role_display_name(user.role) if user.role else '未知角色'
        
        companies[company_name]['users'].append({
            'id': user.id,
            'name': display_name,
            'username': user.username,
            'real_name': display_name,
            'role': user.role,
            'role_display': role_display
        })
    
    # 转换为列表
    companies_list = list(companies.values())
    
    return jsonify({
        'success': True,
        'data': companies_list
    })

@api_bp.route('/projects/check-conflicts', methods=['POST'])
@login_required
@permission_required('project', 'create')
def check_project_conflicts():
    """检查项目导入冲突"""
    try:
        # 添加详细日志记录，用于调试
        current_app.logger.info(f"检查项目冲突接收到的请求数据: {request.json}")
        current_app.logger.info(f"请求内容类型: {request.headers.get('Content-Type')}")
        current_app.logger.info(f"当前用户: {current_user.username if current_user else '未登录'}")
        
        data = request.json
        projects = data.get('projects', [])
        field_mapping = data.get('field_mapping', {})
        
        if not projects:
            error_msg = '没有提供项目数据'
            current_app.logger.warning(f"检查项目冲突失败: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
            
        # 项目信息的冲突检测结果
        conflicts = []
        
        # 处理授权编号格式化：移除HY-前缀
        def format_auth_code(code):
            if code and isinstance(code, str):
                # 移除HY-前缀
                if code.startswith('HY-'):
                    return code[3:]
            return code
        
        # 遍历所有项目检查冲突
        for i, project_data in enumerate(projects):
            # 获取项目名称
            project_name_key = next((k for k, v in field_mapping.items() if v == 'project_name'), '项目名称')
            project_name = project_data.get(project_name_key)
            
            # 获取授权编号
            auth_code_key = next((k for k, v in field_mapping.items() if v == 'authorization_code'), '授权编号')
            auth_code = project_data.get(auth_code_key)
            
            # 格式化授权编号
            formatted_auth_code = format_auth_code(auth_code)
            
            # 检查授权编号冲突 - 只与数据库中的项目比较
            if formatted_auth_code:
                # 检查是否与数据库中现有项目授权编号冲突
                existing_project = Project.query.filter_by(authorization_code=formatted_auth_code).first()
                if existing_project:
                    conflicts.append({
                        'index': i,
                        'project_name': project_name,
                        'authorization_code': formatted_auth_code,
                        'conflict_type': 'code',
                        'conflict_with': 'database',
                        'conflict_id': existing_project.id,
                        'conflict_name': existing_project.project_name
                    })
                    continue  # 如果有授权编号冲突，不再检查项目名称相似度
            
            # 检查项目名称相似度 - 只与数据库中的项目比较
            if project_name:
                # 检查是否与数据库中现有项目名称相似
                existing_projects = Project.query.all()
                
                for existing_project in existing_projects:
                    similarity = fuzz.ratio(project_name, existing_project.project_name)
                    if similarity >= 80:
                        conflicts.append({
                            'index': i,
                            'project_name': project_name,
                            'authorization_code': formatted_auth_code,
                            'conflict_type': 'name',
                            'conflict_with': 'database',
                            'conflict_id': existing_project.id,
                            'conflict_name': existing_project.project_name,
                            'similarity': similarity
                        })
                        break
        
        return jsonify({
            'success': True,
            'conflicts': conflicts
        })
    
    except Exception as e:
        import traceback
        logger.error(f'检查项目冲突出错: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'success': False,
            'message': f'检查项目冲突出错: {str(e)}'
        }), 500

@api_bp.route('/projects/import', methods=['POST'])
@login_required
@permission_required('project', 'create')
def import_projects():
    """批量导入项目"""
    try:
        data = request.json
        owner_id = data.get('owner_id')  # 可能为空
        projects = data.get('projects', [])
        conflict_actions = data.get('conflict_actions', {})
        field_mapping = data.get('field_mapping', {})
        use_excel_owner = data.get('use_excel_owner', False)  # 是否使用Excel中的销售负责人
        sync_report_time_to_created_at = data.get('sync_report_time_to_created_at', False)  # 是否同步报备时间到创建时间
        
        if not projects:
            return jsonify({
                'success': False,
                'message': '没有提供项目数据'
            }), 400
        
        # 如果指定了owner_id，检查是否存在
        selected_owner = None
        if owner_id:
            selected_owner = User.query.get(owner_id)
            if not selected_owner:
                return jsonify({
                    'success': False,
                    'message': f'找不到ID为{owner_id}的用户'
                }), 400
            
        # 状态计数
        imported_count = 0  # 新增
        skipped_count = 0   # 跳过
        error_count = 0     # 错误
        import_log = []     # 导入日志
        error_details = []  # 错误详情
        
        # 处理授权编号格式化：移除HY-前缀
        def format_auth_code(code):
            if code and isinstance(code, str):
                # 移除HY-前缀
                if code.startswith('HY-'):
                    return code[3:]
            return code
        
        # 日期字段处理函数
        def parse_date(date_value):
            if date_value is None:
                return None
            
            # 如果已经是datetime对象，直接返回
            if isinstance(date_value, datetime):
                return date_value
                
            # 如果是Excel的序列号表示日期
            if isinstance(date_value, (int, float)):
                # 将Excel日期序列号转为日期对象，Excel中日期从1900-01-01开始
                # 日期的起始点是1899年12月30日，偏移值是1
                try:
                    excel_epoch = datetime(1899, 12, 30)
                    delta = timedelta(days=int(date_value))
                    return excel_epoch + delta
                except Exception as e:
                    current_app.logger.warning(f"处理Excel日期格式出错: {str(e)}")
                    return datetime.now()
                    
            # 尝试解析字符串格式的日期
            if isinstance(date_value, str):
                try:
                    # 尝试解析常见的日期格式
                    formats = [
                        '%Y-%m-%d', '%Y/%m/%d',  # 年-月-日
                        '%d-%m-%Y', '%d/%m/%Y',  # 日-月-年
                        '%m/%d/%Y', '%m-%d-%Y',  # 月-日-年
                        '%m/%d/%y'  # 美式短格式，如5/9/24
                    ]
                    
                    for fmt in formats:
                        try:
                            return datetime.strptime(date_value, fmt)
                        except ValueError:
                            continue
                    
                    # 特殊处理MM/DD/YY格式
                    if re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_value):
                        parts = date_value.split('/')
                        month = int(parts[0])
                        day = int(parts[1])
                        year = int(parts[2])
                        # 如果年份是两位数
                        if year < 100:
                            year = 2000 + year if year < 50 else 1900 + year
                        try:
                            return datetime(year, month, day)
                        except ValueError:
                            current_app.logger.warning(f"日期值无效: {date_value}")
                    
                    # 如果无法解析，记录警告并返回当前时间
                    current_app.logger.warning(f"无法解析日期格式: {date_value}")
                    return datetime.now()
                except Exception as e:
                    current_app.logger.warning(f"处理日期字符串出错: {str(e)}")
                    return datetime.now()
            
            # 其他情况返回当前时间
            return datetime.now()
        
        # 获取字段映射的反向映射
        reverse_mapping = {}
        for excel_field, db_field in field_mapping.items():
            reverse_mapping[db_field] = excel_field
            
        # 遍历处理所有项目
        for i, project_data in enumerate(projects):
            try:
                # 构建项目数据
                new_project_data = {}
                # 设置项目字段
                for db_field, excel_field in reverse_mapping.items():
                    if excel_field in project_data and project_data[excel_field] is not None:
                        # 特殊处理日期字段
                        if db_field in ['report_time', 'delivery_forecast']:
                            new_project_data[db_field] = parse_date(project_data[excel_field])
                        # 特殊处理授权编号
                        elif db_field == 'authorization_code':
                            new_project_data[db_field] = format_auth_code(project_data[excel_field])
                        # 跳过owner_id字段，稍后处理
                        elif db_field == 'owner_id':
                            pass
                        else:
                            new_project_data[db_field] = project_data[excel_field]
                # 确保创建时间和更新时间是datetime对象
                current_time = datetime.now()
                if sync_report_time_to_created_at and 'report_time' in new_project_data and new_project_data['report_time']:
                    new_project_data['created_at'] = new_project_data['report_time']
                else:
                    new_project_data['created_at'] = current_time
                new_project_data['updated_at'] = current_time
                project_name = new_project_data.get('project_name')
                auth_code = new_project_data.get('authorization_code')
                # 检查是否需要跳过此项目（基于冲突操作）
                if str(i) in conflict_actions and conflict_actions[str(i)] == 'ignore':
                    skipped_count += 1
                    import_log.append(f"跳过项目: {project_name}，原因: 用户选择忽略")
                    continue
                # 修正：优先用project_data['owner_id']（为int或数字字符串）
                owner_id_from_row = project_data.get('owner_id')
                if owner_id_from_row is not None:
                    try:
                        owner_id_candidate = int(owner_id_from_row)
                        owner_obj = User.query.get(owner_id_candidate)
                        if owner_obj:
                            new_project_data['owner_id'] = owner_id_candidate
                        else:
                            # owner_id无效，走后续逻辑
                            owner_id_from_row = None
                    except Exception:
                        owner_id_from_row = None
                if owner_id_from_row is None:
                    if owner_id:
                        new_project_data['owner_id'] = owner_id
                    elif use_excel_owner and 'owner_id' in reverse_mapping:
                        excel_owner_field = reverse_mapping['owner_id']
                        excel_owner_name = project_data.get(excel_owner_field)
                        if excel_owner_name:
                            excel_owner = User.query.filter(User.name == excel_owner_name).first()
                            if excel_owner:
                                new_project_data['owner_id'] = excel_owner.id
                            else:
                                new_project_data['owner_id'] = current_user.id
                                import_log.append(f"项目 {project_name} 的销售负责人 '{excel_owner_name}' 不存在，已使用当前用户作为所有者")
                        else:
                            new_project_data['owner_id'] = current_user.id
                    else:
                        new_project_data['owner_id'] = current_user.id
                # 创建新项目
                new_project = Project(**new_project_data)
                db.session.add(new_project)
                try:
                    db.session.commit()
                    imported_count += 1
                    import_log.append(f"成功导入项目: {project_name}")
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"导入项目 {project_name} 数据库操作失败: {str(db_error)}")
                    error_count += 1
                    error_details.append({
                        'line': i + 2,
                        'project_name': project_name,
                        'reason': f"数据库操作失败: {str(db_error)}"
                    })
                    import_log.append(f"导入项目失败: {project_name}，原因: {str(db_error)}")
            except Exception as project_error:
                logger.error(f"处理项目导入时出错 (行 {i+2}): {str(project_error)}")
                error_count += 1
                error_details.append({
                    'line': i + 2,
                    'project_name': project_data.get(reverse_mapping.get('project_name', '项目名称'), "未知"),
                    'reason': f"处理失败: {str(project_error)}"
                })
                import_log.append(f"导入项目失败，行号: {i+2}，原因: {str(project_error)}")
        
        return jsonify({
            'success': True,
            'message': f'导入完成，新增: {imported_count}，跳过: {skipped_count}，错误: {error_count}',
            'data': {
                'imported': imported_count,
                'skipped': skipped_count,
                'error': error_count,
                'log': import_log,
                'error_details': error_details
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f'导入项目出错: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'success': False,
            'message': f'导入项目出错: {str(e)}'
        }), 500

@api_bp.route('/quotations/check-conflicts', methods=['POST'])
@login_required
@permission_required('quotation', 'create')
def check_quotation_conflicts():
    """检查报价单冲突"""
    try:
        # 添加详细日志记录，用于调试
        current_app.logger.info(f"检查报价单冲突接收到的请求数据: {request.json}")
        current_app.logger.info(f"请求内容类型: {request.headers.get('Content-Type')}")
        current_app.logger.info(f"当前用户: {getattr(current_user, 'username', '未登录')}")
        
        # 检查请求内容类型
        if not request.is_json:
            current_app.logger.warning(f"请求不是JSON格式: {request.headers.get('Content-Type')}")
            return jsonify({
                'success': False,
                'message': '请求格式不正确，应为JSON'
            }), 400
            
        data = request.json
        quotations = data.get('quotations', [])
        
        if not quotations:
            error_msg = '没有提供报价单数据'
            current_app.logger.warning(f"检查报价单冲突失败: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
        
        # 状态计数
        conflicts = []
        
        # 创建项目名称到编号的映射，用于检测导入数据中的内部冲突
        internal_quotations = {}
        
        # 第一遍：检查内部冲突（相同项目名称但编号不同）
        for quotation in quotations:
            project_name = quotation.get('project_name')
            quotation_number = quotation.get('quotation_number')
            
            if not project_name or not quotation_number:
                continue
                
            # 如果此项目已在导入列表中有报价单，检查编号是否一致
            if project_name in internal_quotations:
                existing_number = internal_quotations[project_name]
                if existing_number != quotation_number:
                    # 内部冲突：相同项目名称，不同报价单编号
                    conflicts.append({
                        'project_name': project_name,
                        'conflict_type': 'internal_number_mismatch',
                        'existing_quotation': {
                            'quotation_number': existing_number
                        },
                        'new_quotation_number': quotation_number
                    })
            else:
                # 记录此项目的报价单编号
                internal_quotations[project_name] = quotation_number
        
        # 第二遍：检查与数据库中现有报价单的冲突
        for quotation in quotations:
            project_name = quotation.get('project_name')
            quotation_number = quotation.get('quotation_number')
            
            if not project_name:
                continue
            
            current_app.logger.info(f"检查项目: {project_name}, 报价单编号: {quotation_number}")
                
            # 查找是否有关联此项目名称的报价单
            project = Project.query.filter_by(project_name=project_name).first()
            if project:
                existing_quotation = Quotation.query.filter_by(project_id=project.id).first()
                if existing_quotation:
                    conflicts.append({
                        'project_name': project_name,
                        'conflict_type': 'project_exists',
                        'existing_quotation': {
                            'id': existing_quotation.id,
                            'quotation_number': existing_quotation.quotation_number,
                            'amount': existing_quotation.amount
                        }
                    })
            
            # 检查是否有相同编号的报价单
            if quotation_number:
                existing_quotation_by_number = Quotation.query.filter_by(quotation_number=quotation_number).first()
                if existing_quotation_by_number:
                    conflicts.append({
                        'project_name': project_name,
                        'conflict_type': 'number_exists',
                        'existing_quotation': {
                            'id': existing_quotation_by_number.id,
                            'quotation_number': existing_quotation_by_number.quotation_number,
                            'project_name': existing_quotation_by_number.project.project_name if existing_quotation_by_number.project else '未知项目'
                        }
                    })
        
        return jsonify({
            'success': True,
            'conflicts': conflicts
        })
        
    except Exception as e:
        import traceback
        error_msg = f"检查报价单冲突出错: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': f'检查冲突失败: {str(e)}'
        }), 500

@api_bp.route('/quotations/import', methods=['POST'])
@login_required
@permission_required('quotation', 'create')
def import_quotations():
    """批量导入报价单"""
    try:
        data = request.json
        owner_id = data.get('owner_id')  # 可能为空
        quotations = data.get('quotations', [])
        
        # 添加日志记录请求数据
        current_app.logger.info(f"导入报价单数据: 报价单数量={len(quotations)}")
        
        if not quotations:
            return jsonify({
                'success': False,
                'message': '没有提供报价单数据'
            }), 400
        
        # 如果指定了owner_id，检查是否存在
        selected_owner = None
        if owner_id:
            selected_owner = User.query.get(owner_id)
            if not selected_owner:
                return jsonify({
                    'success': False,
                    'message': f'找不到ID为{owner_id}的用户'
                }), 400
        
        # 状态计数
        imported_count = 0   # 新增报价单
        details_count = 0    # 新增明细
        skipped_count = 0    # 跳过
        error_count = 0      # 错误
        error_details = []   # 错误详情
        
        # 使用字典存储已创建的报价单，仅使用项目名称作为键
        quotation_map = {}
        
        # 日期字段处理函数
        def parse_date(date_value):
            if date_value is None:
                return None
            
            # 如果已经是datetime对象，直接返回
            if isinstance(date_value, datetime):
                return date_value
                
            # 如果是Excel的序列号表示日期
            if isinstance(date_value, (int, float)):
                # 将Excel日期序列号转为日期对象，Excel中日期从1900-01-01开始
                # 日期的起始点是1899年12月30日，偏移值是1
                try:
                    excel_epoch = datetime(1899, 12, 30)
                    delta = timedelta(days=int(date_value))
                    return excel_epoch + delta
                except Exception as e:
                    current_app.logger.warning(f"处理Excel日期格式出错: {str(e)}")
                    return datetime.now()
                    
            # 尝试解析字符串格式的日期
            if isinstance(date_value, str):
                try:
                    # 尝试解析常见的日期格式
                    formats = [
                        '%Y-%m-%d', '%Y/%m/%d',  # 年-月-日
                        '%d-%m-%Y', '%d/%m/%Y',  # 日-月-年
                        '%m/%d/%Y', '%m-%d-%Y',  # 月-日-年
                        '%m/%d/%y'  # 美式短格式，如5/9/24
                    ]
                    
                    for fmt in formats:
                        try:
                            return datetime.strptime(date_value, fmt)
                        except ValueError:
                            continue
                    
                    # 特殊处理MM/DD/YY格式
                    if re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_value):
                        parts = date_value.split('/')
                        month = int(parts[0])
                        day = int(parts[1])
                        year = int(parts[2])
                        # 如果年份是两位数
                        if year < 100:
                            year = 2000 + year if year < 50 else 1900 + year
                        try:
                            return datetime(year, month, day)
                        except ValueError:
                            current_app.logger.warning(f"日期值无效: {date_value}")
                    
                    # 如果无法解析，记录警告并返回当前时间
                    current_app.logger.warning(f"无法解析日期格式: {date_value}")
                    return datetime.now()
                except Exception as e:
                    current_app.logger.warning(f"处理日期字符串出错: {str(e)}")
                    return datetime.now()
            
            # 其他情况返回当前时间
            return datetime.now()
        
        # 处理每个报价单
        for i, quotation_data in enumerate(quotations):
            try:
                project_name = quotation_data.get('project_name')
                quotation_number = quotation_data.get('quotation_number')
                
                if not project_name:
                    error_count += 1
                    error_details.append({
                        'line': i + 2,
                        'project_name': '未知',
                        'reason': '项目名称为空'
                    })
                    continue
                
                if not quotation_number:
                    error_count += 1
                    error_details.append({
                        'line': i + 2,
                        'project_name': project_name,
                        'reason': '报价单编号为空'
                    })
                    continue
                
                # 记录当前处理的报价单
                current_app.logger.info(f"处理报价单: 项目名称={project_name}, 编号={quotation_number}")
                
                # 查找项目，如果不存在则创建
                project = Project.query.filter_by(project_name=project_name).first()
                if not project:
                    # 创建新项目
                    project = Project(
                        project_name=project_name,
                        current_stage=quotation_data.get('project_stage', ''),
                        created_at=parse_date(quotation_data.get('created_at')),
                        updated_at=parse_date(quotation_data.get('updated_at')),
                        owner_id=owner_id if owner_id else current_user.id
                    )
                    db.session.add(project)
                    db.session.flush()  # 为项目生成ID
                
                # 检查该项目是否已经创建了报价单
                if project_name in quotation_map:
                    # 如果已存在，使用已创建的报价单
                    new_quotation = quotation_map[project_name]
                    current_app.logger.info(f"使用已创建的报价单: {project_name} -> {new_quotation.quotation_number}")
                else:
                    # 检查数据库中是否已有此项目的报价单
                    existing_quotation = Quotation.query.filter_by(project_id=project.id).first()
                    conflict_action = quotation_data.get('conflict_action')
                    
                    # 处理冲突
                    if existing_quotation:
                        if conflict_action == 'ignore':
                            skipped_count += 1
                            current_app.logger.info(f"跳过已存在的报价单: {project_name}")
                            continue
                        elif conflict_action == 'overwrite':
                            # 删除现有报价单及其明细
                            for detail in existing_quotation.details:
                                db.session.delete(detail)
                            db.session.delete(existing_quotation)
                            db.session.flush()
                            current_app.logger.info(f"删除并替换已存在的报价单: {project_name}")
                            
                            # 使用前端传来的编号创建新报价单
                            new_quotation = Quotation(
                                quotation_number=quotation_number,  # 使用前端传入的编号
                                project_id=project.id,
                                amount=float(quotation_data.get('amount', 0)),
                                project_stage=quotation_data.get('project_stage', ''),
                                created_at=parse_date(quotation_data.get('created_at')),
                                updated_at=parse_date(quotation_data.get('updated_at')),
                                owner_id=owner_id if owner_id else current_user.id
                            )
                            
                            db.session.add(new_quotation)
                            db.session.flush()  # 生成ID和自动报价单编号（如果未提供）
                        else:
                            # 如果是'add'，则使用现有的报价单，不创建新的
                            new_quotation = existing_quotation
                            current_app.logger.info(f"使用已存在项目的报价单: {project_name} -> {new_quotation.quotation_number}")
                    else:
                        # 如果项目不存在报价单，则创建新的
                        new_quotation = Quotation(
                            quotation_number=quotation_number,  # 使用前端传入的编号
                            project_id=project.id,
                            amount=float(quotation_data.get('amount', 0)),
                            project_stage=quotation_data.get('project_stage', ''),
                            created_at=parse_date(quotation_data.get('created_at')),
                            updated_at=parse_date(quotation_data.get('updated_at')),
                            owner_id=owner_id if owner_id else current_user.id
                        )
                        
                        db.session.add(new_quotation)
                        db.session.flush()  # 生成ID和自动报价单编号（如果未提供）
                    
                    # 记录新生成的报价单编号以便日志跟踪
                    if new_quotation.quotation_number != quotation_number and not (existing_quotation and conflict_action == 'add'):
                        current_app.logger.info(f"报价单编号已更改: 从 {quotation_number} 到 {new_quotation.quotation_number}")
                    
                    # 将报价单存入映射表
                    quotation_map[project_name] = new_quotation
                    
                    # 只有新创建报价单时才增加计数
                    if not (existing_quotation and conflict_action == 'add'):
                        imported_count += 1
                
                # 创建报价单明细
                details = quotation_data.get('details', [])
                current_app.logger.info(f"报价单明细数量: {len(details)}")
                
                for j, detail_data in enumerate(details):
                    try:
                        # 记录明细数据
                        current_app.logger.debug(f"处理明细 #{j+1}: {project_name}")
                        
                        # 数值类型转换
                        try:
                            discount = float(detail_data.get('discount', 1.0))
                            if discount < 0:
                                discount = 0
                        except (ValueError, TypeError):
                            discount = 1.0
                            
                        try:
                            market_price = float(detail_data.get('market_price', 0))
                        except (ValueError, TypeError):
                            market_price = 0
                            
                        try:
                            unit_price = float(detail_data.get('unit_price', 0))
                        except (ValueError, TypeError):
                            unit_price = 0
                            
                        try:
                            total_price = float(detail_data.get('total_price', 0))
                        except (ValueError, TypeError):
                            total_price = 0
                        
                        # 创建报价单明细
                        new_detail = QuotationDetail(
                            quotation_id=new_quotation.id,
                            product_name=detail_data.get('product_name', ''),
                            product_model=detail_data.get('product_model', ''),
                            product_desc=detail_data.get('product_desc', ''),
                            brand=detail_data.get('brand', ''),
                            unit=detail_data.get('unit', ''),
                            discount=discount,
                            market_price=market_price,
                            unit_price=unit_price,
                            total_price=total_price,
                            product_mn=detail_data.get('product_mn', ''),
                            created_at=parse_date(detail_data.get('created_at')),
                            updated_at=parse_date(detail_data.get('updated_at'))
                        )
                        db.session.add(new_detail)
                        details_count += 1
                    except Exception as detail_error:
                        current_app.logger.error(f"处理报价单明细时出错: {str(detail_error)}")
                        # 错误继续，不中断整个流程
                
            except Exception as quotation_error:
                db.session.rollback()
                current_app.logger.error(f"导入报价单时出错: {str(quotation_error)}")
                error_count += 1
                error_details.append({
                    'line': i + 2,
                    'project_name': project_name if project_name else '未知',
                    'reason': f"导入失败: {str(quotation_error)}"
                })
                
        # 最终提交所有改动
        try:
            db.session.commit()
        except Exception as commit_error:
            db.session.rollback()
            current_app.logger.error(f"提交报价单数据时出错: {str(commit_error)}")
            return jsonify({
                'success': False,
                'message': f'提交数据失败: {str(commit_error)}'
            }), 500
        
        current_app.logger.info(f"导入报价单完成: 成功={imported_count}, 明细={details_count}, 跳过={skipped_count}, 错误={error_count}")
        
        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'details_count': details_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'error_details': error_details
        })
        
    except Exception as e:
        current_app.logger.error(f"批量导入报价单出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'导入失败: {str(e)}'
        }), 500

@api_bp.route('/accounts/list', methods=['GET'])
@login_required
def get_accounts_list():
    """获取用户账户列表，按公司分组"""
    try:
        # 获取可访问的用户
        viewable_user_ids = current_user.get_viewable_user_ids()
        users = User.query.filter(User.id.in_(viewable_user_ids)).all()
        
        # 构建用户列表
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'name': user.name or user.username,
                'username': user.username,
                'role': user.role,
                'company': user.company_name or '未分配公司'
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        current_app.logger.error(f"获取用户账户列表出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户账户列表失败: {str(e)}'
        }), 500

@api_bp.route('/quotations/batch-delete', methods=['POST'])
@login_required
@permission_required('quotation', 'delete')
def batch_delete_quotations():
    """批量删除报价单"""
    try:
        data = request.json
        quotation_ids = data.get('quotation_ids', [])
        
        if not quotation_ids:
            return jsonify({
                'success': False,
                'message': '没有提供要删除的报价单ID'
            }), 400
        
        # 状态计数
        deleted_count = 0
        error_count = 0
        error_details = []
        
        # 处理每个报价单
        for quotation_id in quotation_ids:
            try:
                # 查询报价单
                quotation = Quotation.query.get(quotation_id)
                
                if not quotation:
                    error_count += 1
                    error_details.append({
                        'id': quotation_id,
                        'reason': '找不到报价单'
                    })
                    continue
                
                # 删除报价单明细
                for detail in quotation.details:
                    db.session.delete(detail)
                
                # 删除报价单
                db.session.delete(quotation)
                db.session.commit()
                deleted_count += 1
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"删除报价单 {quotation_id} 时出错: {str(e)}")
                error_count += 1
                error_details.append({
                    'id': quotation_id,
                    'reason': f"删除失败: {str(e)}"
                })
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'error_count': error_count,
            'error_details': error_details
        })
        
    except Exception as e:
        current_app.logger.error(f"批量删除报价单出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500

@api_bp.route('/test-check-conflicts', methods=['POST'])
def test_check_conflicts():
    """专门用于测试的无权限检查的API路由"""
    try:
        # 添加详细日志记录，用于调试
        current_app.logger.info(f"测试API - 检查报价单冲突接收到的请求数据: {request.json}")
        current_app.logger.info(f"测试API - 请求内容类型: {request.headers.get('Content-Type')}")
        
        # 检查请求内容类型
        if not request.is_json:
            current_app.logger.warning(f"测试API - 请求不是JSON格式: {request.headers.get('Content-Type')}")
            return jsonify({
                'success': False,
                'message': '请求格式不正确，应为JSON'
            }), 400
            
        data = request.json
        quotations = data.get('quotations', [])
        
        if not quotations:
            error_msg = '没有提供报价单数据'
            current_app.logger.warning(f"测试API - 检查报价单冲突失败: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
        
        # 返回成功响应，用于测试
        return jsonify({
            'success': True,
            'message': '测试API响应成功',
            'data': quotations
        })
        
    except Exception as e:
        import traceback
        error_msg = f"测试API - 检查报价单冲突出错: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': f'测试API - 检查冲突失败: {str(e)}'
        }), 500

@api_bp.route('/vendor-company-name')
@login_required
def get_vendor_company_name():
    """获取当前用户的企业名称"""
    
    # 获取当前用户的企业名称
    user_company_name = current_user.company_name if current_user.company_name else '厂商企业'
    
    return jsonify({
        'success': True,
        'data': {
            'company_name': user_company_name
        }
    }) 