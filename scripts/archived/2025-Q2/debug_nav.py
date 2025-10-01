from app import create_app
import sys
app = create_app()
with app.app_context():
    try:
        # 获取模板上下文
        with app.test_request_context('/'):
            # 从应用中获取上下文处理器函数
            for processor in app.template_context_processors[None]:
                # 仅打印包含权限的处理器
                context = processor()
                if 'has_permission' in context:
                    print('找到has_permission函数')
                    fn = context['has_permission']
                    print(f'函数ID: {id(fn)}')
                    print(f'函数名: {fn.__name__ if hasattr(fn, "__name__") else "未命名"}')
    except Exception as e:
        print(f'错误: {str(e)}')
        import traceback
        traceback.print_exc()
