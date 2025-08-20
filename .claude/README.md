# Function Lifecycle Manager 自动代理系统

## 📖 系统概述

这个系统实现了在主系统进行函数生成时自动激活`function-lifecycle-manager`代理的完整解决方案。通过智能检测代码变更、分析函数生命周期，并自动调用专门的代理进行深度分析和建议。

## 🏗️ 系统架构

```
.claude/
├── agents/                          # 代理定义
│   └── function-lifecycle-manager.md
├── automation/                      # 自动化核心
│   ├── agent-automation.json        # 配置文件
│   ├── function_detector.py         # 函数检测器
│   ├── agent_invoker.py            # 代理调用器
│   └── auto_agent.sh               # 统一启动脚本
├── hooks/                          # 钩子脚本
│   └── function-lifecycle.sh
├── templates/                      # 报告模板
│   └── function-analysis-report.md
├── cache/                          # 缓存目录
├── reports/                        # 分析报告
└── logs/                          # 日志文件
```

## 🚀 快速开始

### 1. 系统初始化
```bash
# 初始化系统配置
./.claude/automation/auto_agent.sh setup

# 检查系统状态
./.claude/automation/auto_agent.sh status
```

### 2. 基本使用

#### 检测函数变更
```bash
# 执行函数检测
./.claude/automation/auto_agent.sh detect

# 详细输出模式
./.claude/automation/auto_agent.sh detect --verbose
```

#### 分析并触发代理
```bash
# 检测 + 分析 + 触发代理
./.claude/automation/auto_agent.sh analyze

# 仅模拟运行
./.claude/automation/auto_agent.sh analyze --dry-run
```

#### 监控模式
```bash
# 启动持续监控（每60秒检查一次）
./.claude/automation/auto_agent.sh monitor

# 自定义检查间隔（秒）
./.claude/automation/auto_agent.sh monitor 300
```

### 3. 系统管理

#### 清理系统
```bash
# 清理7天前的文件
./.claude/automation/auto_agent.sh cleanup

# 清理指定天数前的文件
./.claude/automation/auto_agent.sh cleanup 3
```

#### 运行测试
```bash
# 执行系统测试
./.claude/automation/auto_agent.sh test
```

## ⚙️ 配置说明

### 主配置文件 (`agent-automation.json`)

#### 基本启用配置
```json
{
  "rules": {
    "function-lifecycle-manager": {
      "enabled": true,
      "triggers": {
        "on_function_creation": {
          "enabled": true,
          "conditions": [
            "file_contains_new_function",
            "file_extension_in_python_or_js"
          ]
        }
      }
    }
  }
}
```

#### 文件过滤配置
```json
{
  "file_patterns": {
    "include": [
      "**/*.py",
      "**/*.js", 
      "**/*.ts",
      "app/**/*.py"
    ],
    "exclude": [
      "**/migrations/**",
      "**/venv/**",
      "**/__pycache__/**",
      "**/backup_*/**"
    ]
  }
}
```

#### 分析设置
```json
{
  "analysis_settings": {
    "similarity_threshold": 0.75,
    "complexity_threshold": 10,
    "usage_tracking_days": 30,
    "archival_unused_days": 90
  }
}
```

## 🔄 工作流程

### 自动触发流程

1. **函数检测** → 使用AST解析和正则匹配检测代码中的函数定义
2. **变更分析** → 对比前次分析结果，识别新增、修改、删除的函数
3. **条件评估** → 根据配置的触发条件判断是否需要激活代理
4. **代理调用** → 构建专门的提示，调用function-lifecycle-manager代理
5. **报告生成** → 生成结构化的分析报告和建议

### 支持的触发场景

#### 函数创建时 (`on_function_creation`)
- 检测新增函数的重复性
- 评估函数可重用性
- 提供命名和设计建议

#### 函数修改时 (`on_function_modification`)
- 分析变更影响范围
- 检查向后兼容性
- 提供重构建议

#### 代码清理时 (`on_code_cleanup`)
- 识别未使用函数
- 建议归档方案
- 生成清理报告

## 📊 分析功能

### 函数检测能力

#### Python函数
- 普通函数定义 (`def function_name():`)
- 类方法检测
- 装饰器识别
- 参数分析
- 文档字符串提取

#### JavaScript函数
- 函数声明 (`function name()`)
- 函数表达式 (`var name = function()`)
- 箭头函数 (`const name = () =>`)
- 对象方法 (`obj: function()`)

### 分析报告内容

- **执行摘要**: 统计信息和变更概览
- **新增函数分析**: 重复性检查、可重用性评估、优化建议
- **修改函数分析**: 变更对比、影响范围、兼容性分析
- **删除函数记录**: 依赖检查、风险评估
- **重复函数识别**: 相似度分析、合并建议
- **未使用函数建议**: 归档推荐、风险级别
- **重构建议**: 优先级排序、实施步骤
- **质量指标**: 代码质量得分、趋势分析

## 🔧 高级用法

### 直接使用组件

#### 函数检测器
```bash
# 分析整个项目
python3 .claude/automation/function_detector.py --directory .

# 与之前结果对比
python3 .claude/automation/function_detector.py --compare previous_analysis.json

# 详细输出
python3 .claude/automation/function_detector.py --verbose
```

#### 代理调用器
```bash
# 处理特定分析文件
python3 .claude/automation/agent_invoker.py --analysis-file analysis.json

# 自定义触发类型
python3 .claude/automation/agent_invoker.py --trigger-type on_code_cleanup

# 查看状态
python3 .claude/automation/agent_invoker.py --status
```

### Git钩子集成

#### Pre-commit钩子
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 执行函数分析
if ./.claude/automation/auto_agent.sh analyze --dry-run; then
    echo "✓ 函数分析通过"
else
    echo "✗ 函数分析发现问题，请检查报告"
    exit 1
fi
```

#### Post-commit钩子
```bash
#!/bin/bash
# .git/hooks/post-commit

# 异步执行完整分析
./.claude/automation/auto_agent.sh analyze &
```

### CI/CD集成

#### GitHub Actions
```yaml
name: Function Lifecycle Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.x'
      - name: Run Function Analysis
        run: |
          ./.claude/automation/auto_agent.sh setup
          ./.claude/automation/auto_agent.sh analyze
```

## 📈 监控和维护

### 日志管理

- **系统日志**: `.claude/logs/auto_agent.log`
- **检测器日志**: `.claude/logs/function_detector.log`
- **代理调用日志**: `.claude/logs/agent_invoker.log`

### 缓存管理

- **当前分析**: `.claude/cache/current_analysis.json`
- **对比基准**: `.claude/cache/previous_analysis.json`
- **历史记录**: `.claude/cache/analysis_YYYYMMDD_HHMMSS.json`

### 报告管理

- **代理报告**: `.claude/reports/function-analysis/agent_analysis_*.md`
- **系统报告**: `.claude/reports/function-analysis/analysis_*.json`

## 🐛 故障排除

### 常见问题

#### Claude CLI不可用
- **问题**: `claude (Claude Code CLI) - 代理功能将不可用`
- **解决**: 安装Claude Code CLI，或使用`--dry-run`模式测试其他功能

#### 语法错误警告
- **问题**: 某些Python文件无法解析
- **解决**: 检查文件语法，或在配置中排除问题文件

#### 权限错误
- **问题**: 脚本无法执行
- **解决**: 运行`chmod +x .claude/automation/*.sh`

### 调试技巧

#### 启用详细输出
```bash
./.claude/automation/auto_agent.sh detect --verbose
```

#### 检查配置
```bash
python3 -c "
import json
with open('.claude/automation/agent-automation.json') as f:
    config = json.load(f)
print(json.dumps(config, indent=2))
"
```

#### 测试组件
```bash
# 测试函数检测
python3 .claude/automation/function_detector.py --directory . --verbose

# 测试代理调用器
python3 .claude/automation/agent_invoker.py --status
```

## 🔄 版本历史

- **v1.0** - 基础函数检测和代理调用
- **v1.1** - 增加增量分析和监控模式
- **v1.2** - 支持Git钩子和CI/CD集成
- **v1.3** - 完善报告模板和错误处理

## 🤝 贡献指南

1. 在`.claude/automation/agent-automation.json`中添加新的触发条件
2. 在`function_detector.py`中扩展语言支持
3. 在`function-analysis-report.md`中丰富报告模板
4. 在`auto_agent.sh`中添加新的管理命令

## 📄 许可证

该系统为PMA项目的一部分，遵循项目整体许可证。

---

**更新时间**: 2025-08-20  
**版本**: 1.0  
**维护者**: PMA开发团队