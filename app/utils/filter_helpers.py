#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选状态保持辅助函数

提供统一的筛选条件保持机制，用于列表页、详情页、编辑页之间的导航。
"""

from flask import request, url_for
from urllib.parse import urlparse


def build_return_url(endpoint, **extra_params):
    """
    构建包含当前筛选条件的返回URL

    自动从当前请求中提取所有查询参数（筛选条件），
    并与额外参数合并，生成完整的返回URL。

    Args:
        endpoint: Flask路由端点名称，如 'customer.list_companies'
        **extra_params: 额外的URL参数，会覆盖同名的当前参数

    Returns:
        str: 完整的返回URL字符串，包含所有筛选条件

    使用示例:
        # 在列表页构建详情页链接时保留筛选条件
        return_url = build_return_url('customer.list_companies')
        detail_url = url_for('customer.view_company',
                            company_id=123,
                            return_url=return_url)

        # 在分页时保留筛选条件
        params = preserve_filters(page=2)
        next_page_url = url_for('customer.list_companies', **params)
    """
    params = request.args.to_dict()
    params.update(extra_params)
    return url_for(endpoint, **params)


def get_validated_return_url(default_endpoint, **default_params):
    """
    安全地获取和验证 return_url 参数

    从GET或POST请求中获取 return_url 参数，并进行安全验证：
    1. 防止开放重定向攻击（拒绝外部URL）
    2. 仅允许相对路径
    3. 如果验证失败或不存在，返回默认端点URL

    Args:
        default_endpoint: 默认返回的路由端点，如 'customer.list_companies'
        **default_params: 默认端点的URL参数

    Returns:
        str: 验证后的返回URL（相对路径）

    使用示例:
        # 在详情页视图中获取安全的返回URL
        @app.route('/customer/<int:company_id>')
        def view_company(company_id):
            return_url = get_validated_return_url('customer.list_companies')
            return render_template('customer/view.html',
                                  company=company,
                                  return_url=return_url)

        # 在编辑页保存后返回
        @app.route('/customer/<int:company_id>/edit', methods=['POST'])
        def edit_company(company_id):
            # 保存逻辑...
            return_url = get_validated_return_url('customer.view_company',
                                                  company_id=company_id)
            return redirect(return_url)
    """
    # 从GET或POST请求中获取 return_url
    return_url = request.args.get('return_url') if request.method == 'GET' \
                 else request.form.get('return_url')

    if return_url:
        parsed = urlparse(return_url)
        # 安全检查：防止开放重定向漏洞
        # 只允许相对路径，拒绝包含主机名的绝对URL
        if parsed.netloc and parsed.netloc != request.host:
            return_url = None

    # 如果验证失败或不存在，返回默认URL
    if not return_url:
        return_url = url_for(default_endpoint, **default_params)

    return return_url


def preserve_filters(**filter_params):
    """
    保留当前请求的筛选参数并合并新参数

    从当前请求的查询参数中提取所有筛选条件，
    并与新参数合并（新参数会覆盖同名参数）。

    Args:
        **filter_params: 新的筛选参数（会覆盖同名的当前参数）

    Returns:
        dict: 合并后的参数字典

    使用示例:
        # 保留当前筛选条件，只修改页码
        params = preserve_filters(page=2)
        next_page_url = url_for('customer.list_companies', **params)

        # 保留其他筛选条件，修改排序
        params = preserve_filters(sort='created_at', order='desc')
        sorted_url = url_for('customer.list_companies', **params)

        # 在模板中使用
        {% set params = preserve_filters(status='active') %}
        <a href="{{ url_for('customer.list_companies', **params) }}">
            仅显示活跃客户
        </a>
    """
    params = request.args.to_dict()
    params.update(filter_params)
    return params


def get_list_return_url(list_endpoint, detail_endpoint, item_id_key, item_id_value):
    """
    智能获取列表返回URL

    用于详情页或编辑页，智能判断应该返回的列表页URL：
    - 如果有 return_url 参数，验证后返回（保持筛选条件）
    - 如果没有，返回默认的列表页URL

    Args:
        list_endpoint: 列表页路由端点
        detail_endpoint: 详情页路由端点
        item_id_key: 项目ID参数名，如 'company_id'
        item_id_value: 项目ID值

    Returns:
        tuple: (list_url, detail_url)
            - list_url: 列表页URL（可能包含筛选条件）
            - detail_url: 详情页URL（包含 return_url 参数）

    使用示例:
        # 在编辑页保存后，返回详情页并保留列表筛选
        list_url, detail_url = get_list_return_url(
            'customer.list_companies',
            'customer.view_company',
            'company_id',
            company.id
        )

        # 返回详情页，详情页可以返回带筛选的列表
        return redirect(url_for('customer.view_company',
                               company_id=company.id,
                               return_url=list_url))
    """
    # 获取验证后的列表返回URL
    list_url = get_validated_return_url(list_endpoint)

    # 构建详情页URL（包含列表返回URL）
    detail_url = url_for(detail_endpoint,
                        **{item_id_key: item_id_value, 'return_url': list_url})

    return list_url, detail_url
