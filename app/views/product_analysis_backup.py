from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.permissions import has_permission
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from app.models.product import Product
from app.models.user import User, Affiliation
from app.utils.access_control import get_viewable_data
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta
from app import db
import logging
from app.utils.dictionary_helpers import project_stage_label

logger = logging.getLogger(__name__)

product_analysis = Blueprint('product_analysis', __name__)

def apply_permission_based_filters(query, current_user, quotation_alias=Quotation, project_alias=Project):
    """
    基于四级权限系统应用数据过滤
    """
    if has_permission('product', 'admin'):
        return query
    
    # 检查用户是否有报价单查看权限
    if not current_user.has_permission('quotation', 'view'):
        # 如果没有权限，返回空查询
        return query.filter(False)
    
    # 获取权限级别
    permission_level = current_user.get_permission_level('quotation')
    
    if permission_level == 'system':
        # 系统级权限：可以查看所有数据
        return query
    elif permission_level == 'company' and current_user.company_name:
        # 企业级权限：可以查看企业下所有数据
        company_user_ids = [u.id for u in User.query.filter_by(company_name=current_user.company_name).all()]
        return query.filter(project_alias.owner_id.in_(company_user_ids))
    elif permission_level == 'department' and current_user.department and current_user.company_name:
        # 部门级权限：可以查看部门下所有数据
        dept_user_ids = [u.id for u in User.query.filter(
            User.department == current_user.department,
            User.company_name == current_user.company_name
        ).all()]
        return query.filter(project_alias.owner_id.in_(dept_user_ids))
    else:
        # 个人级权限：应用传统的权限过滤逻辑
        permission_filters = []
        
        # 1. 自己创建的报价单
        permission_filters.append(quotation_alias.owner_id == current_user.id)
        
        # 2. 归属关系 - 使用子查询优化
        affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
            Affiliation.viewer_id == current_user.id
        ).subquery()
        permission_filters.append(quotation_alias.owner_id.in_(affiliation_subquery))
        
        # 3. 销售负责人相关项目
        permission_filters.append(project_alias.vendor_sales_manager_id == current_user.id)
        
        # 4. 其他角色特殊权限
        user_role = current_user.role.strip() if current_user.role else ''
        if user_role == 'channel_manager':
            # 渠道经理：额外可以查看渠道跟进项目
            permission_filters.append(project_alias.project_type == 'channel_follow')
        elif user_role == 'sales_director':
            # 营销总监：额外可以查看销售重点和渠道跟进项目
            permission_filters.append(project_alias.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
        elif user_role in ['service', 'service_manager']:
            # 服务经理：额外可以查看业务机会项目
            permission_filters.append(project_alias.project_type == '业务机会')
        elif user_role == 'business_admin':
            # 商务助理：可以查看同部门用户和归属关系授权用户的项目
            viewable_user_ids = [current_user.id]  # 自己的项目
            
            # 1. 添加同部门用户
            if current_user.department and current_user.company_name:
                dept_users = User.query.filter(
                    User.department == current_user.department,
                    User.company_name == current_user.company_name
                ).all()
                viewable_user_ids.extend([u.id for u in dept_users])
            
            # 2. 添加归属关系授权的用户
            affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            
            # 去重
            viewable_user_ids = list(set(viewable_user_ids))
            
            # 添加权限过滤条件
            permission_filters.append(
                db.or_(
                    project_alias.owner_id.in_(viewable_user_ids),
                    project_alias.vendor_sales_manager_id.in_(viewable_user_ids)
                )
            )
        
        # 应用权限过滤条件
        if permission_filters:
            return query.filter(or_(*permission_filters))
        else:
            # 如果没有任何权限，返回空查询
            return query.filter(False)

# 阶段顺序定义 - 与项目管理模块保持一致
STAGE_ORDER = [
    'discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused', 'unset'
]

# 阶段颜色配置 - 使用项目管理的标准颜色
STAGE_COLORS_COUNT = {
    'discover': 'rgba(2, 103, 5, 0.05)',      # 026705 透明度 5%
    'embed': 'rgba(2, 103, 5, 0.2)',         # 026705 透明度 20%
    'pre_tender': 'rgba(2, 103, 5, 0.3)',    # 026705 透明度 30%
    'tendering': 'rgba(2, 103, 5, 0.5)',     # 026705 透明度 50%
    'awarded': 'rgba(2, 103, 5, 0.7)',       # 026705 透明度 70%
    'quoted': 'rgba(2, 103, 5, 0.8)',        # 026705 透明度 80%
    'signed': 'rgba(2, 103, 5, 1)',          # 026705 透明度 100%
    'lost': 'rgba(108, 3, 3, 1)',            # 6C0303 透明度 100%
    'paused': 'rgba(189, 194, 189, 1)',      # BDC2BD 透明度 100%
    'unset': 'rgba(189, 194, 189, 0.5)'      # BDC2BD 透明度 50%
}

STAGE_COLORS_AMOUNT = {
    'discover': 'rgba(7, 70, 160, 0.05)',    # 0746A0 透明度 5%
    'embed': 'rgba(7, 70, 160, 0.2)',        # 0746A0 透明度 20%
    'pre_tender': 'rgba(7, 70, 160, 0.3)',   # 0746A0 透明度 30%
    'tendering': 'rgba(7, 70, 160, 0.5)',    # 0746A0 透明度 50%
    'awarded': 'rgba(7, 70, 160, 0.7)',      # 0746A0 透明度 70%
    'quoted': 'rgba(7, 70, 160, 0.8)',       # 0746A0 透明度 80%
    'signed': 'rgba(7, 70, 160, 1)',         # 0746A0 透明度 100%
    'lost': 'rgba(108, 3, 3, 1)',            # 6C0303 透明度 100%
    'paused': 'rgba(189, 194, 189, 1)',      # BDC2BD 透明度 100%
    'unset': 'rgba(189, 194, 189, 0.5)'      # BDC2BD 透明度 50%
}

# 兼容性颜色配置
STAGE_COLORS = STAGE_COLORS_COUNT

def get_stage_label(stage_key):
    """获取阶段中文标签"""
    return project_stage_label(stage_key, 'zh')

@product_analysis.route('/analysis')
@login_required
@permission_required('quotation', 'view')
def analysis():
    """产品分析主页面"""
    # 获取所有产品类别、名称和型号供筛选使用
    categories = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None)
    ).order_by(Product.category).all()
    
    product_names = db.session.query(Product.product_name).distinct().filter(
        Product.product_name.isnot(None)
    ).order_by(Product.product_name).all()
    
    product_models = db.session.query(Product.model).distinct().filter(
        Product.model.isnot(None)
    ).order_by(Product.model).all()
    
    return render_template('product_analysis/analysis.html',
                         categories=[c[0] for c in categories],
                         product_names=[p[0] for p in product_names],
                         product_models=[m[0] for m in product_models])

@product_analysis.route('/api/filter_options')
@login_required
@permission_required('quotation', 'view')
def get_filter_options():
    """获取筛选选项的联动数据"""
    try:
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        
        # 构建基础查询
        query = db.session.query(Product)
        
        # 获取产品类别选项（不受其他筛选条件影响）
        categories = db.session.query(Product.category).distinct().filter(
            Product.category.isnot(None)
        ).order_by(Product.category).all()
        
        # 根据已选择的条件进行筛选
        if category:
            query = query.filter(Product.category == category)
        if product_name:
            query = query.filter(Product.product_name == product_name)
        
        # 获取产品名称选项
        product_names = query.with_entities(Product.product_name).distinct().filter(
            Product.product_name.isnot(None)
        ).order_by(Product.product_name).all()
        
        # 获取产品型号选项
        product_models = query.with_entities(Product.model).distinct().filter(
            Product.model.isnot(None)
        ).order_by(Product.model).all()
        
        return jsonify({
            'success': True,
            'categories': [c[0] for c in categories],
            'product_names': [p[0] for p in product_names],
            'product_models': [m[0] for m in product_models]
        })
        
    except Exception as e:
        logger.error(f"获取筛选选项失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_analysis.route('/api/analysis_data')
@login_required
@permission_required('quotation', 'view')
def get_analysis_data():
    """获取产品分析数据 - 性能优化版本"""
    try:
        # 获取筛选参数
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))  # 默认每页50条
        
        # 性能优化：直接在主查询中处理权限逻辑，避免先查询所有可见报价单
        # 构建基础查询 - 避免因Product表重复记录导致的重复统计
        query = db.session.query(
            QuotationDetail.id,
            QuotationDetail.product_name,
            QuotationDetail.product_model,
            QuotationDetail.product_desc,
            QuotationDetail.quantity,
            QuotationDetail.discount,
            QuotationDetail.unit_price,
            QuotationDetail.total_price,
            QuotationDetail.product_mn,
            User.username.label('owner_name'),
            User.real_name.label('owner_real_name'),
            User.company_name.label('company_name'),
            Project.id.label('project_id'),
            Project.project_name,
            Project.current_stage,
            Quotation.id.label('quotation_id'),
            Quotation.quotation_number,
            QuotationDetail.updated_at,
            QuotationDetail.created_at
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用基于权限系统的数据过滤
        query = apply_permission_based_filters(query, current_user)
        
        # 应用筛选条件
        if category:
            # 使用子查询获取指定类别的产品，避免因Product表重复记录导致的重复统计
            category_products = db.session.query(
                Product.product_name, 
                Product.model
            ).filter(
                Product.category == category
            ).distinct().subquery()
            
            query = query.filter(
                and_(
                    QuotationDetail.product_name == category_products.c.product_name,
                    QuotationDetail.product_model == category_products.c.model
                )
            )
        
        if product_name:
            query = query.filter(QuotationDetail.product_name == product_name)
        
        if product_model:
            query = query.filter(QuotationDetail.product_model == product_model)
        
        # 获取总数（用于分页）
        total_count = query.count()
        
        # 执行分页查询 - 默认按更新时间降序排序
        try:
            results = query.order_by(QuotationDetail.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        except Exception as e:
            logger.warning(f"使用updated_at排序失败: {str(e)}, 尝试使用id排序")
            try:
                # 回滚失败的事务
                db.session.rollback()
                results = query.order_by(QuotationDetail.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
            except Exception as e2:
                logger.error(f"产品分析查询失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                results = []
        
        # 格式化数据
        data = []
        for row in results:
            item = {
                'id': row.id,
                'product_name': row.product_name,
                'product_model': row.product_model,
                'product_desc': row.product_desc,
                'quantity': row.quantity,
                'discount': f"{row.discount * 100:.1f}%" if row.discount else "100.0%",
                'unit_price': float(row.unit_price) if row.unit_price else 0,
                'total_price': float(row.total_price) if row.total_price else 0,
                'product_mn': row.product_mn,
                'owner_name': row.owner_name,
                'owner_real_name': row.owner_real_name,
                'company_name': row.company_name,
                'project_id': row.project_id,
                'project_name': row.project_name,
                'current_stage': row.current_stage,
                'quotation_id': row.quotation_id,
                'quotation_number': row.quotation_number,
                'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M') if row.updated_at else '',
                'created_at': row.created_at.strftime('%Y-%m-%d %H:%M') if row.created_at else ''
            }
            data.append(item)
        
        # 性能优化：为统计数据使用单独的聚合查询
        stats_query = query.with_entities(
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.count(QuotationDetail.id).label('record_count')
        )
        stats_result = stats_query.first()
        
        total_amount = float(stats_result.total_amount) if stats_result.total_amount else 0
        total_quantity = int(stats_result.total_quantity) if stats_result.total_quantity else 0
        
        # 计算平均单价
        avg_unit_price = (total_amount / total_quantity) if total_quantity > 0 else 0
        
        # 计算本月新增数量 - 使用单独的查询
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_query = query.filter(QuotationDetail.created_at >= current_month)
        monthly_result = monthly_query.with_entities(func.sum(QuotationDetail.quantity)).scalar()
        monthly_increase = int(monthly_result) if monthly_result else 0
        
        # 计算分页信息
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'success': True,
            'data': data,
            'statistics': {
                'total_amount': total_amount,
                'total_count': total_quantity,
                'monthly_increase': monthly_increase,
                'avg_unit_price': avg_unit_price
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"获取产品分析数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_analysis.route('/api/stage_statistics')
@login_required
def get_stage_statistics():
    """获取阶段统计数据API"""
    try:
        # 获取筛选参数
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')
        
        # 基础查询
        query = db.session.query(
            Project.current_stage,
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.count(QuotationDetail.id).label('record_count')
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用基于权限系统的数据过滤
        query = apply_permission_based_filters(query, current_user)
        
        # 应用筛选条件
        if category:
            # 使用子查询获取指定类别的产品，避免因Product表重复记录导致的重复统计
            category_products = db.session.query(
                Product.product_name, 
                Product.model
            ).filter(
                Product.category == category
            ).distinct().subquery()
            
            query = query.filter(
                and_(
                    QuotationDetail.product_name == category_products.c.product_name,
                    QuotationDetail.product_model == category_products.c.model
                )
            )
        
        if product_name:
            query = query.filter(QuotationDetail.product_name == product_name)
        
        if product_model:
            query = query.filter(QuotationDetail.product_model == product_model)
        
        # 按阶段分组
        results = query.group_by(Project.current_stage).all()
        
        # 构建查询结果的字典
        stage_dict = {}
        for result in results:
            stage = result.current_stage or 'unset'
            stage_dict[stage] = {
                'stage': stage,
                'name': get_stage_label(stage),
                'quantity': int(result.total_quantity) if result.total_quantity else 0,
                'amount': float(result.total_amount) if result.total_amount else 0,
                'count': int(result.record_count) if result.record_count else 0,
                'color_count': STAGE_COLORS_COUNT.get(stage, STAGE_COLORS_COUNT['unset']),
                'color_amount': STAGE_COLORS_AMOUNT.get(stage, STAGE_COLORS_AMOUNT['unset'])
            }
        
        # 按照STAGE_ORDER顺序排序，只包含有数据的阶段
        stage_data = []
        for stage in STAGE_ORDER:
            if stage in stage_dict:
                stage_item = stage_dict[stage]
                stage_item['order'] = STAGE_ORDER.index(stage)  # 添加排序字段
                stage_data.append(stage_item)
        
        return jsonify({
            'success': True,
            'data': stage_data,
            'colors': {
                'count': STAGE_COLORS_COUNT,
                'amount': STAGE_COLORS_AMOUNT
            },
            'stage_order': STAGE_ORDER  # 返回阶段顺序供前端使用
        })
        
    except Exception as e:
        logger.error(f"获取阶段统计数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取阶段统计数据失败: {str(e)}'
        }), 500


@product_analysis.route('/api/products/filter')
@login_required
@permission_required('quotation', 'view')
def products_list_ajax():
    """植入产品分析AJAX筛选端点"""
    try:
        # 获取筛选参数
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        product_name = request.args.get('product_name', '').strip()
        product_model = request.args.get('product_model', '').strip()
        
        # 获取分页参数
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))
        page = (offset // limit) + 1
        
        # 构建基础查询 - 避免因Product表重复记录导致的重复统计
        query = db.session.query(
            QuotationDetail.id,
            QuotationDetail.product_name,
            QuotationDetail.product_model,
            QuotationDetail.product_desc,
            QuotationDetail.quantity,
            QuotationDetail.discount,
            QuotationDetail.unit_price,
            QuotationDetail.total_price,
            QuotationDetail.product_mn,
            User.username.label('owner_name'),
            User.real_name.label('owner_real_name'),
            User.company_name.label('company_name'),
            Project.id.label('project_id'),
            Project.project_name,
            Project.current_stage,
            Quotation.id.label('quotation_id'),
            Quotation.quotation_number,
            QuotationDetail.updated_at,
            QuotationDetail.created_at
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用基于权限系统的数据过滤
        query = apply_permission_based_filters(query, current_user)
        
        # 应用搜索过滤
        if search:
            search_filter = or_(
                QuotationDetail.product_name.ilike(f'%{search}%'),
                QuotationDetail.product_model.ilike(f'%{search}%'),
                QuotationDetail.product_desc.ilike(f'%{search}%'),
                QuotationDetail.product_mn.ilike(f'%{search}%'),
                Project.project_name.ilike(f'%{search}%'),
                Quotation.quotation_number.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.real_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # 应用筛选条件
        if category:
            # 使用子查询获取指定类别的产品，避免因Product表重复记录导致的重复统计
            category_products = db.session.query(
                Product.product_name, 
                Product.model
            ).filter(
                Product.category == category
            ).distinct().subquery()
            
            query = query.filter(
                and_(
                    QuotationDetail.product_name == category_products.c.product_name,
                    QuotationDetail.product_model == category_products.c.model
                )
            )
        
        if product_name:
            query = query.filter(QuotationDetail.product_name == product_name)
        
        if product_model:
            query = query.filter(QuotationDetail.product_model == product_model)
        
        # 获取总数（用于分页）
        total_count = query.count()
        
        # 执行分页查询 - 默认按更新时间降序排序
        try:
            results = query.order_by(QuotationDetail.updated_at.desc()).offset(offset).limit(limit).all()
            logger.info(f"植入产品分析查询成功: 总计 {total_count} 条，offset={offset}, limit={limit}, 返回 {len(results)} 条")
        except Exception as e:
            logger.warning(f"使用updated_at排序失败: {str(e)}, 尝试使用id排序")
            try:
                # 回滚失败的事务
                db.session.rollback()
                results = query.order_by(QuotationDetail.id.desc()).offset(offset).limit(limit).all()
                logger.info(f"植入产品分析查询(id排序)成功: 总计 {total_count} 条，offset={offset}, limit={limit}, 返回 {len(results)} 条")
            except Exception as e2:
                logger.error(f"产品分析查询失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                results = []
        
        # 格式化数据为表格行HTML
        html_rows = []
        if not results:
            # 如果没有结果，返回提示信息
            html_rows.append('<tr><td colspan="14" class="text-center py-4">暂无符合条件的数据</td></tr>')
        else:
            for row in results:
                # 获取阶段标签
                stage_label = get_stage_label(row.current_stage or 'unset')
                
                # 生成表格行HTML
                html_row = f"""
                <tr>
                    <td class="col-name" title="{row.product_name or '-'}">{row.product_name or '-'}</td>
                    <td class="col-model" title="{row.product_model or '-'}">{row.product_model or '-'}</td>
                    <td class="col-desc" title="{row.product_desc or '-'}">{row.product_desc or '-'}</td>
                    <td class="col-quantity text-center" title="{row.quantity or 0}">{row.quantity or 0}</td>
                    <td class="col-discount text-center" title="{f'{(row.discount * 100):.1f}%' if row.discount else '100.0%'}">{f"{(row.discount * 100):.1f}%" if row.discount else "100.0%"}</td>
                    <td class="col-price text-end" title="¥{(row.unit_price or 0):.2f}">¥{(row.unit_price or 0):,.2f}</td>
                    <td class="col-total text-end" title="¥{(row.total_price or 0):.2f}">¥{(row.total_price or 0):,.2f}</td>
                    <td class="col-mn" title="{row.product_mn or '-'}">{row.product_mn or '-'}</td>
                    <td class="col-owner">
                        <span class="badge bg-secondary">{row.owner_real_name or row.owner_name or '未知'}</span>
                    </td>
                    <td class="col-project">
                        <a href="/project/view/{row.project_id}" class="project-link" title="{row.project_name or '-'}">
                            {row.project_name or '-'}
                        </a>
                    </td>
                    <td class="col-stage text-center">
                        <span class="badge rounded-pill" style="background-color: #6c757d; color: #fff;">{stage_label}</span>
                    </td>
                    <td class="col-quotation">
                        <a href="/quotation/view/{row.quotation_id}" class="badge rounded-pill" style="background-color: #e6e6e6; color: #0056b3; text-decoration: none;" title="{row.quotation_number or '-'}">
                            {row.quotation_number or '-'}
                        </a>
                    </td>
                    <td class="col-date" title="{row.updated_at.strftime('%Y-%m-%d %H:%M') if row.updated_at else '-'}">{row.updated_at.strftime('%Y-%m-%d %H:%M') if row.updated_at else '-'}</td>
                    <td class="col-date" title="{row.created_at.strftime('%Y-%m-%d %H:%M') if row.created_at else '-'}">{row.created_at.strftime('%Y-%m-%d %H:%M') if row.created_at else '-'}</td>
                </tr>
                """
                html_rows.append(html_row)
        
        # 计算统计信息
        stats_query = query.with_entities(
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.count(QuotationDetail.id).label('record_count')
        )
        stats_result = stats_query.first()
        
        total_amount = float(stats_result.total_amount) if stats_result.total_amount else 0
        total_quantity = int(stats_result.total_quantity) if stats_result.total_quantity else 0
        
        # 计算平均单价
        avg_unit_price = (total_amount / total_quantity) if total_quantity > 0 else 0
        
        # 计算本月新增数量
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_query = query.filter(QuotationDetail.created_at >= current_month)
        monthly_result = monthly_query.with_entities(func.sum(QuotationDetail.quantity)).scalar()
        monthly_increase = int(monthly_result) if monthly_result else 0
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': total_count,
            'loaded_count': len(results),  # 修正字段名以匹配前端期望
            'displayed_count': len(results),  # 保持兼容性
            'statistics': {
                'total_amount': total_amount,
                'total_quantity': total_quantity,
                'monthly_increase': monthly_increase,
                'avg_unit_price': avg_unit_price
            }
        })
        
    except Exception as e:
        logger.error(f"植入产品分析AJAX筛选失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_analysis.route('/api/export_analysis')
@login_required
@permission_required('quotation', 'view')
def export_analysis():
    """导出产品分析数据"""
    try:
        # 获取分析数据
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')
        
        # 这里可以实现导出功能，例如导出为Excel
        # 暂时返回成功消息
        return jsonify({
            'success': True,
            'message': '导出功能正在开发中'
        })
        
    except Exception as e:
        logger.error(f"导出产品分析数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 