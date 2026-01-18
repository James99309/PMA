# 旧规格系统禁用使用指南

## 📋 快速参考

旧规格系统（ProductCodeField）支持通过特性开关 `LEGACY_SPEC_SYSTEM_ENABLED` 来启用或禁用。

### 当前状态
- **默认状态**: `LEGACY_SPEC_SYSTEM_ENABLED=true`（启用）
- **禁用状态**: `LEGACY_SPEC_SYSTEM_ENABLED=false`（禁用）

---

## 🚀 启用旧规格系统（默认）

### 方式1：直接启动应用（推荐用于开发）

```bash
python run.py
```

或使用启动脚本：

```bash
./start.sh
```

**效果**：
- ✅ 规格字典UI显示
- ✅ 编辑规格按钮显示
- ✅ 规格字段管理功能可用
- ✅ 所有ProductCodeField API正常工作

---

## 🔒 禁用旧规格系统

### 方式1：临时禁用（当前会话）

#### macOS/Linux
```bash
export LEGACY_SPEC_SYSTEM_ENABLED=false
python run.py
```

或使用启动脚本：

```bash
LEGACY_SPEC_SYSTEM_ENABLED=false ./start.sh
```

#### Windows (PowerShell)
```powershell
$env:LEGACY_SPEC_SYSTEM_ENABLED="false"
python run.py
```

#### Windows (CMD)
```cmd
set LEGACY_SPEC_SYSTEM_ENABLED=false
python run.py
```

---

### 方式2：永久禁用（修改配置文件）

编辑 `.env` 文件，添加：

```bash
LEGACY_SPEC_SYSTEM_ENABLED=false
```

然后启动应用：

```bash
python run.py
```

或：

```bash
./start.sh
```

---

## ✅ 禁用后的表现

当 `LEGACY_SPEC_SYSTEM_ENABLED=false` 时：

### 前端表现

**产品分类管理页面**：
- ❌ 规格字典按钮隐藏
- ❌ 编辑规格按钮隐藏
- ❌ 规格字段管理区域隐藏
- ❌ 分类规格管理模态框隐藏

**规格相关页面**：
- ❌ 规格字典模态框不显示
- ❌ 规格选项管理模态框不显示

### 后端表现

**API调用**：
- 所有ProductCodeField相关API返回 **HTTP 503 Service Unavailable**

**示例响应**：
```json
{
  "success": false,
  "source": "legacy_spec_system",
  "error": "Legacy specification system is disabled"
}
```

**HTTP状态码**: `503 Service Unavailable`

### 系统功能

- ✅ 产品创建/编辑正常
- ✅ 报价单系统正常
- ✅ 订单系统正常
- ✅ 其他所有功能正常
- ❌ 仅旧规格系统功能不可用

---

## 🔄 快速切换

### 启用 → 禁用

```bash
# 1. 停止当前应用（Ctrl+C）

# 2. 禁用并重启
export LEGACY_SPEC_SYSTEM_ENABLED=false
python run.py
```

### 禁用 → 启用

```bash
# 1. 停止当前应用（Ctrl+C）

# 2. 启用并重启
unset LEGACY_SPEC_SYSTEM_ENABLED
python run.py
```

或直接启动（使用默认值）：

```bash
python run.py
```

---

## 📊 系统架构

### 启用旧规格系统（LEGACY_SPEC_SYSTEM_ENABLED=true）

```
用户界面
├── 规格字典按钮 ✅
├── 编辑规格按钮 ✅
└── 规格字段管理 ✅

后端系统
├── ProductCodeField API ✅
├── ProductCodeFieldOption API ✅
└── 产品编码生成（旧系统）✅
```

### 禁用旧规格系统（LEGACY_SPEC_SYSTEM_ENABLED=false）

```
用户界面
├── 规格字典按钮 ❌ 隐藏
├── 编辑规格按钮 ❌ 隐藏
└── 规格字段管理 ❌ 隐藏

后端系统
├── ProductCodeField API ❌ 返回503
├── ProductCodeFieldOption API ❌ 返回503
└── 产品编码生成 ✅ 转向新系统

业务系统
├── 产品创建 ✅ 正常
├── 报价单系统 ✅ 正常
└── 订单系统 ✅ 正常
```

---

## 🔧 配置说明

### config.py 中的定义

```python
# 旧规格系统特性开关 - 控制ProductCodeField API和UI的可用性
# [LegacySpecSystem] 此配置用于隐藏和控制旧规格系统，支持未来的完全移除
LEGACY_SPEC_SYSTEM_ENABLED = os.getenv('LEGACY_SPEC_SYSTEM_ENABLED', 'true').lower() == 'true'
```

**参数说明**：
- `os.getenv('LEGACY_SPEC_SYSTEM_ENABLED', 'true')`
  - 从环境变量读取 `LEGACY_SPEC_SYSTEM_ENABLED`
  - 如果未设置，使用默认值 `'true'`
  - 字符串值转换为小写后与 `'true'` 比较

**有效值**：
- `true` / `True` / `TRUE` → 启用（任何其他值都视为禁用）
- `false` / `False` / `FALSE` → 禁用
- 空值 → 使用默认值（启用）

---

## 📋 前端隐藏机制

所有旧规格系统UI都使用条件渲染控制：

```html
{% if config.LEGACY_SPEC_SYSTEM_ENABLED %}
  <!-- 规格UI 只有当系统启用时才显示 -->
{% endif %}
```

**隐藏的UI元素**：

1. **规格字典按钮** - tw_category_management.html L73-79
2. **编辑规格按钮** - tw_category_management.html L81-88
3. **规格字段管理区域** - tw_category_management.html L188-244
4. **分类规格管理模态框** - tw_category_management.html L463-526
5. **规格字典模态框** - tw_spec_dictionary_modal.html L35-357
6. **规格选项模态框** - tw_spec_options_modal.html L31-197

---

## 🛡️ 后端防护机制

所有ProductCodeField相关API都使用 `@feature_flag` 装饰器保护：

```python
from app.utils.legacy_decorators import feature_flag

@blueprint.route('/api/product-code-fields/<int:category_id>')
@feature_flag('LEGACY_SPEC_SYSTEM_ENABLED')  # ← 特性开关
def get_product_code_fields(category_id):
    # API实现...
```

**当系统禁用时**：
- 装饰器拦截请求
- 返回 HTTP 503 Service Unavailable
- 响应包含明确的源标识 `source: 'legacy_spec_system'`

---

## 🎯 使用场景

### 场景1：开发和测试（推荐启用）

```bash
# 需要测试旧规格系统功能
python run.py
```

或：

```bash
./start.sh  # 选择选项1（本地存储）
```

**优势**：
- 完整的功能可用
- 可以测试规格管理功能
- 可以验证产品编码生成

---

### 场景2：验证新系统完整性（推荐禁用）

```bash
# 验证新系统是否完全替代旧系统
export LEGACY_SPEC_SYSTEM_ENABLED=false
python run.py
```

**验证点**：
- ✅ 产品创建是否正常
- ✅ 报价单系统是否正常
- ✅ 订单系统是否正常
- ✅ 产品编码是否正确生成
- ✅ UI中规格相关功能是否都隐藏
- ✅ 调用旧API是否返回503

---

### 场景3：生产环境部署

```bash
# 在.env中设置
LEGACY_SPEC_SYSTEM_ENABLED=false

# 启动应用
python run.py
```

或在部署脚本中：

```bash
export LEGACY_SPEC_SYSTEM_ENABLED=false
./start.sh
```

**好处**：
- 用户界面干净，没有弃用功能
- API调用旧系统会立即返回错误（便于追踪）
- 为未来完全移除旧系统做准备

---

## 🔍 验证禁用是否生效

### 检查1：前端UI隐藏

打开浏览器访问 `http://localhost:5011/product_management/product_category`

检查项：
- [ ] 看不到"规格字典"按钮
- [ ] 看不到"编辑规格"按钮
- [ ] 规格字段管理区域不可见
- [ ] 没有任何规格相关的UI

### 检查2：后端API返回503

```bash
curl -X GET http://localhost:5011/api/product-code-fields/1

# 预期响应（403错误或503）：
# {
#   "success": false,
#   "source": "legacy_spec_system",
#   "error": "Legacy specification system is disabled"
# }
# HTTP状态码: 503
```

### 检查3：浏览器控制台

打开浏览器开发者工具（F12），查看Console选项卡：
- [ ] 没有关于规格系统的JavaScript错误
- [ ] 没有找不到规格相关元素的警告

### 检查4：配置确认

```bash
# 检查环境变量是否设置
echo $LEGACY_SPEC_SYSTEM_ENABLED

# 输出应为：false

# 或检查.env文件
grep LEGACY_SPEC_SYSTEM_ENABLED .env
```

---

## 📚 相关文件

### 核心配置文件

| 文件 | 说明 |
|-----|------|
| `config.py` L223 | 特性开关定义 |
| `app/utils/legacy_decorators.py` | 特性开关装饰器实现 |

### 前端文件（包含条件渲染）

| 文件 | 隐藏内容 |
|-----|--------|
| `app/templates/product_code/tw_category_management.html` | 规格字典按钮、编辑规格按钮、规格字段管理UI、分类规格模态框 |
| `app/templates/components/tw_spec_dictionary_modal.html` | 规格字典模态框 |
| `app/templates/components/product/tw_spec_options_modal.html` | 规格选项模态框 |

### 后端API文件（包含@feature_flag）

| 文件 | 说明 |
|-----|------|
| `app/routes/product_code.py` | 所有ProductCodeField API都受保护 |

---

## ❓ 常见问题

### Q1: 设置了环境变量但规格UI仍然显示？

**A**: 需要重启应用。环境变量仅在应用启动时读取。

```bash
# 1. 停止应用（Ctrl+C）
# 2. 设置环境变量并重启
export LEGACY_SPEC_SYSTEM_ENABLED=false
python run.py
```

### Q2: 禁用旧系统后，现有的产品编码会消失吗？

**A**: 不会。产品编码保存在数据库中，仅禁用了管理界面和API。

- ✅ 现有产品编码值保持不变
- ✅ 产品编码在报价单中正常显示
- ✅ 历史数据完整保留

### Q3: 可以在运行时动态切换吗？

**A**: 不可以。特性开关在应用启动时读取，需要重启应用才能生效。

### Q4: 禁用旧系统后，新产品还能创建吗？

**A**: 可以。产品创建不依赖旧规格系统UI。

- ✅ 产品创建功能正常
- ✅ 使用新规格模板系统
- ✅ 编码生成自动使用新系统

### Q5: 如何在Docker中使用？

**A**: 在docker-compose.yml或启动命令中设置环境变量：

```yaml
services:
  pma:
    environment:
      - LEGACY_SPEC_SYSTEM_ENABLED=false
```

或：

```bash
docker run -e LEGACY_SPEC_SYSTEM_ENABLED=false ...
```

---

## 🔗 相关文档

- [LEGACY_SPEC_DEPENDENCIES.md](./LEGACY_SPEC_DEPENDENCIES.md) - 旧规格系统依赖清单
- [LEGACY_SPEC_TESTING_GUIDE.md](./LEGACY_SPEC_TESTING_GUIDE.md) - 测试验证指南

---

## 📝 最后更新

- **日期**: 2026-01-17
- **版本**: 1.0
- **状态**: 已验证有效 ✅
