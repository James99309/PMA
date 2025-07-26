"""
临时产品API接口
支持手动输入产品功能的后端API
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, desc
from app import db
from app.models.temp_product import TempProduct
from app.decorators import permission_required
from datetime import datetime
import json

# 创建蓝图
temp_products_bp = Blueprint('temp_products', __name__, url_prefix='/api/v1/temp-products')

@temp_products_bp.route('', methods=['GET'])
@login_required
def get_temp_products():
    """
    获取临时产品列表
    支持按分类筛选和分页
    """
    try:
        # 获取查询参数
        category = request.args.get('category')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        include_popular = request.args.get('popular', 'true').lower() == 'true'
        
        # 构建基础查询
        query = TempProduct.query.filter_by(
            created_by=current_user.id,
            is_deleted=False
        )
        
        # 按分类筛选
        if category:
            query = query.filter_by(category=category)
        
        # 排序：使用次数多的在前，最近创建的在前
        if include_popular:
            query = query.order_by(desc(TempProduct.usage_count), desc(TempProduct.updated_at))
        else:
            query = query.order_by(desc(TempProduct.updated_at))
        
        # 获取总数
        total_count = query.count()
        
        # 分页
        items = query.offset(offset).limit(limit).all()
        
        # 转换为字典格式
        products = [item.to_dict() for item in items]
        
        return jsonify({
            'success': True,
            'data': products,
            'total_count': total_count,
            'loaded_count': len(products),
            'has_more': (offset + len(products)) < total_count
        })
        
    except Exception as e:
        current_app.logger.error(f"获取临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('', methods=['POST'])
@login_required
def save_temp_product():
    """
    保存临时产品
    支持新建和更新现有产品
    """
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['product_name', 'product_model', 'product_desc', 'brand', 'unit']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'缺少必需字段: {", ".join(missing_fields)}'
            }), 400
        
        # 检查是否已存在相同型号的临时产品
        existing = TempProduct.query.filter_by(
            product_model=data['product_model'].strip(),
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if existing:
            # 更新现有产品
            existing.product_name = data['product_name'].strip()
            existing.product_desc = data['product_desc'].strip()
            existing.brand = data['brand'].strip()
            existing.unit = data['unit'].strip()
            existing.category = data.get('category', '').strip()
            existing.category_path = data.get('category_path', '').strip()
            existing.increment_usage()
            
            product = existing
            action = 'updated'
            
        else:
            # 创建新产品
            product = TempProduct(
                product_name=data['product_name'].strip(),
                product_model=data['product_model'].strip(),
                product_desc=data['product_desc'].strip(),
                brand=data['brand'].strip(),
                unit=data['unit'].strip(),
                category=data.get('category', '').strip(),
                category_path=data.get('category_path', '').strip(),
                created_by=current_user.id,
                usage_count=1,
                last_used_at=datetime.utcnow()
            )
            
            # 如果前端已经提供了MN号，直接使用；否则生成新的MN号
            if data.get('product_mn'):
                product.product_mn = data['product_mn'].strip()
                current_app.logger.info(f"使用前端提供的MN号: {product.product_mn}")
            else:
                # 生成唯一的MN号
                product.generate_mn()
                current_app.logger.info(f"后端生成MN号: {product.product_mn}")
            
            db.session.add(product)
            action = 'created'
        
        # 提交到数据库
        db.session.commit()
        
        current_app.logger.info(f"临时产品{action}: {product.product_model} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'临时产品已{action}',
            'data': {
                'id': product.id,
                'product_model': product.product_model,
                'action': action,
                'product': product.to_dict()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/<int:product_id>', methods=['GET'])
@login_required
def get_temp_product(product_id):
    """
    获取单个临时产品详情
    """
    try:
        product = TempProduct.query.filter_by(
            id=product_id,
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': '临时产品不存在或无权访问'
            }), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取临时产品详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取临时产品详情失败: {str(e)}'
        }), 500


@temp_products_bp.route('/<int:product_id>/increment', methods=['POST'])
@login_required
def increment_usage(product_id):
    """
    增加临时产品使用次数
    """
    try:
        product = TempProduct.query.filter_by(
            id=product_id,
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': '临时产品不存在或无权访问'
            }), 404
        
        product.increment_usage()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '使用次数已更新',
            'data': {
                'usage_count': product.usage_count,
                'last_used_at': product.last_used_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新使用次数失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新使用次数失败: {str(e)}'
        }), 500


@temp_products_bp.route('/<int:product_id>', methods=['PUT'])
@login_required
def update_temp_product(product_id):
    """
    更新临时产品信息
    """
    try:
        product = TempProduct.query.filter_by(
            id=product_id,
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': '临时产品不存在或无权访问'
            }), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'product_name' in data:
            product.product_name = data['product_name'].strip()
        if 'product_desc' in data:
            product.product_desc = data['product_desc'].strip()
        if 'brand' in data:
            product.brand = data['brand'].strip()
        if 'unit' in data:
            product.unit = data['unit'].strip()
        if 'category' in data:
            product.category = data['category'].strip()
        if 'category_path' in data:
            product.category_path = data['category_path'].strip()
        
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '临时产品已更新',
            'data': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
def delete_temp_product(product_id):
    """
    删除临时产品（软删除）
    """
    try:
        product = TempProduct.query.filter_by(
            id=product_id,
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if not product:
            return jsonify({
                'success': False,
                'message': '临时产品不存在或无权访问'
            }), 404
        
        product.soft_delete()
        db.session.commit()
        
        current_app.logger.info(f"临时产品已删除: {product.product_model} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': '临时产品已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/by-category/<category>', methods=['GET'])
@login_required
def get_temp_products_by_category(category):
    """
    根据分类获取临时产品
    支持按产品名称过滤
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        product_name = request.args.get('product_name', '').strip()
        
        # 构建基础查询
        query = TempProduct.query.filter_by(
            category=category,
            created_by=current_user.id,
            is_deleted=False
        )
        
        # 如果指定了产品名称，添加过滤条件
        if product_name:
            query = query.filter(TempProduct.product_name == product_name)
        
        # 按使用次数和更新时间排序
        products = query.order_by(
            TempProduct.usage_count.desc(), 
            TempProduct.updated_at.desc()
        ).all()
        
        # 限制返回数量
        if limit > 0:
            products = products[:limit]
        
        # 转换为字典格式
        result = [product.to_dict() for product in products]
        
        current_app.logger.info(f"按分类获取临时产品: category={category}, product_name={product_name}, count={len(result)}")
        
        return jsonify({
            'success': True,
            'data': result,
            'category': category,
            'product_name': product_name,
            'count': len(result)
        })
        
    except Exception as e:
        current_app.logger.error(f"按分类获取临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'按分类获取临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/popular', methods=['GET'])
@login_required
def get_popular_temp_products():
    """
    获取热门临时产品
    """
    try:
        category = request.args.get('category')
        limit = request.args.get('limit', 10, type=int)
        
        if category:
            products = TempProduct.get_popular_by_category(category, current_user.id, limit)
        else:
            products = TempProduct.get_by_user(current_user.id, limit)
            # 过滤出使用过的产品
            products = [p for p in products if p.usage_count > 0]
        
        # 转换为字典格式
        result = [product.to_dict() for product in products]
        
        return jsonify({
            'success': True,
            'data': result,
            'category': category,
            'count': len(result)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取热门临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取热门临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/search', methods=['GET'])
@login_required
def search_temp_products():
    """
    搜索临时产品
    """
    try:
        term = request.args.get('term', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索词不能为空'
            })
        
        # 构建搜索查询
        query = TempProduct.query.filter_by(
            created_by=current_user.id,
            is_deleted=False
        ).filter(
            or_(
                TempProduct.product_name.ilike(f'%{term}%'),
                TempProduct.product_model.ilike(f'%{term}%'),
                TempProduct.product_desc.ilike(f'%{term}%'),
                TempProduct.brand.ilike(f'%{term}%')
            )
        ).order_by(desc(TempProduct.usage_count), desc(TempProduct.updated_at))
        
        # 限制结果数量
        products = query.limit(limit).all()
        
        # 转换为字典格式
        result = [product.to_dict() for product in products]
        
        return jsonify({
            'success': True,
            'data': result,
            'search_term': term,
            'count': len(result)
        })
        
    except Exception as e:
        current_app.logger.error(f"搜索临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索临时产品失败: {str(e)}'
        }), 500


@temp_products_bp.route('/cleanup', methods=['POST'])
@login_required
@permission_required('admin', 'manage')
def cleanup_old_products():
    """
    清理旧的临时产品
    仅管理员可用
    """
    try:
        days = request.json.get('days', 90) if request.json else 90
        
        count = TempProduct.cleanup_old_records(days)
        
        current_app.logger.info(f"清理临时产品完成，删除 {count} 条记录")
        
        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {count} 条旧记录',
            'deleted_count': count
        })
        
    except Exception as e:
        current_app.logger.error(f"清理临时产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清理临时产品失败: {str(e)}'
        }), 500


# 错误处理
@temp_products_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@temp_products_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"临时产品API内部错误: {str(error)}")
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500