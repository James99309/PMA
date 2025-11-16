/**
 * 通用拖拽排序工具
 *
 * 基于 SortableJS 实现列表项拖拽排序功能
 * 支持自动AJAX保存、视觉反馈、错误处理和回滚
 *
 * 依赖:
 * - SortableJS 1.14.0+ (https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js)
 * - showTopNotification() 全局通知函数
 *
 * 使用示例:
 * ```javascript
 * initSortableList('tableBodyId', '/api/update-order', {
 *     handle: '.drag-handle',
 *     animation: 150,
 *     onSuccess: () => console.log('排序已保存'),
 *     onError: (error) => console.error('保存失败', error)
 * });
 * ```
 *
 * @author Claude AI
 * @date 2025-11-15
 */

/**
 * 初始化表格拖拽排序功能
 *
 * @param {string} tbodyId - 表格tbody元素的ID
 * @param {string} updateUrl - 更新排序的API端点URL
 * @param {Object} options - 可选配置参数
 * @param {string} [options.handle=null] - 拖拽手柄的CSS选择器，null表示整行可拖
 * @param {number} [options.animation=150] - 拖拽动画时长(毫秒)
 * @param {Function} [options.onSuccess=null] - 保存成功回调函数
 * @param {Function} [options.onError=null] - 保存失败回调函数
 * @param {Function} [options.extractId=null] - 自定义提取行ID的函数，默认读取data-id属性
 * @param {boolean} [options.autoReload=true] - 保存失败时是否自动刷新页面
 * @param {boolean} [options.updateRowNumbers=true] - 拖动后是否自动更新序号列（假设序号在第一个td中）
 * @returns {Sortable|null} Sortable实例，如果初始化失败返回null
 */
function initSortableList(tbodyId, updateUrl, options = {}) {
    // 参数验证
    if (!tbodyId || typeof tbodyId !== 'string') {
        console.error('[SortableList] tbody ID 参数无效:', tbodyId);
        return null;
    }

    if (!updateUrl || typeof updateUrl !== 'string') {
        console.error('[SortableList] 更新URL参数无效:', updateUrl);
        return null;
    }

    // 获取tbody元素
    const tbody = document.getElementById(tbodyId);
    if (!tbody) {
        console.error(`[SortableList] 找不到tbody元素: #${tbodyId}`);
        return null;
    }

    // 检查 SortableJS 是否已加载
    if (typeof Sortable === 'undefined') {
        console.error('[SortableList] SortableJS 未加载，请先引入 Sortable.min.js');
        return null;
    }

    // 合并默认配置
    const config = {
        handle: options.handle || null,           // 拖拽手柄选择器
        animation: options.animation || 150,      // 动画时长
        onSuccess: options.onSuccess || null,     // 成功回调
        onError: options.onError || null,         // 失败回调
        extractId: options.extractId || ((row) => row.dataset.id),  // ID提取函数
        autoReload: options.autoReload !== false, // 失败时自动刷新（默认true）
        updateRowNumbers: options.updateRowNumbers !== false  // 是否更新序号列（默认true）
    };

    /**
     * 更新表格行的序号列
     * 假设序号列是每行的第一个td，且包含拖拽手柄
     */
    function updateRowNumbers() {
        if (!config.updateRowNumbers) return;

        const rows = tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            // 找到第一个td（序号列）
            const firstCell = row.querySelector('td:first-child');
            if (firstCell) {
                // 查找序号文本节点（跳过拖拽手柄图标）
                const handle = firstCell.querySelector('.drag-handle');
                if (handle) {
                    // 移除旧序号，重新设置
                    const textNodes = Array.from(firstCell.childNodes).filter(
                        node => node.nodeType === Node.TEXT_NODE
                    );
                    textNodes.forEach(node => node.remove());

                    // 添加新序号
                    firstCell.appendChild(document.createTextNode((index + 1).toString()));
                } else {
                    // 如果没有拖拽手柄，直接替换文本内容
                    firstCell.textContent = (index + 1).toString();
                }
            }
        });
    }

    // 初始化 Sortable
    const sortable = new Sortable(tbody, {
        animation: config.animation,
        handle: config.handle,
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',
        chosenClass: 'sortable-chosen',

        // 拖拽结束事件
        onEnd: async function(evt) {
            // 立即更新序号列
            updateRowNumbers();

            // 收集新的排序数据
            const rows = tbody.querySelectorAll('tr');
            const items = [];

            rows.forEach((row, index) => {
                try {
                    const id = config.extractId(row);
                    if (id) {
                        items.push({
                            id: parseInt(id),
                            order: index + 1
                        });
                    }
                } catch (error) {
                    console.error('[SortableList] 提取行ID失败:', error, row);
                }
            });

            if (items.length === 0) {
                console.warn('[SortableList] 没有找到有效的行数据');
                return;
            }

            console.log('[SortableList] 准备保存排序:', items);

            // 发送AJAX请求保存排序
            try {
                // 获取CSRF Token
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

                const response = await fetch(updateUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ items: items })
                });

                const result = await response.json();

                if (result.success) {
                    // 保存成功
                    console.log('[SortableList] 排序保存成功');

                    if (typeof showTopNotification === 'function') {
                        showTopNotification('排序已保存', 'success', 3000);
                    }

                    // 执行成功回调
                    if (config.onSuccess) {
                        config.onSuccess(result);
                    }
                } else {
                    // 保存失败
                    console.error('[SortableList] 排序保存失败:', result.message || result);

                    if (typeof showTopNotification === 'function') {
                        showTopNotification(
                            result.message || '保存排序失败，请刷新重试',
                            'error',
                            5000
                        );
                    }

                    // 执行失败回调
                    if (config.onError) {
                        config.onError(result);
                    }

                    // 自动刷新恢复
                    if (config.autoReload) {
                        setTimeout(() => {
                            location.reload();
                        }, 2000);
                    }
                }
            } catch (error) {
                // 网络错误或其他异常
                console.error('[SortableList] 保存排序时发生错误:', error);

                if (typeof showTopNotification === 'function') {
                    showTopNotification('保存失败，请检查网络连接', 'error', 5000);
                }

                // 执行失败回调
                if (config.onError) {
                    config.onError(error);
                }

                // 自动刷新恢复
                if (config.autoReload) {
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                }
            }
        }
    });

    console.log(`[SortableList] 已初始化拖拽排序: #${tbodyId}`);
    return sortable;
}
