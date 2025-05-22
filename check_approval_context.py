from app import create_app

app = create_app()
with app.app_context():
    # 获取所有已注册的上下文处理器
    context_processors = app.template_context_processors[None]
    
    # 遍历所有处理器，检查输出
    for processor in context_processors:
        context = processor()
        if context and 'get_available_templates' in context:
            print("找到get_available_templates函数!")
            print(f"在处理器 {processor.__name__ if hasattr(processor, '__name__') else '匿名函数'} 中")
            
            # 测试函数是否能够正常执行
            from app.helpers.approval_helpers import get_available_templates
            templates = get_available_templates('project')
            print(f"项目模板数量: {len(templates)}")
            for t in templates:
                print(f"  - {t.name} (ID: {t.id})")
            
            break
    else:
        print("未找到get_available_templates函数!") 