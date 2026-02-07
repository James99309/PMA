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
# Python 语法检查（仅主业务代码，排除 venv/.venv/.git/migrations 等）
# ========================
echo "[信息] 正在检查主业务 Python 文件语法..."
syntax_error_found=0

find ./app -type f -name "*.py" \
    -o -path "./run.py" \
    -o -path "./config.py" \
    | grep -vE '^\./venv/|^\./.venv/|^\./.git/|^\./migrations/' \
    | while IFS= read -r file; do
    if [ -f "$file" ]; then
        if ! python3 -m py_compile "$file"; then
            echo -e "\033[31m[语法错误] $file\033[0m"
            syntax_error_found=1
        fi
    fi
done

if [ "$syntax_error_found" -ne 0 ]; then
    echo -e "\033[41;97m[错误] 存在语法错误，自动推送中止。请修正所有语法错误后再提交。\033[0m"
    exit 1
fi

# ========================
# Git 提交与推送
# ========================
git status

# 添加所有更改
git add .

# 检查是否有除 app_version.json 之外的实际改动
REAL_CHANGES=$(git diff --cached --name-only | grep -v '^app_version.json$')

if [ -z "$REAL_CHANGES" ]; then
    echo ""
    echo -e "\033[33m[信息] 没有实际代码改动（仅 app_version.json 时间戳变化），跳过提交和推送。\033[0m"
    # 还原 app_version.json 的暂存
    git restore --staged app_version.json 2>/dev/null
    git checkout -- app_version.json 2>/dev/null
    SKIP_PUSH=1
else
    SKIP_PUSH=0

    # ========================
    # 询问是否增加版本号
    # ========================
    VERSION_FILE="app_version.json"
    if [ -f "$VERSION_FILE" ]; then
        CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['app_version'])")
        echo ""
        echo "当前版本: $CURRENT_VERSION"
        echo "是否增加版本号？"
        echo "  1) 小迭代 (patch: x.x.X+1)"
        echo "  2) 功能更新 (minor: x.X+1.0)"
        echo "  3) 主版本 (major: X+1.0.0)"
        echo "  n) 不改版本号"
        read -p "选择 [1/2/3/n]: " ver_choice

        if [ "$ver_choice" = "1" ] || [ "$ver_choice" = "2" ] || [ "$ver_choice" = "3" ]; then
            IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
            case "$ver_choice" in
                1) PATCH=$((PATCH + 1)) ;;
                2) MINOR=$((MINOR + 1)); PATCH=0 ;;
                3) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
            esac
            NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

            python3 -c "
import json
with open('$VERSION_FILE', 'r') as f:
    data = json.load(f)
data['app_version'] = '$NEW_VERSION'
with open('$VERSION_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"
            # 同步更新 config.py 中的 APP_VERSION
            sed -i '' "s/APP_VERSION = '.*'/APP_VERSION = '$NEW_VERSION'/" config.py
            echo -e "\033[32m[版本] $CURRENT_VERSION → $NEW_VERSION\033[0m"
            git add "$VERSION_FILE" config.py
        else
            echo "[信息] 保持当前版本 $CURRENT_VERSION"
        fi
    fi

    # 读取提交信息
    echo ""
    echo "请输入提交信息："
    read msg

    # 如果未输入，则自动生成
    if [ -z "$msg" ]; then
        msg="Auto commit at $(date)"
    fi

    # 提交并推送
    git commit -m "$msg"
    git push origin main

    if [ $? -ne 0 ]; then
        echo -e "\033[31m[错误] git push 失败，跳过 NAS 拉新。\033[0m"
        exit 1
    fi
fi

# ========================
# NAS 拉新通用函数
# ========================
pull_nas() {
    local NAS_NAME="$1"
    local TUNNEL_HOST="$2"
    local LOCAL_PORT="$3"
    local NAS_USER="$4"
    local UPDATE_SCRIPT="$5"

    echo ""
    echo -e "\033[36m========== $NAS_NAME 拉新开始 ==========\033[0m"

    echo "[信息] 启动 Cloudflare 隧道 → $TUNNEL_HOST ..."
    lsof -ti:$LOCAL_PORT | xargs kill -9 2>/dev/null
    sleep 1
    cloudflared access tcp --hostname "$TUNNEL_HOST" --url "localhost:$LOCAL_PORT" &
    CF_PID=$!

    echo "[信息] 等待隧道建立..."
    sleep 3
    for i in $(seq 1 10); do
        if ssh -p $LOCAL_PORT -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$NAS_USER@localhost" "echo ok" &>/dev/null; then
            echo -e "\033[32m[信息] 隧道已建立\033[0m"
            break
        fi
        if [ "$i" -eq 10 ]; then
            echo -e "\033[31m[错误] $NAS_NAME 隧道建立超时，请检查网络。\033[0m"
            kill "$CF_PID" 2>/dev/null
            return 1
        fi
        sleep 1
    done

    echo -e "\033[36m[信息] 通过隧道执行 $NAS_NAME 更新...\033[0m"
    ssh -p $LOCAL_PORT \
        -o StrictHostKeyChecking=accept-new \
        -o BatchMode=yes \
        -o ServerAliveInterval=5 \
        -o ServerAliveCountMax=6 \
        "$NAS_USER@localhost" "bash $UPDATE_SCRIPT"

    if [ $? -ne 0 ]; then
        echo -e "\033[31m[错误] $NAS_NAME 更新执行失败\033[0m"
    else
        echo -e "\033[32m[信息] $NAS_NAME 更新完成\033[0m"
    fi

    echo "[信息] 关闭 $NAS_NAME 连接..."
    kill "$CF_PID" 2>/dev/null
    wait "$CF_PID" 2>/dev/null

    echo -e "\033[36m========== $NAS_NAME 拉新结束 ==========\033[0m"
}

# ========================
# 询问是否在 NAS 上拉新
# ========================
echo ""
echo "是否要在 NAS 上拉新？"
echo "  1) 中国 NAS (SP8D)"
echo "  2) 新加坡 NAS (OVS)"
echo "  3) 两台都拉新"
echo "  n) 跳过"
read -p "选择 [1/2/3/n]: " nas_choice

case "$nas_choice" in
    1)
        pull_nas "中国 NAS" "ssh.jamesgpone.win" 2222 "james.sh" "/volume1/docker/pma/deploy/synology-cn/update.sh"
        ;;
    2)
        pull_nas "新加坡 NAS" "sg-ssh.jamesgpone.win" 2223 "admin" "/volume1/docker/pma/deploy/synology-sa/update.sh"
        ;;
    3)
        pull_nas "中国 NAS" "ssh.jamesgpone.win" 2222 "james.sh" "/volume1/docker/pma/deploy/synology-cn/update.sh"
        pull_nas "新加坡 NAS" "sg-ssh.jamesgpone.win" 2223 "admin" "/volume1/docker/pma/deploy/synology-sa/update.sh"
        ;;
    *)
        echo "[信息] 跳过 NAS 拉新。"
        ;;
esac