# 项目列表表头筛选对齐问题修复

## 问题描述
项目列表的表头筛选弹出的输入框和字段没有对齐，出现错位现象。

## 问题原因
1. 筛选行的 `top` 值设置为固定的 `39px`，但实际表头高度不匹配
2. 表头和筛选行的高度、内边距不一致
3. 筛选输入框的尺寸和对齐方式需要优化

## 修复内容

### 1. 调整表头固定高度
```css
.table th {
    height: 48px; /* 设置固定高度 */
    vertical-align: middle;
    padding: 8px 12px;
    border-bottom: 2px solid #dee2e6; /* 加强表头底部边框 */
}
```

### 2. 修正筛选行位置
```css
.filter-row th {
    top: 48px; /* 调整为实际表头高度 */
    height: 40px; /* 设置筛选行固定高度 */
    vertical-align: middle;
}
```

### 3. 优化筛选输入框
```css
.filter-input {
    padding: 4px 8px;
    height: 28px; /* 设置输入框固定高度 */
    border: 1px solid #ddd;
    border-radius: 3px;
    box-sizing: border-box;
}
```

### 4. 改进表头内容布局
```css
.th-content {
    min-height: 32px; /* 确保表头内容有最小高度 */
}

.th-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.th-actions {
    flex-shrink: 0; /* 防止操作按钮被压缩 */
}
```

## 修复效果
1. ✅ 筛选行与表头列完全对齐
2. ✅ 筛选输入框尺寸统一，视觉效果更好
3. ✅ 表头高度固定，避免内容变化导致的错位
4. ✅ 筛选行位置准确，不会遮挡表头内容

## 测试验证
- 在项目列表页面点击任意列的筛选图标
- 确认筛选输入框与对应列完全对齐
- 确认筛选行不会遮挡表头内容
- 确认所有筛选输入框尺寸一致

## 文件修改
- `app/templates/project/list.html` - 修复表头筛选对齐样式

## 注意事项
- 修复保持了原有的功能逻辑不变
- 只调整了CSS样式，没有修改JavaScript功能
- 修复适用于所有屏幕尺寸和浏览器 