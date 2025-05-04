#!/bin/bash

# ========================
# 显示当前路径
# ========================
echo "[信息] 当前工作目录：$(pwd)"

# ========================
# 创建标准 .gitignore（若不存在）
# ========================
if [ ! -f .gitignore ]; then
    echo "[信息] 创建 .gitignore..."
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
*.sqlite*
app.db

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

# 临时和备份
*.bak
*.swp
*.tmp
tmp/
backups/
*.csv
*.json
*.zip
*.tar
*.gz
*.7z
*.rar

# 构建输出
dist/
build/
*.egg-info/

# 静态上传文件
uploads/
media/
app/static/uploads/

# 测试脚本
test_*.py
*_test.py
final_test.py
login_test.py
test_app_with_render.py
check_user.py
verify_admin_login.py
reset_admin_password.py

# 数据导入/迁移脚本
db_export*.json
complete_db_export.json
complete_fix.py
export_sqlite_data.py
migrate_to_render*.py
migrate_data_to_render.py

# Cursor IDE相关
.cursor/

# 项目结构
instance/

# 保留必要文件
!requirements.txt
!run.py
!config.py
!wsgi.py
!app/
!migrations/
!templates/
!static/
!render.yaml
!render_start.sh
!render_startup_hook.py
!render_migration.sh
!render_migration_run.py
!render_db_sync.py
!sync_db_to_render.py
EOF
else
    echo "[信息] 已存在 .gitignore，跳过生成。"
fi

# ========================
# Python 语法检查（逐个文件并显示详细错误）
# ========================
echo "[信息] 正在检查所有 Python 文件语法..."
syntax_error_found=0

while IFS= read -r file; do
    if ! python3 -m py_compile "$file"; then
        echo -e "\033[31m[语法错误] $file\033[0m"
        syntax_error_found=1
    fi
done < <(find . -type f -name "*.py")

if [ "$syntax_error_found" -ne 0 ]; then
    echo "[错误] 存在语法错误，自动推送中止。请修正后再提交。"
    exit 1
fi

# ========================
# Git 提交与推送
# ========================
git status

# 添加所有更改
git add .

# 读取提交信息
echo "请输入提交信息："
read msg

# 如果未输入，则自动生成
if [ -z "$msg" ]; then
    msg="Auto commit at $(date)"
fi

# 提交并推送
git commit -m "$msg"
git push origin main