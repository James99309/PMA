from app import create_app
from app.helpers.approval_helpers import get_available_templates, get_template_steps

app = create_app()
with app.app_context():
    # 获取项目审批模板
    templates = get_available_templates('project')
    if not templates:
        print("没有找到项目审批模板!")
        exit(1)
    
    # 检查第一个模板的步骤
    template = templates[0]
    print(f"模板: {template.name} (ID: {template.id})")
    
    steps = get_template_steps(template.id)
    if not steps:
        print("该模板没有配置审批步骤!")
        exit(1)
    
    print(f"审批步骤数量: {len(steps)}")
    for step in steps:
        print(f"  步骤 {step.step_order}: {step.step_name} - 审批人: {step.approver.username if step.approver else '未指定'}") 