#!/usr/bin/env python3
import re

file_path = 'app/utils/access_control.py'"
with open(file_path, 'r') as f:
    content = f.read()

# 查找特定位置
pattern = r'(# 管理员有全部编辑权限.*?return True.*?)'"
replacement = r"'\1
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ""

    # 渠道经理特殊处理：对于报价单，只能编辑自己创建的
    if user_role == "channel_manager" and hasattr(model_obj, "__tablename__") and model_obj.__tablename__ == "quotations":
        return model_obj.owner_id == user.id
'"

# 替换内容
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 写回文件
with open(file_path, 'w') as f:
    f.write(new_content)

print("修复完成：已在can_edit_data函数中添加渠道经理特殊处理逻辑")
