from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import gettext as _
from app.models.expense import Expense, ExpenseDetail, EXPENSE_CATEGORIES, EXPENSE_STATUS
from app.models.customer import Company
from app.models.project import Project
from app.models.action import Action
from app.models.user import User
from app import db
from app.permissions import permission_required
from sqlalchemy import or_, func, desc, extract
from sqlalchemy.orm import joinedload
from datetime import datetime, date
import logging
from app.utils.access_control import get_viewable_data, can_edit_data
from types import SimpleNamespace

logger = logging.getLogger(__name__)

expense = Blueprint('expense', __name__)

@expense.route('/')
@login_required
@permission_required('expense', 'view')
def expense_list():
    """报销单列表"""
    # 获取筛选参数
    search = request.args.get('search', '').strip()
    customer_id = request.args.get('customer_id', '')
    owner_id = request.args.get('owner_id', '')
    expense_category = request.args.get('expense_category', '')
    status = request.args.get('status', '')
    # 移除department_id参数获取，因为已从模型中删除
    
    # 构建基础查询（主从表结构）
    query = db.session.query(
        Expense.id,
        Expense.expense_number,
        Expense.title,
        Expense.total_amount,
        Expense.status,
        Expense.created_at,
        Company.company_name.label('customer_name'),
        Project.project_name.label('project_name'),
        User,
        func.count(ExpenseDetail.id).label('detail_count')
    ).select_from(Expense)\
     .join(Company, Expense.customer_id == Company.id)\
     .outerjoin(Project, Expense.project_id == Project.id)\
     .join(User, Expense.owner_id == User.id)\
     .outerjoin(ExpenseDetail, Expense.id == ExpenseDetail.expense_id)\
     .filter(Expense.is_deleted == False)\
     .group_by(
        Expense.id, Expense.expense_number, Expense.title, Expense.total_amount,
        Expense.status, Expense.created_at, Company.company_name,
        Project.project_name, User.id, User.username, User.real_name
    )
    
    # 访问控制
    # TODO: 报销模块访问控制逻辑需要实现
    # query = get_viewable_data(Expense, current_user)
    
    # 应用搜索筛选
    if search:
        query = query.filter(
            or_(
                Expense.expense_number.ilike(f'%{search}%'),
                Expense.title.ilike(f'%{search}%'),
                Company.company_name.ilike(f'%{search}%')
            )
        )
    
    if customer_id:
        query = query.filter(Expense.customer_id == customer_id)
    
    if owner_id:
        query = query.filter(Expense.owner_id == owner_id)
    
    # 移除expense_category筛选，因为它现在在明细表中
    # 如果需要按科目筛选，需要join明细表进行筛选
    
    if status:
        query = query.filter(Expense.status == status)
    
    # 移除department_id筛选，因为已从模型中删除
    
    # 排序和执行查询
    total_query = query
    query = query.order_by(desc(Expense.created_at))
    expenses = query.all()
    
    # 格式化数据
    formatted_expenses = []
    for row in expenses:
        # 处理owner字段，确保它是可以安全显示的字符串
        owner_display = ""
        if row[8]:  # User对象
            if hasattr(row[8], 'real_name') and row[8].real_name:
                owner_display = row[8].real_name
            elif hasattr(row[8], 'username'):
                owner_display = row[8].username
            else:
                owner_display = str(row[8])
        
        formatted_row = SimpleNamespace(
            id=row[0],
            expense_number=row[1],
            title=row[2],
            total_amount=row[3],
            status=row[4],
            created_at=row[5],
            customer_name=row[6],
            project_name=row[7] if row[7] else '-',
            owner=owner_display,  # 现在是安全的字符串
            owner_obj=row[8],  # 保留原始User对象
            detail_count=row[9]
        )
        formatted_expenses.append(formatted_row)
    
    # 计算统计数据（基于主表总金额）
    base_stats_query = db.session.query(Expense).filter(Expense.is_deleted == False)
    
    total_count = base_stats_query.count()
    total_amount = db.session.query(func.sum(Expense.total_amount)).filter(
        Expense.is_deleted == False
    ).scalar() or 0
    
    pending_count = base_stats_query.filter(Expense.status == 'pending').count()
    pending_amount = db.session.query(func.sum(Expense.total_amount)).filter(
        Expense.is_deleted == False,
        Expense.status == 'pending'
    ).scalar() or 0
    
    approved_count = base_stats_query.filter(Expense.status == 'approved').count()
    approved_amount = db.session.query(func.sum(Expense.total_amount)).filter(
        Expense.is_deleted == False,
        Expense.status == 'approved'
    ).scalar() or 0
    
    # 获取筛选选项数据
    customers = Company.query.filter(Company.is_deleted == False).order_by(Company.company_name).all()
    users = User.query.filter(User.is_active == True).order_by(User.real_name, User.username).all()
    
    # 构建筛选配置
    filter_config = {
        'action_url': url_for('expense.expense_list'),
        'form_id': 'expenseFilterForm',
        'reset_url': url_for('expense.expense_list'),
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '报销单号、标题或客户名称',
            'value': search,
            'col_width': 4
        },
        'filter_fields': [
            {
                'name': 'customer_id',
                'label': '客户',
                'all_option_text': '全部客户',
                'current_value': customer_id,
                'col_width': 2,
                'options': [{'value': str(c.id), 'label': c.company_name, 'translate': False} for c in customers]
            },
            {
                'name': 'owner_id',
                'label': '申请人',
                'all_option_text': '全部申请人',
                'current_value': owner_id,
                'col_width': 2,
                'options': [{'value': str(u.id), 'label': u.real_name or u.username, 'translate': False} for u in users]
            },
            # 移除报销科目筛选，因为现在在明细表中，可以考虑后续通过明细表联查实现
            {
                'name': 'status',
                'label': '审批状态',
                'all_option_text': '全部状态',
                'current_value': status,
                'col_width': 2,
                'options': [{'value': k, 'label': v, 'translate': True} for k, v in EXPENSE_STATUS]
            }
        ],
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    # 使用通用列表组件配置
    list_config = {
        'module_name': 'expense',
        'title': '报销管理',
        'ajax_mode': True,
        
        # 统计卡片配置
        'stats': {
            'cards': [
                {
                    'id': 'total',
                    'title': '全部报销',
                    'icon': 'fas fa-receipt',
                    'value': total_count,
                    'amount': total_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'primary',
                    'clickable': True,
                    'click_params': {}
                },
                {
                    'id': 'pending',
                    'title': '待审批',
                    'icon': 'fas fa-clock',
                    'value': pending_count,
                    'amount': pending_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'warning',
                    'clickable': True,
                    'click_params': {'status': 'pending'}
                },
                {
                    'id': 'approved',
                    'title': '已通过',
                    'icon': 'fas fa-check-circle',
                    'value': approved_count,
                    'amount': approved_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'success',
                    'clickable': True,
                    'click_params': {'status': 'approved'}
                }
            ]
        },
        
        # 筛选配置
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'expenseTableBody',
            'title': '报销列表',
            'icon': 'fas fa-table',
            'columns': [
                {
                    'key': 'expense_number',
                    'label': '报销单号',
                    'type': 'link',
                    'url_template': '/expense/{id}',
                    'render': 'render_expense_number',
                    'width': '140px'
                },
                {
                    'key': 'title',
                    'label': '报销标题',
                    'type': 'text',
                    'width': '200px'
                },
                {
                    'key': 'customer_name',
                    'label': '客户',
                    'type': 'text',
                    'width': '150px'
                },
                {
                    'key': 'project_name',
                    'label': '项目',
                    'type': 'text',
                    'width': '150px'
                },
                {
                    'key': 'detail_count',
                    'label': '明细数量',
                    'type': 'text',
                    'width': '80px'
                },
                {
                    'key': 'total_amount',
                    'label': '总金额',
                    'type': 'number',
                    'format': 'currency',
                    'align': 'end',
                    'width': '100px'
                },
                {
                    'key': 'status',
                    'label': '状态',
                    'type': 'badge',
                    'render': 'render_expense_status_badge',
                    'align': 'start',
                    'width': '100px'
                },
                {
                    'key': 'owner',
                    'label': '申请人',
                    'type': 'text',
                    'align': 'start',
                    'width': '100px'
                },
                {
                    'key': 'created_at',
                    'label': '创建时间',
                    'type': 'date',
                    'format': '%Y-%m-%d',
                    'width': '120px'
                }
            ]
        }
    }
    
    return render_template('expense/expense_list.html', 
                         list_config=list_config,
                         expenses=formatted_expenses)

@expense.route('/ajax/test')
def test_ajax():
    """测试AJAX端点"""
    return jsonify({'status': 'ok', 'message': 'AJAX端点工作正常'})

@expense.route('/ajax')
@login_required
@permission_required('expense', 'view')
def expense_list_ajax():
    """报销列表AJAX端点"""
    try:
        logger.info(f"AJAX请求开始，参数: {dict(request.args)}")
        
        # 获取筛选参数
        search = request.args.get('search', '').strip()
        customer_id = request.args.get('customer_id', '')
        owner_id = request.args.get('owner_id', '')
        status = request.args.get('status', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 构建查询（与列表页面相同的逻辑）
        query = db.session.query(
            Expense.id,
            Expense.expense_number,
            Expense.title,
            Expense.total_amount,
            Expense.status,
            Expense.created_at,
            Company.company_name.label('customer_name'),
            Project.project_name.label('project_name'),
            User,
            func.count(ExpenseDetail.id).label('detail_count')
        ).select_from(Expense)\
         .join(Company, Expense.customer_id == Company.id)\
         .outerjoin(Project, Expense.project_id == Project.id)\
         .join(User, Expense.owner_id == User.id)\
         .outerjoin(ExpenseDetail, Expense.id == ExpenseDetail.expense_id)\
         .filter(Expense.is_deleted == False)\
         .group_by(
            Expense.id, Expense.expense_number, Expense.title, Expense.total_amount,
            Expense.status, Expense.created_at, Company.company_name,
            Project.project_name, User.id, User.username, User.real_name
        )
        
        # 应用筛选
        if search:
            query = query.filter(
                or_(
                    Expense.expense_number.ilike(f'%{search}%'),
                    Expense.title.ilike(f'%{search}%'),
                    Company.company_name.ilike(f'%{search}%')
                )
            )
        
        if customer_id:
            query = query.filter(Expense.customer_id == customer_id)
        if owner_id:
            query = query.filter(Expense.owner_id == owner_id)
        if status:
            query = query.filter(Expense.status == status)
        
        # 执行查询
        total_count = query.count()
        expenses = query.order_by(desc(Expense.created_at))\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        
        # 格式化数据并渲染HTML
        html_rows = []
        for row in expenses:
            # 处理owner字段，确保它是可以安全显示的字符串
            owner_display = ""
            if row[8]:  # User对象
                if hasattr(row[8], 'real_name') and row[8].real_name:
                    owner_display = row[8].real_name
                elif hasattr(row[8], 'username'):
                    owner_display = row[8].username
                else:
                    owner_display = str(row[8])
            
            formatted_row = SimpleNamespace(
                id=row[0],
                expense_number=row[1],
                title=row[2],
                total_amount=row[3],
                status=row[4],
                created_at=row[5],
                customer_name=row[6],
                project_name=row[7] if row[7] else '-',
                owner=owner_display,  # 现在是安全的字符串
                owner_obj=row[8],  # 保留原始User对象
                detail_count=row[9]
            )
            
            html_row = render_template('expense/expense_rows.html', expense=formatted_row)
            html_rows.append(html_row)
        
        # 计算统计数据
        stats_query = db.session.query(Expense).filter(Expense.is_deleted == False)
        
        total_stats_count = stats_query.count()
        total_stats_amount = db.session.query(func.sum(Expense.total_amount)).filter(
            Expense.is_deleted == False
        ).scalar() or 0
        
        pending_stats_count = stats_query.filter(Expense.status == 'pending').count()
        pending_stats_amount = db.session.query(func.sum(Expense.total_amount)).filter(
            Expense.is_deleted == False,
            Expense.status == 'pending'
        ).scalar() or 0
        
        approved_stats_count = stats_query.filter(Expense.status == 'approved').count()
        approved_stats_amount = db.session.query(func.sum(Expense.total_amount)).filter(
            Expense.is_deleted == False,
            Expense.status == 'approved'
        ).scalar() or 0
        
        statistics = {
            'total_count': total_stats_count,
            'total_amount': total_stats_amount / 10000,
            'pending_count': pending_stats_count,
            'pending_amount': pending_stats_amount / 10000,
            'approved_count': approved_stats_count,
            'approved_amount': approved_stats_amount / 10000
        }
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': total_count,
            'loaded_count': len(expenses),
            'statistics': statistics
        })
    
    except Exception as e:
        import traceback
        logger.error(f"报销列表AJAX请求失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'html': '<tr><td colspan="9" class="text-center text-danger">数据加载失败</td></tr>'
        }), 500

@expense.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('expense', 'create')
def create_expense():
    """创建报销单"""
    if request.method == 'POST':
        try:
            # 获取主表表单数据
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            customer_id = request.form.get('customer_id', type=int)
            project_id = request.form.get('project_id', type=int) or None
            
            # 数据验证
            if not all([title, customer_id]):
                flash('请填写所有必填字段', 'error')
                return redirect(url_for('expense.create_expense'))
            
            # 获取报销明细数据 - 新组件使用不同的字段名格式
            # 格式: details[0][expense_date], details[1][expense_date], etc.
            detail_data = {}
            for key, value in request.form.items():
                if key.startswith('details[') and '][' in key:
                    # 解析 details[index][field] 格式
                    try:
                        index_end = key.find('][')
                        index = int(key[8:index_end])  # 提取索引
                        field = key[index_end+2:-1]    # 提取字段名
                        
                        if index not in detail_data:
                            detail_data[index] = {}
                        detail_data[index][field] = value
                    except (ValueError, IndexError):
                        continue
            
            # 验证明细数据
            if not detail_data:
                flash('请至少添加一条报销明细', 'error')
                return redirect(url_for('expense.create_expense'))
            
            # 验证明细数据完整性
            detail_items = []
            total_amount = 0.0
            
            for index in sorted(detail_data.keys()):
                detail = detail_data[index]
                try:
                    # 检查必填字段
                    required_fields = ['expense_category', 'expense_date', 'description', 'amount']
                    for field in required_fields:
                        if not detail.get(field) or not str(detail[field]).strip():
                            flash(f'第{index+1}个明细项目的{field}字段为必填项', 'error')
                            return redirect(url_for('expense.create_expense'))
                    
                    # 转换数据类型
                    expense_date = datetime.strptime(detail['expense_date'], '%Y-%m-%d').date()
                    amount = float(detail['amount'])
                    document_count = int(detail.get('document_count', 1)) if detail.get('document_count') else 1
                    
                    if amount <= 0:
                        flash(f'第{index+1}个明细项目的金额必须大于0', 'error')
                        return redirect(url_for('expense.create_expense'))
                    
                    detail_items.append({
                        'expense_date': expense_date,
                        'expense_category': detail['expense_category'],
                        'description': detail['description'].strip(),
                        'document_count': document_count,
                        'amount': amount
                    })
                    
                    total_amount += amount
                    
                except (ValueError, KeyError) as e:
                    flash(f'第{index+1}个明细项目数据格式错误: {str(e)}', 'error')
                    return redirect(url_for('expense.create_expense'))
            
            # 创建报销单（主表）
            expense_obj = Expense(
                title=title,
                description=description,
                customer_id=customer_id,
                project_id=project_id,
                owner_id=current_user.id,
                total_amount=total_amount  # 根据明细计算总金额
            )
            
            db.session.add(expense_obj)
            db.session.flush()  # 获取主表ID
            
            # 创建报销明细
            for detail_data in detail_items:
                detail_obj = ExpenseDetail(
                    expense_id=expense_obj.id,
                    expense_date=detail_data['expense_date'],
                    expense_category=detail_data['expense_category'],
                    description=detail_data['description'],
                    document_count=detail_data['document_count'],
                    amount=detail_data['amount']
                )
                db.session.add(detail_obj)
            
            db.session.commit()
            
            flash(f'报销单创建成功，共添加 {len(detail_items)} 条明细，总金额 ¥{total_amount:.2f}', 'success')
            return redirect(url_for('expense.expense_detail', id=expense_obj.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建报销单失败: {e}")
            flash('创建报销单失败，请重试', 'error')
    
    # GET请求，显示创建表单
    return render_template('expense/create_expense.html')

@expense.route('/<int:id>')
@login_required
@permission_required('expense', 'view')
def expense_detail(id):
    """报销单详情"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.customer),
        db.joinedload(Expense.project),
        db.joinedload(Expense.owner),
        db.joinedload(Expense.approver),
        db.joinedload(Expense.details)
        # 移除action和department关联加载，因为已从模型中删除
    ).get_or_404(id)
    
    # 检查访问权限
    if not can_edit_data(expense_obj, current_user):
        flash('您没有权限查看此报销单', 'error')
        return redirect(url_for('expense.expense_list'))
    
    return render_template('expense/expense_detail.html', expense=expense_obj)

@expense.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('expense', 'edit')
def edit_expense(id):
    """编辑报销单"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.customer),
        db.joinedload(Expense.project),
        db.joinedload(Expense.owner)
        # 移除action和department关联加载，因为已从模型中删除
    ).get_or_404(id)
    
    # 检查编辑权限
    if not can_edit_data(expense_obj, current_user):
        flash('您没有权限编辑此报销单', 'error')
        return redirect(url_for('expense.expense_detail', id=id))
    
    # 已审批的报销单不能编辑
    if expense_obj.status not in ['draft', 'pending']:
        flash('已审批的报销单不能编辑', 'error')
        return redirect(url_for('expense.expense_detail', id=id))
    
    if request.method == 'POST':
        try:
            # 更新报销单信息（仅主表字段）
            expense_obj.title = request.form.get('title', '').strip()
            expense_obj.description = request.form.get('description', '').strip()
            expense_obj.customer_id = request.form.get('customer_id', type=int)
            expense_obj.project_id = request.form.get('project_id', type=int) or None
            # 移除department_id设置，因为已从模型中删除
            
            db.session.commit()
            flash('报销单更新成功', 'success')
            return redirect(url_for('expense.expense_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新报销单失败: {e}")
            flash('更新报销单失败，请重试', 'error')
    
    # GET请求，显示编辑表单
    customers = Company.query.filter(Company.is_deleted == False).order_by(Company.company_name).all()
    projects = Project.query.order_by(Project.project_name).all()
    # 移除departments查询，因为已从模型中删除
    
    return render_template('expense/edit_expense.html',
                         expense=expense_obj,
                         customers=customers,
                         projects=projects)

@expense.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('expense', 'delete')
def delete_expense(id):
    """删除报销单"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.owner)
    ).get_or_404(id)
    
    # 检查删除权限
    if not can_edit_data(expense_obj, current_user):
        return jsonify({'success': False, 'message': '您没有权限删除此报销单'})
    
    # 已审批的报销单不能删除
    if expense_obj.status not in ['draft', 'pending']:
        return jsonify({'success': False, 'message': '已审批的报销单不能删除'})
    
    try:
        # 软删除
        expense_obj.is_deleted = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '报销单删除成功',
            'redirect_url': url_for('expense.expense_list')
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除报销单失败: {e}")
        return jsonify({'success': False, 'message': '删除报销单失败，请重试'})

@expense.route('/api/expense/monthly_stats')
@login_required
@permission_required('expense', 'view')
def monthly_expense_stats():
    """当月费用统计"""
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # 查询当月已通过的报销（基于明细表）
    monthly_query = db.session.query(
        func.sum(ExpenseDetail.amount).label('total_amount'),
        func.count(ExpenseDetail.id).label('total_count'),
        ExpenseDetail.expense_category
    ).join(Expense, ExpenseDetail.expense_id == Expense.id)\
     .filter(
        Expense.is_deleted == False,
        Expense.status == 'approved',
        extract('year', Expense.approved_at) == current_year,
        extract('month', Expense.approved_at) == current_month
    ).group_by(ExpenseDetail.expense_category).all()
    
    # 按用户统计（基于主表总金额）
    user_stats = db.session.query(
        func.sum(Expense.total_amount).label('total_amount'),
        func.count(Expense.id).label('total_count'),
        User.username,
        User.real_name
    ).join(User, Expense.owner_id == User.id)\
     .filter(
        Expense.is_deleted == False,
        Expense.status == 'approved',
        extract('year', Expense.approved_at) == current_year,
        extract('month', Expense.approved_at) == current_month
    ).group_by(User.id, User.username, User.real_name).all()
    
    # 格式化统计数据
    category_stats = {}
    # 移除department_stats，因为已从模型中删除部门功能
    
    for row in monthly_query:
        category = dict(EXPENSE_CATEGORIES).get(row.expense_category, row.expense_category)
        if category not in category_stats:
            category_stats[category] = {'amount': 0, 'count': 0}
        category_stats[category]['amount'] += row.total_amount or 0
        category_stats[category]['count'] += row.total_count or 0
    
    user_stats_formatted = []
    for row in user_stats:
        user_stats_formatted.append({
            'username': row.username,
            'real_name': row.real_name,
            'amount': row.total_amount or 0,
            'count': row.total_count or 0
        })
    
    return jsonify({
        'success': True,
        'month': f'{current_year}年{current_month}月',
        'category_stats': category_stats,
        # 移除department_stats，因为已从模型中删除部门功能
        'user_stats': user_stats_formatted
    })