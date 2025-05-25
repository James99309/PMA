#!/usr/bin/env python3
with open('app/views/main.py', 'r') as file:
    content = file.read()

modified_content = content.replace(
    "recent_projects = get_viewable_data(Project, current_user).order_by(Project.updated_at.desc()).limit(5).all()",
    """try:
        # 恢复使用updated_at进行排序
        recent_projects = get_viewable_data(Project, current_user).order_by(Project.updated_at.desc()).limit(5).all()
    except Exception as e:
        logger.error(f\"使用updated_at排序查询项目失败: {str(e)}\")
        # 如果updated_at查询失败，改用id排序作为备选
        recent_projects = get_viewable_data(Project, current_user).order_by(Project.id.desc()).limit(5).all()"""
)

with open('app/views/main.py', 'w') as file:
    file.write(modified_content)

print("已经成功添加错误处理到main.py")
