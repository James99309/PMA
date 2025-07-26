#!/usr/bin/env python3
"""
重建干净的AJAX函数
"""

def create_clean_ajax_function():
    """创建一个干净的AJAX函数"""
    
    ajax_function = '''
@quotation.route('/api/quotations/filter', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def quotations_list_ajax():
    """报价单列表AJAX筛选API"""
    try:
        # 基础测试 - 确保AJAX端点能正常响应
        current_app.logger.info("AJAX端点被调用")
        
        # 获取参数
        search = request.args.get('search', '').strip()
        owner_filter = request.args.get('owner_filter', '')
        
        # 基础查询
        query = get_viewable_data(Quotation, current_user)
        
        # 简单测试：只返回前5个报价单
        quotations = query.limit(5).all()
        
        # 生成简单HTML
        html_rows = []
        for q in quotations:
            html_rows.append(f'''
            <tr>
                <td>{q.quotation_number or ""}</td>
                <td>{q.owner.real_name if q.owner else ""}</td>
                <td>{q.project.project_name if q.project else ""}</td>
                <td class="text-end">¥{q.amount or 0:,.2f}</td>
                <td>{q.project.current_stage if q.project else ""}</td>
                <td>{q.project.project_type if q.project else ""}</td>
                <td>{q.updated_at.strftime("%Y-%m-%d") if q.updated_at else ""}</td>
                <td>{q.created_at.strftime("%Y-%m-%d") if q.created_at else ""}</td>
            </tr>
            ''')
        
        html = '\\n'.join(html_rows)
        
        return jsonify({
            'success': True,
            'html': html,
            'total_count': len(quotations),
            'loaded_count': len(quotations),
            'has_more': False,
            'statistics': {
                'total': len(quotations),
                'total_amount': 0,
                'approved': 0,
                'approved_amount': 0,
                'pending': 0,
                'pending_amount': 0,
                'draft': 0,
                'draft_amount': 0
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"AJAX端点错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'错误: {str(e)}',
            'html': '<tr><td colspan="8" class="text-center text-muted">加载失败</td></tr>',
            'total_count': 0,
            'loaded_count': 0,
            'has_more': False,
            'statistics': {
                'total': 0,
                'total_amount': 0,
                'approved': 0,
                'approved_amount': 0,
                'pending': 0,
                'pending_amount': 0,
                'draft': 0,
                'draft_amount': 0
            }
        }), 500
'''
    
    return ajax_function.strip()

def main():
    """主函数"""
    print("🔧 创建干净的AJAX函数...")
    
    ajax_code = create_clean_ajax_function()
    
    with open("clean_ajax_function.txt", "w", encoding="utf-8") as f:
        f.write(ajax_code)
    
    print("✅ 干净的AJAX函数已保存到 clean_ajax_function.txt")
    print("📋 接下来需要:")
    print("   1. 找到quotation.py中的AJAX函数位置")
    print("   2. 删除当前有问题的AJAX函数")
    print("   3. 替换为这个干净的函数")

if __name__ == "__main__":
    main()