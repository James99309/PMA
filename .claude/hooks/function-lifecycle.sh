#!/bin/bash
#
# Function Lifecycle Hook Script
# 函数生命周期钩子脚本
# 
# 用于在代码变更时自动触发function-lifecycle-manager代理
#

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/.claude/automation/agent-automation.json"
DETECTOR_SCRIPT="$PROJECT_ROOT/.claude/automation/function_detector.py"
REPORTS_DIR="$PROJECT_ROOT/.claude/reports/function-analysis"
CACHE_DIR="$PROJECT_ROOT/.claude/cache"

# 日志配置
LOG_LEVEL=${LOG_LEVEL:-"INFO"}
LOG_FILE="$PROJECT_ROOT/.claude/logs/function-lifecycle.log"

# 创建必要的目录
mkdir -p "$REPORTS_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    local level=$1
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
}

log_error() {
    log "ERROR" "$@"
}

log_debug() {
    [[ "$LOG_LEVEL" == "DEBUG" ]] && log "DEBUG" "$@"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未找到"
        exit 1
    fi
    
    # 检查Claude CLI
    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI 未找到，请确保已安装Claude Code"
        exit 1
    fi
    
    # 检查配置文件
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "配置文件未找到: $CONFIG_FILE"
        exit 1
    fi
    
    # 检查检测器脚本
    if [[ ! -f "$DETECTOR_SCRIPT" ]]; then
        log_error "函数检测器脚本未找到: $DETECTOR_SCRIPT"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 加载配置
load_config() {
    log_debug "加载配置文件: $CONFIG_FILE"
    
    # 检查配置是否启用
    local enabled=$(python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    enabled = config.get('rules', {}).get('function-lifecycle-manager', {}).get('enabled', False)
    print('true' if enabled else 'false')
except:
    print('false')
    ")
    
    if [[ "$enabled" != "true" ]]; then
        log_info "function-lifecycle-manager 代理未启用，跳过处理"
        exit 0
    fi
}

# 检测函数变更
detect_function_changes() {
    local mode=${1:-"full"}  # full | incremental
    local output_file="$CACHE_DIR/current_analysis.json"
    local previous_file="$CACHE_DIR/previous_analysis.json"
    
    log_info "开始检测函数变更 (模式: $mode)..."
    
    # 保存之前的分析结果
    if [[ -f "$output_file" ]]; then
        cp "$output_file" "$previous_file"
    fi
    
    # 执行函数检测
    local cmd="python3 '$DETECTOR_SCRIPT' --directory '$PROJECT_ROOT' --output '$output_file'"
    
    if [[ "$mode" == "incremental" && -f "$previous_file" ]]; then
        cmd="$cmd --compare '$previous_file'"
    fi
    
    if [[ "$LOG_LEVEL" == "DEBUG" ]]; then
        cmd="$cmd --verbose"
    fi
    
    log_debug "执行命令: $cmd"
    
    if ! eval "$cmd"; then
        log_error "函数检测失败"
        return 1
    fi
    
    log_info "函数检测完成，结果保存到: $output_file"
    return 0
}

# 分析变更并决定是否触发代理
should_trigger_agent() {
    local analysis_file="$CACHE_DIR/current_analysis.json"
    
    if [[ ! -f "$analysis_file" ]]; then
        log_error "分析结果文件不存在: $analysis_file"
        return 1
    fi
    
    # 检查是否有新函数或修改的函数
    local has_changes=$(python3 -c "
import json
try:
    with open('$analysis_file', 'r') as f:
        analysis = json.load(f)
    
    changes = analysis.get('changes', {})
    new_functions = len(changes.get('new_functions', []))
    modified_functions = len(changes.get('modified_functions', []))
    deleted_functions = len(changes.get('deleted_functions', []))
    
    total_changes = new_functions + modified_functions + deleted_functions
    
    if total_changes > 0:
        print(f'NEW:{new_functions},MODIFIED:{modified_functions},DELETED:{deleted_functions}')
        exit(0)
    else:
        exit(1)
except Exception as e:
    print(f'ERROR:{e}')
    exit(2)
    ")
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "检测到函数变更: $has_changes"
        return 0
    elif [[ $exit_code -eq 1 ]]; then
        log_info "未检测到函数变更"
        return 1
    else
        log_error "检查变更时出错: $has_changes"
        return 2
    fi
}

# 触发function-lifecycle-manager代理
trigger_agent() {
    local analysis_file="$CACHE_DIR/current_analysis.json"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local report_file="$REPORTS_DIR/agent_analysis_$timestamp.md"
    
    log_info "触发 function-lifecycle-manager 代理..."
    
    # 构建代理提示
    local prompt="我需要你使用function-lifecycle-manager代理来分析最新的函数变更。

分析结果文件: $analysis_file

请执行以下任务:
1. 分析新增、修改和删除的函数
2. 检查是否存在重复功能的函数
3. 评估函数的可重用性
4. 提供优化和重构建议
5. 识别可以归档的未使用函数

请将详细的分析报告保存到: $report_file"
    
    # 调用Claude CLI触发代理
    log_debug "调用Claude CLI..."
    
    if claude task function-lifecycle-manager "$prompt" > "$report_file.tmp" 2>&1; then
        mv "$report_file.tmp" "$report_file"
        log_info "代理分析完成，报告保存到: $report_file"
        
        # 显示摘要
        if [[ -f "$report_file" ]]; then
            log_info "分析报告摘要:"
            head -20 "$report_file" | while IFS= read -r line; do
                log_info "  $line"
            done
        fi
        
        return 0
    else
        log_error "代理执行失败"
        if [[ -f "$report_file.tmp" ]]; then
            log_error "错误输出:"
            cat "$report_file.tmp" | while IFS= read -r line; do
                log_error "  $line"
            done
            rm -f "$report_file.tmp"
        fi
        return 1
    fi
}

# 清理旧文件
cleanup_old_files() {
    local days=${1:-7}  # 保留天数
    
    log_info "清理 $days 天前的旧文件..."
    
    # 清理报告文件
    find "$REPORTS_DIR" -name "*.md" -mtime +$days -delete 2>/dev/null || true
    find "$REPORTS_DIR" -name "*.json" -mtime +$days -delete 2>/dev/null || true
    
    # 清理日志文件
    if [[ -f "$LOG_FILE" ]]; then
        # 保留最后1000行日志
        tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
    
    log_info "清理完成"
}

# 主函数
main() {
    local mode=${1:-"incremental"}  # full | incremental | check
    
    log_info "========== Function Lifecycle Hook 启动 =========="
    log_info "模式: $mode"
    log_info "项目根目录: $PROJECT_ROOT"
    
    # 检查依赖
    check_dependencies
    
    # 加载配置
    load_config
    
    case "$mode" in
        "full")
            # 完整分析模式
            detect_function_changes "full"
            trigger_agent
            ;;
        "incremental")
            # 增量分析模式
            if detect_function_changes "incremental"; then
                if should_trigger_agent; then
                    trigger_agent
                else
                    log_info "无需触发代理"
                fi
            fi
            ;;
        "check")
            # 仅检查模式
            detect_function_changes "incremental"
            should_trigger_agent
            ;;
        "cleanup")
            # 清理模式
            cleanup_old_files
            ;;
        *)
            log_error "未知模式: $mode"
            echo "用法: $0 [full|incremental|check|cleanup]"
            exit 1
            ;;
    esac
    
    log_info "========== Function Lifecycle Hook 完成 =========="
}

# 处理信号
trap 'log_error "脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@"