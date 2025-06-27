from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.decorators import permission_required
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
        
        # 性能优化：直接在查询中应用权限过滤，避免子查询
        if current_user.role != 'admin':
            # 构建权限过滤条件
            permission_filters = []
            
            # 4. 角色特殊权限检查
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 财务总监、产品经理、解决方案经理可以查看所有
            if user_role in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution']:
                # 不添加任何过滤条件，可以查看所有数据
                pass
            else:
                # 对于其他角色，添加基础权限过滤条件
                
                # 1. 自己创建的报价单
                permission_filters.append(Quotation.owner_id == current_user.id)
                
                # 2. 归属关系 - 使用子查询优化
                affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
                    Affiliation.viewer_id == current_user.id
                ).subquery()
                permission_filters.append(Quotation.owner_id.in_(affiliation_subquery))
                
                # 3. 销售负责人相关项目 - 直接在主查询中处理
                permission_filters.append(Project.vendor_sales_manager_id == current_user.id)
                
                # 4. 其他角色特殊权限
                if user_role == 'channel_manager':
                    # 渠道经理：额外可以查看渠道跟进项目
                    permission_filters.append(Project.project_type == 'channel_follow')
                elif user_role == 'sales_director':
                    # 营销总监：额外可以查看销售重点和渠道跟进项目
                    permission_filters.append(Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
                elif user_role in ['service', 'service_manager']:
                    # 服务经理：额外可以查看业务机会项目
                    permission_filters.append(Project.project_type == '业务机会')
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
                            Project.owner_id.in_(viewable_user_ids),
                            Project.vendor_sales_manager_id.in_(viewable_user_ids)
                        )
                    )
                
                # 应用权限过滤条件
                if permission_filters:
                    query = query.filter(db.or_(*permission_filters))
        
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
        
        # 应用权限过滤
        if current_user.role != 'admin':
            # 构建权限过滤条件
            permission_filters = []
            
            # 4. 角色特殊权限检查
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 财务总监、产品经理、解决方案经理可以查看所有
            if user_role in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution']:
                # 不添加任何过滤条件，可以查看所有数据
                pass
            else:
                # 对于其他角色，添加基础权限过滤条件
                
                # 1. 自己创建的报价单
                permission_filters.append(Quotation.owner_id == current_user.id)
                
                # 2. 归属关系 - 使用子查询优化
                affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
                    Affiliation.viewer_id == current_user.id
                ).subquery()
                permission_filters.append(Quotation.owner_id.in_(affiliation_subquery))
                
                # 3. 销售负责人相关项目 - 直接在主查询中处理
                permission_filters.append(Project.vendor_sales_manager_id == current_user.id)
                
                # 4. 其他角色特殊权限
                if user_role == 'channel_manager':
                    # 渠道经理：额外可以查看渠道跟进项目
                    permission_filters.append(Project.project_type == 'channel_follow')
                elif user_role == 'sales_director':
                    # 营销总监：额外可以查看销售重点和渠道跟进项目
                    permission_filters.append(Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
                elif user_role in ['service', 'service_manager']:
                    # 服务经理：额外可以查看业务机会项目
                    permission_filters.append(Project.project_type == '业务机会')
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
                            Project.owner_id.in_(viewable_user_ids),
                            Project.vendor_sales_manager_id.in_(viewable_user_ids)
                        )
                    )
                
                # 应用权限过滤条件
                if permission_filters:
                    query = query.filter(or_(*permission_filters))
                else:
                    # 如果没有任何权限，返回空结果
                    return jsonify({
                        'success': True,
                        'data': []
                    })
        
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

def get_monthly_increase(category=None, product_name=None, product_model=None):
    """获取本月新增产品数量"""
    try:
        # 获取当前月份的开始时间
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 构建基础查询 - 避免因Product表重复记录导致的重复统计
        query = db.session.query(func.sum(QuotationDetail.quantity)).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            Project, Quotation.project_id == Project.id
        ).filter(
            QuotationDetail.created_at >= current_month  # 修改：筛选本月新增的产品明细
        )
        
        # 应用权限过滤
        if current_user.role != 'admin':
            # 构建权限过滤条件
            permission_filters = []
            
            # 4. 角色特殊权限检查
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 财务总监、产品经理、解决方案经理可以查看所有
            if user_role in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution']:
                # 不添加任何过滤条件，可以查看所有数据
                pass
            else:
                # 对于其他角色，添加基础权限过滤条件
                
                # 1. 自己创建的报价单
                permission_filters.append(Quotation.owner_id == current_user.id)
                
                # 2. 归属关系 - 使用子查询优化
                affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
                    Affiliation.viewer_id == current_user.id
                ).subquery()
                permission_filters.append(Quotation.owner_id.in_(affiliation_subquery))
                
                # 3. 销售负责人相关项目 - 直接在主查询中处理
                permission_filters.append(Project.vendor_sales_manager_id == current_user.id)
                
                # 4. 其他角色特殊权限
                if user_role == 'channel_manager':
                    # 渠道经理：额外可以查看渠道跟进项目
                    permission_filters.append(Project.project_type == 'channel_follow')
                elif user_role == 'sales_director':
                    # 营销总监：额外可以查看销售重点和渠道跟进项目
                    permission_filters.append(Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
                elif user_role in ['service', 'service_manager']:
                    # 服务经理：额外可以查看业务机会项目
                    permission_filters.append(Project.project_type == '业务机会')
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
                            Project.owner_id.in_(viewable_user_ids),
                            Project.vendor_sales_manager_id.in_(viewable_user_ids)
                        )
                    )
                
                # 应用权限过滤条件
                if permission_filters:
                    query = query.filter(or_(*permission_filters))
                else:
                    # 如果没有任何权限，返回0
                    return 0
        
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
        
        result = query.scalar()
        return int(result) if result else 0
        
    except Exception as e:
        logger.error(f"获取本月新增数量时出错: {str(e)}")
        return 0

@product_analysis.route('/api/monthly_increase_data')
@login_required
@permission_required('quotation', 'view')
def get_monthly_increase_data():
    """获取本月新增产品明细数据"""
    try:
        # 获取筛选参数
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # 获取当前月份的开始时间
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 构建基础查询 - 只查询本月新增的数据
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
        ).filter(
            QuotationDetail.created_at >= current_month  # 只查询本月新增的产品明细
        )
        
        # 应用权限过滤
        if current_user.role != 'admin':
            # 构建权限过滤条件
            permission_filters = []
            
            # 1. 自己创建的报价单
            permission_filters.append(Quotation.owner_id == current_user.id)
            
            # 2. 归属关系 - 使用子查询优化
            affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
                Affiliation.viewer_id == current_user.id
            ).subquery()
            permission_filters.append(Quotation.owner_id.in_(affiliation_subquery))
            
            # 3. 销售负责人相关项目 - 直接在主查询中处理
            permission_filters.append(Project.vendor_sales_manager_id == current_user.id)
            
            # 4. 角色特殊权限
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 财务总监、产品经理、解决方案经理可以查看所有
            if user_role in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution']:
                # 不添加额外过滤条件，可以查看所有
                pass
            elif user_role == 'channel_manager':
                # 渠道经理：额外可以查看渠道跟进项目
                permission_filters.append(Project.project_type == 'channel_follow')
            elif user_role == 'sales_director':
                # 营销总监：额外可以查看销售重点和渠道跟进项目
                permission_filters.append(Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
            elif user_role in ['service', 'service_manager']:
                # 服务经理：额外可以查看业务机会项目
                permission_filters.append(Project.project_type == '业务机会')
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
                        Project.owner_id.in_(viewable_user_ids),
                        Project.vendor_sales_manager_id.in_(viewable_user_ids)
                    )
                )
            
            # 应用权限过滤（如果不是特殊角色）
            if user_role not in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution', 'business_admin']:
                query = query.filter(db.or_(*permission_filters))
        
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
        
        # 计算分页信息
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        # 执行分页查询 - 按创建时间降序排序
        results = query.order_by(QuotationDetail.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
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
                'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                'created_at': row.created_at.isoformat() if row.created_at else None
            }
            data.append(item)
        
        # 计算统计信息
        total_amount = sum(item['total_price'] for item in data)
        total_quantity = sum(item['quantity'] for item in data)
        avg_unit_price = total_amount / total_quantity if total_quantity > 0 else 0
        
        return jsonify({
            'success': True,
            'data': data,
            'statistics': {
                'total_amount': total_amount,
                'total_count': total_quantity,
                'monthly_increase': total_quantity,  # 本月新增就是当前查询的总数量
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
        logger.error(f"获取本月新增产品明细数据失败: {str(e)}")
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