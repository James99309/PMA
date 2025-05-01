from flask import Flask, session, redirect, url_for, request
from config import Config
import logging
from app.extensions import db, migrate, login_manager, jwt
import os
from flask_login import login_required, current_user
from app.models import User
from app.routes.product import bp as product_bp
from app.routes.product_code import product_code_bp
from app.routes.product_management import product_management_bp
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化CSRF保护
csrf = CSRFProtect()

# 定义受保护模板文件列表 - 这些文件不应被随意修改
PROTECTED_TEMPLATES = [
    'project/list.html',  # 项目列表页面 - 修改前必须获得倪捷的明确许可
]

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
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
    
    # CSRF配置 - 排除API路由
    @csrf.exempt
    def csrf_exempt_api():
        # API路径豁免
        if request.path.startswith('/api/'):
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

    # 导入所有视图
    from app.views import main, customer, project, auth, user_bp
    from app.views.quotation import quotation
    from app.routes.api import api_bp
    
    # 导入新的API视图
    from app.api.v1 import api_v1_bp

    # 注册所有Blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(customer, url_prefix='/customer')
    app.register_blueprint(project, url_prefix='/project')
    app.register_blueprint(quotation, url_prefix='/quotation')
    app.register_blueprint(product_bp, url_prefix='')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(product_code_bp, url_prefix='/product-code')
    app.register_blueprint(product_management_bp, url_prefix='/product-management')
    
    # 注册API v1蓝图
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 数据初始化
    with app.app_context():
        # 创建数据库表
        db.create_all()
        logger.info("数据库表创建成功")
        
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
        logger.debug('Request URL: %s', request.url)
        logger.debug('Request Endpoint: %s', request.endpoint)
        logger.debug('Session: %s', session)
        
        # 不需要登录就能访问的路由
        public_endpoints = ['auth.login', 'auth.register', 'static']
        public_paths = [
            '/auth/login', 
            '/auth/register', 
            '/auth/forgot-password',
            # 添加密码重置路径到公开路径，使用startswith确保所有带token的路径都可以访问
            '/auth/reset-password'
        ]
        
        # 检查是否是API请求（API请求由JWT处理）
        if request.path.startswith('/api/'):
            return
        
        # 检查是否是公开路径 - 使用startswith来匹配以公开路径开头的URL
        for path in public_paths:
            if request.path.startswith(path):
                logger.debug('Public path, skipping auth check')
                return
        
        # 检查是否是静态文件
        if request.endpoint and request.endpoint.startswith('static'):
            logger.debug('Static file request, skipping auth check')
            return
        
        # 使用Flask-Login的current_user检查用户是否已登录
        if not current_user.is_authenticated:
            logger.debug('User not logged in, redirecting to login')
            return redirect(url_for('auth.login'))
        
        logger.debug('User is logged in, proceeding with request')

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
        
    # 添加权限检查全局上下文处理器
    @app.context_processor
    def inject_permissions():
        """向模板上下文注入当前用户的权限信息"""
        def has_permission(module, action):
            from flask_login import current_user
            from app.permissions import check_permission, Permissions
            
            # 如果用户未登录，则没有权限
            if not current_user.is_authenticated:
                return False
                
            # 管理员默认拥有所有权限
            if current_user.role == 'admin':
                return True
            
            try:
                # 首先检查基于角色的权限系统
                permission_name = f"{module}_{action}"
                permission_attr = getattr(Permissions, permission_name.upper(), None)
                
                if permission_attr is not None:
                    if check_permission(permission_attr):
                        return True
                
                # 然后检查数据库中的用户权限记录
                return current_user.has_permission(module, action)
            except Exception as e:
                app.logger.error(f"权限检查错误: {str(e)}")
                return False
            
        return {'has_permission': has_permission}

    # 注册自定义过滤器
    from app.utils.filters import project_type_style, project_stage_style, format_date, format_datetime, format_currency

    # 在create_app函数内
    app.jinja_env.filters['project_type_style'] = project_type_style
    app.jinja_env.filters['project_stage_style'] = project_stage_style
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_currency'] = format_currency

    return app 