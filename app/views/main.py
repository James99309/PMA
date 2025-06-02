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
from app.utils.dictionary_helpers import project_type_label
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    logger.info('Accessing index page')
    logger.info('User logged in, rendering index page')
    
    # 获取当前版本信息
    try:
        from app.models.version_management import VersionRecord
        current_version = VersionRecord.get_current_version()
        version_number = current_version.version_number if current_version else '1.2.0'
    except Exception as e:
        logger.warning(f"获取版本信息失败: {str(e)}")
        version_number = '1.2.0'  # 默认版本号
    
    # 查询当前用户可见的最近5个项目，按更新时间倒序
    recent_projects = get_viewable_data(Project, current_user).order_by(Project.updated_at.desc()).limit(5).all()
    # 查询当前用户可见的最近5条报价，按更新时间倒序
    recent_quotations = get_viewable_data(Quotation, current_user).order_by(Quotation.updated_at.desc()).limit(5).all()
    # 查询当前用户可见的最近5个客户，按更新时间倒序
    recent_companies = get_viewable_data(Company, current_user).order_by(Company.updated_at.desc()).limit(5).all()
    # 在index视图中，recent_projects处理类型key转中文
    for p in recent_projects:
        if hasattr(p, 'project_type'):
            p.project_type_display = project_type_label(p.project_type)
    return render_template('index.html', 
                         now=datetime.now(), 
                         recent_projects=recent_projects, 
                         recent_quotations=recent_quotations, 
                         recent_companies=recent_companies,
                         current_version_number=version_number)

@main.route('/api/recent_work_records')
@login_required
def get_recent_work_records():
    """
    获取最近5天的工作记录
    支持权限过滤和账户筛选
    """
    try:
        # 获取参数
        account_id = request.args.get('account_id', type=int)
        
        # 计算5天前的日期
        five_days_ago = datetime.now().date() - timedelta(days=5)
        
        # 基础查询 - 获取最近5天的记录
        base_query = Action.query.filter(Action.date >= five_days_ago)
        
        # 账户筛选逻辑
        if account_id:
            # 如果指定了account_id，检查权限后只显示该账户的记录
            if current_user.role == 'admin':
                # 管理员可以查看任何账户的记录
                base_query = base_query.filter(Action.owner_id == account_id)
            elif current_user.role in ['sales_director', 'service_manager']:
                # 总监级别只能查看下属的记录
                target_user = User.query.get(account_id)
                if target_user and (target_user.department == current_user.department and current_user.is_department_manager):
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
                # 其他角色只能查看自己的记录
                if account_id != current_user.id:
                    return jsonify({
                        'success': True,
                        'data': [],
                        'total': 0,
                        'message': '无权限查看该账户的记录'
                    })
                base_query = base_query.filter(Action.owner_id == current_user.id)
        else:
            # 如果没有指定account_id，按照原有权限逻辑显示
            if current_user.role == 'admin':
                # 管理员可以查看所有记录
                pass
            elif current_user.role in ['sales_director', 'service_manager']:
                # 总监级别可以查看自己和下属的记录（如果是部门负责人）
                if current_user.is_department_manager:
                    subordinate_ids = [user.id for user in User.query.filter_by(department=current_user.department).all()]
                else:
                    subordinate_ids = [current_user.id]
                base_query = base_query.filter(Action.owner_id.in_(subordinate_ids))
            else:
                # 其他角色只能查看自己的记录
                base_query = base_query.filter(Action.owner_id == current_user.id)
        
        # 加载关联数据并按时间倒序排列（不包括replies，因为它是动态关系）
        records = base_query.options(
            joinedload(Action.company),
            joinedload(Action.contact),
            joinedload(Action.project),
            joinedload(Action.owner)
        ).order_by(Action.date.desc(), Action.created_at.desc()).all()
        
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
            if record.owner:
                # 判断是否为厂商账户
                if record.owner.company_name == '和源通信（上海）股份有限公司':
                    # 厂商账户使用胶囊造型徽章
                    display_name = record.owner.real_name if record.owner.real_name else record.owner.username
                    owner_badge_html = f'<span class="badge bg-primary rounded-pill">{display_name}</span>'
                else:
                    # 非厂商账户使用默认造型徽章
                    display_name = record.owner.real_name if record.owner.real_name else record.owner.username
                    owner_badge_html = f'<span class="badge bg-secondary">{display_name}</span>'
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
                'owner_id': record.owner_id
            }
            result.append(record_data)
            
        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
        
    except Exception as e:
        logger.error(f"获取最近工作记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取工作记录失败',
            'error': str(e)
        }), 500

@main.route('/api/available_accounts')
@login_required  
def get_available_accounts():
    """
    获取当前用户有权限查看的账户列表
    """
    try:
        accounts = []
        
        if current_user.role == 'admin':
            # 管理员可以查看所有用户
            all_users = User.query.filter(User.id != current_user.id).all()
            for user in all_users:
                accounts.append({
                    'id': user.id,
                    'name': user.real_name or user.username,
                    'role': user.role
                })
        elif current_user.role in ['sales_director', 'service_manager']:
            # 总监级别可以查看同部门下属（如果是部门负责人）
            if current_user.is_department_manager:
                subordinates = User.query.filter_by(department=current_user.department).filter(User.id != current_user.id).all()
                for user in subordinates:
                    accounts.append({
                        'id': user.id,
                        'name': user.real_name or user.username,
                        'role': user.role
                    })
        
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