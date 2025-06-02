from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.models.change_log import ChangeLog
from app.models.user import User
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.extensions import db
from sqlalchemy import desc, and_, or_, func
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

change_history_bp = Blueprint('change_history', __name__, url_prefix='/admin/history')

@change_history_bp.route('/')
@login_required
def index():
    """历史记录主页"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 过滤参数
    table_name = request.args.get('table_name', '')
    operation_type = request.args.get('operation_type', '')
    user_id = request.args.get('user_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # 构建查询
    query = ChangeLog.query
    
    # 如果不是管理员，只能查看自己的操作记录
    if current_user.role != 'admin':
        query = query.filter(ChangeLog.user_id == current_user.id)
    
    if table_name:
        query = query.filter(ChangeLog.table_name == table_name)
    
    if operation_type:
        query = query.filter(ChangeLog.operation_type == operation_type)
    
    # 只有管理员可以按用户过滤
    if user_id and current_user.role == 'admin':
        query = query.filter(ChangeLog.user_id == user_id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ChangeLog.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ChangeLog.created_at < date_to_obj)
        except ValueError:
            pass
    
    # 按时间倒序排列
    query = query.order_by(desc(ChangeLog.created_at))
    
    # 分页
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 获取所有用户用于过滤（只有管理员可以看到）
    users = []
    if current_user.role == 'admin':
        users = User.query.order_by(User.real_name).all()
    
    # 获取所有表名用于过滤
    if current_user.role == 'admin':
        table_names = ChangeLog.query.with_entities(ChangeLog.table_name).distinct().all()
    else:
        # 普通用户只能看到自己操作过的表
        table_names = ChangeLog.query.filter(ChangeLog.user_id == current_user.id).with_entities(ChangeLog.table_name).distinct().all()
    table_names = [t[0] for t in table_names if t[0]]
    
    return render_template('admin/change_history.html',
                         pagination=pagination,
                         users=users,
                         table_names=table_names,
                         filters={
                             'table_name': table_name,
                             'operation_type': operation_type,
                             'user_id': user_id,
                             'date_from': date_from,
                             'date_to': date_to
                         },
                         is_admin=current_user.role == 'admin')

@change_history_bp.route('/detail/<int:log_id>')
@login_required
def detail(log_id):
    """查看历史记录详情"""
    log = ChangeLog.query.get_or_404(log_id)
    
    # 如果不是管理员，只能查看自己的记录
    if current_user.role != 'admin' and log.user_id != current_user.id:
        from flask import abort
        abort(403)
    
    # 解析JSON数据
    old_values = {}
    new_values = {}
    
    if log.old_values:
        try:
            old_values = json.loads(log.old_values)
        except json.JSONDecodeError:
            old_values = {}
    
    if log.new_values:
        try:
            new_values = json.loads(log.new_values)
        except json.JSONDecodeError:
            new_values = {}
    
    return render_template('admin/change_history_detail.html',
                         log=log,
                         old_values=old_values,
                         new_values=new_values)

@change_history_bp.route('/api/stats')
@login_required
@admin_required
def stats():
    """获取历史记录统计信息（仅管理员）"""
    try:
        # 按操作类型统计
        operation_stats = db.session.query(
            ChangeLog.operation_type,
            func.count(ChangeLog.id).label('count')
        ).group_by(ChangeLog.operation_type).all()
        
        # 按表名统计
        table_stats = db.session.query(
            ChangeLog.table_name,
            func.count(ChangeLog.id).label('count')
        ).group_by(ChangeLog.table_name).all()
        
        # 按日期统计（最近7天）
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_stats = db.session.query(
            func.date(ChangeLog.created_at).label('date'),
            func.count(ChangeLog.id).label('count')
        ).filter(
            ChangeLog.created_at >= seven_days_ago
        ).group_by(func.date(ChangeLog.created_at)).all()
        
        return jsonify({
            'operation_stats': [{'type': op, 'count': count} for op, count in operation_stats],
            'table_stats': [{'table': table, 'count': count} for table, count in table_stats],
            'daily_stats': [{'date': str(date), 'count': count} for date, count in daily_stats]
        })
    except Exception as e:
        logger.error(f"获取历史记录统计失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@change_history_bp.route('/api/logs')
@login_required
def get_logs():
    """获取改动记录API"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        module_name = request.args.get('module_name', '').strip()
        operation_type = request.args.get('operation_type', '').strip()
        user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        search = request.args.get('search', '').strip()
        
        # 构建查询
        query = ChangeLog.query
        
        # 如果不是管理员，只能查看自己的操作记录
        if current_user.role != 'admin':
            query = query.filter(ChangeLog.user_id == current_user.id)
        
        # 模块过滤
        if module_name:
            query = query.filter(ChangeLog.module_name == module_name)
        
        # 操作类型过滤
        if operation_type:
            query = query.filter(ChangeLog.operation_type == operation_type)
        
        # 用户过滤（只有管理员可以按用户过滤）
        if user_id and current_user.role == 'admin':
            query = query.filter(ChangeLog.user_id == user_id)
        
        # 日期范围过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(ChangeLog.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(ChangeLog.created_at <= end_dt)
            except ValueError:
                pass
        
        # 搜索过滤
        if search:
            search_filter = or_(
                ChangeLog.record_info.contains(search),
                ChangeLog.field_name.contains(search),
                ChangeLog.old_value.contains(search),
                ChangeLog.new_value.contains(search)
            )
            query = query.filter(search_filter)
        
        # 排序
        query = query.order_by(desc(ChangeLog.created_at))
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 格式化数据
        logs = []
        for log in pagination.items:
            # 获取用户名
            user_name = '系统'
            if log.user_id:
                user = User.query.get(log.user_id)
                if user:
                    user_name = user.name or user.username
            
            logs.append({
                'id': log.id,
                'module_name': log.module_name,
                'operation_type': log.operation_type,
                'record_info': log.record_info or '',
                'field_name': log.field_name or '',
                'old_value': log.old_value or '',
                'new_value': log.new_value or '',
                'user_name': user_name,
                'ip_address': log.ip_address or '',
                'created_at_formatted': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
            })
        
        return jsonify({
            'success': True,
            'data': logs,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取记录失败: {str(e)}'
        }), 500

@change_history_bp.route('/api/users')
@login_required
@admin_required
def get_users():
    """获取用户列表API（仅管理员）"""
    try:
        # 获取所有有操作记录的用户
        user_ids = ChangeLog.query.filter(
            ChangeLog.user_id.isnot(None)
        ).distinct(ChangeLog.user_id).all()
        
        user_ids = [log.user_id for log in user_ids]
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'name': user.name or user.username
            })
        
        # 按姓名排序
        user_list.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'data': user_list
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500

def get_record_info(module_name, table_name, record_id):
    """获取记录的详细信息"""
    try:
        if table_name == 'projects':
            project = Project.query.get(record_id)
            if project:
                return f"项目: {project.project_name}"
        elif table_name == 'companies':
            company = Company.query.get(record_id)
            if company:
                return f"客户: {company.company_name}"
        elif table_name == 'contacts':
            contact = Contact.query.get(record_id)
            if contact:
                return f"联系人: {contact.name}"
        elif table_name == 'quotations':
            quotation = Quotation.query.get(record_id)
            if quotation:
                return f"报价单: {quotation.quotation_number}"
        elif table_name == 'users':
            user = User.query.get(record_id)
            if user:
                return f"用户: {user.real_name or user.username}"
        
        return f"{table_name}[{record_id}]"
        
    except Exception as e:
        logger.error(f"获取记录信息失败: {str(e)}")
        return f"{table_name}[{record_id}]" 