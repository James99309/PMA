/**
 * 通用拖拽排序工具
 *
 * 使用方式：
 * initDragSort({
 *     containerId: 'categoryList',      // 容器元素ID
 *     itemSelector: '.category-item',   // 可拖拽项选择器
 *     dataIdAttr: 'categoryId',         // data属性名（用于获取ID）
 *     onOrderChange: async (items) => { // 顺序变化回调
 *         // items: [{id: 1, order: 0}, {id: 2, order: 1}, ...]
 *     },
 *     draggingClass: 'dragging',        // 拖拽中的CSS类（可选）
 *     dragOverClass: 'drag-over',       // 拖拽悬停的CSS类（可选）
 *     skipDomMove: false                // 跳过DOM移动（可选，用于Alpine/Vue等框架）
 * });
 *
 * HTML 结构要求：
 * <div id="containerId">
 *     <div class="item-class" draggable="true" data-category-id="1">...</div>
 *     <div class="item-class" draggable="true" data-category-id="2">...</div>
 * </div>
 *
 * CSS 建议：
 * .dragging { opacity: 0.5; background: rgba(19, 127, 236, 0.1); }
 * .drag-over { border-top: 2px solid #137fec; }
 */
function initDragSort(options) {
    const {
        containerId,
        itemSelector,
        dataIdAttr = 'id',
        onOrderChange,
        draggingClass = 'dragging',
        dragOverClass = 'drag-over',
        skipDomMove = false  // 跳过 DOM 移动（用于 Alpine/Vue 等框架渲染的内容）
    } = options;

    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`[drag-sort] Container #${containerId} not found`);
        return null;
    }

    // 防止重复初始化
    if (container.dataset.dragSortInitialized) {
        console.warn(`[drag-sort] Container #${containerId} already initialized`);
        return null;
    }
    container.dataset.dragSortInitialized = 'true';

    let draggedItem = null;
    let dropTarget = null;  // 记录放置目标（skipDomMove 模式用）

    // 为每个可拖拽项添加事件监听
    function attachEvents(item) {
        // 防止同一元素重复绑定事件
        if (item.dataset.dragEventsAttached) {
            console.log('[drag-sort] Events already attached to item:', item.dataset[dataIdAttr]);
            return;
        }
        item.dataset.dragEventsAttached = 'true';

        console.log('[drag-sort] Attaching events to item:', item.dataset[dataIdAttr], item);

        item.addEventListener('dragstart', function(e) {
            console.log('[drag-sort] dragstart on:', this.dataset[dataIdAttr]);
            draggedItem = this;
            this.classList.add(draggingClass);
            e.dataTransfer.effectAllowed = 'move';
            // 设置拖拽数据（某些浏览器需要）
            e.dataTransfer.setData('text/plain', this.dataset[dataIdAttr] || '');
        });

        item.addEventListener('dragend', function() {
            console.log('[drag-sort] dragend on:', this.dataset[dataIdAttr]);
            this.classList.remove(draggingClass);
            // 清除所有 drag-over 状态
            container.querySelectorAll(itemSelector).forEach(i =>
                i.classList.remove(dragOverClass)
            );

            // 使用 requestAnimationFrame 确保 DOM 已更新后再收集顺序
            requestAnimationFrame(() => {
                console.log('[drag-sort] requestAnimationFrame callback, draggedItem:', draggedItem?.dataset[dataIdAttr]);
                // 收集新顺序并触发回调
                if (onOrderChange && draggedItem) {
                    let items = [];

                    if (skipDomMove && dropTarget) {
                        // skipDomMove 模式：根据原始顺序和放置目标计算新顺序
                        console.log('[drag-sort] skipDomMove mode - calculating new order from dropTarget');
                        const allItems = [...container.querySelectorAll(itemSelector)];
                        const { draggedIndex, droppedIndex } = dropTarget;

                        // 构建新顺序数组
                        const ids = allItems.map(item => parseInt(item.dataset[dataIdAttr]));
                        const draggedId = ids[draggedIndex];

                        // 从原数组中移除被拖拽项
                        ids.splice(draggedIndex, 1);
                        // 插入到新位置
                        const insertIndex = draggedIndex < droppedIndex ? droppedIndex : droppedIndex;
                        ids.splice(insertIndex, 0, draggedId);

                        items = ids.map((id, index) => ({ id, order: index }));
                        console.log('[drag-sort] Calculated new order:', items);
                    } else {
                        // 普通模式：从 DOM 读取顺序
                        container.querySelectorAll(itemSelector).forEach((item, index) => {
                            const id = item.dataset[dataIdAttr];
                            console.log('[drag-sort] Collecting item:', id, 'at index:', index);
                            if (id) {
                                items.push({ id: parseInt(id), order: index });
                            }
                        });
                    }

                    console.log('[drag-sort] Calling onOrderChange with:', items);
                    onOrderChange(items);
                } else {
                    console.log('[drag-sort] Not calling onOrderChange - onOrderChange:', !!onOrderChange, 'draggedItem:', !!draggedItem);
                }
                draggedItem = null;
                dropTarget = null;
            });
        });

        item.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (this !== draggedItem && draggedItem) {
                console.log('[drag-sort] dragover on:', this.dataset[dataIdAttr]);
                this.classList.add(dragOverClass);
            }
        });

        item.addEventListener('dragleave', function() {
            this.classList.remove(dragOverClass);
        });

        item.addEventListener('drop', function(e) {
            e.preventDefault();
            console.log('[drag-sort] drop on:', this.dataset[dataIdAttr], 'draggedItem:', draggedItem?.dataset[dataIdAttr]);
            if (this !== draggedItem && draggedItem) {
                const allItems = [...container.querySelectorAll(itemSelector)];
                const draggedIndex = allItems.indexOf(draggedItem);
                const droppedIndex = allItems.indexOf(this);
                console.log('[drag-sort] Moving from index', draggedIndex, 'to', droppedIndex);

                if (skipDomMove) {
                    // 不移动 DOM，只记录放置目标（让框架处理渲染）
                    dropTarget = { element: this, draggedIndex, droppedIndex };
                    console.log('[drag-sort] skipDomMove mode - recorded drop target');
                } else {
                    // 直接移动 DOM
                    if (draggedIndex < droppedIndex) {
                        this.parentNode.insertBefore(draggedItem, this.nextSibling);
                    } else {
                        this.parentNode.insertBefore(draggedItem, this);
                    }
                    console.log('[drag-sort] DOM move completed');
                }
            }
            this.classList.remove(dragOverClass);
        });
    }

    // 初始化现有元素
    container.querySelectorAll(itemSelector).forEach(attachEvents);

    // 返回一个对象，允许重新初始化（用于动态添加的元素）
    return {
        refresh: function() {
            container.querySelectorAll(itemSelector).forEach(attachEvents);
        },
        destroy: function() {
            // 移除事件监听器标记（允许重新初始化）
            container.querySelectorAll(itemSelector).forEach(item => {
                item.removeAttribute('draggable');
                delete item.dataset.dragEventsAttached;
            });
            delete container.dataset.dragSortInitialized;
        }
    };
}

// 如果使用模块系统
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initDragSort };
}
