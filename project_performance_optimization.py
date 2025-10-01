# =============================================================================
# 项目列表首次加载性能优化方案
# =============================================================================
# 解决首次加载3-5秒的问题

"""
关键性能瓶颈分析：
1. 首次加载使用 .all() 获取所有470个项目
2. 遍历所有项目计算总金额和汇率转换
3. 调用 _calculate_project_stage_stats 遍历所有项目
4. 重复的货币转换计算

优化策略：
1. 首次加载改为分页（只获取首批30个项目用于显示）
2. 使用数据库聚合查询计算统计数据
3. 缓存汇率转换结果
4. 异步加载统计数据
"""

def get_project_stats_optimized(query, current_user):
    """
    优化的项目统计数据获取
    使用数据库聚合查询而不是Python遍历
    """
    from sqlalchemy import func, case
    from app.models.project import Project
    from app.utils.i18n import get_current_language

    # 获取当前语言和货币
    current_lang = get_current_language()
    target_currency = 'USD' if current_lang == 'en' else 'CNY'

    # 1. 基础统计查询（数量）
    base_stats = query.with_entities(
        func.count(Project.id).label('total_count'),
        func.sum(case([(Project.is_active == True, 1)], else_=0)).label('active_count'),
        func.sum(case([(Project.is_active == False, 1)], else_=0)).label('inactive_count'),
        func.sum(func.coalesce(Project.quotation_customer, 0)).label('total_amount')
    ).first()

    # 2. 阶段统计查询
    stage_stats_raw = query.with_entities(
        Project.current_stage,
        func.count(Project.id).label('count'),
        func.sum(func.coalesce(Project.quotation_customer, 0)).label('amount')
    ).group_by(Project.current_stage).all()

    # 3. 处理阶段统计数据
    all_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']
    stage_stats = {}

    # 初始化所有阶段
    for stage in all_stages:
        stage_stats[stage] = {'count': 0, 'amount': 0}

    # 填充查询结果
    total_cny_amount = 0
    for stage, count, amount in stage_stats_raw:
        if stage in stage_stats:
            stage_stats[stage]['count'] = count or 0
            stage_stats[stage]['amount'] = amount or 0
            total_cny_amount += (amount or 0)

    # 4. 汇率转换（只转换一次总金额）
    if target_currency == 'USD' and total_cny_amount > 0:
        from app.services.exchange_rate_service import exchange_rate_service
        total_converted = exchange_rate_service.convert_amount(total_cny_amount, 'CNY', 'USD')

        # 按比例转换各阶段金额
        conversion_ratio = total_converted / total_cny_amount if total_cny_amount > 0 else 1
        for stage in stage_stats:
            if stage_stats[stage]['amount'] > 0:
                stage_stats[stage]['amount'] *= conversion_ratio

    return {
        'total_count': base_stats.total_count or 0,
        'active_count': base_stats.active_count or 0,
        'inactive_count': base_stats.inactive_count or 0,
        'total_value': total_converted if target_currency == 'USD' and total_cny_amount > 0 else (base_stats.total_amount or 0),
        'stage_stats': stage_stats
    }


def list_projects_optimized():
    """
    优化的项目列表函数
    """
    from flask import request, render_template, jsonify, url_for
    from flask_login import current_user
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.utils.access_control import get_viewable_data
    from sqlalchemy.orm import joinedload
    from app.utils.dictionary_helpers import get_default_currency, get_currency_symbol

    search = request.args.get('search', '')
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    keep_panel = request.args.get('keep_panel', 'false') == 'true'

    # 构建基础查询
    query = get_viewable_data(Project, current_user).options(joinedload(Project.owner))

    # 应用搜索条件
    if search:
        query = query.filter(Project.project_name.ilike(f'%{search}%'))

    # 处理筛选参数
    filters = {}
    for key, value in request.args.items():
        if key.startswith('filter_') and value:
            field = key[7:]
            filters[field] = value

    # 应用筛选逻辑（保持原有的复杂筛选逻辑）
    query = apply_project_filters(query, filters)

    # 排序
    try:
        if sort == 'project_name':
            if order == 'desc':
                sort_column = Project.rating.desc().nullslast()
            else:
                sort_column = Project.rating.asc().nullslast()
        else:
            sort_column = getattr(Project, sort, Project.id)
            if order == 'desc':
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
    except Exception:
        sort_column = Project.id.desc()

    # 关键优化1: 首次加载只获取前30个项目用于显示
    initial_page_size = 30
    projects = query.order_by(sort_column).limit(initial_page_size).all()

    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.args.get('format') == 'json':
        html = render_template('project/list_partial.html',
                             projects=projects,
                             search_term=search,
                             Quotation=Quotation,
                             filter_params={key: value for key, value in request.args.items() if key.startswith('filter_')})
        return jsonify({'success': True, 'html': html})

    # 关键优化2: 使用聚合查询获取统计数据
    stats_data = get_project_stats_optimized(query, current_user)

    # 获取货币符号
    default_currency = get_default_currency()
    currency_symbol = get_currency_symbol(default_currency)

    # 构建统计配置
    from app.utils.i18n import get_current_language
    current_lang = get_current_language()
    amount_unit = '万美元' if current_lang == 'en' else '万元'

    stats_config = {
        'cards': [
            {
                'title': '项目总数',
                'value': stats_data['total_count'],
                'icon': 'fa-project-diagram',
                'color': 'primary'
            },
            {
                'title': '活跃项目',
                'value': stats_data['active_count'],
                'icon': 'fa-chart-line',
                'color': 'success'
            },
            {
                'title': '总金额',
                'value': f'{currency_symbol}{stats_data["total_value"] / 10000:.2f}',
                'subtitle': amount_unit,
                'icon': 'fa-yen-sign',
                'color': 'warning'
            }
        ]
    }

    # 构建筛选配置
    filter_config = {
        'action_url': url_for('project.list_projects'),
        'form_id': 'projectFilterForm',
        'search_field': {
            'name': 'search',
            'label': '搜索项目',
            'placeholder': '搜索项目名称或授权编号',
            'value': search
        },
        'quick_filters': [
            {
                'name': 'filter_stage_not',
                'label': '有效项目',
                'value': 'lost,paused,signed',
                'description': '排除失败、搁置、已签约',
                'active': filters.get('stage_not') == 'lost,paused,signed'
            }
        ]
    }

    # 构建表格配置
    table_config = {
        'columns': [
            {'key': 'project_name', 'label': '项目名称', 'sortable': True},
            {'key': 'current_stage', 'label': '当前阶段'},
            {'key': 'quotation_customer', 'label': '报价金额'},
            {'key': 'owner', 'label': '负责人'},
            {'key': 'updated_at', 'label': '更新时间', 'sortable': True}
        ],
        'sort_field': sort,
        'sort_direction': order
    }

    # 构建列表配置
    list_config = {
        'module_name': 'project',
        'title': None,
        'ajax_mode': True,
        'ajax_endpoint': url_for('project.project_list_ajax'),
        'infinite_scroll': {
            'enabled': True,
            'page_size': 30,
            'scroll_threshold': 100,
            'container_selector': '.table-responsive'
        },
        'stats': stats_config,
        'filter': filter_config,
        'table': table_config,
    }

    filter_params = {key: value for key, value in request.args.items() if key.startswith('filter_')}

    return render_template(
        'project/list.html',
        projects=projects,
        search_term=search,
        Quotation=Quotation,
        filter_params=filter_params,
        keep_panel=keep_panel,
        list_config=list_config
    )


def apply_project_filters(query, filters):
    """
    应用项目筛选条件
    从原函数中提取出来，保持筛选逻辑不变
    """
    # 这里保持原有的复杂筛选逻辑
    # 包括 stage_not, updated_this_month, current_stage 等
    # （省略具体实现，保持与原函数一致）
    return query


# =============================================================================
# 实施建议
# =============================================================================

"""
1. 立即优化（高优先级）：
   - 将 list_projects() 中的 .all() 改为 .limit(30)
   - 统计数据改为异步加载或使用聚合查询

2. 中期优化：
   - 实现统计数据缓存（Redis）
   - 汇率转换结果缓存

3. 长期优化：
   - 考虑使用数据库视图预计算统计数据
   - 实现前端虚拟滚动
"""