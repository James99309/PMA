from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
import logging
from datetime import datetime, timedelta
from flask_login import current_user, login_required
from app import db
from app.models.project import Project
from app.utils.access_control import get_viewable_data
from app.models.quotation import Quotation
from app.models.customer import Company
from app.models.action import Action, ActionReply
from app.models.user import User
from app.utils.dictionary_helpers import project_type_label, get_currency_symbol
from app.services.exchange_rate_service import exchange_rate_service
from sqlalchemy import and_, or_, extract, func
from config import Config
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    logger.info('Accessing index page')
    logger.info('User logged in, rendering index page')
    
    # 获取当前版本信息和最近升级时间
    try:
        from app.models.version_management import VersionRecord
        from app.utils.version_auto_generator import get_current_app_version
        
        current_version = VersionRecord.get_current_version()
        version_number = current_version.version_number if current_version else '1.3.5'
        
        # 获取统一的应用版本
        app_version = get_current_app_version()
        
        # 获取最近升级时间
        last_upgrade_time = current_version.release_date if current_version else None
        
    except Exception as e:
        logger.warning(f"获取版本信息失败: {str(e)}")
        version_number = '1.3.5'  # 默认版本号
        app_version = '1.3.5'
        last_upgrade_time = None
    
    # 查询当前用户可见的最近5个项目，按更新时间倒序
    recent_projects = []
    if current_user.has_permission('project', 'view'):
        try:
            recent_projects = get_viewable_data(Project, current_user).order_by(Project.updated_at.desc()).limit(5).all()
        except Exception as e:
            logger.warning(f"使用updated_at查询项目失败: {str(e)}，尝试使用id排序")
            try:
                # 回滚失败的事务
                db.session.rollback()
                recent_projects = get_viewable_data(Project, current_user).order_by(Project.id.desc()).limit(5).all()
            except Exception as e2:
                logger.error(f"项目查询完全失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                recent_projects = []
    
    # 查询当前用户可见的最近5条报价，按更新时间倒序
    recent_quotations = []
    if current_user.has_permission('quotation', 'view'):
        try:
            recent_quotations = get_viewable_data(Quotation, current_user).order_by(Quotation.updated_at.desc()).limit(5).all()
        except Exception as e:
            logger.warning(f"报价查询失败: {str(e)}")
            try:
                # 回滚失败的事务
                db.session.rollback()
                recent_quotations = get_viewable_data(Quotation, current_user).order_by(Quotation.id.desc()).limit(5).all()
            except Exception as e2:
                logger.error(f"报价查询完全失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                recent_quotations = []
    
    # 查询当前用户可见的最近5个客户，按更新时间倒序
    recent_companies = []
    if current_user.has_permission('customer', 'view'):
        try:
            recent_companies = get_viewable_data(Company, current_user).order_by(Company.updated_at.desc()).limit(5).all()
        except Exception as e:
            logger.warning(f"客户查询失败: {str(e)}")
            try:
                # 回滚失败的事务
                db.session.rollback()
                recent_companies = get_viewable_data(Company, current_user).order_by(Company.id.desc()).limit(5).all()
            except Exception as e2:
                logger.error(f"客户查询完全失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                recent_companies = []
    
    # 查询当前用户可见的最近5个报销单，按更新时间倒序
    recent_expenses = []
    if current_user.has_permission('expense', 'view'):
        try:
            from app.models.expense import Expense
            from app.helpers.approval_helpers import get_object_approval_instances_batch

            # 获取最近的报销单，包含关联的审批实例信息
            recent_expenses_query = get_viewable_data(Expense, current_user).options(
                joinedload(Expense.owner),
                joinedload(Expense.project)
            ).order_by(Expense.updated_at.desc()).limit(5)

            raw_expenses = recent_expenses_query.all()

            # 批量获取所有报销单的审批实例（1次IN查询替代N次循环查询）
            expense_ids = [e.id for e in raw_expenses]
            approval_map = get_object_approval_instances_batch('expense', expense_ids)

            for expense in raw_expenses:
                approval_instance = approval_map.get(expense.id)
                if approval_instance:
                    expense.approval_status = approval_instance.status.value
                else:
                    expense.approval_status = 'draft'
                recent_expenses.append(expense)

        except Exception as e:
            logger.warning(f"报销单查询失败: {str(e)}")
            try:
                # 回滚失败的事务
                db.session.rollback()
                from app.models.expense import Expense
                recent_expenses_query = get_viewable_data(Expense, current_user).options(
                    joinedload(Expense.owner),
                    joinedload(Expense.project)
                ).order_by(Expense.id.desc()).limit(5)

                raw_expenses = recent_expenses_query.all()
                for expense in raw_expenses:
                    expense.approval_status = expense.status  # 使用报销单自身状态
                    recent_expenses.append(expense)

            except Exception as e2:
                logger.error(f"报销单查询完全失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                recent_expenses = []

    # 获取当前用户今年各月份报销统计（用于首页图表）
    # 使用用户的结算货币进行汇率转换
    expense_monthly_stats = []
    expense_year_total = 0
    user_settlement_currency = current_user.settlement_currency or Config.DEFAULT_CURRENCY
    user_currency_symbol = get_currency_symbol(user_settlement_currency)
    # 获取 CNY → 用户结算货币 的汇率
    user_exchange_rate = exchange_rate_service.get_exchange_rate('CNY', user_settlement_currency)
    if current_user.has_permission('expense', 'view'):
        try:
            from app.models.expense import Expense
            current_year = datetime.now().year
            # 查询今年每笔报销单的月份、金额和货币（用于汇率转换）
            expense_query = db.session.query(
                extract('month', Expense.created_at).label('month'),
                Expense.total_amount,
                Expense.currency
            ).filter(
                Expense.owner_id == current_user.id,
                Expense.is_deleted == False,
                Expense.status.in_(['pending', 'approved', 'paid']),
                extract('year', Expense.created_at) == current_year
            ).all()

            # 按月汇总，同时进行货币转换
            monthly_dict = {i: 0.0 for i in range(1, 13)}
            for row in expense_query:
                month = int(row.month)
                amount = float(row.total_amount or 0)
                expense_currency = row.currency or Config.DEFAULT_CURRENCY

                # 如果货币不同，进行汇率转换
                if expense_currency != user_settlement_currency:
                    try:
                        amount = exchange_rate_service.convert_amount(
                            amount, expense_currency, user_settlement_currency
                        )
                    except Exception as conv_err:
                        logger.warning(f"首页报销统计货币转换失败 {expense_currency} -> {user_settlement_currency}: {conv_err}")

                monthly_dict[month] += amount

            expense_monthly_stats = [round(monthly_dict.get(i, 0), 2) for i in range(1, 13)]
            expense_year_total = round(sum(expense_monthly_stats), 2)
        except Exception as e:
            logger.warning(f"报销月度统计查询失败: {str(e)}")
            expense_monthly_stats = [0] * 12
            expense_year_total = 0

    # 在index视图中，recent_projects处理类型key转中文，支持语言感知
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    
    for p in recent_projects:
        if hasattr(p, 'project_type'):
            p.project_type_display = project_type_label(p.project_type, lang_code)
    # 获取数据库类型标识和调试模式
    from flask import current_app
    import logging
    is_sp8d = current_app.config.get('IS_SP8D', False)
    is_debug = current_app.config.get('DEBUG', False)
    show_manual_download = is_sp8d or is_debug

    # 调试日志 - 用于排查说明书按钮显示问题
    db_url = current_app.config.get('DATABASE_URL', '')
    logging.info(f"[DEBUG] DATABASE_URL contains 'pma_db_sp8d': {'pma_db_sp8d' in db_url}")
    logging.info(f"[DEBUG] IS_SP8D={is_sp8d}, DEBUG={is_debug}, show_manual_download={show_manual_download}")

    # 获取当前用户的AI分析启用状态
    ai_enabled = False
    try:
        from app.models.salary_config import EmployeeSalaryConfig
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=current_user.id).first()
        ai_enabled = employee_config.ai_analysis_enabled if employee_config else False
    except Exception as e:
        logger.warning(f"获取AI启用状态失败: {str(e)}")
        ai_enabled = False

    return render_template('index.html',
                         now=datetime.now(),
                         recent_projects=recent_projects,
                         recent_quotations=recent_quotations,
                         recent_companies=recent_companies,
                         recent_expenses=recent_expenses,
                         expense_monthly_stats=expense_monthly_stats,
                         expense_year_total=expense_year_total,
                         user_currency_symbol=user_currency_symbol,
                         user_settlement_currency=user_settlement_currency,
                         user_exchange_rate=user_exchange_rate,
                         current_version_number=version_number,
                         app_version=app_version,
                         last_upgrade_time=last_upgrade_time,
                         show_manual_download=show_manual_download,
                         ai_enabled=ai_enabled)

@main.route('/api/recent_work_records')
@login_required
def get_recent_work_records():
    """
    获取工作记录（支持无限滚动分页）
    支持权限过滤和账户筛选
    """
    try:
        # 导入权限检查函数
        from app.permissions import is_admin_or_ceo

        # 获取分页参数
        account_id = request.args.get('account_id', type=int)
        offset = request.args.get('offset', 0, type=int)  # 偏移量
        limit = request.args.get('limit', 20, type=int)  # 每页数量

        # 使用权限系统获取可查看的Action记录（不限时间）
        base_query = get_viewable_data(Action, current_user)

        # 账户筛选逻辑 - 使用权限配置系统
        # 注：查看他人记录的权限通过权限级别控制
        # - system级权限可以查看所有账户
        # - department级权限可以查看本部门账户
        # - personal级权限只能查看自己
        if account_id:
            # 检查是否有权查看指定账户的记录
            permission_level = current_user.get_permission_level('customer')
            if is_admin_or_ceo() or permission_level == 'system':
                # 系统级权限可以查看任何账户的记录
                base_query = base_query.filter(Action.owner_id == account_id)
            elif permission_level in ['company', 'department'] or current_user.is_department_manager:
                # 部门级权限只能查看下属的记录
                target_user = User.query.get(account_id)
                if target_user and (target_user.department == current_user.department):
                    base_query = base_query.filter(Action.owner_id == account_id)
                else:
                    # 没有权限查看该账户，返回空结果
                    return jsonify({
                        'success': True,
                        'data': [],
                        'total': 0,
                        'message': '无权限查看该账户的记录'
                    })
            else:
                # 个人级权限只能查看自己的记录
                if account_id != current_user.id:
                    return jsonify({
                        'success': True,
                        'data': [],
                        'total': 0,
                        'message': '无权限查看该账户的记录'
                    })
                base_query = base_query.filter(Action.owner_id == current_user.id)
        
        # 计算总数（用于判断是否还有更多数据）
        total_count = base_query.count()

        # 加载关联数据并按时间倒序排列（使用分页）
        records = base_query.options(
            joinedload(Action.company),
            joinedload(Action.contact),
            joinedload(Action.project),
            joinedload(Action.owner)
        ).order_by(Action.date.desc(), Action.created_at.desc()).offset(offset).limit(limit).all()
        
        # 处理数据
        result = []
        for record in records:
            # 检查是否有回复（使用动态关系的count()方法）
            has_reply = record.replies.count() > 0
            
            # 获取客户信息
            customer_name = ''
            customer_id = None
            if record.company:
                customer_name = record.company.company_name
                customer_id = record.company.id
            elif record.contact and record.contact.company:
                customer_name = record.contact.company.company_name
                customer_id = record.contact.company.id
                
            # 获取联系人信息
            contact_name = record.contact.name if record.contact else ''
            
            # 获取关联项目
            project_name = record.project.project_name if record.project else ''
            project_id = record.project.id if record.project else None
            
            # 使用render_owner宏生成拥有者徽章HTML
            owner_initials = ''
            if record.owner:
                # 判断是否为厂商账户
                if record.owner.is_vendor_user():
                    # 厂商账户使用胶囊造型徽章
                    display_name = record.owner.real_name if record.owner.real_name else record.owner.username
                    owner_badge_html = f'<span class="badge bg-primary rounded-pill">{display_name}</span>'
                else:
                    # 非厂商账户使用默认造型徽章
                    display_name = record.owner.real_name if record.owner.real_name else record.owner.username
                    owner_badge_html = f'<span class="badge bg-secondary">{display_name}</span>'

                # 计算拥有人姓名缩写（用于 Tailwind 首页头像显示）
                name = record.owner.real_name or record.owner.username
                if name:
                    # 统一取第1个字符（中文取首字，英文取首字母大写）
                    if any('\u4e00' <= c <= '\u9fff' for c in name):
                        owner_initials = name[:1]
                    else:
                        owner_initials = name[0].upper()
            else:
                owner_badge_html = '<span class="badge bg-secondary">未知</span>'

            record_data = {
                'id': record.id,
                'date': record.date.strftime('%Y-%m-%d'),
                'time': record.created_at.strftime('%H:%M') if record.created_at else '',
                'customer_name': customer_name,
                'customer_id': customer_id,
                'contact_name': contact_name,
                'project_name': project_name,
                'project_id': project_id,
                'communication': record.communication,
                'has_reply': has_reply,
                'reply_count': record.replies.count(),
                'owner_name': record.owner.real_name or record.owner.username if record.owner else '',
                'owner_badge_html': owner_badge_html,  # 使用render_owner逻辑的徽章HTML
                'owner_id': record.owner_id,
                'owner_initials': owner_initials  # 拥有人姓名缩写（用于 Tailwind 首页）
            }
            result.append(record_data)

        # 返回分页数据
        response_data = {
            'success': True,
            'data': result,
            'loaded_count': len(result),  # 本次加载的记录数
            'total': total_count,  # 总记录数
            'has_more': offset + len(result) < total_count  # 是否还有更多数据
        }

        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取最近工作记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取工作记录失败',
            'error': str(e)
        }), 500

@main.route('/test')
def test_page():
    """测试页面 - 用于调试页面显示问题"""
    return '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PMA系统测试页面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            color: #16a0bf;
            margin-bottom: 30px;
        }
        .status {
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .test-item {
            margin: 15px 0;
            padding: 10px;
            border-left: 4px solid #16a0bf;
            background-color: #f8f9fa;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #16a0bf;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 5px;
        }
        .btn:hover {
            background-color: #0e7c8f;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PMA系统测试页面</h1>
            <p>验证系统是否正常运行</p>
        </div>

        <div class="status success">
            ✅ 如果你能看到这个页面，说明系统基本功能正常
        </div>

        <div class="status info">
            📋 系统信息：
            <ul>
                <li>运行端口: 6000</li>
                <li>数据库: 本地PostgreSQL</li>
                <li>环境: local</li>
                <li>版本: 1.0.1</li>
            </ul>
        </div>

        <div class="test-item">
            <h3>🔍 测试项目</h3>
            <p><strong>1. 静态文件访问测试</strong></p>
            <p>CSS文件: <span id="css-status">检测中...</span></p>
            <p>Logo图片: <span id="img-status">检测中...</span></p>
            
            <p><strong>2. 页面跳转测试</strong></p>
            <a href="/auth/login" class="btn">访问登录页面</a>
            <a href="/backup/" class="btn">访问备份管理</a>
            <a href="/" class="btn">访问首页</a>
        </div>

        <div class="test-item">
            <h3>💡 如果登录页面显示空白</h3>
            <p>可能的原因和解决方案：</p>
            <ul>
                <li>浏览器缓存问题 - 尝试强制刷新 (Ctrl+F5 或 Cmd+Shift+R)</li>
                <li>外部CDN资源加载失败 - 检查网络连接</li>
                <li>JavaScript错误 - 打开浏览器开发者工具查看控制台</li>
                <li>CSS样式冲突 - 尝试禁用浏览器扩展</li>
            </ul>
        </div>

        <div class="test-item">
            <h3>🛠️ 调试步骤</h3>
            <ol>
                <li>打开浏览器开发者工具 (F12)</li>
                <li>查看Console标签页是否有错误信息</li>
                <li>查看Network标签页检查资源加载情况</li>
                <li>尝试在隐私模式/无痕模式下访问</li>
            </ol>
        </div>
    </div>

    <script>
        // 测试静态文件访问
        function testStaticFiles() {
            // 测试CSS文件
            fetch('/static/css/style.css')
                .then(response => {
                    document.getElementById('css-status').innerHTML = 
                        response.ok ? '✅ 正常' : '❌ 失败';
                })
                .catch(() => {
                    document.getElementById('css-status').innerHTML = '❌ 失败';
                });

            // 测试图片文件
            const img = new Image();
            img.onload = () => {
                document.getElementById('img-status').innerHTML = '✅ 正常';
            };
            img.onerror = () => {
                document.getElementById('img-status').innerHTML = '❌ 失败';
            };
            img.src = '/static/img/logo.png';
        }

        // 页面加载完成后执行测试
        document.addEventListener('DOMContentLoaded', testStaticFiles);
    </script>
</body>
</html>
    '''

@main.route('/api/available_accounts')
@login_required
def get_available_accounts():
    """
    获取当前用户有权限查看的账户列表
    排序规则：有未读消息的排在前面，按最新消息时间倒序
    """
    try:
        accounts = []

        # 获取有未读日志消息的发送者信息（包含最新消息时间）
        from app.models.message import Message
        from sqlalchemy import func

        # 查询每个发送者的最新未读消息时间
        unread_info = db.session.query(
            Message.sender_id,
            func.max(Message.created_at).label('latest_time')
        ).filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False,
            Message.related_object_type == 'worklog'
        ).group_by(Message.sender_id).all()

        # 构建字典：sender_id -> 最新消息时间
        unread_sender_times = {info[0]: info[1] for info in unread_info}
        unread_sender_ids = set(unread_sender_times.keys())

        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            # 管理员和CEO可以查看所有活跃用户
            all_users = User.query.filter(
                User.id != current_user.id,
                User._is_active == True
            ).all()
            for user in all_users:
                accounts.append({
                    'id': user.id,
                    'name': user.real_name or user.username,
                    'role': user.role,
                    'has_unread': user.id in unread_sender_ids,
                    'latest_time': unread_sender_times.get(user.id)
                })
        else:
            # 使用权限配置系统判断可见账户
            # 注：可见账户范围通过 worklog 模块权限级别控制
            permission_level = current_user.get_permission_level('worklog')

            if permission_level == 'company':
                # company 级权限：可查看同公司所有用户
                all_users = User.query.filter(
                    User.id != current_user.id,
                    User._is_active == True,
                    User.company_name == current_user.company_name
                ).all()
                for user in all_users:
                    accounts.append({
                        'id': user.id,
                        'name': user.real_name or user.username,
                        'role': user.role,
                        'has_unread': user.id in unread_sender_ids,
                        'latest_time': unread_sender_times.get(user.id)
                    })
            elif permission_level in ['department'] or current_user.is_department_manager:
                # 获取用户管理的所有部门名称
                from app.models.expense import Department
                managed_depts = Department.query.filter_by(manager_id=current_user.id).all()
                managed_dept_names = [d.name for d in managed_depts]

                # 包含自己的部门
                if current_user.department and current_user.department not in managed_dept_names:
                    managed_dept_names.append(current_user.department)

                # 查询这些部门的所有用户
                subordinates = User.query.filter(
                    User.department.in_(managed_dept_names),
                    User.id != current_user.id,
                    User._is_active == True
                ).all()
                for user in subordinates:
                    accounts.append({
                        'id': user.id,
                        'name': user.real_name or user.username,
                        'role': user.role,
                        'has_unread': user.id in unread_sender_ids,
                        'latest_time': unread_sender_times.get(user.id)
                    })
            else:
                # personal 级权限：检查是否有数据归属下属
                from app.views.worklog import get_subordinate_user_ids
                subordinate_ids = get_subordinate_user_ids(current_user)
                if subordinate_ids:
                    subordinates = User.query.filter(
                        User.id.in_(subordinate_ids),
                        User._is_active == True
                    ).all()
                    for user in subordinates:
                        accounts.append({
                            'id': user.id,
                            'name': user.real_name or user.username,
                            'role': user.role,
                            'has_unread': user.id in unread_sender_ids,
                            'latest_time': unread_sender_times.get(user.id)
                        })

        # 排序：有未读的排前面，按最新消息时间倒序
        from datetime import datetime
        accounts.sort(key=lambda x: (
            not x['has_unread'],  # False (有未读) 排前面
            -(x['latest_time'].timestamp() if x['latest_time'] else 0)  # 时间倒序
        ))

        # 移除 latest_time 字段（前端不需要）
        for acc in accounts:
            del acc['latest_time']

        return jsonify({
            'success': True,
            'data': accounts
        })
        
    except Exception as e:
        logger.error(f"获取可用账户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取账户列表失败'
        }), 500 