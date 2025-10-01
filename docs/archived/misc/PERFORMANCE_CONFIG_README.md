# 角色绩效配置系统

## 🎯 功能概述

角色绩效配置系统是一个灵活的绩效管理解决方案，允许为不同角色配置专属的绩效考核方案，完全解决了原有系统硬编码绩效指标的问题。

## ✨ 核心特性

### 🔧 灵活配置
- **角色级别配置**: 每个角色可以有独立的绩效配置方案
- **动态字段管理**: 可添加/编辑/删除绩效项目
- **多种计算方法**: 求和、平均、计数、最大值、最小值、自定义公式
- **四级统计范围**: 个人、部门、企业、系统

### 📊 智能评估
- **多级合格标准**: 优秀、良好、合格三级阈值设置
- **权重配置**: 支持加权综合评分
- **达成率计算**: 自动计算目标达成情况
- **颜色等级**: 直观的视觉化评级展示

### 🎨 用户友好
- **拖拽排序**: 项目顺序可拖拽调整
- **公式模板**: 预定义常用计算公式
- **实时预览**: 配置效果即时预览
- **响应式设计**: 完美适配桌面和移动端

## 📁 文件结构

```
角色绩效配置系统/
├── 数据库迁移/
│   └── migrations/versions/add_performance_config_tables.py
├── 数据模型/
│   └── app/models/performance_config.py
├── 控制器/
│   └── app/views/performance_config.py
├── 前端界面/
│   ├── app/templates/performance/role_config.html
│   └── app/templates/performance/role_config_optimized.html
├── 部署脚本/
│   ├── setup_performance_config.py
│   ├── test_performance_config.py
│   └── PERFORMANCE_CONFIG_README.md (本文件)
└── 设计文档/
    ├── design_role_performance_config.sql
    └── performance_config_ui_design.md
```

## 🚀 快速部署

### 1. 执行数据库迁移
```bash
# 方法一：使用Flask-Migrate（推荐）
flask db upgrade

# 方法二：使用部署脚本
python setup_performance_config.py
```

### 2. 配置权限
系统会自动为以下角色配置绩效管理权限：
- **admin**: 完整权限（系统级）
- **hrdp_manager**: 完整权限（系统级）
- **ceo**: 查看权限（系统级）
- **sales_director**: 查看权限（部门级）
- **service_manager**: 查看权限（部门级）
- **channel_manager**: 查看权限（部门级）

### 3. 验证安装
```bash
# 运行测试脚本
python test_performance_config.py
```

## 📊 数据库设计

### 核心表结构

#### 1. performance_metrics_definition (绩效指标定义)
- 定义系统中所有可用的绩效指标
- 包含指标代码、名称、类型、单位等

#### 2. role_performance_config (角色绩效配置主表)
- 每个角色的绩效配置方案
- 包含配置名称、说明、创建者等

#### 3. role_performance_items (绩效项目配置)
- 具体的绩效考核项目
- 包含计算方法、合格标准、显示配置等

#### 4. performance_formula_templates (公式模板)
- 预定义的常用计算公式
- 支持用户自定义公式

#### 5. role_performance_access (数据访问权限)
- 控制不同角色的数据访问范围
- 支持个人、部门、企业、系统四级权限

## 🔧 使用指南

### 访问配置界面
1. 确保用户有 `performance_management` 编辑权限
2. 访问 `/performance/config/` 或从用户菜单进入
3. 选择要配置的角色

### 创建绩效配置方案
1. **选择角色**: 从左侧角色列表选择
2. **填写基本信息**: 
   - 配置方案名称
   - 数据访问范围
   - 配置说明
3. **添加绩效项目**:
   - 点击"添加项目"按钮
   - 填写项目基本信息
   - 设置统计配置（范围、计算方法）
   - 定义合格标准（优秀/良好/合格阈值）
   - 配置显示选项（单位、小数位数、图标）
4. **保存配置**: 点击"保存配置"按钮

### 使用公式模板
系统提供常用公式模板：
- **销售金额统计**: `SUM(pricing_orders.pricing_total_amount) WHERE status = 'approved'`
- **客户增长率**: `(当月新增客户数 - 上月新增客户数) / 上月新增客户数 * 100`
- **综合评分**: `sales_amount * 0.4 + implant_amount * 0.3 + customer_count * 100 * 0.3`

## 🛠️ 高级配置

### 自定义计算公式
支持以下函数和运算符：
- **函数**: SUM, AVG, COUNT, MAX, MIN
- **运算符**: +, -, *, /, (, )
- **变量**: 支持引用数据表字段

### 统计范围说明
- **个人**: 仅统计用户个人数据
- **部门**: 统计用户所在部门的所有数据
- **企业**: 统计用户所在企业的所有数据
- **系统**: 统计系统中的全部数据

### 权限级别配置
- **system**: 系统级权限，可查看所有数据
- **company**: 企业级权限，可查看同企业数据
- **department**: 部门级权限，可查看同部门数据
- **personal**: 个人级权限，仅可查看个人数据

## 🔍 API端点

### 主要API接口
- `GET /performance/config/api/roles` - 获取可配置角色列表
- `GET /performance/config/api/role/<role_code>` - 获取指定角色配置
- `POST /performance/config/api/role/<role_code>` - 保存角色配置
- `GET /performance/config/api/metrics` - 获取绩效指标列表
- `GET /performance/config/api/formula-templates` - 获取公式模板

### 请求示例
```javascript
// 保存角色配置
fetch('/performance/config/api/role/sales_director', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        config_name: '销售总监绩效方案',
        access_scope: 'department',
        description: '主要考核销售团队整体业绩',
        items: [
            {
                item_name: '团队销售金额',
                item_code: 'team_sales',
                stat_scope: 'department',
                calculation_method: 'sum',
                qualified_threshold: 200,
                good_threshold: 300,
                excellent_threshold: 500
            }
        ]
    })
})
```

## 🧪 测试说明

### 运行测试
```bash
python test_performance_config.py
```

### 测试覆盖
- 数据库连接和表结构
- 数据模型CRUD操作
- API端点可用性
- 绩效计算服务
- 权限配置完整性

## 📋 维护指南

### 添加新的绩效指标
1. 在 `performance_metrics_definition` 表中添加新指标
2. 更新相关的计算服务
3. 在配置界面中添加选项

### 扩展计算方法
1. 在 `ConfigurablePerformanceService` 中添加新方法
2. 更新前端选择器选项
3. 添加相应的公式模板

### 性能优化建议
- 对大数据量查询使用索引
- 考虑缓存频繁查询的配置
- 异步计算复杂的绩效指标

## ⚠️ 注意事项

### 数据安全
- 所有配置操作需要相应权限
- 支持数据访问范围控制
- 记录配置变更日志

### 兼容性
- 与现有绩效系统完全兼容
- 不影响现有绩效数据
- 支持渐进式迁移

### 备份建议
- 定期备份配置数据
- 测试环境验证新配置
- 保留配置变更历史

## 🆘 故障排除

### 常见问题
1. **配置保存失败**: 检查用户权限和数据库连接
2. **API返回401/403**: 确认用户已登录且有相应权限
3. **页面加载异常**: 检查蓝图注册和模板路径
4. **数据计算错误**: 验证计算公式和数据源配置

### 日志查看
```bash
# 查看应用日志
tail -f app.log | grep performance

# 查看数据库日志
tail -f postgresql.log | grep performance
```

## 🔄 版本信息

- **当前版本**: v1.0.0
- **兼容版本**: PMA系统 v2.1.0+
- **更新日期**: 2025-01-XX

## 📞 技术支持

如需技术支持，请提供：
1. 错误日志和截图
2. 操作步骤描述
3. 系统环境信息
4. 用户角色和权限信息

---

*角色绩效配置系统 - 让绩效管理更灵活、更智能！*