# 旧规格系统解耦 - 测试与验证指南

**文档**: 测试验证清单
**更新日期**: 2026-01-17
**范围**: ProductCodeField (旧规格系统) 完整功能验证
**目的**: 确保架构解耦成功且无副作用

---

## 🎯 测试概览

### 双模式测试策略

本测试验证在**两种配置**下进行，确保：
1. **启用模式** (`LEGACY_SPEC_SYSTEM_ENABLED=true`) - 系统正常工作
2. **禁用模式** (`LEGACY_SPEC_SYSTEM_ENABLED=false`) - 系统平滑降级

---

## ✅ 启用状态测试 (LEGACY_SPEC_SYSTEM_ENABLED=true)

### 前置条件
```bash
# 设置启用模式
export LEGACY_SPEC_SYSTEM_ENABLED=true

# 启动应用
./start.sh
# 或
python run.py
```

### 1️⃣ 前端UI验证

#### 1.1 规格管理按钮可见性
```
页面: 产品分类管理页面 (产品代码模块)
位置: 分类列表 → 选择分类 → "编辑规格"按钮

✅ 检查点:
□ "编辑规格"按钮显示
□ 按钮可点击（enabled状态）
□ 点击后打开分类规格模态框
□ 浏览器控制台无JavaScript错误
```

#### 1.2 子分类规格管理UI
```
页面: 产品分类管理页面
操作: 选择分类 → 选择子分类 → "添加规格"按钮

✅ 检查点:
□ "添加规格"按钮显示
□ 按钮可点击
□ 点击后打开规格添加表单
□ 规格名称可选择
□ 规格编码选项可配置
```

#### 1.3 规格字段列表
```
页面: 子分类详情右侧 - 规格字段表格

✅ 检查点:
□ 规格字段表格显示
□ 字段列表包含: 名称、编码、来源、状态等列
□ 可编辑和删除按钮显示
□ 拖拽排序手柄显示
□ 继承字段显示"继承"标签
```

### 2️⃣ 后端API验证

#### 2.1 规格字段创建API
```bash
curl -X POST http://localhost:5000/product-code/api/fields \
  -H "Content-Type: application/json" \
  -d '{
    "subcategory_id": 1,
    "name": "测试规格",
    "is_required": true,
    "use_in_code": true
  }'

✅ 预期响应:
{
  "success": true,
  "message": "规格创建成功",
  "data": {
    "id": 123,
    "name": "测试规格",
    "position": 14,
    "is_required": true,
    "use_in_code": true
  }
}

✅ 检查点:
□ HTTP 200 响应
□ success: true
□ 返回创建的规格ID
□ 日志包含 [LegacySpecSystem] 标记
```

#### 2.2 规格字段获取API
```bash
curl http://localhost:5000/product-code/api/fields/123

✅ 预期响应:
{
  "success": true,
  "data": {
    "id": 123,
    "name": "测试规格",
    "use_in_code": true,
    "is_required": true
  }
}

✅ 检查点:
□ HTTP 200 响应
□ 返回完整字段信息
□ 无错误消息
```

#### 2.3 规格字段更新API
```bash
curl -X PUT http://localhost:5000/product-code/api/fields/123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新规格",
    "is_required": false,
    "use_in_code": true
  }'

✅ 预期响应:
{
  "success": true,
  "message": "规格更新成功"
}

✅ 检查点:
□ HTTP 200 响应
□ success: true
□ 字段已更新
□ 日志记录更新操作
```

#### 2.4 规格字段删除API
```bash
curl -X DELETE http://localhost:5000/product-code/api/fields/123

✅ 预期响应:
{
  "success": true,
  "message": "规格删除成功"
}

✅ 检查点:
□ HTTP 200 响应
□ success: true
□ 字段已删除
□ 日志记录删除操作
```

### 3️⃣ 功能验证

#### 3.1 产品创建流程
```
页面: 产品管理 → 添加产品
操作: 创建新产品，选择子分类

✅ 检查点:
□ 子分类选择成功
□ 规格字段自动加载
□ 规格快照生成成功
□ products.code_definition_snapshot 包含规格数据
□ 创建完成，无错误提示
```

#### 3.2 产品编辑流程
```
页面: 产品管理 → 编辑产品
操作: 修改产品规格

✅ 检查点:
□ 现有规格字段加载
□ 规格值可修改
□ 快照重新生成
□ 编辑完成，无错误
```

#### 3.3 报价单创建
```
页面: 报价管理 → 创建报价
操作: 选择产品，创建报价

✅ 检查点:
□ 产品选择成功
□ 规格信息从快照读取
□ 规格选项显示正确
□ 报价创建成功
```

### 4️⃣ 日志验证

#### 4.1 应用日志检查
```bash
# 查看应用日志 (实时)
tail -f logs/pma.log

# 搜索旧规格系统日志
grep "[LegacySpecSystem]" logs/pma.log

✅ 预期日志:
[LegacySpecSystem] CategoryManager initialized
[LegacySpecSystem] Creating product code field
[LegacySpecSystem] Product code field created: id=123, name=规格名称
[LegacySpecSystem] Updating product code field: id=123
[LegacySpecSystem] Deleting product code field: id=123
```

#### 4.2 浏览器控制台检查
```javascript
// 打开浏览器开发者工具 (F12)
// 查看Console选项卡

✅ 预期日志:
[LegacySpec] CategoryManager initialized
[LegacySpec] SpecFieldManager initialized
[LegacySpec] Generating product snapshot with legacy spec fields

✅ 检查点:
□ 无红色错误信息
□ [LegacySpec] 前缀日志显示
□ 无undefined引用错误
```

---

## ❌ 禁用状态测试 (LEGACY_SPEC_SYSTEM_ENABLED=false)

### 前置条件
```bash
# 设置禁用模式
export LEGACY_SPEC_SYSTEM_ENABLED=false

# 重启应用
./start.sh
# 或
python run.py
```

### 1️⃣ 前端UI验证

#### 1.1 规格管理UI隐藏
```
页面: 产品分类管理页面
检查: "编辑规格"按钮

✅ 检查点:
□ "编辑规格"按钮不显示
□ 分类/子分类基本管理按钮仍显示
□ 规格字段表格不显示
□ 规格管理相关UI完全隐藏
```

#### 1.2 信息提示显示
```
页面: 产品分类管理页面
位置: 规格字段区域

✅ 检查点:
□ 显示提示信息框
□ 文本: "规格管理已迁移至规格模板系统，请使用新系统进行规格定义"
□ 样式正确（蓝色提示框）
□ 不影响分类管理功能
```

#### 1.3 JavaScript错误检查
```
工具: 浏览器开发者工具 (F12 → Console)
检查: 所有错误和警告

✅ 检查点:
□ 无JavaScript错误（红色信息）
□ 无undefined引用错误
□ [LegacySpec] 警告日志显示
□ 应用功能正常
```

### 2️⃣ 后端API验证

#### 2.1 规格字段API返回503
```bash
curl http://localhost:5000/product-code/api/fields \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'

✅ 预期响应:
HTTP/1.1 503 Service Unavailable
{
  "success": false,
  "source": "legacy_spec_system",
  "error": "Legacy specification system is disabled",
  "message": "旧规格系统已禁用，请使用新规格模板系统"
}

✅ 检查点:
□ HTTP 503 状态码
□ source: legacy_spec_system (清晰标识)
□ success: false
□ 错误信息清晰
```

#### 2.2 所有ProductCodeField API返回503
```bash
# 逐个测试所有API

# GET
curl http://localhost:5000/product-code/api/fields/1
curl http://localhost:5000/product-code/api/category/1/fields

# POST
curl -X POST http://localhost:5000/product-code/api/fields \
  -H "Content-Type: application/json" \
  -d '{...}'

# PUT
curl -X PUT http://localhost:5000/product-code/api/fields/1 \
  -H "Content-Type: application/json" \
  -d '{...}'

# DELETE
curl -X DELETE http://localhost:5000/product-code/api/fields/1

✅ 检查点:
□ 所有API都返回503
□ 所有响应包含 source: legacy_spec_system
□ 无内部服务器错误 (500)
□ 错误消息一致
```

### 3️⃣ 功能验证

#### 3.1 产品创建仍正常
```
页面: 产品管理 → 添加产品
操作: 创建新产品

✅ 检查点:
□ 产品分类选择正常
□ 子分类选择正常
□ 新产品创建成功
□ 快照生成（即使无规格字段）
□ 无任何错误提示
```

#### 3.2 报价单创建仍正常
```
页面: 报价管理 → 创建报价
操作: 创建报价

✅ 检查点:
□ 产品选择正常
□ 使用现有快照数据
□ 规格信息显示（来自快照）
□ 报价创建成功
□ 无任何错误
```

#### 3.3 产品查询仍正常
```
操作: 查询产品列表、产品详情

✅ 检查点:
□ 产品列表加载正常
□ 产品详情显示正常
□ 快照数据可读
□ 无API调用失败
```

### 4️⃣ UI交互验证

#### 4.1 尝试添加规格（应被拦截）
```
页面: 产品分类管理 → 选择子分类
操作: 点击"添加规格"按钮

预期: 由于UI隐藏，按钮不存在，无法点击

如果能点击 (UI未正确隐藏):
✅ 检查点:
□ 提示信息: "规格系统已禁用，请使用新规格模板系统"
□ 操作被取消
□ 浏览器控制台有警告日志
□ 无实际规格被创建
```

#### 4.2 直接调用JavaScript方法
```javascript
// 打开浏览器控制台，尝试直接调用

CategoryManager.showAddFieldModal()

✅ 检查点:
□ 提示信息显示
□ 表单不打开
□ 控制台输出警告: [LegacySpec] Attempt to add field...
□ 不执行实际操作
```

### 5️⃣ 日志验证

#### 5.1 应用日志
```bash
grep "[LegacySpecSystem]" logs/pma.log

✅ 预期日志:
[LegacySpecSystem] API "create_field" called but system is disabled
[LegacySpecSystem] API "get_product_code_fields" called but system is disabled
```

#### 5.2 浏览器日志
```javascript
// F12 → Console

✅ 预期日志:
[LegacySpec] CategoryManager initialized with legacySpecSystemEnabled=false
[LegacySpec] Attempt to open category fields when legacy system is disabled
[LegacySpec] Legacy spec system is disabled, field loading skipped
```

---

## 📊 完整性检查清单

### 数据库
- [ ] ProductCodeField 表存在且数据完整
- [ ] ProductCodeFieldOption 表存在且数据完整
- [ ] product_codes 表存在且数据完整
- [ ] 快照数据完整保存

### 特性开关
- [ ] config.LEGACY_SPEC_SYSTEM_ENABLED 设置正确
- [ ] 环境变量可覆盖默认值
- [ ] 两种模式都能正确切换

### 前端
- [ ] 启用时UI显示完整
- [ ] 禁用时UI完全隐藏
- [ ] 没有JavaScript错误
- [ ] 控制台日志标记正确

### 后端
- [ ] API 装饰器工作正确
- [ ] 启用时返回正常响应
- [ ] 禁用时返回503
- [ ] 错误响应标记正确

### 文档
- [ ] LEGACY_SPEC_DEPENDENCIES.md 完整
- [ ] 代码标记 [LegacySpecSystem] 已添加
- [ ] 日志前缀 [LegacySpecSystem] 已统一
- [ ] API文档已更新

---

## 🔍 常见问题排查

### Q1: 启用模式下规格按钮不显示
```
原因: 模板条件逻辑错误
检查:
1. config.LEGACY_SPEC_SYSTEM_ENABLED = True
2. {% if config.LEGACY_SPEC_SYSTEM_ENABLED %} 条件正确
3. 重新加载页面（清除缓存）
4. 检查浏览器控制台是否有模板错误
```

### Q2: 禁用模式下API返回500而非503
```
原因: 装饰器未正确应用
检查:
1. @feature_flag('LEGACY_SPEC_SYSTEM_ENABLED') 装饰器存在
2. 装饰器在路由之后、函数之前
3. import legacy_decorators 已正确添加
4. 重启应用
```

### Q3: 快照数据为空
```
原因: 产品创建时快照生成失败
检查:
1. ProductCodeField 查询是否成功
2. JSON序列化是否成功
3. 检查日志中是否有 [LegacySpecSystem] 错误
4. 验证 product.code_definition_snapshot 字段
```

### Q4: 报价单规格显示不正确
```
原因: 快照格式与报价单解析不匹配
检查:
1. 快照JSON格式是否正确
2. 报价单解析代码是否正确
3. 字段映射是否正确
4. 查看数据库 product.code_definition_snapshot 内容
```

---

## 📋 测试执行计划

### 第一轮: 启用模式完整测试
**时间**: 约30分钟
**步骤**:
1. 设置 LEGACY_SPEC_SYSTEM_ENABLED=true
2. 运行前端UI检查（5分钟）
3. 运行API测试（10分钟）
4. 运行功能验证（10分钟）
5. 查看日志（5分钟）

### 第二轮: 禁用模式完整测试
**时间**: 约30分钟
**步骤**:
1. 设置 LEGACY_SPEC_SYSTEM_ENABLED=false
2. 重启应用
3. 运行UI隐藏检查（5分钟）
4. 运行API 503验证（10分钟）
5. 运行功能兼容性测试（10分钟）
6. 查看日志（5分钟）

### 第三轮: 模式切换测试
**时间**: 约20分钟
**步骤**:
1. 从启用切换到禁用
2. 验证UI隐藏
3. 验证API返回503
4. 从禁用切换回启用
5. 验证UI显示
6. 验证API恢复正常

### 总预计时间: 80分钟 (约1.5小时)

---

## ✅ 验证通过标准

### 全部通过
所有以下条件满足时，视为验证**完全通过** ✅
- [ ] 启用模式: UI显示完整，所有API正常，日志正确
- [ ] 禁用模式: UI完全隐藏，所有API返回503，日志正确
- [ ] 功能测试: 产品创建、报价单创建、数据查询都正常
- [ ] 日志检查: [LegacySpecSystem] 标记显示正确
- [ ] 错误处理: 无内部服务器错误，无JavaScript异常

### 条件通过
以下情况下视为**有条件通过**，需要进一步调查 ⚠️
- UI有部分隐藏不完全
- API有个别异常
- 日志标记不完整
- 性能有轻微下降

### 验证失败
出现以下情况视为验证**失败** ❌
- 启用模式功能中断
- 禁用模式报价单无法创建
- 数据丢失或损坏
- 频繁出现内部服务器错误

---

## 📝 测试报告模板

```markdown
# 旧规格系统解耦 - 测试报告

**测试日期**: 2026-01-17
**测试人员**:
**环境**: 本地 / 云端
**系统版本**: 1.21.18

## 启用模式测试 (LEGACY_SPEC_SYSTEM_ENABLED=true)

### UI验证
- [ ] 规格管理按钮显示正常
- [ ] 子分类规格管理UI正常
- [ ] 规格字段列表正常

### API验证
- [ ] 创建API正常
- [ ] 读取API正常
- [ ] 更新API正常
- [ ] 删除API正常

### 功能验证
- [ ] 产品创建正常
- [ ] 报价单创建正常
- [ ] 数据查询正常

### 日志验证
- [ ] [LegacySpecSystem] 日志出现
- [ ] 无JavaScript错误
- [ ] 无内部服务器错误

## 禁用模式测试 (LEGACY_SPEC_SYSTEM_ENABLED=false)

### UI验证
- [ ] 规格管理UI完全隐藏
- [ ] 提示信息显示正确
- [ ] 无JavaScript错误

### API验证
- [ ] 所有API返回503
- [ ] source: legacy_spec_system 标识正确
- [ ] 无内部服务器错误

### 功能验证
- [ ] 产品创建仍正常
- [ ] 报价单创建仍正常
- [ ] 数据查询仍正常

### 日志验证
- [ ] 系统禁用日志显示
- [ ] 无异常错误
- [ ] [LegacySpec] 警告日志显示

## 总体评估

**测试结果**: ✅ 通过 / ⚠️ 有条件通过 / ❌ 失败

**问题列表**:
(如有)

**建议**:
(如有)

**签名**: ________________  **日期**: __________
```

---

**测试指南完成** ✅

下一步: 按照此指南执行完整测试验证
