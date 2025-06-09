from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.customer import Company
from app import db
from datetime import datetime
import logging
from app.decorators import permission_required  # 添加导入权限装饰器
import json
from app.utils.access_control import get_viewable_data

logger = logging.getLogger(__name__)

bp = Blueprint('project', __name__, url_prefix='/project')

# 添加全局请求拦截器记录详细日志
@bp.before_request
def log_request_info():
    print("\n======================= 请求信息 =======================")
    print(f"URL: {request.url}")
    print(f"方法: {request.method}")
    print(f"参数: {request.args}")
    print(f"表单数据: {request.form}")
    print(f"JSON数据: {request.json}")
    print(f"请求头: {request.headers}")
    print("========================================================\n")

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('project', 'edit')  # 添加权限装饰器
def edit_project(id):
    """编辑项目"""
    print(f"\n开始处理项目编辑请求，ID: {id}\n")
    
    # 保证companies始终有一个默认值
    default_companies = {
        'users': [], 
        'designers': [], 
        'contractors': [], 
        'system_integrators': [], 
        'dealers': []
    }
    
    # 获取项目信息
    project = Project.query.get_or_404(id)
    
    # 检查权限：只有项目创建者和管理员可以编辑
    if not current_user.is_admin and project.creator_id != current_user.id:
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    # 处理POST请求
    if request.method == 'POST':
        try:
            print("收到POST请求，开始处理表单数据")
            
            # 1. 收集表单数据
            form_data = request.form.to_dict()
            print(f"接收到表单数据: {form_data}")
            
            # 2. 更新项目基本信息
            project.project_name = form_data.get('project_name')
            project.report_source = form_data.get('report_source')
            # 编辑时保留原始项目类型，不进行更新
            # project.project_type = form_data.get('project_type') 
            project.product_situation = form_data.get('product_situation')
            project.current_stage = form_data.get('current_stage')
            project.end_user = form_data.get('end_user')
            project.design_issues = form_data.get('design_issues')
            project.contractor = form_data.get('contractor')
            project.system_integrator = form_data.get('system_integrator')
            project.dealer = form_data.get('dealer')
            project.stage_description = form_data.get('stage_description')
            
            # 3. 处理特殊字段            
            # 金额字段处理
            quotation_str = form_data.get('quotation_customer', '')
            if quotation_str:
                # 移除所有逗号和其他非数字字符(保留小数点)
                clean_quotation = ''.join(c for c in quotation_str if c.isdigit() or c == '.')
                try:
                    project.quotation_customer = float(clean_quotation)
                except ValueError:
                    project.quotation_customer = None
            else:
                project.quotation_customer = None
                
            # 日期字段处理 - 编辑时保留原始报备日期，不进行更新
            # if form_data.get('report_time'):
            #     project.report_time = datetime.strptime(form_data['report_time'], '%Y-%m-%d').date()
            
            if form_data.get('delivery_forecast'):
                project.delivery_forecast = datetime.strptime(form_data['delivery_forecast'], '%Y-%m-%d').date()
            
            # 4. 保存到数据库
            db.session.commit()
            print("项目更新成功")
            flash('项目更新成功', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"更新项目失败: {str(e)}")
            flash(f'更新项目失败：{str(e)}', 'danger')
        
        # 5. 渲染模板
        return render_template(
            'project/edit.html', 
            project=project,
            title="编辑项目",
            companies=default_companies
        )
    
    # 处理GET请求
    # 添加日期格式化，确保前端能正确显示
    if project.report_time:
        project.formatted_report_time = project.report_time.strftime('%Y-%m-%d')
    if project.delivery_forecast:
        project.formatted_delivery_forecast = project.delivery_forecast.strftime('%Y-%m-%d')
    
    # 确保project_type保持原始值，不进行转换处理
    # 前端会根据 project.project_type 的值来正确选择下拉菜单中的选项
    
    # 获取所有可用的公司信息
    company_query = get_viewable_data(Company, current_user)
    companies = {
        'users': company_query.filter_by(company_type='用户').all(),
        'designers': company_query.filter_by(company_type='设计院及顾问').all(),
        'contractors': company_query.filter_by(company_type='总承包单位').all(),
        'integrators': company_query.filter_by(company_type='系统集成商').all(),
        'dealers': company_query.filter_by(company_type='经销商').all()
    }
    
    return render_template(
        'project/edit.html', 
        project=project,
        title="编辑项目",
        companies=companies
    )

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('project', 'create')  # 添加权限装饰器
def add_project():
    companies = None  # 在函数开始就定义companies变量
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            project_data = {
                'project_name': request.form.get('project_name'),
                'report_time': datetime.strptime(request.form.get('report_time'), '%Y-%m-%d'),
                'report_source': request.form.get('report_source'),
                'project_type': request.form.get('project_type'),
                'product_situation': request.form.get('product_situation'),
                'current_stage': request.form.get('current_stage'),
                'quotation_customer': float(request.form.get('quotation_customer').replace(',', '') or 0),
                'delivery_forecast': datetime.strptime(request.form.get('delivery_forecast'), '%Y-%m-%d'),
                'end_user': request.form.get('end_user'),
                'design_issues': request.form.get('design_issues'),
                'contractor': request.form.get('contractor'),
                'system_integrator': request.form.get('system_integrator'),
                'dealer': request.form.get('dealer'),
                'stage_description': request.form.get('stage_description')
            }
            
            # 创建新项目
            new_project = Project(**project_data)
            db.session.add(new_project)
            db.session.commit()
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('project.list_projects'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERROR - 添加项目失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            flash(f'添加项目失败：{str(e)}', 'danger')
            
            # 获取不同类型的公司列表，确保在异常时也能显示表单
            if not companies:
                try:
                    companies = {
                        'users': Company.query.filter_by(company_type='用户').all(),
                        'designers': Company.query.filter_by(company_type='设计院及顾问').all(),
                        'contractors': Company.query.filter_by(company_type='总承包单位').all(),
                        'integrators': Company.query.filter_by(company_type='系统集成商').all(),
                        'dealers': Company.query.filter_by(company_type='经销商').all()
                    }
                except:
                    companies = {
                        'users': [],
                        'designers': [],
                        'contractors': [],
                        'integrators': [],
                        'dealers': []
                    }
            
            return render_template('project/edit.html', project=None, companies=companies)
    
    # 获取不同类型的公司列表
    try:
        companies = {
            'users': Company.query.filter_by(company_type='用户').all(),
            'designers': Company.query.filter_by(company_type='设计院及顾问').all(),
            'contractors': Company.query.filter_by(company_type='总承包单位').all(),
            'integrators': Company.query.filter_by(company_type='系统集成商').all(),
            'dealers': Company.query.filter_by(company_type='经销商').all()
        }
        
        # 添加调试日志
        print("DEBUG - 公司数据:")
        for company_type, company_list in companies.items():
            print(f"{company_type}: {len(company_list)} 家公司")
            for company in company_list:
                print(f"  - {company.company_name} ({company.company_type})")
    except Exception as e:
        print(f"ERROR - 获取公司数据失败: {str(e)}")
        companies = {
            'users': [],
            'designers': [],
            'contractors': [],
            'integrators': [],
            'dealers': []
        }
    
    return render_template('project/edit.html', project=None, companies=companies)

@bp.route('/')
@login_required
@permission_required('project', 'view')  # 添加权限装饰器
def list_projects():
    """
    项目列表页面
    
    ⚠️ 重要保护说明 ⚠️
    1. 此函数负责渲染项目列表页面，页面布局经过精心设计
    2. 必须始终传递 companies 和 projects 变量给模板
    3. 不得修改模板变量名称或数据结构
    4. 对此函数或相关模板的任何修改必须先获得倪捷的明确许可
    """
    companies = None  # 在函数开始就定义companies变量
    try:
        # 获取请求参数
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'id')
        order = request.args.get('order', 'desc')
        
        # 构建查询
        query = Project.query
        
        # 添加搜索条件
        if search:
            query = query.filter(Project.project_name.ilike(f'%{search}%'))
        
        # 处理筛选参数
        filters = {}
        for key, value in request.args.items():
            if key.startswith('filter_') and value:
                field = key[7:]  # 移除'filter_'前缀
                filters[field] = value
        
        # 应用筛选条件
        for field, value in filters.items():
            if hasattr(Project, field):
                # 处理不同类型的字段
                if field in ['report_time', 'delivery_forecast', 'created_at', 'updated_at']:
                    # 日期字段
                    try:
                        date_value = datetime.strptime(value, '%Y-%m-%d').date()
                        query = query.filter(getattr(Project, field) == date_value)
                    except (ValueError, TypeError):
                        # 日期格式错误，忽略此筛选
                        pass
                elif field == 'quotation_customer':
                    # 数字字段，使用模糊匹配
                    query = query.filter(getattr(Project, field).cast(db.String).ilike(f'%{value}%'))
                else:
                    # 文本字段，使用模糊匹配
                    query = query.filter(getattr(Project, field).ilike(f'%{value}%'))
        
        # 添加排序条件
        try:
            sort_column = getattr(Project, sort, Project.id)
            if order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        except Exception as e:
            logger.warning(f"排序出错：{str(e)}，使用默认排序")
            query = query.order_by(Project.id.desc())
            
        projects = query.all()
        
        # 获取不同类型的公司列表
        company_query = get_viewable_data(Company, current_user)
        companies = {
            'users': company_query.filter_by(company_type='用户').all(),
            'designers': company_query.filter_by(company_type='设计院及顾问').all(),
            'contractors': company_query.filter_by(company_type='总承包单位').all(),
            'integrators': company_query.filter_by(company_type='系统集成商').all(),
            'dealers': company_query.filter_by(company_type='经销商').all()
        }
        
        # 添加调试日志
        print("DEBUG - 项目列表页面数据:")
        print(f"项目数量: {len(projects)}")
        print("公司数据:")
        for company_type, company_list in companies.items():
            print(f"{company_type}: {len(company_list)} 家公司")
        
        # ⚠️ 警告: 不要修改这一行 - 必须保持两个变量的传递
        return render_template('project/list.html', projects=projects, companies=companies, search_term=search)
    except Exception as e:
        # 确保companies变量存在，即使在异常情况下
        if not companies:
            companies = {
                'users': [],
                'designers': [],
                'contractors': [],
                'integrators': [],
                'dealers': []
            }
            
        logger.error(f'加载项目列表页面出现错误: {str(e)}')
        print(f"ERROR - 加载项目列表页面失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        flash('加载项目列表失败！', 'error')
        try:
            projects = []
            search = request.args.get('search', '')
            # ⚠️ 警告: 不要修改这一行 - 即使在错误处理中也必须保持变量结构
            return render_template('project/list.html', projects=projects, companies=companies, search_term=search)
        except:
            return redirect(url_for('main.index'))

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('project', 'delete')  # 添加权限装饰器
def delete_project(id):
    """删除项目"""
    try:
        project = Project.query.get_or_404(id)
        db.session.delete(project)
        db.session.commit()
        flash('项目删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除项目失败：{str(e)}')
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('project.list_projects'))

@bp.route('/api/update_stage', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def update_project_stage():
    """
    更新项目阶段
    用于项目阶段可视化进度条组件调用
    
    注意：此功能已移至app/views/project.py中实现，
    此处保留代码作为参考，但已不再使用
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
            
        project_id = data.get('project_id')
        new_stage = data.get('current_stage')
        
        if not project_id or not new_stage:
            return jsonify({'success': False, 'message': '项目ID和阶段不能为空'}), 400
            
        # 查询项目
        project = Project.query.get_or_404(project_id)
        
        # 检查权限
        allowed = False
        if current_user.role == 'admin':
            allowed = True
        elif project.owner_id == current_user.id:
            allowed = True
        else:
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                allowed = True
        
        if not allowed:
            return jsonify({'success': False, 'message': '您没有权限修改此项目'}), 403
            
        # 更新项目阶段
        old_stage = project.current_stage
        project.current_stage = new_stage
        
        # 在阶段说明中添加阶段变更记录
        change_record = f"\n[阶段变更] {old_stage} → {new_stage} (更新者: {current_user.username}, 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        if project.stage_description:
            project.stage_description += change_record
        else:
            project.stage_description = change_record
            
        # 保存更新
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '项目阶段已更新',
            'data': {
                'project_id': project.id,
                'current_stage': project.current_stage,
                'old_stage': old_stage
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"更新项目阶段出错: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500 