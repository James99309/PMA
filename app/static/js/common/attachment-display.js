/**
 * 附件显示工具函数
 * 用于生成统一的附件图标方块 HTML
 *
 * 使用场景：日志附件、公告附件等
 *
 * 使用示例：
 * ```javascript
 * // 基本用法 - 只显示图标，点击预览
 * const html = renderAttachmentIcon({
 *     filename: 'document.pdf',
 *     url: '/api/preview/123',
 *     onPreview: "previewFile('url', 'filename')"
 * });
 *
 * // 带删除按钮
 * const html = renderAttachmentIcon({
 *     filename: 'image.jpg',
 *     url: '/api/preview/456',
 *     onPreview: "previewFile('url', 'filename')",
 *     showDelete: true,
 *     onDelete: "deleteAttachment(456)"
 * });
 * ```
 */

/**
 * 根据文件名获取文件类型图标
 * @param {string} filename - 文件名
 * @returns {Object} {icon: 图标名称, colorClass: 颜色类名}
 */
function getFileTypeIcon(filename) {
    const ext = (filename || '').toLowerCase();

    if (/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/i.test(ext)) {
        return { icon: 'image', colorClass: 'text-primary' };
    } else if (/\.pdf$/i.test(ext)) {
        return { icon: 'picture_as_pdf', colorClass: 'text-red-500' };
    } else if (/\.(doc|docx)$/i.test(ext)) {
        return { icon: 'description', colorClass: 'text-blue-500' };
    } else if (/\.(xls|xlsx)$/i.test(ext)) {
        return { icon: 'table_chart', colorClass: 'text-green-500' };
    } else if (/\.(ppt|pptx)$/i.test(ext)) {
        return { icon: 'slideshow', colorClass: 'text-orange-500' };
    } else if (/\.(zip|rar|7z|tar|gz)$/i.test(ext)) {
        return { icon: 'folder_zip', colorClass: 'text-amber-500' };
    } else if (/\.(txt|md|json|xml|csv)$/i.test(ext)) {
        return { icon: 'article', colorClass: 'text-slate-500' };
    } else {
        return { icon: 'attach_file', colorClass: 'text-slate-400' };
    }
}

/**
 * 转义 HTML 属性值中的特殊字符
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的字符串
 */
function escapeHtmlAttr(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * 渲染附件图标方块
 * @param {Object} options - 配置选项
 * @param {string} options.filename - 文件名
 * @param {string} options.url - 文件 URL（用于预览）
 * @param {string} options.onPreview - 预览点击事件（字符串形式的 JS 代码）
 * @param {boolean} [options.showDelete=false] - 是否显示删除按钮
 * @param {string} [options.onDelete] - 删除点击事件（字符串形式的 JS 代码）
 * @param {string} [options.id] - 可选的数据 ID
 * @returns {string} HTML 字符串
 */
function renderAttachmentIcon(options) {
    const { filename, url, onPreview, showDelete = false, onDelete, id } = options;
    const { icon, colorClass } = getFileTypeIcon(filename);

    // 转义 HTML 属性值
    const safeFilename = escapeHtmlAttr(filename);
    const safeOnPreview = escapeHtmlAttr(onPreview);
    const safeOnDelete = escapeHtmlAttr(onDelete);

    // 基础图标方块
    let html = `
        <div class="relative group inline-block"${id ? ` data-id="${id}"` : ''}>
            <div class="w-8 h-8 rounded bg-slate-100 dark:bg-slate-700 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform"
                 onclick="${safeOnPreview}"
                 title="${safeFilename}">
                <span class="material-symbols-outlined text-lg ${colorClass}">${icon}</span>
            </div>`;

    // 可选的删除按钮
    if (showDelete && onDelete) {
        html += `
            <button type="button" onclick="event.stopPropagation(); ${safeOnDelete}"
                class="absolute -top-1 -right-1 w-4 h-4 bg-slate-500 hover:bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                title="删除">
                <span class="material-symbols-outlined text-white" style="font-size: 10px;">close</span>
            </button>`;
    }

    html += `
        </div>`;

    return html;
}

/**
 * 渲染附件列表
 * @param {Array} attachments - 附件数组 [{filename, url, id?}, ...]
 * @param {Object} options - 配置选项
 * @param {Function|string} options.onPreview - 预览函数，接收 (url, filename) 或字符串模板
 * @param {boolean} [options.showDelete=false] - 是否显示删除按钮
 * @param {Function|string} [options.onDelete] - 删除函数，接收 (id) 或字符串模板
 * @param {string} [options.label] - 附件区域标题
 * @returns {string} HTML 字符串
 */
function renderAttachmentList(attachments, options = {}) {
    if (!attachments || attachments.length === 0) {
        return '';
    }

    const { onPreview, showDelete = false, onDelete, label } = options;

    let html = '';

    // 可选的标题
    if (label) {
        html += `<div class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">${label}</div>`;
    }

    html += '<div class="flex flex-wrap gap-2">';

    attachments.forEach((att, index) => {
        // 转义 JavaScript 字符串中的特殊字符（用于 onclick 中的字符串参数）
        const escapeJsString = (str) => {
            if (!str) return '';
            return String(str)
                .replace(/\\/g, '\\\\')
                .replace(/'/g, "\\'")
                .replace(/"/g, '\\"')
                .replace(/\n/g, '\\n')
                .replace(/\r/g, '\\r');
        };

        const url = att.url || att.file_url || '';
        const filename = att.filename || '';

        // 构建预览事件
        let previewEvent;
        if (typeof onPreview === 'function') {
            previewEvent = `(${onPreview.toString()})(${JSON.stringify(url)}, ${JSON.stringify(filename)})`;
        } else if (typeof onPreview === 'string') {
            previewEvent = onPreview
                .replace('{url}', escapeJsString(url))
                .replace('{filename}', escapeJsString(filename))
                .replace('{index}', index);
        } else {
            previewEvent = '';
        }

        // 构建删除事件
        let deleteEvent = '';
        if (showDelete && onDelete) {
            if (typeof onDelete === 'function') {
                deleteEvent = `(${onDelete.toString()})(${att.id || index})`;
            } else if (typeof onDelete === 'string') {
                deleteEvent = onDelete
                    .replace('{id}', att.id || '')
                    .replace('{index}', index);
            }
        }

        html += renderAttachmentIcon({
            filename: att.filename,
            url: att.url || att.file_url,
            onPreview: previewEvent,
            showDelete: showDelete,
            onDelete: deleteEvent,
            id: att.id
        });
    });

    html += '</div>';

    return html;
}

// 导出为全局函数
window.getFileTypeIcon = getFileTypeIcon;
window.renderAttachmentIcon = renderAttachmentIcon;
window.renderAttachmentList = renderAttachmentList;
