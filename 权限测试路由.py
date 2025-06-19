# 临时权限测试路由
# 将这段代码添加到 app/__init__.py 的最后

@app.route('/test-tonglei-permission')
def test_tonglei_permission():
    """临时测试童蕾用户权限的路由"""
    from flask import render_template_string
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>童蕾权限测试页面</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
            .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-warning { background-color: #ffc107; color: #212529; }
        </style>
    </head>
    <body>
        <h1>童蕾权限测试页面</h1>
        
        <h2>用户信息</h2>
        <p>当前用户: {{ current_user.username if current_user.is_authenticated else '未登录' }}</p>
        <p>用户角色: {{ current_user.role if current_user.is_authenticated else '无' }}</p>
        <p>用户ID: {{ current_user.id if current_user.is_authenticated else '无' }}</p>
        
        <h2>权限检查结果</h2>
        <p>is_admin_or_ceo 模板变量: {{ is_admin_or_ceo }}</p>
        <p>is_admin_or_ceo 类型: {{ is_admin_or_ceo.__class__.__name__ }}</p>
        
        <h2>条件测试</h2>
        <p>{% if is_admin_or_ceo %}is_admin_or_ceo 为 True{% else %}is_admin_or_ceo 为 False{% endif %}</p>
        
        <h2>模拟批价单状态测试</h2>
        {% set mock_status = 'approved' %}
        <p>模拟状态: {{ mock_status }}</p>
        <p>完整条件测试: {% if is_admin_or_ceo and mock_status == 'approved' %}应该显示退回按钮{% else %}不应该显示退回按钮{% endif %}</p>
        
        <h2>按钮测试</h2>
        {% if is_admin_or_ceo and mock_status == 'approved' %}
        <div class="alert alert-danger">
            ❌ 错误：退回审批按钮会显示！
            <button type="button" class="btn btn-warning">退回审批</button>
        </div>
        {% else %}
        <div class="alert alert-success">
            ✅ 正确：退回审批按钮不会显示
        </div>
        {% endif %}
        
        <h2>调试信息</h2>
        <p>测试时间: {{ now() }}</p>
        <p>请求路径: {{ request.path }}</p>
        
        <script>
            console.log('=== 前端权限测试 ===');
            console.log('页面标题:', document.title);
            console.log('当前时间:', new Date().toLocaleString());
            
            // 检查是否有退回按钮
            const rollbackButton = document.querySelector('button');
            console.log('页面中是否有按钮:', !!rollbackButton);
            if (rollbackButton) {
                console.log('按钮文本:', rollbackButton.textContent);
                console.log('❌ 发现问题：权限检查失效！');
            } else {
                console.log('✅ 权限检查正常：无退回按钮');
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(template) 