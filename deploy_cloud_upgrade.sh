#!/bin/bash

# PMA系统云端部署升级脚本 - v1.2.2
# 创建日期: 2025年6月4日
# 作者: 倪捷

set -e  # 遇到错误立即退出

echo "🚀 PMA系统云端部署升级开始 - v1.2.2"
echo "================================================"

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

# 检查必要的环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查Git状态
    if ! git status >/dev/null 2>&1; then
        log_error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "检测到未提交的更改，将进行提交"
    fi
    
    log_success "环境检查完成"
}

# 备份关键文件
backup_files() {
    log_info "备份关键文件..."
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份重要配置文件
    cp config.py "$BACKUP_DIR/"
    cp -r migrations/ "$BACKUP_DIR/"
    cp CLOUD_DEPLOYMENT_PACKAGE_2025_06_04.md "$BACKUP_DIR/"
    
    log_success "文件备份完成: $BACKUP_DIR"
}

# 更新代码版本信息
update_version_info() {
    log_info "更新版本信息..."
    
    # 创建版本记录文件
    cat > VERSION_INFO.md << EOF
# PMA系统版本信息

## 当前版本: v1.2.2
- **发布日期**: $(date +%Y-%m-%d)
- **Git提交**: $(git rev-parse --short HEAD)
- **分支**: $(git branch --show-current)

## 主要更新
- 修复项目列表筛选功能
- 优化用户界面交互
- 完善数据库约束

## 部署信息
- **部署时间**: $(date)
- **部署人**: 倪捷
- **目标环境**: Render.com云端
EOF
    
    log_success "版本信息更新完成"
}

# 提交代码更改
commit_changes() {
    log_info "提交代码更改..."
    
    # 添加所有更改
    git add .
    
    # 检查是否有更改需要提交
    if git diff --staged --quiet; then
        log_info "没有新的更改需要提交"
    else
        # 提交更改
        git commit -m "云端部署升级 - v1.2.2 - 筛选功能完全重构

- 修复项目列表筛选按钮点击无响应问题
- 重构筛选功能JavaScript逻辑
- 优化DOM事件监听器和CSS样式
- 增强移动端兼容性
- 完善数据库约束和权限系统
- 添加调试功能便于问题诊断

Date: $(date)
Deployer: 倪捷"
        
        log_success "代码提交完成"
    fi
}

# 推送到远程仓库
push_to_remote() {
    log_info "推送代码到远程仓库..."
    
    # 获取当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    
    # 推送到远程
    git push origin "$CURRENT_BRANCH"
    
    log_success "代码推送完成 - 分支: $CURRENT_BRANCH"
}

# 显示部署状态
show_deployment_status() {
    log_info "部署状态信息..."
    
    echo ""
    echo "📋 部署摘要"
    echo "============"
    echo "版本: v1.2.2"
    echo "时间: $(date)"
    echo "Git提交: $(git rev-parse --short HEAD)"
    echo "分支: $(git branch --show-current)"
    echo ""
    echo "🔗 相关链接"
    echo "============"
    echo "生产环境: https://pma-system.onrender.com"
    echo "Render仪表板: https://dashboard.render.com"
    echo ""
    echo "📞 联系信息"
    echo "============"
    echo "技术负责人: 倪捷"
    echo "邮箱: James.ni@evertacsolutions.com"
    echo ""
}

# 等待用户确认
wait_for_confirmation() {
    echo ""
    read -p "🤔 是否继续部署? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "部署已取消"
        exit 0
    fi
}

# 显示部署后指导
show_post_deployment_guide() {
    log_success "代码推送完成! 🎉"
    echo ""
    echo "📋 接下来需要做的:"
    echo "==================="
    echo "1. 等待Render自动检测并部署 (通常5-10分钟)"
    echo "2. 检查Render部署日志确认无错误"
    echo "3. 访问生产环境验证功能:"
    echo "   - 项目列表页面加载正常"
    echo "   - 筛选图标可以点击"
    echo "   - 筛选输入框正常弹出"
    echo "   - 实时筛选功能工作正常"
    echo "4. 如有问题，运行浏览器控制台中的调试函数:"
    echo "   - debugFilterFunction()"
    echo "   - testFilter()"
    echo ""
    echo "🔍 故障排除:"
    echo "============="
    echo "如果筛选功能仍有问题，请检查:"
    echo "- 浏览器控制台是否有JavaScript错误"
    echo "- 网络请求是否正常"
    echo "- 数据库连接是否稳定"
    echo ""
    echo "✅ 部署升级包: CLOUD_DEPLOYMENT_PACKAGE_2025_06_04.md"
    echo "✅ 版本信息: VERSION_INFO.md"
    echo ""
}

# 主执行流程
main() {
    echo "开始时间: $(date)"
    echo ""
    
    # 显示升级信息
    echo "🎯 本次升级内容:"
    echo "- 修复项目列表筛选功能"
    echo "- 优化用户界面交互体验"
    echo "- 完善数据库约束和权限"
    echo "- 增强移动端兼容性"
    echo ""
    
    # 等待确认
    wait_for_confirmation
    
    # 执行部署步骤
    check_environment
    backup_files
    update_version_info
    commit_changes
    push_to_remote
    show_deployment_status
    show_post_deployment_guide
    
    echo ""
    log_success "云端部署升级脚本执行完成! 🚀"
    echo "完成时间: $(date)"
}

# 错误处理
trap 'log_error "脚本执行出错，请检查上面的错误信息"; exit 1' ERR

# 执行主函数
main "$@" 