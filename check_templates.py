from app import create_app
import os
app = create_app()
with app.app_context():
    # 检查客户模块的模板文件
    template_path = os.path.join(app.root_path, 'templates', 'customer')
    print(f'客户模块模板路径: {template_path}')
    if os.path.exists(template_path):
        print('模板文件列表:')
        for template_file in os.listdir(template_path):
            print(f' - {template_file}')
    else:
        print('客户模块模板目录不存在!')
    # 检查base.html是否存在
    base_template = os.path.join(app.root_path, 'templates', 'base.html')
    if os.path.exists(base_template):
        print(f'base.html 存在，大小: {os.path.getsize(base_template)} 字节')
    else:
        print('base.html 不存在!')
