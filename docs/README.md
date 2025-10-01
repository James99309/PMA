# PMA 项目文档索引

> **快速导航**: 本文档提供PMA项目所有文档的完整索引和访问路径

---

## 📖 核心规范文档

位于项目根目录，Claude AI 和开发人员必读：

### 主规范
- **[CLAUDE.md](../CLAUDE.md)** - 核心开发规范和项目规则（主文档）
  - 包含核心原则、优先级排序、开发工作流
  - 包含文件组织规范、定期维护规则
  - 版本：v2.5.0

### 专项规范
- **[CLAUDE-COMPONENTS.md](../CLAUDE-COMPONENTS.md)** - 组件和UI规范
  - 页面结构规范、按钮组件、筛选搜索组件
  - 徽章组件、通用列表、共享功能组件
  - 审批组件使用规范

- **[CLAUDE-DATABASE.md](../CLAUDE-DATABASE.md)** - 数据库备份和迁移规范
  - 数据库字段规范、查询规范
  - 备份工具使用、迁移升级工具
  - SP8D和OVS数据库管理

- **[CLAUDE-I18N.md](../CLAUDE-I18N.md)** - 翻译与国际化规范
  - 中英文翻译规则、标准映射
  - pybabel工具使用、前端翻译规范

- **[CLAUDE-SCRIPTS.md](../CLAUDE-SCRIPTS.md)** - 脚本创建与管理规范
  - 脚本存放位置、命名规范
  - 标准脚本模板、生命周期管理

---

## 📚 使用指南

操作指南和最佳实践文档：

### 部署与运维
- **[guides/RENDER_DEPLOY_GUIDE.md](guides/RENDER_DEPLOY_GUIDE.md)** - Render云端部署指南
  - Render平台部署流程
  - 环境变量配置
  - 常见部署问题解决

- **[guides/BACKUP_USAGE_GUIDE.md](guides/BACKUP_USAGE_GUIDE.md)** - 数据库备份使用指南
  - SP8D数据库备份流程
  - OVS数据库备份流程
  - 备份文件管理和恢复

- **[guides/BACKUP_CONFIGURATION_GUIDE.md](guides/BACKUP_CONFIGURATION_GUIDE.md)** - 备份配置指南
  - 备份系统配置
  - 自动化备份设置

### 开发管理
- **[guides/VERSION_MANAGEMENT_GUIDE.md](guides/VERSION_MANAGEMENT_GUIDE.md)** - 版本管理指南
  - 版本号规则
  - 版本发布流程
  - Git工作流程

- **[guides/ARCHITECTURE_SUGGESTION.md](guides/ARCHITECTURE_SUGGESTION.md)** - 架构建议
  - 系统架构设计建议
  - 模块化开发建议

### 前端开发
- **[guides/BUTTON_DESIGN_SYSTEM_GUIDE.md](guides/BUTTON_DESIGN_SYSTEM_GUIDE.md)** - 按钮设计系统指南
  - 按钮组件规范
  - 样式和交互规范
  - 使用示例

- **[guides/UNIVERSAL_COMPONENTS_CHANGELOG.md](guides/UNIVERSAL_COMPONENTS_CHANGELOG.md)** - 通用组件变更日志
  - 通用组件版本历史
  - 重要变更记录
  - 向后兼容性说明

---

## 🎨 前端规范文档

前端开发规范和设计系统（位于 `frontend-specs/`）：

- **[frontend-specs/设计系统文档.md](frontend-specs/设计系统文档.md)** - 完整设计系统文档
  - UI设计原则
  - 组件设计规范
  - 样式指南

- **[frontend-specs/设计系统总结.md](frontend-specs/设计系统总结.md)** - 设计系统总结
  - 设计系统概览
  - 核心设计决策

- **[frontend-specs/规范检查结果.md](frontend-specs/规范检查结果.md)** - 规范检查结果
  - 代码规范检查报告
  - 改进建议

---

## 📁 文档目录结构

```
PMA/
├── CLAUDE.md                           # 核心规范（主文档）
├── CLAUDE-COMPONENTS.md                # 组件规范
├── CLAUDE-DATABASE.md                  # 数据库规范
├── CLAUDE-I18N.md                      # 国际化规范
├── CLAUDE-SCRIPTS.md                   # 脚本管理规范
├── README.md                           # 项目说明
│
└── docs/
    ├── README.md                       # 本文档索引
    │
    ├── guides/                         # 使用指南
    │   ├── ARCHITECTURE_SUGGESTION.md
    │   ├── BACKUP_CONFIGURATION_GUIDE.md
    │   ├── BACKUP_USAGE_GUIDE.md
    │   ├── BUTTON_DESIGN_SYSTEM_GUIDE.md
    │   ├── RENDER_DEPLOY_GUIDE.md
    │   ├── UNIVERSAL_COMPONENTS_CHANGELOG.md
    │   └── VERSION_MANAGEMENT_GUIDE.md
    │
    ├── frontend-specs/                 # 前端规范
    │   ├── 设计系统文档.md
    │   ├── 设计系统总结.md
    │   └── 规范检查结果.md
    │
    └── archived/                       # 历史归档文档
        ├── summaries/                  # 任务总结
        ├── fixes/                      # 修复记录
        ├── analyses/                   # 分析报告
        ├── reports/                    # 报告文档
        └── misc/                       # 其他归档
```

---

## 🔍 快速查找

### 按主题查找

**翻译问题** → [CLAUDE-I18N.md](../CLAUDE-I18N.md)

**组件使用** → [CLAUDE-COMPONENTS.md](../CLAUDE-COMPONENTS.md)

**数据库操作** → [CLAUDE-DATABASE.md](../CLAUDE-DATABASE.md)

**脚本管理** → [CLAUDE-SCRIPTS.md](../CLAUDE-SCRIPTS.md)

**云端部署** → [guides/RENDER_DEPLOY_GUIDE.md](guides/RENDER_DEPLOY_GUIDE.md)

**数据备份** → [guides/BACKUP_USAGE_GUIDE.md](guides/BACKUP_USAGE_GUIDE.md)

**版本管理** → [guides/VERSION_MANAGEMENT_GUIDE.md](guides/VERSION_MANAGEMENT_GUIDE.md)

**设计系统** → [frontend-specs/设计系统文档.md](frontend-specs/设计系统文档.md)

### 按角色查找

**Claude AI 助手** → 必读所有 CLAUDE-*.md 文档

**新开发者入职** →
1. [README.md](../README.md) - 项目介绍
2. [CLAUDE.md](../CLAUDE.md) - 核心规范
3. [docs/README.md](README.md) - 文档索引（本文档）

**前端开发** →
1. [CLAUDE-COMPONENTS.md](../CLAUDE-COMPONENTS.md)
2. [CLAUDE-I18N.md](../CLAUDE-I18N.md)
3. [frontend-specs/设计系统文档.md](frontend-specs/设计系统文档.md)

**后端开发** →
1. [CLAUDE.md](../CLAUDE.md)
2. [CLAUDE-DATABASE.md](../CLAUDE-DATABASE.md)
3. [CLAUDE-SCRIPTS.md](../CLAUDE-SCRIPTS.md)

**运维部署** →
1. [guides/RENDER_DEPLOY_GUIDE.md](guides/RENDER_DEPLOY_GUIDE.md)
2. [guides/BACKUP_USAGE_GUIDE.md](guides/BACKUP_USAGE_GUIDE.md)
3. [CLAUDE-DATABASE.md](../CLAUDE-DATABASE.md)

---

## 📝 文档维护

### 更新规则

- **核心规范** (CLAUDE-*.md) - 重大变更需要更新版本号和更新日志
- **使用指南** (guides/) - 随功能更新及时维护
- **前端规范** (frontend-specs/) - 设计系统变更时更新

### 贡献指南

更新文档时请遵循：
1. 使用清晰的Markdown格式
2. 保持文档结构一致
3. 更新本索引文档的相关链接
4. 在主文档更新日志中记录重大变更

---

## 📊 文档统计

- **核心规范文档**: 5个（CLAUDE-*.md）
- **使用指南**: 7个（guides/）
- **前端规范**: 3个（frontend-specs/）
- **总计**: 15个活跃文档

**最后更新**: 2025-09-30
**文档索引版本**: v1.0.0