#!/bin/bash
#
# 函数生命周期自动代理系统
# Auto Agent System for Function Lifecycle Management
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 脚本路径
FUNCTION_DETECTOR="$SCRIPT_DIR/function_detector.py"
AGENT_INVOKER="$SCRIPT_DIR/agent_invoker.py"
LIFECYCLE_HOOK="$PROJECT_ROOT/.claude/hooks/function-lifecycle.sh"

# 配置文件
CONFIG_FILE="$SCRIPT_DIR/agent-automation.json"
CACHE_DIR="$PROJECT_ROOT/.claude/cache"
REPORTS_DIR="$PROJECT_ROOT/.claude/reports/function-analysis"

# 日志配置
LOG_FILE="$PROJECT_ROOT/.claude/logs/auto_agent.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$1] $2" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$1"
}

log_error() {
    log "ERROR" "$1"
}

# 显示帮助信息
show_help() {
    cat << EOF
函数生命周期自动代理系统

用法: $0 <命令> [选项]

命令:
  detect      执行函数检测和分析
  analyze     触发代理分析
  monitor     监控模式（持续监听文件变更）
  status      显示系统状态
  setup       初始化系统配置
  cleanup     清理旧文件和缓存
  test        运行系统测试

选项:
  --config FILE     指定配置文件路径
  --verbose         详细输出
  --dry-run         模拟运行，不实际执行
  --help            显示此帮助信息

示例:
  $0 detect                    # 检测函数变更
  $0 analyze --verbose         # 分析并触发代理
  $0 monitor                   # 启动监控模式
  $0 status                    # 查看系统状态
  $0 setup                     # 初始化配置
  $0 cleanup                   # 清理缓存
  $0 test                      # 运行测试

EOF
}

# 检查依赖
check_dependencies() {
    local check_claude=${1:-true}
    
    log_info "检查系统依赖..."
    
    local missing_deps=()
    local warnings=()
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # 检查Claude CLI (可选)
    if [[ "$check_claude" == "true" ]] && ! command -v claude &> /dev/null; then
        warnings+=("claude (Claude Code CLI) - 代理功能将不可用")
    fi
    
    # 检查脚本文件
    if [[ ! -f "$FUNCTION_DETECTOR" ]]; then
        missing_deps+=("function_detector.py")
    fi
    
    if [[ ! -f "$AGENT_INVOKER" ]]; then
        missing_deps+=("agent_invoker.py")
    fi
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        missing_deps+=("agent-automation.json")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少关键依赖: ${missing_deps[*]}"
        return 1
    fi
    
    if [[ ${#warnings[@]} -gt 0 ]]; then
        for warning in "${warnings[@]}"; do
            log_info "警告: $warning"
        done
    fi
    
    log_info "依赖检查通过"
    return 0
}

# 初始化系统配置
setup_system() {
    log_info "初始化系统配置..."
    
    # 创建必要目录
    mkdir -p "$CACHE_DIR"
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$PROJECT_ROOT/.claude/logs"
    
    # 设置脚本权限
    chmod +x "$FUNCTION_DETECTOR" 2>/dev/null || true
    chmod +x "$AGENT_INVOKER" 2>/dev/null || true
    chmod +x "$LIFECYCLE_HOOK" 2>/dev/null || true
    
    # 检查配置文件
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "检查配置文件有效性..."
        if python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
            log_info "配置文件格式正确"
        else
            log_error "配置文件格式错误"
            return 1
        fi
    fi
    
    log_info "系统配置初始化完成"
    return 0
}

# 执行函数检测
run_detection() {
    local verbose=${1:-false}
    local dry_run=${2:-false}
    
    log_info "开始函数检测..."
    
    local cmd="python3 '$FUNCTION_DETECTOR' --directory '$PROJECT_ROOT'"
    local output_file="$CACHE_DIR/current_analysis_$(date +%Y%m%d_%H%M%S).json"
    local previous_file="$CACHE_DIR/previous_analysis.json"
    
    # 保存之前的分析结果
    if [[ -f "$CACHE_DIR/current_analysis.json" ]]; then
        cp "$CACHE_DIR/current_analysis.json" "$previous_file"
        cmd="$cmd --compare '$previous_file'"
    fi
    
    cmd="$cmd --output '$output_file'"
    
    if [[ "$verbose" == "true" ]]; then
        cmd="$cmd --verbose"
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "模拟执行: $cmd"
        return 0
    fi
    
    log_info "执行: $(basename "$FUNCTION_DETECTOR")"
    
    if eval "$cmd"; then
        # 更新当前分析结果链接
        ln -sf "$output_file" "$CACHE_DIR/current_analysis.json"
        log_info "函数检测完成: $output_file"
        echo "$output_file"  # 返回输出文件路径
        return 0
    else
        log_error "函数检测失败"
        return 1
    fi
}

# 触发代理分析
run_analysis() {
    local analysis_file="$1"
    local verbose=${2:-false}
    local dry_run=${3:-false}
    
    if [[ -z "$analysis_file" ]]; then
        analysis_file="$CACHE_DIR/current_analysis.json"
    fi
    
    if [[ ! -f "$analysis_file" ]]; then
        log_error "分析文件不存在: $analysis_file"
        return 1
    fi
    
    log_info "触发代理分析: $analysis_file"
    
    local cmd="python3 '$AGENT_INVOKER' --analysis-file '$analysis_file'"
    
    if [[ "$verbose" == "true" ]]; then
        cmd="$cmd --verbose"
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "模拟执行: $cmd"
        return 0
    fi
    
    log_info "执行: $(basename "$AGENT_INVOKER")"
    
    if eval "$cmd"; then
        log_info "代理分析完成"
        return 0
    else
        log_error "代理分析失败"
        return 1
    fi
}

# 监控模式
run_monitor() {
    local interval=${1:-60}  # 检查间隔（秒）
    
    log_info "启动监控模式 (检查间隔: ${interval}s)"
    log_info "按 Ctrl+C 停止监控"
    
    # 信号处理
    trap 'log_info "监控已停止"; exit 0' INT TERM
    
    local last_check_file="$CACHE_DIR/last_monitor_check"
    
    while true; do
        log_info "执行监控检查..."
        
        # 检查Git状态（如果是Git仓库）
        if [[ -d "$PROJECT_ROOT/.git" ]]; then
            # 检查自上次检查以来是否有提交
            local current_commit=$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "")
            local last_commit=""
            
            if [[ -f "$last_check_file" ]]; then
                last_commit=$(cat "$last_check_file")
            fi
            
            if [[ -n "$current_commit" && "$current_commit" != "$last_commit" ]]; then
                log_info "检测到新提交，执行分析..."
                
                # 执行检测和分析
                if analysis_file=$(run_detection false false); then
                    run_analysis "$analysis_file" false false
                fi
                
                # 更新最后检查记录
                echo "$current_commit" > "$last_check_file"
            else
                log_info "无新提交"
            fi
        else
            # 非Git仓库，基于文件修改时间检查
            log_info "基于文件修改时间进行检查..."
            if analysis_file=$(run_detection false false); then
                run_analysis "$analysis_file" false false
            fi
        fi
        
        log_info "等待 ${interval} 秒..."
        sleep "$interval"
    done
}

# 显示系统状态
show_status() {
    log_info "系统状态检查..."
    
    echo "========== 函数生命周期自动代理系统状态 =========="
    echo "项目根目录: $PROJECT_ROOT"
    echo "配置文件: $CONFIG_FILE"
    echo "缓存目录: $CACHE_DIR"
    echo "报告目录: $REPORTS_DIR"
    echo ""
    
    # 检查依赖
    echo "=== 依赖检查 ==="
    if command -v python3 &> /dev/null; then
        echo "✓ Python3: $(python3 --version)"
    else
        echo "✗ Python3: 未安装"
    fi
    
    if command -v claude &> /dev/null; then
        echo "✓ Claude CLI: 已安装"
    else
        echo "✗ Claude CLI: 未安装"
    fi
    echo ""
    
    # 检查配置
    echo "=== 配置状态 ==="
    if [[ -f "$CONFIG_FILE" ]]; then
        local enabled=$(python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    enabled = config.get('rules', {}).get('function-lifecycle-manager', {}).get('enabled', False)
    print('启用' if enabled else '禁用')
except:
    print('错误')
        " 2>/dev/null || echo "错误")
        echo "✓ 配置文件: 存在 ($enabled)"
    else
        echo "✗ 配置文件: 不存在"
    fi
    echo ""
    
    # 检查文件状态
    echo "=== 文件状态 ==="
    if [[ -f "$CACHE_DIR/current_analysis.json" ]]; then
        local mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$CACHE_DIR/current_analysis.json" 2>/dev/null || echo "未知")
        echo "✓ 当前分析: $mod_time"
    else
        echo "✗ 当前分析: 无"
    fi
    
    local report_count=$(find "$REPORTS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    echo "✓ 分析报告数量: $report_count"
    echo ""
    
    # 代理状态
    echo "=== 代理状态 ==="
    if python3 "$AGENT_INVOKER" --status 2>/dev/null; then
        echo ""
    else
        echo "✗ 无法获取代理状态"
    fi
}

# 清理系统
cleanup_system() {
    local days=${1:-7}  # 保留天数
    
    log_info "清理系统 (保留 $days 天的数据)..."
    
    # 清理报告文件
    find "$REPORTS_DIR" -name "*.md" -mtime +$days -delete 2>/dev/null || true
    find "$REPORTS_DIR" -name "*.json" -mtime +$days -delete 2>/dev/null || true
    
    # 清理缓存文件（保留current_analysis.json和previous_analysis.json）
    find "$CACHE_DIR" -name "*.json" -mtime +$days ! -name "current_analysis.json" ! -name "previous_analysis.json" -delete 2>/dev/null || true
    
    # 清理日志文件
    if [[ -f "$LOG_FILE" ]]; then
        tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
    
    log_info "清理完成"
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."
    
    echo "=== 函数生命周期自动代理系统测试 ==="
    
    # 测试1: 依赖检查
    echo "测试1: 依赖检查"
    if check_dependencies; then
        echo "✓ 通过"
    else
        echo "✗ 失败"
        return 1
    fi
    
    # 测试2: 配置加载
    echo "测试2: 配置文件"
    if python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
        echo "✓ 通过"
    else
        echo "✗ 失败"
        return 1
    fi
    
    # 测试3: 函数检测（模拟运行）
    echo "测试3: 函数检测"
    if run_detection false true >/dev/null; then
        echo "✓ 通过"
    else
        echo "✗ 失败"
        return 1
    fi
    
    # 测试4: 代理调用器状态
    echo "测试4: 代理调用器"
    if python3 "$AGENT_INVOKER" --status >/dev/null 2>&1; then
        echo "✓ 通过"
    else
        echo "✗ 失败"
        return 1
    fi
    
    echo ""
    log_info "所有测试通过"
}

# 主函数
main() {
    local command="$1"
    shift
    
    local verbose=false
    local dry_run=false
    local config=""
    
    # 解析选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                config="$2"
                shift 2
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
    
    # 使用自定义配置文件
    if [[ -n "$config" ]]; then
        CONFIG_FILE="$config"
    fi
    
    case "$command" in
        "detect")
            check_dependencies false || exit 1
            run_detection "$verbose" "$dry_run"
            ;;
        "analyze")
            check_dependencies || exit 1
            if analysis_file=$(run_detection "$verbose" "$dry_run"); then
                run_analysis "$analysis_file" "$verbose" "$dry_run"
            fi
            ;;
        "monitor")
            check_dependencies || exit 1
            run_monitor "${1:-60}"
            ;;
        "status")
            show_status
            ;;
        "setup")
            setup_system
            ;;
        "cleanup")
            cleanup_system "${1:-7}"
            ;;
        "test")
            run_tests
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"