# 📸 发票预览组件设计方案

## 🎯 设计目标

模仿确认组件(`render_confirm_dialog`)的设计规范，创建一个标准化的发票预览组件：
- **按键标准化**：使用统一的按钮组件
- **四角弧形**：采用圆角设计，保持视觉一致性
- **文件信息显示**：展示详细的文件元数据
- **组件化**：可复用的宏定义

## 🏗️ 组件结构设计

### 1. 宏定义接口
```jinja2
{% macro render_invoice_preview_dialog(dialog_id='standardInvoicePreviewDialog') %}
```

### 2. HTML结构
```html
<div id="{{ dialog_id }}" class="standard-invoice-preview-dialog" style="display: none;">
    <div class="dialog-overlay"></div>
    <div class="dialog-container">
        <div class="dialog-content">
            <!-- 头部：标题和关闭按钮 -->
            <div class="dialog-header">
                <h5 class="dialog-title">
                    <i class="fas fa-file-invoice text-primary me-2"></i>
                    发票预览
                </h5>
                <button type="button" class="dialog-close-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <!-- 文件信息栏 -->
            <div class="file-info-bar">
                <div class="file-details">
                    <span class="file-name"></span>
                    <span class="file-meta"></span>
                </div>
                <div class="file-actions">
                    <button type="button" class="btn btn-outline-primary btn-sm download-btn">
                        <i class="fas fa-download me-1"></i>下载
                    </button>
                </div>
            </div>
            
            <!-- 图片预览区域 -->
            <div class="image-preview-container">
                <div class="image-wrapper">
                    <img class="preview-image" alt="发票预览" />
                    <div class="image-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>加载中...</span>
                    </div>
                    <div class="image-error" style="display: none;">
                        <i class="fas fa-exclamation-triangle text-danger"></i>
                        <span>图片加载失败</span>
                    </div>
                </div>
            </div>
            
            <!-- 底部操作栏 -->
            <div class="dialog-actions">
                {{ render_button('关闭', None, color='secondary', type='button', extra_class='dialog-close-btn', size='') }}
                {{ render_button('下载', None, color='primary', type='button', extra_class='dialog-download-btn', size='') }}
            </div>
        </div>
    </div>
</div>
```

## 🎨 样式设计

### 1. 主容器样式
```css
.standard-invoice-preview-dialog {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1070; /* 高于 Bootstrap 模态框和确认对话框 */
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(3px);
}

.dialog-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    cursor: pointer;
}

.dialog-container {
    position: relative;
    width: 90vw;
    max-width: 900px;
    max-height: 90vh;
    z-index: 1;
    animation: slideInScale 0.3s ease-out;
}
```

### 2. 内容区域样式
```css
.dialog-content {
    background: #fff;
    border-radius: 12px; /* 🔥 四角弧形 */
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    max-height: 90vh;
    overflow: hidden;
}

.dialog-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8f9fa;
    border-radius: 12px 12px 0 0; /* 顶部圆角 */
}

.dialog-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #495057;
}

.dialog-close-btn {
    background: none;
    border: none;
    padding: 0.25rem;
    cursor: pointer;
    color: #6c757d;
    font-size: 1.2rem;
    border-radius: 50%;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.dialog-close-btn:hover {
    background: #e9ecef;
    color: #495057;
}
```

### 3. 文件信息栏样式
```css
.file-info-bar {
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.file-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
    min-width: 0;
}

.file-name {
    font-weight: 600;
    color: #495057;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.file-meta {
    font-size: 0.875rem;
    color: #6c757d;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.file-actions {
    flex-shrink: 0;
}
```

### 4. 图片预览区域样式
```css
.image-preview-container {
    flex: 1;
    overflow: auto;
    padding: 1rem;
    background: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: center;
}

.image-wrapper {
    position: relative;
    max-width: 100%;
    max-height: 100%;
    text-align: center;
}

.preview-image {
    max-width: 100%;
    max-height: 60vh;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: transform 0.3s ease;
}

.preview-image:hover {
    transform: scale(1.02);
}

.image-loading,
.image-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem;
    color: #6c757d;
}

.image-loading i {
    font-size: 2rem;
    color: #007bff;
}

.image-error i {
    font-size: 2rem;
}
```

### 5. 底部操作栏样式
```css
.dialog-actions {
    padding: 1rem 1.5rem;
    border-top: 1px solid #e9ecef;
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    background: #f8f9fa;
    border-radius: 0 0 12px 12px; /* 底部圆角 */
}

/* 🔥 标准化按钮样式 - 与确认组件保持一致 */
.dialog-actions .btn {
    min-width: 80px;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.dialog-actions .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
```

### 6. 动画效果
```css
@keyframes slideInScale {
    0% {
        opacity: 0;
        transform: scale(0.8) translateY(-20px);
    }
    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

@keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

.standard-invoice-preview-dialog.show {
    animation: fadeIn 0.3s ease-out;
}
```

## 🔧 JavaScript功能

### 1. 核心功能函数
```javascript
/**
 * 显示发票预览对话框
 * @param {string} imagePath - 图片路径
 * @param {string} filename - 文件名
 * @param {Object} fileInfo - 文件信息 {size, type, uploadTime}
 * @param {string} dialogId - 对话框ID
 */
function showInvoicePreviewDialog(imagePath, filename, fileInfo = {}, dialogId = 'standardInvoicePreviewDialog') {
    const dialog = document.getElementById(dialogId);
    if (!dialog) {
        console.error(`发票预览对话框 ${dialogId} 不存在`);
        return;
    }
    
    // 更新文件信息
    updateFileInfo(dialog, filename, fileInfo);
    
    // 加载图片
    loadPreviewImage(dialog, imagePath, filename);
    
    // 设置下载链接
    setupDownloadAction(dialog, imagePath, filename);
    
    // 显示对话框
    dialog.style.display = 'flex';
    dialog.classList.add('show');
    
    // 设置关闭事件
    setupCloseEvents(dialog);
}

/**
 * 更新文件信息显示
 */
function updateFileInfo(dialog, filename, fileInfo) {
    const fileNameEl = dialog.querySelector('.file-name');
    const fileMetaEl = dialog.querySelector('.file-meta');
    
    fileNameEl.textContent = filename || '未知文件';
    
    const metaInfo = [];
    if (fileInfo.size) {
        metaInfo.push(`大小: ${formatFileSize(fileInfo.size)}`);
    }
    if (fileInfo.type) {
        metaInfo.push(`类型: ${fileInfo.type}`);
    }
    if (fileInfo.uploadTime) {
        metaInfo.push(`上传时间: ${formatDateTime(fileInfo.uploadTime)}`);
    }
    
    fileMetaEl.innerHTML = metaInfo.join(' • ');
}

/**
 * 加载预览图片
 */
function loadPreviewImage(dialog, imagePath, filename) {
    const imageWrapper = dialog.querySelector('.image-wrapper');
    const previewImage = dialog.querySelector('.preview-image');
    const loadingEl = dialog.querySelector('.image-loading');
    const errorEl = dialog.querySelector('.image-error');
    
    // 显示加载状态
    loadingEl.style.display = 'flex';
    errorEl.style.display = 'none';
    previewImage.style.display = 'none';
    
    // 加载图片
    previewImage.src = imagePath;
    previewImage.alt = filename || '发票预览';
    
    previewImage.onload = function() {
        loadingEl.style.display = 'none';
        previewImage.style.display = 'block';
    };
    
    previewImage.onerror = function() {
        loadingEl.style.display = 'none';
        errorEl.style.display = 'flex';
    };
}

/**
 * 设置下载功能
 */
function setupDownloadAction(dialog, imagePath, filename) {
    const downloadBtns = dialog.querySelectorAll('.download-btn, .dialog-download-btn');
    
    downloadBtns.forEach(btn => {
        btn.onclick = function() {
            const link = document.createElement('a');
            link.href = imagePath;
            link.download = filename || 'invoice';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        };
    });
}

/**
 * 设置关闭事件
 */
function setupCloseEvents(dialog) {
    const overlay = dialog.querySelector('.dialog-overlay');
    const closeBtns = dialog.querySelectorAll('.dialog-close-btn');
    
    // 点击遮罩层关闭
    overlay.onclick = () => hideInvoicePreviewDialog(dialog);
    
    // 点击关闭按钮
    closeBtns.forEach(btn => {
        btn.onclick = () => hideInvoicePreviewDialog(dialog);
    });
    
    // ESC键关闭
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            hideInvoicePreviewDialog(dialog);
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

/**
 * 隐藏对话框
 */
function hideInvoicePreviewDialog(dialog) {
    dialog.classList.remove('show');
    setTimeout(() => {
        dialog.style.display = 'none';
    }, 300);
}

/**
 * 工具函数：格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 工具函数：格式化日期时间
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
```

## 📋 使用示例

### 1. 在模板中引入组件
```jinja2
{% from 'macros/ui_helpers.html' import render_invoice_preview_dialog %}

<!-- 页面底部引入组件 -->
{{ render_invoice_preview_dialog('expenseInvoicePreview') }}
```

### 2. 调用预览功能
```javascript
// 简单调用
showInvoicePreviewDialog('/uploads/invoice123.jpg', 'invoice123.jpg');

// 带文件信息的调用
showInvoicePreviewDialog(
    '/uploads/invoice123.jpg', 
    'invoice123.jpg',
    {
        size: 1024000,
        type: 'image/jpeg',
        uploadTime: '2025-01-15 10:30:00'
    }
);
```

## ✨ 组件特性总结

### 🎯 设计统一性
- 与确认组件保持一致的视觉风格
- 统一的圆角设计(12px)
- 标准化的按钮组件
- 一致的动画效果

### 📱 用户体验
- 响应式设计，适配各种屏幕
- 平滑的加载和错误处理
- 键盘快捷键支持(ESC关闭)
- 图片缩放悬停效果

### 🔧 功能完整
- 详细的文件信息显示
- 下载功能集成
- 错误状态处理
- 可定制的对话框ID

### 🎨 视觉优化
- 毛玻璃背景效果
- 渐变色文件信息栏
- 阴影和圆角设计
- 统一的配色方案

这个组件设计既保持了与现有确认组件的一致性，又针对发票预览的特定需求进行了优化，提供了完整的用户体验和开发者友好的接口。