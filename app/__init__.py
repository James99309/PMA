import app.utils.update_active_status_fix
from flask import Flask, session, redirect, url_for, request, current_app, flash
from config import Config
import logging
from app.extensions import db, migrate, login_manager, jwt, csrf, babel
import os
from flask_login import login_required, current_user, logout_user
from app.models import User
from app.routes.product import bp as product_bp
from app.routes.product_code import product_code_bp
from app.routes.product_management import product_management_bp
from datetime import timedelta, datetime
from app.utils import version_check
import datetime
from app.utils.filters import project_type_style, project_stage_style, format_date, format_datetime, format_currency
from app.utils.dictionary_helpers import (
    project_type_label, project_stage_label, report_source_label, authorization_status_label, company_type_label, product_situation_label, industry_label, status_label, brand_status_label, reporting_source_label, share_permission_label, user_label, get_role_display_name
)
from app.utils.access_control import can_edit_company_info, can_edit_data, can_change_company_owner, can_start_approval
from sqlalchemy.exc import OperationalError
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
import traceback
import json
from functools import wraps
from werkzeug.exceptions import HTTPException

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# 确保所有处理器都设置为DEBUG级别
for handler in logging.getLogger().handlers:
    handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# 定义受保护模板文件列表 - 这些文件不应被随意修改
PROTECTED_TEMPLATES = [
    # 'project/list.html',  # 项目列表页面 - 临时移除保护以进行阶段过滤修复
]

# 创建用于跟踪数据库查询时间的函数
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(datetime.datetime.now())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = datetime.datetime.now() - conn.info['query_start_time'].pop(-1)
    if total.total_seconds() > 0.5:  # 记录执行时间超过0.5秒的查询
        logger.warning(f"慢查询 ({total.total_seconds():.2f}s): {statement}")

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)
    
    # 设置应用版本
    app.config['APP_VERSION'] = '1.0.1'  # 根据实际版本修改
    
    # 添加Jinja扩展 - 支持try/except块
    app.jinja_env.add_extension('jinja2.ext.do')
    
    # 确保SECRET_KEY被设置
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'hard-to-guess-string-for-pma-app'
    
    # JWT配置
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_VERIFY_SUB'] = False  # 禁用sub声明验证，解决PyJWT 2.10.0版本兼容性问题
    
    # 会话配置
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 会话保持7天
    app.config['SESSION_COOKIE_SECURE'] = False  # 在开发环境中设为False，生产环境设为True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 调试模式或开发环境关闭CSRF
    if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1':
        app.config['WTF_CSRF_ENABLED'] = False
        logger.info("开发模式: CSRF保护已禁用")

    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)

    # 初始化登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化CSRF保护
    csrf.init_app(app)
    
    # 配置Babel国际化
    app.config['LANGUAGES'] = {'zh_CN': '简体中文', 'en': 'English'}
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'Asia/Shanghai'
    
    # 初始化Babel国际化
    from app.utils.i18n import get_current_language
    babel.init_app(app, locale_selector=get_current_language)
    
    # CSRF配置 - 排除API路由
    @csrf.exempt
    def csrf_exempt_api():
        # API路径豁免 - 修改为支持所有HTTP方法
        if request.path.startswith('/api/'):
            logger.debug(f'CSRF exempt API path: {request.path}, Method: {request.method}')
            return True
            
        # 语言切换API路径豁免
        if request.path.startswith('/language/'):
            logger.debug(f'CSRF exempt Language API path: {request.path}, Method: {request.method}')
            return True
            
        # 审批API路径豁免
        if request.path.startswith('/approval/api/'):
            logger.debug(f'CSRF exempt Approval API path: {request.path}, Method: {request.method}')
            return True
            
        # 审批配置模块API路径豁免
        if request.path.startswith('/admin/approval/field-options/'):
            logger.debug(f'CSRF exempt Approval Config API path: {request.path}, Method: {request.method}')
            return True
            
        # 批价单相关API路径豁免
        if request.path.startswith('/pricing_order/') and request.method in ['POST', 'PUT', 'DELETE']:
            logger.debug(f'CSRF exempt Pricing Order API path: {request.path}, Method: {request.method}')
            return True
            
        # 特定的product_code API路径豁免
        product_code_exempt_routes = [
            '/product-code/generate-preview',
            '/product-code/save',
            '/product-code/api/products',
            '/product-code/api/category/',
            '/product-code/api/subcategory/',
            '/product-code/api/generate-letter',
            '/product-code/api/generate-subcategory-letter',
            '/product-code/categories/update-order',
            '/product-code/api/subcategory/',
            '/product-code/api/category/'
        ]
        
        # 特定的product_management API路径豁免
        product_management_exempt_routes = [
            '/product-management/save',
            '/product-management/api/region-options',
            '/product-management/api/category/',
            '/product-management/api/subcategory/',
            '/product-management/',  # 根路径
            '/product-management/new',  # 新建产品
            '/product-management/api/',  # 所有API路径
            '/product-management/inventory',  # 库存页面
        ]
        
        # 添加产品管理的动态路径
        # 检查是否是产品管理的更新/删除/详情等动态路径
        if request.path.startswith('/product-management/'):
            parts = request.path.split('/')
            if len(parts) >= 3 and parts[2].isdigit():
                # 匹配形如 /product-management/数字/action 的路径
                return True
        
        # 项目管理模块路径豁免
        project_management_exempt_routes = [
            '/project/add',
            '/project/',
            '/project/edit/',
            '/project/delete/',
            '/project/search',
            '/project/view/',
            '/project/import',
            '/project/export',
        ]
        
        # 添加项目管理的动态路径
        # 检查是否是项目管理的编辑/删除/详情等动态路径
        if request.path.startswith('/project/'):
            parts = request.path.split('/')
            if len(parts) >= 3 and parts[2].isdigit():
                # 匹配形如 /project/数字/action 的路径
                return True
        
        for route in product_code_exempt_routes:
            if request.path.startswith(route):
                return True
        
        for route in product_management_exempt_routes:
            if request.path.startswith(route):
                return True
                
        for route in project_management_exempt_routes:
            if request.path.startswith(route):
                return True
                
        return False
        
    # CSRF配置 - 对于特定IP地址的请求豁免CSRF检查（内部应用间通信）
    @csrf.exempt
    def csrf_exempt_internal():
        allowed_ips = ['192.168.1.174', '127.0.0.1', 'localhost']
        remote_addr = request.remote_addr
        return remote_addr in allowed_ips

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 导入所有模型以确保它们被注册
    from app.models.user import User, Permission
    from app.models.customer import Company, Contact
    from app.models.project import Project
    from app.models.action import Action
    from app.models.quotation import Quotation
    from app.models.product import Product
    from app.models.product_code import ProductCategory, ProductCodeField, ProductCodeFieldOption, ProductCode, ProductCodeFieldValue
    from app.models.dev_product import DevProduct, DevProductSpec
    from app.models.dictionary import Dictionary
    from app.models.projectpm_statistics import ProjectStatistics
    from app.models.change_log import ChangeLog

    # 导入所有视图
    from app.views import main, customer, project, auth, user_bp
    from app.views.quotation import quotation
    from app.views.product_analysis import product_analysis
    from app.routes.api import api_bp
    from app.routes.projectpm_routes import bp as projectpm_bp
    from app.views.approval import approval_bp
    from app.views.approval_config import approval_config_bp
    
    # 导入新的API视图
    from app.api.v1 import api_v1_bp
    
    # 导入搜索API
    from app.api.v1.search import search_bp
    
    # 导入语言切换蓝图
    from app.views.language import language_bp

    # 导入评分系统蓝图
    from app.views.scoring_config import scoring_config
    from app.views.project_scoring_api import project_scoring_api
    
    # 导入历史记录蓝图
    from app.views.change_history import change_history_bp

    # 导入批价单蓝图
    from app.routes.pricing_order_routes import pricing_order_bp
    
    # 导入库存管理蓝图
    from app.routes.inventory import inventory

    # 注册所有Blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(customer, url_prefix='/customer')
    app.register_blueprint(project, url_prefix='/project')
    app.register_blueprint(quotation, url_prefix='/quotation')
    app.register_blueprint(product_analysis, url_prefix='/product_analysis')
    app.register_blueprint(product_bp, url_prefix='')
    app.register_blueprint(api_bp, url_prefix='/api')
    csrf.exempt(api_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(product_code_bp, url_prefix='/product-code')
    app.register_blueprint(product_management_bp, url_prefix='/product-management')
    app.register_blueprint(projectpm_bp, url_prefix='/projectpm')
    app.register_blueprint(approval_bp)
    app.register_blueprint(approval_config_bp)
    app.register_blueprint(pricing_order_bp, url_prefix='/pricing_order')  # 添加URL前缀
    csrf.exempt(pricing_order_bp)  # 豁免批价单蓝图的CSRF保护
    app.register_blueprint(inventory, url_prefix='/inventory')  # 注册库存管理蓝图
    
    # 注册API v1蓝图
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 注册搜索API蓝图
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')
    csrf.exempt(search_bp)
    
    # 注册语言切换蓝图
    from app.views.language import language_bp
    app.register_blueprint(language_bp)
    csrf.exempt(language_bp)
    
    # 注册管理员蓝图
    from app.views.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # 注册评分系统蓝图
    app.register_blueprint(scoring_config)
    app.register_blueprint(project_scoring_api)
    
    # 注册历史记录蓝图
    app.register_blueprint(change_history_bp)
    
    # 注册版本管理蓝图
    from app.views.version_management import version_management_bp
    app.register_blueprint(version_management_bp)
    
    # 注册备份管理蓝图
    from app.routes.backup_routes import backup_bp
    app.register_blueprint(backup_bp)
    
    # 注册测试功能蓝图
    from app.routes.test_routes import test_bp
    app.register_blueprint(test_bp, url_prefix='/test')
    
    # 添加版本信息API路由
    @app.route('/api/version', methods=['GET'])
    def get_app_version():
        """返回应用版本信息"""
        try:
            from app.utils.version_check import get_app_version
            version_info = get_app_version()
            return {'success': True, 'data': version_info}
        except Exception as e:
            logger.error(f"获取应用版本信息失败: {str(e)}")
            return {'success': False, 'message': '获取版本信息失败', 'error': str(e)}, 500
    
    # 数据初始化
    with app.app_context():
        # 创建数据库表
        db.create_all()
        logger.info("数据库表创建成功")
            
        # 版本检查
        try:
            from app.utils.version_check import update_version_check
            update_version_check()
            logger.info("应用版本检查完成")
        except Exception as e:
            logger.error(f"应用版本检查失败: {str(e)}")
        
        # 版本管理初始化
        try:
            from app.utils.version_management_init import initialize_version_management, apply_version_upgrades
            initialize_version_management()
            apply_version_upgrades()
            logger.info("版本管理系统初始化完成")
        except Exception as e:
            logger.error(f"版本管理系统初始化失败: {str(e)}")
        
        # 数据所有权初始化 - 已关闭
        '''
        try:
            from app.utils.data_init import initialize_data_ownership
            initialize_data_ownership()
            logger.info("数据所有权初始化成功")
        except Exception as e:
            logger.error(f"数据所有权初始化失败: {str(e)}")
        '''
        logger.info("数据所有权初始化已被关闭")
        
        # 字典数据初始化 - 已关闭
        '''
        try:
            from app.utils.dictionary_init import init_dictionary
            init_dictionary()
            logger.info("字典数据初始化成功")
        except Exception as e:
            logger.error(f"字典数据初始化失败: {str(e)}")
        '''
        logger.info("字典数据初始化已被关闭")

    # 登录检查
    @app.before_request
    def check_login():
        """检查登录状态和角色一致性"""
        # 排除不需要登录的路径
        excluded_paths = [
            '/auth/login', '/auth/logout', '/auth/register', 
            '/auth/forgot-password', '/auth/reset-password',
            '/auth/activate', '/static', '/api/version',
            '/language/current', '/language/switch'
        ]
        
        # 检查当前路径是否需要登录
        if any(request.path.startswith(path) for path in excluded_paths):
            return
            
        # 如果用户未登录，重定向到登录页面
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        # 如果用户已登录，检查角色一致性
        if current_user.is_authenticated:
            # 从数据库重新获取用户信息
            from app.models.user import User
            db_user = User.query.get(current_user.id)
            
            if not db_user:
                # 用户在数据库中不存在，强制登出
                logger.warning(f"用户 {current_user.username} 在数据库中不存在，强制登出")
                logout_user()
                session.clear()
                flash('用户信息已失效，请重新登录', 'warning')
                return redirect(url_for('auth.login'))
            
            # 检查角色是否一致
            session_role = session.get('role')
            if session_role != db_user.role:
                logger.info(f"用户 {current_user.username} 角色不一致：会话中为 {session_role}，数据库中为 {db_user.role}，强制重新登录")
                logout_user()
                session.clear()
                flash(f'您的角色已更新为 {db_user.role}，请重新登录', 'info')
                return redirect(url_for('auth.login'))
            
            # 检查用户是否仍然活跃
            if not db_user.is_active:
                logger.warning(f"用户 {current_user.username} 已被禁用，强制登出")
                logout_user()
                session.clear()
                flash('您的账户已被禁用，请联系管理员', 'danger')
                return redirect(url_for('auth.login'))

    # 添加全局模板保护检查
    @app.before_request
    def check_protected_templates():
        """检查受保护的模板文件是否被修改"""
        try:
            for template_path in PROTECTED_TEMPLATES:
                full_path = os.path.join(app.root_path, 'templates', template_path)
                # 这里可以添加额外的检查逻辑，如文件哈希值验证等
                # 现在仅作为标记
                pass
        except Exception as e:
            app.logger.error(f"模板保护检查失败: {str(e)}")

    # 添加全局上下文处理器
    @app.context_processor
    def inject_protected_templates():
        """向模板上下文注入受保护模板列表"""
        return {'protected_templates': PROTECTED_TEMPLATES}
        
    # 添加用户查询上下文处理器
    @app.context_processor
    def inject_user_helpers():
        """向模板上下文注入用户辅助函数"""
        def get_user_by_id(user_id):
            """根据用户ID获取用户对象"""
            if not user_id:
                return None
            from app.models.user import User
            return User.query.get(int(user_id))
        
        return {'get_user_by_id': get_user_by_id}
        
    # 确保current_user在模板中可用
    @app.context_processor
    def inject_current_user():
        """向模板上下文注入current_user"""
        from flask_login import current_user
        return {'current_user': current_user}
        
    # 添加权限检查全局上下文处理器
    @app.context_processor
    def inject_permissions():
        """向模板上下文注入当前用户的权限信息"""
        def has_permission(module, action):
            from flask_login import current_user
            import sys
            print(f"[DEBUG][context_processor.has_permission] user={getattr(current_user, 'username', None)}, role={getattr(current_user, 'role', None)}, module={module}, action={action}", file=sys.stderr)
            
            try:
                # 如果用户未登录，则没有权限
                if not current_user.is_authenticated:
                    print("[DEBUG][context_processor.has_permission] not authenticated, return False", file=sys.stderr)
                    return False
                    
                # 管理员和CEO默认拥有所有权限
                from app.permissions import is_admin_or_ceo
                if is_admin_or_ceo():
                    print(f"[DEBUG][context_processor.has_permission] admin/ceo ({current_user.role}), return True", file=sys.stderr)
                    return True
                    
                # 获取角色权限
                from app.models.role_permissions import RolePermission
                role_permission = RolePermission.query.filter_by(role=current_user.role, module=module).first()
                role_has_permission = False
                if role_permission:
                    if action == 'view':
                        role_has_permission = role_permission.can_view
                    elif action == 'create':
                        role_has_permission = role_permission.can_create
                    elif action == 'edit':
                        role_has_permission = role_permission.can_edit
                    elif action == 'delete':
                        role_has_permission = role_permission.can_delete
                    
                # 获取个人权限
                from app.models.user import Permission
                permission = Permission.query.filter_by(user_id=current_user.id, module=module).first()
                personal_has_permission = False
                if permission:
                    if action == 'view':
                        personal_has_permission = permission.can_view
                    elif action == 'create':
                        personal_has_permission = permission.can_create
                    elif action == 'edit':
                        personal_has_permission = permission.can_edit
                    elif action == 'delete':
                        personal_has_permission = permission.can_delete
                
                # 最终权限 = 角色权限 OR 个人权限
                final_permission = role_has_permission or personal_has_permission
                
                if role_permission:
                    print(f"[DEBUG][context_processor.has_permission] using role_permission: role={current_user.role}, module={module}", file=sys.stderr)
                
                return final_permission
                
            except Exception as e:
                # 发生数据库错误时，回滚事务并记录错误
                print(f"[ERROR][context_processor.has_permission] Database error: {str(e)}", file=sys.stderr)
                try:
                    from app import db
                    db.session.rollback()
                    print("[DEBUG][context_processor.has_permission] Transaction rolled back", file=sys.stderr)
                except Exception as rollback_error:
                    print(f"[ERROR][context_processor.has_permission] Rollback failed: {str(rollback_error)}", file=sys.stderr)
                
                # 对于权限检查失败，默认返回False（安全策略）
                # 但对于管理员和CEO，即使数据库出错也应该有权限
                from app.permissions import is_admin_or_ceo
                if is_admin_or_ceo():
                    print(f"[DEBUG][context_processor.has_permission] Admin/CEO fallback ({current_user.role}), return True", file=sys.stderr)
                    return True
                
                return False
                
        # 添加管理员/CEO检查函数到模板上下文
        def is_admin_or_ceo_template():
            from app.permissions import is_admin_or_ceo
            return is_admin_or_ceo()
            
        return {
            'has_permission': has_permission,
            'is_admin_or_ceo': is_admin_or_ceo_template
        }

    # 添加公司编辑权限函数到模板上下文
    @app.context_processor
    def inject_company_edit_permission():
        """向模板注入公司编辑权限函数"""
        from app.views.quotation import can_view_quotation
        from app.utils.access_control import can_start_approval
        
        def get_project_by_id(project_id):
            from app.models.project import Project
            return Project.query.get(project_id)
        
        def get_quotation_by_id(quotation_id):
            from app.models.quotation import Quotation
            return Quotation.query.get(quotation_id)
        
        def get_company_by_id(company_id):
            from app.models.customer import Company
            return Company.query.get(company_id)
        
        return {
            'can_edit_company_info': can_edit_company_info,
            'can_edit_data': can_edit_data,
            'can_change_company_owner': can_change_company_owner,
            'can_view_quotation': can_view_quotation,
            'can_start_approval': can_start_approval,
            'get_project_by_id': get_project_by_id,
            'get_quotation_by_id': get_quotation_by_id,
            'get_company_by_id': get_company_by_id
        }

    # 注册自定义过滤器
    from app.utils.filters import project_type_style, project_stage_style, format_date, format_datetime, format_currency

    # 在create_app函数内
    app.jinja_env.filters['project_type_style'] = project_type_style
    app.jinja_env.filters['project_stage_style'] = project_stage_style
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['project_type_label'] = project_type_label
    app.jinja_env.filters['project_stage_label'] = project_stage_label
    app.jinja_env.filters['report_source_label'] = report_source_label
    app.jinja_env.filters['authorization_status_label'] = authorization_status_label
    app.jinja_env.filters['company_type_label'] = company_type_label
    app.jinja_env.filters['product_situation_label'] = product_situation_label
    app.jinja_env.filters['industry_label'] = industry_label
    app.jinja_env.filters['status_label'] = status_label
    app.jinja_env.filters['brand_status_label'] = brand_status_label
    app.jinja_env.filters['reporting_source_label'] = reporting_source_label
    app.jinja_env.filters['user_label'] = user_label
    app.jinja_env.filters['share_permission_label'] = share_permission_label

    def datetimeformat(value):
        if not value:
            return '-'
        try:
            return datetime.fromtimestamp(float(value)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(value)

    app.jinja_env.filters['datetimeformat'] = datetimeformat

    # 导入并运行模板检查
    # try:
    #     from app.check_templates import check_templates
    #     # 检查并修复模板问题
    #     check_templates()
    # except Exception as e:
    #     app.logger.warning(f"模板检查时出错: {str(e)}")

    app.jinja_env.globals['now'] = datetime.datetime.now

    # 注册为全局函数，便于模板直接调用
    app.jinja_env.globals['project_stage_label'] = project_stage_label

    # 统计图表
    from app.views.projectpm_statistics import projectpm_statistics
    app.register_blueprint(projectpm_statistics, url_prefix='/projectpm/statistics')

    app.jinja_env.globals['get_role_display_name'] = get_role_display_name

    # 注册全局权限函数上下文处理器
    from app.context_processors import inject_permission_functions
    app.context_processor(inject_permission_functions)

    # 注册通知蓝图
    from app.routes.notification import notification
    app.register_blueprint(notification)

    # 添加审批相关函数到模板上下文
    from app.context_processors import inject_approval_functions
    app.context_processor(inject_approval_functions)
    
    # 添加项目相关函数到模板上下文
    from app.context_processors import inject_project_functions
    app.context_processor(inject_project_functions)

    # 添加项目阶段配置函数到模板上下文
    from app.context_processors import inject_project_stages_config
    app.context_processor(inject_project_stages_config)

    # 添加用户辅助函数到模板上下文
    from app.context_processors import inject_user_helpers
    app.context_processor(inject_user_helpers)

    # 注册全局帮助函数
    from app.helpers.ui_helpers import format_datetime, render_action_button, render_user_badge, get_user_display_name, render_filter_button
    app.jinja_env.globals['format_datetime'] = format_datetime
    app.jinja_env.globals['render_action_button'] = render_action_button
    app.jinja_env.globals['render_user_badge'] = render_user_badge
    app.jinja_env.globals['get_user_display_name'] = get_user_display_name
    app.jinja_env.globals['render_filter_button'] = render_filter_button
    
    # 从approval_helpers导入ApprovalStatus并注册到Jinja环境中
    from app.models.approval import ApprovalStatus
    app.jinja_env.globals['ApprovalStatus'] = ApprovalStatus
    
    # 将审批相关函数直接添加到Jinja的globals中
    from app.helpers.approval_helpers import (
        get_available_templates,
        get_object_approval_instance,
        can_user_approve,
        get_current_step_info,
        get_object_type_display,
        check_template_in_use,
        get_rejected_approval_history,
        get_template_steps,
        get_workflow_steps,
        get_pending_approval_count
    )
    app.jinja_env.globals['get_available_templates'] = get_available_templates
    app.jinja_env.globals['get_object_approval_instance'] = get_object_approval_instance
    app.jinja_env.globals['can_user_approve'] = can_user_approve
    app.jinja_env.globals['get_current_step_info'] = get_current_step_info
    app.jinja_env.globals['get_object_type_display'] = get_object_type_display
    app.jinja_env.globals['check_template_in_use'] = check_template_in_use
    app.jinja_env.globals['get_rejected_approval_history'] = get_rejected_approval_history
    app.jinja_env.globals['get_template_steps'] = get_template_steps
    app.jinja_env.globals['get_workflow_steps'] = get_workflow_steps
    app.jinja_env.globals['get_pending_approval_count'] = get_pending_approval_count
    
    # 添加权限检查和业务对象获取函数
    from app.utils.access_control import can_start_approval
    app.jinja_env.globals['can_start_approval'] = can_start_approval
    
    def get_project_by_id(project_id):
        from app.models.project import Project
        return Project.query.get(project_id)
    
    def get_quotation_by_id(quotation_id):
        from app.models.quotation import Quotation
        return Quotation.query.get(quotation_id)
    
    def get_company_by_id(company_id):
        from app.models.customer import Company
        return Company.query.get(company_id)
    
    def get_pricing_order_by_id(pricing_order_id):
        from app.models.pricing_order import PricingOrder
        return PricingOrder.query.get(pricing_order_id)
    
    app.jinja_env.globals['get_project_by_id'] = get_project_by_id
    app.jinja_env.globals['get_quotation_by_id'] = get_quotation_by_id
    app.jinja_env.globals['get_company_by_id'] = get_company_by_id
    app.jinja_env.globals['get_pricing_order_by_id'] = get_pricing_order_by_id

    # 添加日志调试信息
    @app.context_processor
    def inject_debug_functions():
        """注入调试函数"""
        def debug_log(message):
            current_app.logger.info(message)
            return ''
        return {'debug_log': debug_log}

    # 添加审批调试函数
    @app.before_request
    def debug_approval_templates():
        # 使用current_app而不是直接app
        from flask import current_app, request
        if request and request.endpoint == 'project.view_project':
            from app.helpers.approval_helpers import get_available_templates
            templates = get_available_templates('project')
            current_app.logger.info(f"测试项目模板数量: {len(templates)}")
            for t in templates:
                current_app.logger.info(f"模板: {t.id} - {t.name} (活跃: {t.is_active})")

            # 初始化系统设置
    with app.app_context():
        try:
            from app.models.settings import initialize_default_settings
            initialize_default_settings()
            app.logger.info("系统默认设置初始化完成")
        except Exception as e:
            app.logger.error(f"初始化系统设置时出错: {str(e)}")
            
        # 初始化备份服务
        try:
            from app.services.database_backup import init_backup_service
            backup_service = init_backup_service(app)
            app.logger.info("数据库备份服务初始化完成")
        except Exception as e:
            app.logger.error(f"初始化数据库备份服务时出错: {str(e)}")
    
    # 注册上下文处理器
    from app.utils.access_control import register_context_processors
    register_context_processors(app)

    return app 