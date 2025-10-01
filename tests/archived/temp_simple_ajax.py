@expense.route('/expense/ajax')
@login_required
@permission_required('expense', 'view')
def expense_list_ajax():
    """报销列表AJAX端点"""
    try:
        logger.info(f"AJAX请求开始，参数: {dict(request.args)}")
        
        # 简单测试：直接返回测试数据
        return jsonify({
            'success': True,
            'html': '<tr><td colspan="9" class="text-center">测试数据加载成功</td></tr>',
            'total_count': 0,
            'loaded_count': 0,
            'statistics': {
                'total_count': 0,
                'total_amount': 0,
                'pending_count': 0,
                'pending_amount': 0,
                'approved_count': 0,
                'approved_amount': 0
            }
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