
# Cursor 修改说明：产品管理页面滚动与错位修复

## 🎯 目标效果

1. **产品表格横向可滚动**，以便展示全部字段。
2. **操作图标列固定右侧，且垂直联动同步上下滚动（或页面不滚动）**。
3. 页面 **不允许垂直滚动**，用户通过 **“每页数量选择器”**决定展示数量。
4. 所有表格行高度严格一致，避免错位。

---

## 🧩 技术要点

### ✅ 实现建议

- `table-container` 应该：
  - 保持 `overflow-x: auto; overflow-y: hidden;`
  - 高度根据 `per-page` 自动增长，禁用内部垂直滚动。

- `action-body` 中行高必须与 `product-table tr` 完全一致（同 `height` 和 `padding`）。

- JavaScript 中同步滚动（`scrollTop`）逻辑可以 **去掉**，因为不再使用内部 `scroll`。

---

## 🔨 必修修改点

### 1. HTML & CSS

- 移除 `.body-container` 和 `.action-body` 的 `overflow: auto` 或 `overflow: hidden`。
- 统一 `.product-table tr` 和 `.action-table tr` 使用 `min-height: 42px;` 和 `box-sizing: border-box;`。
- `.action-body` 不再使用 `transform: translateY(...)` 方式，而是自然由父容器高度撑开。

### 2. JS

- **移除** `setupScrollSync()` 函数及其 `scrollTop` 同步逻辑。
- 所有加载数据、渲染按钮函数（如 `loadProducts()`）应确保：
  - `tbody#product-list` 和 `tbody#action-buttons` 渲染数量一致；
  - 所有 `<tr>` 高度一致；
  - 若为奇偶行配色，保持两个表格样式完全统一。

---

## ✅ 成品效果示例代码片段（CSS）：

```css
.product-table tr,
.action-table tr {
  height: 42px;
  box-sizing: border-box;
}

.body-scroll {
  overflow-x: auto;
  overflow-y: hidden;
}

.table-container {
  overflow-x: auto;
  overflow-y: hidden;
  height: auto;
}
```

---

## ⚠️ 注意事项

- 不再通过 JS 控制滚动同步。
- 所有对齐依赖于：
  - HTML 行结构保持一致；
  - CSS 设定高度 & 盒模型一致；
  - 避免嵌套滚动容器。
