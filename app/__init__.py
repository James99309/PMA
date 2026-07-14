import app.utils.update_active_status_fix
from flask import Flask, session, redirect, url_for, request, current_app, flash
from config import Config
import logging
from app.extensions import db, migrate, login_manager, jwt, csrf, babel
import os
from flask_login import login_required, current_user, logout_user
from app.models import User
from app.models.temp_product import TempProduct
from app.routes.product import bp as product_bp
from app.routes.product_code import product_code_bp
# 研发库已废弃，相关蓝图已移除 (2025-12-26)
# from app.routes.product_management import product_management_bp
# from app.routes.dev_product_management import bp as dev_product_bp
from app.routes.performance import register_performance_routes
from datetime import timedelta, datetime
from app.utils import version_check
import datetime
from app.utils.filters import project_type_style, project_stage_style, format_date, format_datetime, format_currency, format_achievement_rate
from app.utils.dictionary_helpers import (
    project_type_label, project_stage_label, project_type_label_i18n, project_stage_label_i18n, report_source_label, authorization_status_label, company_type_label, company_type_color, product_situation_label, industry_label, industry_color, status_label, share_permission_label, user_label, get_role_display_name, get_all_active_roles, get_all_user_companies, get_amount_unit_config, get_currency_symbol, get_default_currency, approval_status_label, product_type_label, product_status_label, dev_product_status_label, active_status_label, country_label,
    activity_status_label, activity_status_color,
    make_i18n_filter
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
    
    # 检查存储配置
    try:
        force_local_storage = os.getenv('FORCE_LOCAL_STORAGE', '').lower() == 'true'
        force_cloud_upload = os.getenv('FORCE_CLOUD_UPLOAD', '').lower() == 'true'
        supabase_url = os.getenv('SUPABASE_URL')

        # 只在明确要求云端上传且缺少配置时才尝试加载 .env.supabase.prod
        if force_cloud_upload and not supabase_url:
            logger.info("FORCE_CLOUD_UPLOAD=true 但缺少 SUPABASE_URL，尝试从配置文件加载...")
            env_file_path = os.path.join(os.path.dirname(app.root_path), '.env.supabase.prod')
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key in ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_BUCKET', 'FORCE_CLOUD_UPLOAD']:
                                os.environ[key] = value
                                logger.info(f"已从配置文件加载环境变量: {key}")

        # 记录最终的存储配置状态
        logger.info(f"Flask应用创建时的存储配置:")
        logger.info(f"  FORCE_LOCAL_STORAGE: {os.getenv('FORCE_LOCAL_STORAGE', 'NOT SET')}")
        logger.info(f"  NAS_STORAGE_ENABLED: {os.getenv('NAS_STORAGE_ENABLED', 'NOT SET')}")
        logger.info(f"  SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
        logger.info(f"  FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD', 'NOT SET')}")

    except Exception as e:
        logger.error(f"加载存储配置时出错: {e}")
    
    # 统一版本号管理 - 优先使用配置文件中的版本号
    if not app.config.get('APP_VERSION'):
        app.config['APP_VERSION'] = '1.2.2'  # 兜底版本号
    
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

    # 多 localhost 实例隔离:本地同时跑多个 PMA(主 worktree + RF + mobile-test 等)
    # 都用默认 cookie 名 'session' 会互相覆盖 → 各自跳登录。按 PORT 派生 cookie 名,
    # 让每个实例的 session/remember 互不影响。
    # 生产 / NAS / 单一实例场景:不设 PORT 时回退默认名,行为不变。
    _local_port = (os.environ.get('PORT') or os.environ.get('FLASK_RUN_PORT') or '').strip()
    if _local_port:
        app.config['SESSION_COOKIE_NAME']  = f'pma_session_{_local_port}'
        app.config['REMEMBER_COOKIE_NAME'] = f'pma_remember_{_local_port}'
    
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

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        # AJAX / API 请求返回 JSON 401，避免返回 HTML 重定向
        if (request.is_json
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or request.path.startswith('/api/')
                or '/api/' in request.path):
            return jsonify({'success': False, 'message': '会话已过期，请刷新页面重新登录'}), 401
        return redirect(url_for('auth.login', next=request.url))
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化CSRF保护
    csrf.init_app(app)
    
    # 配置Babel国际化
    app.config['LANGUAGES'] = {'zh': '简体中文', 'en': 'English'}
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
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
            
        # 库存管理审批API路径豁免
        if request.path.startswith('/inventory/api/approval/'):
            logger.debug(f'CSRF exempt Inventory Approval API path: {request.path}, Method: {request.method}')
            return True
            
        # 审批操作路径豁免（包括审批通过/拒绝操作）
        if request.path.startswith('/approval/approve/') or request.path.startswith('/approval/process/'):
            logger.debug(f'CSRF exempt Approval Action path: {request.path}, Method: {request.method}')
            return True

        # Claude AI 代理 API 路径豁免（/user/api/<id>/claude-ai/*）
        if '/claude-ai' in request.path and '/api/' in request.path:
            logger.debug(f'CSRF exempt Claude AI API path: {request.path}, Method: {request.method}')
            return True

        # 报销模块API路径豁免
        if request.path.startswith('/expense/api/'):
            logger.debug(f'CSRF exempt Expense API path: {request.path}, Method: {request.method}')
            return True

        # CLI Agent API 路径豁免:闲置超 1h 后 CSRF token 过期会导致 HTTP 400
        # 已有 @login_required + _require_cli_access() 双重保护,JSON 请求 + 自定义 header
        if request.path.startswith('/cli/api/'):
            logger.debug(f'CSRF exempt CLI API path: {request.path}, Method: {request.method}')
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
        
        # 研发库已废弃，相关豁免路由已移除 (2025-12-26)

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
    from app.models.company_asset import CompanyAsset
    from app.models.performance_config import (
        PerformanceMetricsDefinition, RolePerformanceConfig, RolePerformanceItem,
        PerformanceFormulaTemplate, RolePerformanceAccess
    )
    from app.models.data_source_config import DataTableConfig, DataFieldConfig, FormulaTemplate
    from app.models.prospect_project import ProspectProject, ProspectStakeholder
    from app.models.prospect_claim_request import ProspectClaimRequest
    from app.models.chat import ChatConversation, ChatParticipant, ChatMessage, ChatTranslation
    from app.models.training import (
        TrainingModuleState, TrainingQuizAttempt,
        TrainingStreak, TrainingApplicationSubmission,
    )
    from app.models.course import InteractiveCourse

    # 导入所有视图
    from app.views import main, customer, project, auth, user_bp
    from app.views.quotation import quotation
    from app.views.product_analysis import product_analysis
    from app.routes.api import api_bp
    from app.routes.projectpm_routes import bp as projectpm_bp
    from app.views.approval import approval_bp
    from app.views.approval_config import approval_config_bp
    from app.views.performance_config import performance_config_bp
    
    # 导入新的API视图
    from app.api.v1 import api_v1_bp
    
    # 导入搜索API
    from app.api.v1.search import search_bp
    
    # 导入汇率API
    from app.api.v1.exchange_rate import exchange_rate_bp
    
    # 导入临时产品API蓝图
    from app.api.v1.temp_products import temp_products_bp
    
    # 导入导出辅助API蓝图
    from app.api.v1.export_helpers import export_helpers_api
    
    # 导入语言切换蓝图
    from app.views.language import language_bp

    # 导入评分系统蓝图
    from app.views.scoring_config import scoring_config
    from app.views.project_scoring_api import project_scoring_api
    
    # 导入历史记录蓝图
    from app.views.change_history import change_history_bp

    # 导入批价单蓝图
    from app.routes.pricing_order_routes import pricing_order_bp

    # 导入客户订单蓝图
    from app.routes.sales_order_routes import sales_order_bp

    # 导入发货管理蓝图
    from app.routes.shipment_routes import shipment_bp

    # 导入序列号管理蓝图
    from app.routes.product_sn_routes import product_sn_bp

    # AT 设计系统预览(开发期临时)
    from app.routes.at_preview_routes import at_preview_bp

    # 中国官网预览(测试用途,需登录)
    from app.routes.website_preview_routes import website_preview_bp

    # 导入库存管理蓝图
    from app.routes.inventory import inventory

    # 导入采购订单蓝图（Tailwind风格）
    from app.routes.purchase_order_routes import purchase_order_bp

    # 导入报销管理蓝图
    from app.views.expense import expense

    # 导入 NAS 存储代理蓝图
    from app.views.storage import storage_bp

    # 导入配置管理蓝图
    from app.views.config_management import config_management_bp


    # 导入工作日历蓝图
    from app.views.worklog import worklog

    # 导入积分系统蓝图
    from app.views.points import points_bp

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
    # 研发库已废弃 (2025-12-26)
    # app.register_blueprint(product_management_bp, url_prefix='/product-management')
    # app.register_blueprint(dev_product_bp)
    app.register_blueprint(projectpm_bp, url_prefix='/projectpm')
    app.register_blueprint(approval_bp)
    app.register_blueprint(approval_config_bp)
    app.register_blueprint(performance_config_bp)
    app.register_blueprint(pricing_order_bp, url_prefix='/pricing_order')  # 添加URL前缀
    csrf.exempt(pricing_order_bp)  # 豁免批价单蓝图的CSRF保护
    app.register_blueprint(sales_order_bp, url_prefix='/sales-order')  # 注册客户订单蓝图
    csrf.exempt(sales_order_bp)  # 豁免客户订单蓝图的CSRF保护
    app.register_blueprint(shipment_bp, url_prefix='/shipment')  # 注册发货管理蓝图
    csrf.exempt(shipment_bp)  # 豁免发货管理蓝图的CSRF保护
    app.register_blueprint(product_sn_bp, url_prefix='/product-sn')  # 注册序列号管理蓝图
    csrf.exempt(product_sn_bp)  # 豁免序列号管理蓝图的CSRF保护

    app.register_blueprint(at_preview_bp)  # AT 设计系统预览(开发期)
    app.register_blueprint(website_preview_bp)  # 中国官网预览(测试用途,需登录)
    app.register_blueprint(inventory, url_prefix='/inventory')  # 注册库存管理蓝图
    app.register_blueprint(purchase_order_bp)  # 注册采购订单蓝图（Tailwind风格）
    csrf.exempt(purchase_order_bp)  # 豁免采购订单蓝图的CSRF保护
    app.register_blueprint(expense, url_prefix='/expense')  # 注册报销管理蓝图
    app.register_blueprint(storage_bp)  # 注册 NAS 存储代理蓝图
    app.register_blueprint(config_management_bp)  # 注册配置管理蓝图
    csrf.exempt(config_management_bp)  # 豁免配置管理蓝图的CSRF保护

    # 注册工作日历蓝图
    app.register_blueprint(worklog)
    csrf.exempt(worklog)  # 豁免工作日历蓝图的CSRF保护

    # 注册通用实体附件蓝图(项目等复用同一套上传/删除)
    from app.views.attachments import attachments_bp
    app.register_blueprint(attachments_bp)
    csrf.exempt(attachments_bp)  # 上传为 multipart,豁免 CSRF(与 worklog 一致)

    # 注册积分系统蓝图
    app.register_blueprint(points_bp)

    # 注册文件管理蓝图
    from app.views.file_manager import file_manager_bp
    app.register_blueprint(file_manager_bp)
    csrf.exempt(file_manager_bp)  # 豁免文件管理蓝图的CSRF保护（用于文件上传）

    # 注册管理员视角的文件管理蓝图
    from app.views.file_manager_admin import file_manager_admin_bp
    app.register_blueprint(file_manager_admin_bp)
    csrf.exempt(file_manager_admin_bp)

    # 注册会议录音纪要蓝图
    from app.views.meeting import meeting
    app.register_blueprint(meeting)
    csrf.exempt(meeting)  # 豁免会议蓝图的CSRF保护（用于录音上传）

    # 注册 CLI Agent 智能终端蓝图（见 docs/plans/2026-04-05-pma-cli-agent-design.md）
    from app.views.cli import cli_bp
    app.register_blueprint(cli_bp)

    # 注册内置 Skill（首次启动时写入数据库，已存在则跳过）
    with app.app_context():
        try:
            from app.services.cli_agent.builtin_skills import register_builtin_skills
            register_builtin_skills()
        except Exception as e:
            app.logger.warning(f'内置 Skill 注册跳过: {e}')

    # 注册规格字典/模板管理蓝图（仅 SP8D/CN NAS 启用，OVS/SG NAS 数据通过物化视图只读同步）
    if not app.config.get('IS_OVS'):
        from app.views.spec_definition import spec_definition_bp
        app.register_blueprint(spec_definition_bp)
        csrf.exempt(spec_definition_bp)

        from app.views.spec_template import spec_template_bp
        app.register_blueprint(spec_template_bp)
        csrf.exempt(spec_template_bp)

    # 注册API v1蓝图
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    csrf.exempt(api_v1_bp)  # 豁免API v1蓝图的CSRF保护（供外部系统调用）

    # 为移动端 API 添加 CORS（允许 Capacitor WebView 跨域访问）
    from flask_cors import CORS
    CORS(app, resources={r'/api/v1/*': {
        'origins': '*',
        'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
    }}, supports_credentials=False)

    # 注册外部API蓝图（供Stargirl培训系统等外部系统调用）
    from app.api.external import external_api_bp
    app.register_blueprint(external_api_bp)
    csrf.exempt(external_api_bp)
    
    # 注册搜索API蓝图
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')
    csrf.exempt(search_bp)
    
    # 注册汇率API蓝图
    app.register_blueprint(exchange_rate_bp)
    csrf.exempt(exchange_rate_bp)
    
    # 注册临时产品API蓝图
    app.register_blueprint(temp_products_bp)
    csrf.exempt(temp_products_bp)
    
    # 注册导出辅助API蓝图
    app.register_blueprint(export_helpers_api)
    csrf.exempt(export_helpers_api)

    # 注册规格字典API蓝图
    from app.routes.spec_dictionary import spec_dict_bp
    app.register_blueprint(spec_dict_bp)
    csrf.exempt(spec_dict_bp)

    # 注册语言切换蓝图
    from app.views.language import language_bp
    app.register_blueprint(language_bp)
    csrf.exempt(language_bp)
    
    # 注册管理员蓝图
    from app.views.admin import admin_bp
    app.register_blueprint(admin_bp)

    # 钉钉集成管理蓝图（CN only） + 事件回调蓝图（CSRF 豁免）
    from app.views.dingtalk import dingtalk_bp, dingtalk_callback_bp
    app.register_blueprint(dingtalk_bp)
    app.register_blueprint(dingtalk_callback_bp)
    csrf.exempt(dingtalk_callback_bp)
    
    # 注册评分系统蓝图
    app.register_blueprint(scoring_config)
    app.register_blueprint(project_scoring_api)
    
    # 注册历史记录蓝图
    app.register_blueprint(change_history_bp)
    
    # 注册版本管理蓝图
    from app.views.version_management import version_management_bp
    app.register_blueprint(version_management_bp)
    
    # 注册知识库API蓝图
    from app.views.knowledge import knowledge_bp
    app.register_blueprint(knowledge_bp)
    csrf.exempt(knowledge_bp)

    # Wiki 知识库（Karpathy LLM Wiki 方案）
    from app.views.knowledge_wiki import knowledge_wiki_bp
    app.register_blueprint(knowledge_wiki_bp)
    csrf.exempt(knowledge_wiki_bp)

    # 团队 Skills 商店（内嵌 Cowork marketplace，不搬动本体）
    from app.views.skills_marketplace import skills_marketplace_bp
    app.register_blueprint(skills_marketplace_bp)

    # 注册资源池蓝图
    from app.routes.resource_pool import resource_pool_bp
    app.register_blueprint(resource_pool_bp)
    csrf.exempt(resource_pool_bp)

    # 注册新功能说明书蓝图
    from app.routes.guide import guide_bp
    app.register_blueprint(guide_bp)

    # 注册 GEO Monitor 蓝图
    from app.routes.geo_monitor import geo_monitor_bp
    app.register_blueprint(geo_monitor_bp, url_prefix='/geo')

    # 注册内部 API 蓝图（供 MCP Server 以用户身份查询数据，使用 X-Internal-Token 鉴权）
    from app.routes.internal_api import internal_api_bp
    app.register_blueprint(internal_api_bp)
    csrf.exempt(internal_api_bp)  # 内部 API 使用 token 鉴权，豁免 CSRF

    # pma-training v2 内部 API (X-Internal-Token + X-User-ID 鉴权)
    from app.routes.training_api import training_api_bp, wiki_image_public_bp
    app.register_blueprint(training_api_bp)
    csrf.exempt(training_api_bp)

    # 公开 wiki 图片端点 (HMAC token 鉴权, 无 session/X-Internal-Token)
    # 路径: /wiki-img/<token>  — 供 Cowork 客户端渲染 markdown 图片用
    app.register_blueprint(wiki_image_public_bp)
    csrf.exempt(wiki_image_public_bp)

    # 注册备份管理蓝图
    from app.routes.backup_routes import backup_bp
    app.register_blueprint(backup_bp)


    # 注册绩效管理蓝图
    register_performance_routes(app)

    # 注册每日智能分析报告API蓝图
    from app.api.v1.daily_report import daily_report_api
    app.register_blueprint(daily_report_api)

    # 注册测试功能蓝图 - 暂时禁用以避免云端部署问题
    # try:
    #     from app.routes.test_routes import test_bp
    #     app.register_blueprint(test_bp, url_prefix='/test')
    #     logger.info("测试功能蓝图注册成功")
    # except ImportError as e:
    #     logger.warning(f"测试功能蓝图导入失败: {e}")
    # except Exception as e:
    #     logger.error(f"测试功能蓝图注册失败: {e}")
    logger.info("测试功能蓝图已暂时禁用")
    
    # 注册测试合并蓝图（仅本地调试）
    try:
        from app.routes.test_merge import test_merge_bp
        app.register_blueprint(test_merge_bp, url_prefix='/debug')
        csrf.exempt(test_merge_bp)
        logger.info("测试合并蓝图注册成功")
    except Exception as e:
        logger.warning(f"测试合并蓝图注册失败: {e}")
    
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

    # 健康检查端点（用于 Docker 健康检查）
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查端点，用于容器健康检查"""
        try:
            # 简单检查数据库连接
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'ok'}, 200
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}, 503

    # 数据初始化
    with app.app_context():
        # 为Supabase环境设置search_path，解决表创建问题
        if 'supabase.com' in app.config['SQLALCHEMY_DATABASE_URI'] or 'supabase.co' in app.config['SQLALCHEMY_DATABASE_URI']:
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text('SET search_path TO public'))
                    conn.commit()
                logger.info("✅ Supabase环境已设置search_path为public")
            except Exception as e:
                logger.warning(f"⚠️ 设置search_path失败: {e}")
        
        # 创建数据库表
        db.create_all()
        logger.info("数据库表创建成功")

        # Auto-migrate: product_specs 添加 field_value_en 字段
        try:
            from sqlalchemy import inspect as sa_inspect, text as sa_text
            insp = sa_inspect(db.engine)
            ps_cols = [col['name'] for col in insp.get_columns('product_specs')]
            if 'field_value_en' not in ps_cols:
                with db.engine.connect() as conn:
                    conn.execute(sa_text('ALTER TABLE product_specs ADD COLUMN field_value_en VARCHAR(255)'))
                    conn.commit()
                logger.info("Auto-migrate: product_specs.field_value_en 字段已添加")
        except Exception as e:
            logger.warning(f"Auto-migrate product_specs.field_value_en 失败: {e}")

        # Auto-migrate: product_specs 添加 unit 字段
        try:
            if 'unit' not in ps_cols:
                with db.engine.connect() as conn:
                    conn.execute(sa_text('ALTER TABLE product_specs ADD COLUMN unit VARCHAR(20)'))
                    conn.commit()
                logger.info("Auto-migrate: product_specs.unit 字段已添加")
        except Exception as e:
            logger.warning(f"Auto-migrate product_specs.unit 失败: {e}")

        # Auto-migrate: products 添加 unit_en 字段
        try:
            prod_cols = [col['name'] for col in insp.get_columns('products')]
            if 'unit_en' not in prod_cols:
                with db.engine.connect() as conn:
                    conn.execute(sa_text('ALTER TABLE products ADD COLUMN unit_en VARCHAR(20)'))
                    conn.commit()
                logger.info("Auto-migrate: products.unit_en 字段已添加")
        except Exception as e:
            logger.warning(f"Auto-migrate products.unit_en 失败: {e}")

        # Auto-migrate: specification_options 添加 value_en 字段
        try:
            from sqlalchemy import inspect as sa_inspect, text as sa_text
            insp = sa_inspect(db.engine)
            spec_opt_cols = [col['name'] for col in insp.get_columns('specification_options')]
            if 'value_en' not in spec_opt_cols:
                with db.engine.connect() as conn:
                    conn.execute(sa_text('ALTER TABLE specification_options ADD COLUMN value_en VARCHAR(100)'))
                    conn.commit()
                logger.info("Auto-migrate: specification_options.value_en 字段已添加")
            else:
                logger.debug("Auto-migrate: specification_options.value_en 已存在，跳过")
        except Exception as e:
            logger.warning(f"Auto-migrate specification_options.value_en 失败: {e}")

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
            '/language/current', '/language/switch', '/storage',
            '/p/',  # 产品公开信息页面（二维码扫描）
            '/wiki/pub/',  # 互动课件公开页（二维码扫描，仅标记 .public 的课程，只下发干净 deck）
            '/api/v1/',  # API v1端点（有自己的认证机制）
            '/api/external/',  # 外部API端点（供Stargirl等系统调用，使用API Key认证）
            '/chat/api/ai/',  # OpenClaw AI API（db-query, db-schema, upload-file，均使用 token 认证）
            '/health',  # 健康检查（Docker + OpenClaw 回调验证）
            '/system-diagram/s/',  # 系统设计图外部分享页面（邮箱验证访问）
            '/api/dingtalk/',  # 钉钉服务器回调（企业事件推送，自有签名验证）
            '/internal/api/',  # 内部 API（MCP Server 专用，使用 X-Internal-Token 鉴权）
            '/user/api/claude-ai/download-dxt',  # DXT 下载（使用 ?t=token 认证，无需登录）
            '/wiki-img/',  # 公开 wiki 图片端点（HMAC token 鉴权，供 Cowork 客户端渲染 markdown 图片）
            '/quotation/mobile-view/',  # 移动端报价单预览（JWT token 自包含鉴权）
        ]
        
        # 检查当前路径是否需要登录
        if any(request.path.startswith(path) for path in excluded_paths):
            return
            
        # 如果用户未登录，重定向到登录页面
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        # 强制重新登录：2026-02-24 当天，所有旧 session 必须重新登录
        # （2026-02-25 自动失效，届时可删除此段代码）
        from datetime import date, datetime
        FORCE_RELOGIN_DATE = date(2026, 2, 24)
        if date.today() == FORCE_RELOGIN_DATE:
            login_time = session.get('login_time', 0)
            # 如果登录时间在 2月24日 00:00 之前，强制重新登录
            cutoff = datetime(2026, 2, 24).timestamp()
            if login_time < cutoff:
                logout_user()
                session.clear()
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

    # 注入当前语言到所有模板（与 Flask-Babel locale 一致）
    @app.context_processor
    def inject_current_locale():
        """向模板上下文注入当前语言，确保 HTML lang 与翻译一致"""
        from app.utils.i18n import get_current_language
        return {'current_locale': get_current_language()}

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

    @app.context_processor
    def inject_task_types():
        """向模板注入当前用户可选的任务类型(日常+本岗位),供全局任务创建模态框使用"""
        from flask_login import current_user
        try:
            if not current_user.is_authenticated:
                return {'available_task_types': [], 'available_task_type_groups': [], 'task_type_labels_map': {}}
            from app.helpers.task_types import (
                task_types_for, task_type_groups_for, task_type_labels_for)
            types = task_types_for(current_user)
            return {
                'available_task_types': types,
                'available_task_type_groups': task_type_groups_for(current_user),
                'task_type_labels_map': task_type_labels_for(current_user),
                'task_type_review_codes': [t['code'] for t in types if t.get('require_review')],
                'task_type_nolink_codes': [t['code'] for t in types if not t.get('allow_link', True)],
            }
        except Exception:
            return {'available_task_types': [], 'available_task_type_groups': [],
                    'task_type_labels_map': {}, 'task_type_review_codes': [], 'task_type_nolink_codes': []}

    @app.context_processor
    def inject_js_i18n():
        """向模板注入 js_i18n_map(供 _js_i18n.html 渲染 window.I18N 给客户端 JS)"""
        from app.helpers.js_i18n import js_i18n_map
        return {'js_i18n_map': js_i18n_map}

    # 添加权限检查全局上下文处理器
    @app.context_processor
    def inject_permissions():
        """向模板上下文注入当前用户的权限信息"""
        def has_permission(module, action):
            from flask_login import current_user

            try:
                if not current_user.is_authenticated:
                    return False

                # CEO 额外检查（has_permission 已处理 admin）
                from app.permissions import is_admin_or_ceo
                if is_admin_or_ceo():
                    return True

                # 委托给 User.has_permission()（已有请求级缓存）
                return current_user.has_permission(module, action)

            except Exception as e:
                try:
                    from flask import current_app
                    current_app.logger.error(f"Permission check database error: {str(e)}")
                except:
                    pass
                try:
                    from app import db
                    db.session.rollback()
                except Exception:
                    pass

                from app.permissions import is_admin_or_ceo
                if is_admin_or_ceo():
                    return True

                return False

        # 添加管理员/CEO检查函数到模板上下文
        def is_admin_or_ceo_template():
            from app.permissions import is_admin_or_ceo
            from flask_login import current_user
            return is_admin_or_ceo(current_user)

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
    app.jinja_env.filters['format_achievement_rate'] = format_achievement_rate
    app.jinja_env.filters['project_type_label'] = project_type_label_i18n
    app.jinja_env.filters['project_stage_label'] = project_stage_label_i18n
    # 注册 label 过滤器（使用 make_i18n_filter 包装以支持自动语言检测）
    app.jinja_env.filters['report_source_label'] = make_i18n_filter(report_source_label)
    app.jinja_env.filters['authorization_status_label'] = make_i18n_filter(authorization_status_label)
    app.jinja_env.filters['company_type_label'] = make_i18n_filter(company_type_label)
    app.jinja_env.filters['company_type_color'] = company_type_color
    app.jinja_env.filters['product_situation_label'] = make_i18n_filter(product_situation_label)
    app.jinja_env.filters['industry_label'] = make_i18n_filter(industry_label)
    app.jinja_env.filters['country_label'] = country_label
    from app.utils.dictionary_helpers import currency_type_label
    app.jinja_env.filters['currency_label'] = currency_type_label

    # 报销科目 label(基于 model 的 EXPENSE_CATEGORIES list,无需重复定义)
    from app.models.expense import EXPENSE_CATEGORIES
    _expense_cat_map = dict(EXPENSE_CATEGORIES)
    app.jinja_env.filters['expense_category_label'] = lambda v: _expense_cat_map.get(v, v) if v else ''
    app.jinja_env.filters['industry_color'] = industry_color
    app.jinja_env.filters['status_label'] = make_i18n_filter(status_label)
    app.jinja_env.filters['activity_status_label'] = make_i18n_filter(activity_status_label)
    app.jinja_env.globals['activity_status_color'] = activity_status_color
    app.jinja_env.filters['user_label'] = user_label
    app.jinja_env.filters['share_permission_label'] = make_i18n_filter(share_permission_label)
    app.jinja_env.filters['approval_status_label'] = make_i18n_filter(approval_status_label)
    app.jinja_env.filters['product_type_label'] = make_i18n_filter(product_type_label)
    app.jinja_env.filters['product_status_label'] = make_i18n_filter(product_status_label)
    # 研发库已废弃 (2025-12-26)，但保留过滤器以避免模板解析错误
    app.jinja_env.filters['dev_product_status_label'] = make_i18n_filter(dev_product_status_label)
    app.jinja_env.filters['active_status_label'] = make_i18n_filter(active_status_label)

    # AT 状态徽章统一映射(label + tone),供模板用 at_status_pill 宏调用
    from app.utils.status_meta import get_status_meta, get_status_label
    app.jinja_env.globals['get_status_meta'] = get_status_meta
    app.jinja_env.globals['get_status_label'] = get_status_label

    # AT 关联数据服务:导入触发注册(company / project / ... 各实体的关联模块)
    from app.utils import related_data_register  # noqa: F401

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
    app.jinja_env.globals['project_stage_label'] = project_stage_label_i18n

    # 统计图表
    from app.views.projectpm_statistics import projectpm_statistics
    app.register_blueprint(projectpm_statistics, url_prefix='/projectpm/statistics')

    app.jinja_env.globals['get_role_display_name'] = get_role_display_name
    app.jinja_env.globals['get_all_active_roles'] = get_all_active_roles
    app.jinja_env.globals['get_all_user_companies'] = get_all_user_companies
    # 注册语言感知的货币单位相关函数
    app.jinja_env.globals['get_amount_unit_config'] = get_amount_unit_config
    app.jinja_env.globals['get_currency_symbol'] = get_currency_symbol
    app.jinja_env.globals['get_default_currency'] = get_default_currency

    # 注册全局权限函数上下文处理器
    from app.context_processors import inject_permission_functions
    app.context_processor(inject_permission_functions)

    # 注册消息蓝图
    from app.views.message import message as message_bp
    app.register_blueprint(message_bp)

    # 注册公告蓝图
    from app.views.announcement import announcement_bp
    app.register_blueprint(announcement_bp)

    # 注册任务蓝图
    from app.views.task import task as task_bp
    app.register_blueprint(task_bp)

    # 注册聊天蓝图
    from app.views.chat import chat as chat_bp
    app.register_blueprint(chat_bp)
    csrf.exempt(chat_bp)

    # 注册星图蓝图
    from app.views.star_graph import star_graph as star_graph_bp
    app.register_blueprint(star_graph_bp)

    # 注册系统图蓝图
    from app.views.system_diagram import system_diagram as system_diagram_bp
    app.register_blueprint(system_diagram_bp)
    csrf.exempt(system_diagram_bp)

    # 注册市场情报库蓝图
    from app.views.prospect import prospect_bp
    app.register_blueprint(prospect_bp, url_prefix='/prospect')

    # 注册个人关注(收藏)蓝图
    from app.views.favorite import favorite_bp
    app.register_blueprint(favorite_bp)

    # 添加审批相关函数到模板上下文
    from app.context_processors import inject_approval_functions
    app.context_processor(inject_approval_functions)
    
    # 添加项目相关函数到模板上下文
    from app.context_processors import inject_project_functions
    app.context_processor(inject_project_functions)

    # 添加语言相关函数到模板上下文
    from app.context_processors import inject_language_functions
    app.context_processor(inject_language_functions)
    
    # 将翻译函数注册到 Jinja2 全局环境（备用方案）
    from flask_babel import gettext, ngettext
    app.jinja_env.globals['_'] = gettext
    app.jinja_env.globals['gettext'] = gettext
    app.jinja_env.globals['ngettext'] = ngettext
    
    # 将语言检测函数注册到 Jinja2 全局环境
    app.jinja_env.globals['get_current_language'] = get_current_language

    # 添加通用阶段配置函数到模板上下文
    from app.context_processors import inject_stage_configs
    app.context_processor(inject_stage_configs)

    # 添加货币配置到模板上下文（基于数据库类型，与语言解耦）
    from app.context_processors import inject_currency_config
    app.context_processor(inject_currency_config)

    # 添加资源池辅助函数到模板上下文
    from app.context_processors import inject_resource_pool_helpers
    app.context_processor(inject_resource_pool_helpers)

    # 添加用户辅助函数到模板上下文
    from app.context_processors import inject_user_helpers
    app.context_processor(inject_user_helpers)

    # 添加字典辅助函数到模板上下文（厂商企业信息等）
    @app.context_processor
    def inject_dictionary_helpers():
        """向模板上下文注入字典辅助函数"""
        from app.utils.dictionary_helpers import get_vendor_company, get_vendor_company_by_user
        return {
            'get_vendor_company': get_vendor_company,
            'get_vendor_company_by_user': get_vendor_company_by_user
        }

    # 添加文件URL处理函数到Jinja2全局环境
    from app.utils.file_url_helper import (
        normalize_file_url, 
        get_invoice_image_url, 
        is_cloud_deployment,
        ensure_absolute_url,
        validate_image_url
    )
    app.jinja_env.globals['normalize_file_url'] = normalize_file_url
    app.jinja_env.globals['get_invoice_image_url'] = get_invoice_image_url
    app.jinja_env.globals['is_cloud_deployment'] = is_cloud_deployment
    app.jinja_env.globals['ensure_absolute_url'] = ensure_absolute_url
    app.jinja_env.globals['validate_image_url'] = validate_image_url

    # 注册全局帮助函数
    from app.helpers.ui_helpers import format_datetime, render_action_button, get_user_display_name, render_filter_button
    app.jinja_env.globals['format_datetime'] = format_datetime
    app.jinja_env.globals['render_action_button'] = render_action_button
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
        check_template_has_instances,
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
    app.jinja_env.globals['check_template_has_instances'] = check_template_has_instances
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
    
    # 注册移动端检测函数到模板全局环境
    from app.utils.mobile_helpers import is_mobile_request
    app.jinja_env.globals['is_mobile_request'] = is_mobile_request

    # 临时权限测试路由
    @app.route('/test-tonglei-permission')
    def test_tonglei_permission():
        """临时测试童蕾用户权限的路由"""
        from flask import render_template_string
        
        template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>童蕾权限测试页面</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
                .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .alert-danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
                .btn-warning { background-color: #ffc107; color: #212529; }
            </style>
        </head>
        <body>
            <h1>童蕾权限测试页面</h1>
            
            <h2>用户信息</h2>
            <p>当前用户: {{ current_user.username if current_user.is_authenticated else '未登录' }}</p>
            <p>用户角色: {{ current_user.role if current_user.is_authenticated else '无' }}</p>
            <p>用户ID: {{ current_user.id if current_user.is_authenticated else '无' }}</p>
            
            <h2>权限检查结果</h2>
            <p>is_admin_or_ceo 模板变量: {{ is_admin_or_ceo }}</p>
            <p>is_admin_or_ceo 类型: {{ is_admin_or_ceo.__class__.__name__ }}</p>
            
            <h2>条件测试</h2>
            <p>{% if is_admin_or_ceo %}is_admin_or_ceo 为 True{% else %}is_admin_or_ceo 为 False{% endif %}</p>
            
            <h2>模拟批价单状态测试</h2>
            {% set mock_status = 'approved' %}
            <p>模拟状态: {{ mock_status }}</p>
            <p>完整条件测试: {% if is_admin_or_ceo and mock_status == 'approved' %}应该显示退回按钮{% else %}不应该显示退回按钮{% endif %}</p>
            
            <h2>按钮测试</h2>
            {% if is_admin_or_ceo and mock_status == 'approved' %}
            <div class="alert alert-danger">
                ❌ 错误：退回审批按钮会显示！
                <button type="button" class="btn btn-warning">退回审批</button>
            </div>
            {% else %}
            <div class="alert alert-success">
                ✅ 正确：退回审批按钮不会显示
            </div>
            {% endif %}
            
            <h2>调试信息</h2>
            <p>测试时间: {{ now() }}</p>
            <p>请求路径: {{ request.path }}</p>
            
            <script>
                console.log('=== 前端权限测试 ===');
                console.log('页面标题:', document.title);
                console.log('当前时间:', new Date().toLocaleString());
                
                // 检查是否有退回按钮
                const rollbackButton = document.querySelector('button');
                console.log('页面中是否有按钮:', !!rollbackButton);
                if (rollbackButton) {
                    console.log('按钮文本:', rollbackButton.textContent);
                    console.log('❌ 发现问题：权限检查失效！');
                } else {
                    console.log('✅ 权限检查正常：无退回按钮');
                }
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(template)

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
            
        # 初始化 Supabase 备份服务
        try:
            from app.services.supabase_backup_service import init_backup_service
            backup_service = init_backup_service()
            app.logger.info("Supabase 备份服务初始化完成")
        except Exception as e:
            app.logger.error(f"初始化 Supabase 备份服务时出错: {str(e)}")

        # 启动客户活跃度定时修正任务（仅在非测试环境）
        if not app.config.get('TESTING'):
            try:
                from app.utils.scheduled_tasks import start_scheduler
                start_scheduler(run_time="01:00")  # 每日凌晨1点执行
                app.logger.info("客户活跃度定时修正任务已启动")
            except Exception as e:
                app.logger.error(f"启动客户活跃度定时任务时出错: {str(e)}")

        # 注册合格新客户/项目「达标时间」实时盖戳监听(集中式会话事件;每小时任务作兜底)
        try:
            from app.services.kpi_actual_service import register_qualified_at_listeners
            register_qualified_at_listeners()
            app.logger.info("达标时间实时盖戳监听已注册")
        except Exception as e:
            app.logger.error(f"注册达标盖戳监听时出错: {str(e)}")

        # 同步积分行为注册表到数据库
        try:
            from app.services.points_service import sync_registry_to_db
            sync_registry_to_db()
            app.logger.info("积分行为注册表同步完成")
        except Exception as e:
            app.logger.error(f"同步积分注册表时出错: {str(e)}")

        # 钉钉集成：仅单向拉取（钉钉 → PMA），无反向推送
        try:
            from app.services.dingtalk.config import is_dingtalk_enabled
            if is_dingtalk_enabled() and not app.config.get('TESTING'):
                app.logger.info("钉钉拉取模式已启用（每小时由 scheduled_tasks 触发）")
            else:
                app.logger.info("钉钉集成未启用（非 CN 环境或未配置凭证），跳过")
        except Exception as e:
            app.logger.error(f"初始化钉钉集成时出错: {str(e)}")

    # 注册上下文处理器
    from app.utils.access_control import register_context_processors
    register_context_processors(app)
    
    # 注册共享模块上下文处理器
    from app.utils.sharing import register_sharing_context_processors
    register_sharing_context_processors(app)

    # 添加本地存储文件服务路由
    @app.route('/storage/<path:filename>')
    def serve_storage_file(filename):
        """
        为本地存储的文件提供访问服务
        当使用本地存储时，通过此路由访问存储在./storage/目录下的文件
        """
        try:
            import os
            from flask import send_from_directory, abort
            
            # 构建存储目录的绝对路径
            storage_dir = os.path.join(app.root_path, '..', 'storage')  # ./storage/
            storage_dir = os.path.abspath(storage_dir)
            
            # 安全检查：确保请求的文件在存储目录内
            requested_path = os.path.join(storage_dir, filename)
            requested_path = os.path.abspath(requested_path)
            
            if not requested_path.startswith(storage_dir):
                logger.warning(f"拒绝访问存储目录外的文件: {filename}")
                abort(403)
            
            # 检查文件是否存在
            if not os.path.exists(requested_path):
                logger.warning(f"请求的文件不存在: {filename}")
                abort(404)
            
            # 返回文件（支持 ?name= 参数指定下载文件名）
            from flask import request as _req
            download_name = _req.args.get('name')
            if download_name:
                return send_from_directory(storage_dir, filename,
                                           as_attachment=True, download_name=download_name)
            return send_from_directory(storage_dir, filename)
            
        except Exception as e:
            logger.error(f"服务本地存储文件失败: {str(e)}")
            abort(500)

    # 本地开发：为 /uploads/ 目录提供文件访问（NAS部署时由WebDAV处理）
    @app.route('/uploads/<path:filename>')
    def serve_uploads_file(filename):
        import os
        from flask import send_from_directory, abort
        uploads_dir = os.path.join(app.root_path, '..', 'uploads')
        uploads_dir = os.path.abspath(uploads_dir)
        requested_path = os.path.abspath(os.path.join(uploads_dir, filename))
        if not requested_path.startswith(uploads_dir) or not os.path.exists(requested_path):
            abort(404)
        return send_from_directory(os.path.dirname(requested_path), os.path.basename(requested_path))

    # 注册统一中文映射功能到Jinja2模板环境
    try:
        from app.utils.chinese_mapping_manager import mapping_manager
        
        def get_field_display_name(table_name, field_name, default=None):
            """
            Jinja2模板函数：获取字段的中文显示名称
            优先级: 配置表 → 全局映射 → 字典映射 → 友好名称生成
            """
            try:
                result = mapping_manager.get_field_display_name(table_name, field_name)
                return result if result != field_name else (default or field_name)
            except Exception as e:
                logger.warning(f"获取字段显示名称失败: {table_name}.{field_name}, 错误: {e}")
                return default or field_name
        
        def get_table_display_name(table_name, default=None):
            """
            Jinja2模板函数：获取表的中文显示名称
            """
            try:
                result = mapping_manager.get_table_display_name(table_name)
                return result if result != table_name else (default or table_name)
            except Exception as e:
                logger.warning(f"获取表显示名称失败: {table_name}, 错误: {e}")
                return default or table_name
        
        # 创建支持翻译的字段显示名称函数
        def get_field_display_name_i18n(table_name, field_name, default=None):
            """
            Jinja2全局函数：获取字段显示名称并支持翻译
            优先级: 配置表 → 全局映射 → 字典映射 → 友好名称
            最终结果会通过翻译系统进行本地化处理
            """
            try:
                # 获取映射结果
                mapped_name = mapping_manager.get_field_display_name(table_name, field_name)
                if mapped_name != field_name:
                    # 对映射结果进行翻译
                    from flask_babel import gettext
                    return gettext(mapped_name)
                # 映射失败时使用默认值并翻译
                elif default:
                    from flask_babel import gettext
                    return gettext(default)
                else:
                    from flask_babel import gettext
                    return gettext(field_name)
            except Exception as e:
                logger.warning(f"获取字段显示名称失败: {table_name}.{field_name}, 错误: {e}")
                from flask_babel import gettext
                return gettext(default) if default else gettext(field_name)
        
        # 创建get_column_title函数（保持兼容）
        def get_column_title(table_name, field_name, fallback_label=None):
            """
            Jinja2全局函数：获取列标题的统一映射（兼容版本）
            """
            try:
                # 优先使用支持翻译的版本
                return get_field_display_name_i18n(table_name, field_name, fallback_label)
            except Exception as e:
                logger.warning(f"获取列标题失败: {table_name}.{field_name}, 错误: {e}")
                from flask_babel import gettext
                return gettext(fallback_label) if fallback_label else gettext(field_name)
        
        # 注册到Jinja2全局环境
        app.jinja_env.globals['get_field_display_name'] = get_field_display_name
        app.jinja_env.globals['get_field_display_name_i18n'] = get_field_display_name_i18n
        app.jinja_env.globals['get_table_display_name'] = get_table_display_name
        app.jinja_env.globals['get_column_title'] = get_column_title
        
        logger.info("✅ 统一中文映射功能已注册到Jinja2模板环境")
        
    except ImportError as e:
        logger.warning(f"⚠️ 统一中文映射模块导入失败: {e}")
    except Exception as e:
        logger.error(f"❌ 注册统一中文映射功能失败: {e}")

    return app 