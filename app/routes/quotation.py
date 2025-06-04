from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.quotation import Quotation
from app.extensions import db

@quotation_bp.route('/<int:quotation_id>/confirmation-badge', methods=['POST'])
@login_required
def set_confirmation_badge(quotation_id):
    """设置报价单确认徽章"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        color = data.get('color')
        if not color:
            return jsonify({'success': False, 'message': '请选择徽章颜色'}), 400
        
        # 获取报价单
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 检查用户权限 - 只有解决方案经理可以设置确认徽章
        from app.permissions import has_permission
        if not (current_user.role == 'admin' or current_user.role == 'solution_manager' or has_permission('quotation', 'edit')):
            return jsonify({'success': False, 'message': '无权限执行此操作'}), 403
        
        # 设置确认徽章
        quotation.set_confirmation_badge(color, current_user.id)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '确认徽章设置成功',
            'badge_html': quotation.confirmation_badge_html
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"设置确认徽章失败: {str(e)}")
        return jsonify({'success': False, 'message': f'设置徽章失败: {str(e)}'}), 500

@quotation_bp.route('/<int:quotation_id>/confirmation-badge', methods=['DELETE'])
@login_required
def clear_confirmation_badge(quotation_id):
    """清除报价单确认徽章"""
    try:
        # 获取报价单
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 检查用户权限 - 只有解决方案经理可以清除确认徽章
        from app.permissions import has_permission
        if not (current_user.role == 'admin' or current_user.role == 'solution_manager' or has_permission('quotation', 'edit')):
            return jsonify({'success': False, 'message': '无权限执行此操作'}), 403
        
        # 清除确认徽章
        quotation.clear_confirmation_badge()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '确认徽章已清除'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清除确认徽章失败: {str(e)}")
        return jsonify({'success': False, 'message': f'清除徽章失败: {str(e)}'}), 500 