#!/bin/bash

# 自动生成标准 .gitignore 文件，避免无关文件被上传
cat > .gitignore <<EOF
# 虚拟环境
venv/
.venv/

# Python缓存文件
__pycache__/
*.py[cod]
*$py.class

# 数据库文件
*.db
app.db
*.sqlite
*.sqlite3

# 环境配置文件
.env
.flaskenv

# 日志文件
*.log
logs/

# IDE配置
.idea/
.vscode/
*.sublime-*

# 操作系统文件
.DS_Store
Thumbs.db

# 个人开发临时文件
*.bak
*.swp
*.tmp

# 测试文件和缓存
.pytest_cache/
.coverage
htmlcov/

# Cursor IDE相关
.cursor/

# 未使用的文件目录
unused/

# 本地配置
instance/

# 媒体和上传文件
uploads/
media/

# 构建输出
dist/
build/
*.egg-info/

# Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd

# 编辑器/IDE
.vscode/
.idea/
*.swp

# 操作系统
.DS_Store
Thumbs.db

# 数据库和本地配置
*.sqlite
*.db
*.bak
.env

# 备份和临时
backups/
tmp/
*.tmp
*.log
*.csv
*.json
*.zip
*.tar
*.gz
*.7z
*.rar

# 静态上传文件
app/static/uploads/

# 测试和个人脚本
final_test.py
login_test.py
test_*.py
*_test.py
test_app_with_render.py
check_user.py
check_db_connection.py
check_render_data.py
verify_admin_login.py
reset_admin_password.py

# 迁移/导出中间产物
db_export*.json
complete_db_export.json
complete_fix.py
export_sqlite_data.py
migrate_to_render.sh
migrate_to_render_new.py
migrate_data_to_render.py

# 只保留主程序结构和必要文件
# 保留run.py、app/、static/、templates/、migrations/、config.py

# 允许覆盖规则
!requirements.txt
!run.py
!config.py
!wsgi.py
!build.sh
!update_build.sh
!render.yaml
!render_start.sh
!render_startup_hook.py
!render_migration.sh
!render_migration_run.py
!render_db_sync.py
!sync_db_to_render.py
!app/
!migrations/
!templates/
!static/ 
EOF

# 自动 Git 提交 + 推送脚本

# 显示当前修改状态
git status

# 添加所有变更（包括新增、修改、删除的文件）
git add .

# 提示输入 commit 信息
echo "请输入提交信息："
read msg

# 如果没输入就用默认
if [ -z "$msg" ]; then
    msg="Auto commit at $(date)"
fi

# 执行提交
git commit -m "$msg"

# 推送到远端
git push origin main 

# 自动 Git 提交 + 推送脚本

# 显示当前修改状态
git status

# 添加所有变更（包括新增、修改、删除的文件）
git add .

# 提示输入 commit 信息
echo "请输入提交信息："
read msg

# 如果没输入就用默认
if [ -z "$msg" ]; then
    msg="Auto commit at $(date)"
fi

# 执行提交
git commit -m "$msg"

# 推送到远端
git push origin main 