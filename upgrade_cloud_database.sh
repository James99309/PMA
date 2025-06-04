#!/bin/bash

# PMA系统云端数据库升级脚本 - 安全版本
# 使用说明：推送代码到云端后，在Render Terminal中执行此脚本

set -e  # 遇到错误立即退出

echo "🚀 PMA系统云端数据库安全升级开始"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    log_info "检查升级环境..."
    
    # 检查Python和Flask
    if ! command -v python &> /dev/null; then
        log_error "Python命令未找到"
        exit 1
    fi
    
    if ! command -v flask &> /dev/null; then
        log_error "Flask命令未找到，请确保在正确的Python环境中"
        exit 1
    fi
    
    # 检查数据库连接
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL环境变量未设置"
        exit 1
    fi
    
    # 检查安全升级脚本是否存在
    if [ -f "safe_cloud_database_upgrade.py" ]; then
        log_success "找到安全升级脚本"
    else
        log_warning "安全升级脚本不存在，将使用传统方式"
    fi
    
    log_success "环境检查完成"
}

# 显示当前状态
show_current_status() {
    log_info "显示当前数据库状态..."
    
    echo ""
    echo "📊 当前状态信息:"
    echo "=================="
    
    # 显示当前迁移版本
    log_info "当前迁移版本:"
    flask db current || echo "无法获取迁移版本"
    
    # 检查关键表的存在性
    log_info "检查关键表的存在性..."
    python -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    tables = ['project_rating_records', 'project_scoring_config', 'project_scoring_records', 'approval_record']
    for table in tables:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f'✓ {table}: {count} 条记录')
        except Exception as e:
            print(f'✗ {table}: 不存在或无法访问')
"
    
    echo ""
}

# 执行安全升级
perform_safe_upgrade() {
    log_info "执行安全数据库升级..."
    
    if [ -f "safe_cloud_database_upgrade.py" ]; then
        log_info "使用安全升级脚本..."
        
        # 执行安全升级脚本
        if python safe_cloud_database_upgrade.py; then
            log_success "安全升级脚本执行成功"
            return 0
        else
            log_error "安全升级脚本执行失败"
            return 1
        fi
    else
        log_warning "使用传统升级方式..."
        return perform_traditional_upgrade
    fi
}

# 传统升级方式（带存在性检查）
perform_traditional_upgrade() {
    log_info "执行传统数据库升级..."
    
    # 1. 修复数据完整性问题
    log_info "修复approval_record.step_id NULL值..."
    
    NULL_COUNT=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$NULL_COUNT" -gt 0 ]; then
        log_warning "发现 $NULL_COUNT 条step_id为NULL的记录，正在修复..."
        
        # 修复NULL值
        psql $DATABASE_URL -c "UPDATE approval_record SET step_id = (SELECT MIN(id) FROM approval_step LIMIT 1) WHERE step_id IS NULL;" || {
            log_error "数据修复失败"
            return 1
        }
        
        log_success "数据完整性问题修复成功"
    else
        log_success "数据完整性检查通过，无需修复"
    fi
    
    # 2. 安全删除可能不存在的索引和约束
    log_info "安全删除索引和约束..."
    
    # 删除可能存在的索引（忽略错误）
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_project_rating_records_created_at;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_project_rating_records_project_id;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_project_rating_records_user_id;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_scoring_config_category;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_scoring_records_category;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_scoring_records_project;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_quotations_is_locked;" 2>/dev/null || true
    psql $DATABASE_URL -c "DROP INDEX IF EXISTS idx_quotations_locked_by;" 2>/dev/null || true
    
    log_success "索引清理完成"
    
    # 3. 执行Flask迁移
    log_info "执行Flask数据库迁移..."
    if flask db upgrade; then
        log_success "数据库迁移执行成功"
        return 0
    else
        log_error "数据库迁移执行失败"
        return 1
    fi
}

# 验证升级结果
verify_upgrade() {
    log_info "验证升级结果..."
    
    # 检查目标版本
    CURRENT_VERSION=$(flask db current 2>/dev/null | tail -1 | awk '{print $1}' || echo "unknown")
    TARGET_VERSION="c1308c08d0c9"
    
    if [[ "$CURRENT_VERSION" == *"$TARGET_VERSION"* ]]; then
        log_success "数据库版本验证成功: $CURRENT_VERSION"
    else
        log_error "数据库版本不匹配！当前: $CURRENT_VERSION, 期望: $TARGET_VERSION"
        return 1
    fi
    
    # 验证数据完整性
    NULL_COUNT=$(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL;" 2>/dev/null | tr -d ' ' || echo "0")
    if [ "$NULL_COUNT" -eq 0 ]; then
        log_success "数据完整性验证通过"
    else
        log_error "数据完整性验证失败，发现 $NULL_COUNT 条NULL记录"
        return 1
    fi
    
    return 0
}

# 显示升级摘要
show_upgrade_summary() {
    echo ""
    echo "📋 升级摘要"
    echo "============"
    echo "升级时间: $(date)"
    echo "目标版本: c1308c08d0c9"
    echo "数据库: PostgreSQL (Render)"
    echo "状态: 升级成功 ✅"
    echo ""
    echo "🔍 重要说明："
    echo "本次升级使用了安全的存在性检查机制，避免了以下风险："
    echo "- 删除不存在的索引或约束"
    echo "- 修改不存在的表结构"
    echo "- 数据完整性约束冲突"
    echo ""
    echo "🔍 下一步验证："
    echo "1. 访问应用确认正常启动"
    echo "2. 测试登录功能"
    echo "3. 验证项目列表筛选功能"
    echo "4. 检查所有关键功能正常"
    echo ""
    echo "📞 如有问题，请联系: James.ni@evertacsolutions.com"
    echo ""
}

# 主执行流程
main() {
    echo "开始时间: $(date)"
    echo ""
    
    # 执行升级步骤
    check_environment
    show_current_status
    
    if perform_safe_upgrade; then
        if verify_upgrade; then
            show_upgrade_summary
            log_success "云端数据库安全升级完成！🎉"
            echo "完成时间: $(date)"
            return 0
        else
            log_error "升级验证失败"
            return 1
        fi
    else
        log_error "数据库升级执行失败"
        return 1
    fi
}

# 错误处理
trap 'log_error "数据库升级出错，请检查上面的错误信息"; exit 1' ERR

# 执行主函数
main "$@" 