#!/bin/bash
# PMA 数据迁移脚本
# 从新加坡 NAS → 本地 Mac → 中国 DS925+
# 用法: bash migrate-data.sh [export|transfer|import|verify]

set -e

# ============ 配置 ============

# 新加坡 NAS（源）
SG_NAS_HOST="localhost"          # 通过 cloudflared 代理
SG_NAS_SSH_PORT="2222"           # cloudflared 代理端口
SG_NAS_USER="admin"
SG_NAS_DIRECT_HOST="192.168.1.2" # 内网直连（如在同一网络）

# 中国 DS925+（目标）
CN_NAS_HOST="${CN_NAS_HOST:-192.168.31.91}"
CN_NAS_PORT="${CN_NAS_PORT:-72}"
CN_NAS_USER="${CN_NAS_USER:-james.sh}"

# 本地中转目录
LOCAL_BACKUP_DIR="${HOME}/pma-migration-$(date +%Y%m%d)"

# 数据库信息
DB_NAME="pma_synology"
DB_USER="pma"

# ============ 颜色输出 ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# ============ 函数定义 ============

start_sg_proxy() {
    info "启动新加坡 NAS SSH 代理..."
    # 检查是否已经在运行
    if lsof -i :2222 &>/dev/null; then
        info "代理已在运行 (端口 2222)"
        return 0
    fi
    cloudflared access tcp --hostname ssh.jamesgpone.win --url localhost:2222 &
    PROXY_PID=$!
    sleep 3
    if ! kill -0 $PROXY_PID 2>/dev/null; then
        error "SSH 代理启动失败"
    fi
    info "代理已启动 (PID: $PROXY_PID)"
}

ssh_sg() {
    ssh -p "$SG_NAS_SSH_PORT" "$SG_NAS_USER@$SG_NAS_HOST" "$@"
}

ssh_cn() {
    ssh -p "$CN_NAS_PORT" "$CN_NAS_USER@$CN_NAS_HOST" "$@"
}

# ============ Phase 1: 导出（从新加坡 NAS） ============

do_export() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Phase 1: 从新加坡 NAS 导出数据${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    mkdir -p "$LOCAL_BACKUP_DIR"

    # 启动 SSH 代理
    start_sg_proxy

    # 1. 导出数据库（双格式）
    step "1/4 导出数据库 (custom 格式)..."
    ssh_sg "sudo docker exec pma-postgres pg_dump -U $DB_USER -Fc $DB_NAME" > "$LOCAL_BACKUP_DIR/sp8d_backup.dump"
    DUMP_SIZE=$(du -h "$LOCAL_BACKUP_DIR/sp8d_backup.dump" | cut -f1)
    info "Custom 格式备份完成: $DUMP_SIZE"

    step "2/4 导出数据库 (SQL 格式)..."
    ssh_sg "sudo docker exec pma-postgres pg_dump -U $DB_USER $DB_NAME" > "$LOCAL_BACKUP_DIR/sp8d_backup.sql"
    SQL_SIZE=$(du -h "$LOCAL_BACKUP_DIR/sp8d_backup.sql" | cut -f1)
    info "SQL 格式备份完成: $SQL_SIZE"

    # 2. 导出表行数（用于验证）
    step "3/4 导出各表行数..."
    ssh_sg "sudo docker exec pma-postgres psql -U $DB_USER -d $DB_NAME -c \"
        SELECT schemaname, relname, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY relname;
    \"" > "$LOCAL_BACKUP_DIR/table_counts_source.txt"
    info "表行数统计已保存"

    # 3. 导出 WebDAV 文件
    step "4/4 导出 WebDAV 文件..."
    warn "WebDAV 文件导出可能需要较长时间..."
    echo ""

    read -p "是否导出 WebDAV 文件？(Y/n) " export_files
    if [ "$export_files" != "n" ] && [ "$export_files" != "N" ]; then
        # 先在 NAS 上打包
        info "在新加坡 NAS 上打包文件..."
        ssh_sg "sudo tar czf /tmp/pma-files.tar.gz -C /volume1 pma-files/"

        # 下载到本地
        info "下载文件到本地..."
        scp -P "$SG_NAS_SSH_PORT" "$SG_NAS_USER@$SG_NAS_HOST:/tmp/pma-files.tar.gz" "$LOCAL_BACKUP_DIR/"

        # 清理 NAS 上的临时文件
        ssh_sg "rm -f /tmp/pma-files.tar.gz"

        FILES_SIZE=$(du -h "$LOCAL_BACKUP_DIR/pma-files.tar.gz" | cut -f1)
        info "WebDAV 文件导出完成: $FILES_SIZE"
    else
        warn "跳过 WebDAV 文件导出"
    fi

    echo ""
    echo -e "${GREEN}导出完成！备份目录: $LOCAL_BACKUP_DIR${NC}"
    ls -lh "$LOCAL_BACKUP_DIR/"
}

# ============ Phase 2: 传输（Mac → DS925+） ============

do_transfer() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Phase 2: 传输数据到 DS925+${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    if [ ! -d "$LOCAL_BACKUP_DIR" ]; then
        error "备份目录不存在: $LOCAL_BACKUP_DIR\n请先执行 export 步骤"
    fi

    # 在 DS925+ 上创建临时目录
    step "创建目标目录..."
    ssh_cn "mkdir -p /volume1/docker/pma-migration"

    # 传输数据库备份
    step "传输数据库备份..."
    scp -P "$CN_NAS_PORT" "$LOCAL_BACKUP_DIR/sp8d_backup.dump" "$CN_NAS_USER@$CN_NAS_HOST:/volume1/docker/pma-migration/"
    scp -P "$CN_NAS_PORT" "$LOCAL_BACKUP_DIR/sp8d_backup.sql" "$CN_NAS_USER@$CN_NAS_HOST:/volume1/docker/pma-migration/"
    scp -P "$CN_NAS_PORT" "$LOCAL_BACKUP_DIR/table_counts_source.txt" "$CN_NAS_USER@$CN_NAS_HOST:/volume1/docker/pma-migration/"

    # 传输 WebDAV 文件（如存在）
    if [ -f "$LOCAL_BACKUP_DIR/pma-files.tar.gz" ]; then
        step "传输 WebDAV 文件..."
        scp -P "$CN_NAS_PORT" "$LOCAL_BACKUP_DIR/pma-files.tar.gz" "$CN_NAS_USER@$CN_NAS_HOST:/volume1/docker/pma-migration/"
    fi

    info "传输完成！"
    echo ""
    echo "DS925+ 上的文件:"
    ssh_cn "ls -lh /volume1/docker/pma-migration/"
}

# ============ Phase 3: 导入（在 DS925+ 上执行） ============

do_import() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Phase 3: 在 DS925+ 上导入数据${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # 检查容器是否运行
    step "检查 PostgreSQL 容器..."
    ssh_cn "sudo docker ps | grep pma-postgres" || error "pma-postgres 容器未运行，请先启动: docker-compose up -d"

    # 复制备份文件到容器
    step "复制备份文件到容器..."
    ssh_cn "sudo docker cp /volume1/docker/pma-migration/sp8d_backup.dump pma-postgres:/tmp/"

    # 导入数据库
    step "导入数据库..."
    warn "这将清空目标数据库并导入新数据"
    read -p "确认导入？(y/N) " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        warn "取消导入"
        exit 0
    fi

    # 先删除现有数据并重建
    info "重建数据库..."
    ssh_cn "sudo docker exec pma-postgres dropdb -U $DB_USER --if-exists $DB_NAME"
    ssh_cn "sudo docker exec pma-postgres createdb -U $DB_USER -E UTF8 $DB_NAME"

    # 使用 pg_restore 导入
    info "导入数据（pg_restore）..."
    ssh_cn "sudo docker exec pma-postgres pg_restore -U $DB_USER -d $DB_NAME --no-owner --no-acl /tmp/sp8d_backup.dump" || {
        warn "pg_restore 有一些非致命错误（通常是权限相关），继续..."
    }

    # 导入 WebDAV 文件
    if ssh_cn "test -f /volume1/docker/pma-migration/pma-files.tar.gz" 2>/dev/null; then
        step "解压 WebDAV 文件..."
        ssh_cn "sudo tar xzf /volume1/docker/pma-migration/pma-files.tar.gz -C /volume1/"
        info "WebDAV 文件已解压到 /volume1/pma-files/"
    fi

    # 清理容器中的临时文件
    ssh_cn "sudo docker exec pma-postgres rm -f /tmp/sp8d_backup.dump"

    info "数据导入完成！"
}

# ============ Phase 4: 验证 ============

do_verify() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Phase 4: 验证数据一致性${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # 获取目标数据库表行数
    step "获取 DS925+ 数据库表行数..."
    ssh_cn "sudo docker exec pma-postgres psql -U $DB_USER -d $DB_NAME -c \"
        SELECT schemaname, relname, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY relname;
    \"" > "$LOCAL_BACKUP_DIR/table_counts_target.txt"

    # 先执行 ANALYZE 更新统计信息
    step "更新数据库统计信息..."
    ssh_cn "sudo docker exec pma-postgres psql -U $DB_USER -d $DB_NAME -c 'ANALYZE;'"

    # 重新获取准确的行数
    sleep 2
    ssh_cn "sudo docker exec pma-postgres psql -U $DB_USER -d $DB_NAME -c \"
        SELECT schemaname, relname, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY relname;
    \"" > "$LOCAL_BACKUP_DIR/table_counts_target.txt"

    # 对比
    echo ""
    echo -e "${CYAN}=== 源数据库（新加坡）表行数 ===${NC}"
    cat "$LOCAL_BACKUP_DIR/table_counts_source.txt"

    echo ""
    echo -e "${CYAN}=== 目标数据库（DS925+）表行数 ===${NC}"
    cat "$LOCAL_BACKUP_DIR/table_counts_target.txt"

    echo ""
    info "请人工对比以上两个表的行数是否一致"
    echo ""

    # 基本功能验证
    step "验证 PMA 应用连接..."
    PMA_STATUS=$(ssh_cn "curl -s -o /dev/null -w '%{http_code}' http://localhost:5001/" 2>/dev/null || echo "FAILED")
    if [ "$PMA_STATUS" = "200" ] || [ "$PMA_STATUS" = "302" ]; then
        info "PMA 应用响应正常 (HTTP $PMA_STATUS)"
    else
        warn "PMA 应用响应异常 (HTTP $PMA_STATUS)"
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  验证检查清单${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "  [ ] 容器运行正常 (docker-compose ps)"
    echo "  [ ] 数据库表数和行数与源一致"
    echo "  [ ] 用户登录/登出正常"
    echo "  [ ] 客户、项目、报价 CRUD 正常"
    echo "  [ ] PDF 导出正常 (WeasyPrint)"
    echo "  [ ] 审批流程正常"
    echo "  [ ] 文件上传/下载正常 (WebDAV)"
    echo "  [ ] 中英文切换正常"
    echo "  [ ] 外网访问稳定 (FRP)"
    echo "  [ ] 连续运行 24 小时无异常"
}

# ============ 主程序 ============

case "${1:-}" in
    export)
        do_export
        ;;
    transfer)
        do_transfer
        ;;
    import)
        do_import
        ;;
    verify)
        do_verify
        ;;
    all)
        do_export
        echo ""
        read -p "导出完成，继续传输？(Y/n) " cont
        [ "$cont" = "n" ] || [ "$cont" = "N" ] && exit 0
        do_transfer
        echo ""
        read -p "传输完成，继续导入？(Y/n) " cont
        [ "$cont" = "n" ] || [ "$cont" = "N" ] && exit 0
        do_import
        echo ""
        do_verify
        ;;
    *)
        echo "PMA 数据迁移工具"
        echo ""
        echo "用法: bash migrate-data.sh <command>"
        echo ""
        echo "命令:"
        echo "  export    - 从新加坡 NAS 导出数据库和文件"
        echo "  transfer  - 将备份文件传输到 DS925+"
        echo "  import    - 在 DS925+ 上导入数据"
        echo "  verify    - 验证数据一致性"
        echo "  all       - 执行全部步骤"
        echo ""
        echo "建议在周末执行迁移，步骤顺序: export → transfer → import → verify"
        echo ""
        echo "环境变量:"
        echo "  CN_NAS_HOST  - DS925+ IP (默认: 192.168.31.91)"
        echo "  CN_NAS_PORT  - DS925+ SSH 端口 (默认: 72)"
        echo "  CN_NAS_USER  - DS925+ SSH 用户 (默认: james.sh)"
        ;;
esac
