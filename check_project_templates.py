from app import create_app
from app.helpers.approval_helpers import get_available_templates

app = create_app()
with app.app_context():
    templates = get_available_templates('project')
    print(f"项目审批模板数量: {len(templates)}")
    for t in templates:
        print(f"模板ID: {t.id}, 名称: {t.name}, 活跃状态: {t.is_active}") 