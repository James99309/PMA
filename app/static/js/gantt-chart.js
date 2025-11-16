/**
 * 通用甘特图组件
 * 基于研发产品甘特图演示提取的通用JavaScript类
 */

class GanttChart {
    constructor(options) {
        // 基础配置
        this.containerId = options.containerId || 'ganttChart';
        this.objectType = options.objectType || 'rd_product';
        this.objectId = options.objectId;
        this.currentStage = options.currentStage;
        this.stageHistory = options.stageHistory || [];
        this.stageConfig = options.stageConfig || {};
        this.stageColors = {}; // 每个阶段的颜色配置
        this.canEdit = options.canEdit || false;
        this.csrfToken = options.csrfToken || 
            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
            document.querySelector('input[name="csrf_token"]')?.value;
        this.apiEndpoints = options.apiEndpoints || {};
        this.currentUserId = options.currentUserId;
        this.creatorId = options.creatorId;
        this.isCreator = this.currentUserId && this.creatorId && this.currentUserId === this.creatorId;
        
        // 初始化状态
        this.currentDate = new Date();
        this.selectedTask = null;
        this.tasks = {};
        this.isDetailsVisible = false;
        this.currentDetailTaskId = null;
        
        // 事件处理函数引用（用于防止重复绑定）
        this.detailClickHandler = null;
        
        // 初始化组件
        this.init();
    }

    /**
     * 初始化甘特图组件
     */
    init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`甘特图容器未找到: ${this.containerId}`);
            return;
        }

        // 从JSON配置中加载数据
        this.loadDataFromScript();
        
        // 生成任务数据
        this.generateTasksFromStageConfig();
        
        // 绑定事件
        this.bindEvents();
        
        // 渲染甘特图
        this.renderGantt();
        
        // 更新今日线
        this.updateTodayLine();

        // 加载已保存的子阶段（里程碑）
        this.loadSubStages();
        
        console.log('甘特图组件初始化完成', this);
    }

    /**
     * 从页面脚本标签中加载配置数据
     */
    loadDataFromScript() {
        const scriptElement = document.getElementById(`gantt-data-${this.containerId}`);
        if (scriptElement) {
            try {
                const data = JSON.parse(scriptElement.textContent);
                Object.assign(this, data);
            } catch (e) {
                console.warn('甘特图数据解析失败，使用默认配置', e);
            }
        }
    }

    /**
     * 从阶段配置生成任务数据
     */
    generateTasksFromStageConfig() {
        this.tasks = {};
        
        // 生成主阶段
        if (this.stageConfig.mainStages) {
            this.stageConfig.mainStages.forEach(stage => {
                // 保存颜色配置（如果提供）
                if (stage.colors) {
                    this.stageColors[stage.key] = stage.colors;
                }
                const sd = this.getStageStartDate(stage.key);
                const ed = this.getStageEndDate(stage.key);
                this.tasks[stage.key] = {
                    name: stage.name || stage.zh_name,
                    type: 'main',
                    status: this.getStageStatus(stage.key, sd, ed),
                    progress: this.getStageProgress(stage.key),
                    owner: this.getStageOwner(stage.key),
                    description: stage.description,
                    order: stage.order,
                    startDate: sd,
                    endDate: ed
                };
            });
        }

        // 子阶段将通过API动态加载，目前不生成假数据
    }

    /**
     * 获取阶段进度（主阶段）
     * 优先从stage_history记录的progress读取；若该阶段已完成则返回100；当前阶段无记录则返回0
     */
    getStageProgress(stageKey) {
        const history = this.stageHistory || [];
        const rec = history.find(h => h.stage === stageKey);
        if (rec && typeof rec.progress !== 'undefined' && rec.progress !== null) {
            const p = parseInt(rec.progress);
            return isNaN(p) ? 0 : Math.max(0, Math.min(100, p));
        }
        if (this.isStageCompleted(stageKey)) return 100;
        if (stageKey === this.currentStage) return 0;
        return 0;
    }

    /**
     * 加载子阶段数据（从API获取或本地存储）
     */
    async loadSubStages() {
        try {
            if (!this.objectId) return;
            const url = `/product-management/api/rd-products/${this.objectId}/stages`;
            const res = await fetch(url, { credentials: 'include' });
            const result = await res.json();
            if (!result.success) {
                console.warn('加载子阶段失败:', result.message);
                return;
            }

            // 注入到任务映射
            (result.stages || []).forEach(s => {
                const taskId = String(s.id);
                this.tasks[taskId] = {
                    id: taskId,
                    name: s.name,
                    type: 'sub',
                    parent: s.stage_key,
                    owner: s.owner || '',
                    startDate: s.start_date ? new Date(s.start_date) : null,
                    endDate: s.end_date ? new Date(s.end_date) : null,
                    progress: parseInt(s.progress || 0),
                    status: s.status || 'planned',
                    description: s.description || ''
                };
            });

            // 重新渲染视图
            this.renderTaskList();
            this.renderGantt();
        } catch (e) {
            console.error('加载子阶段时发生错误:', e);
        }
    }

    /**
     * 获取阶段状态
     */
    getStageStatus(stageKey, startDate = null, endDate = null) {
        const history = this.stageHistory || [];
        const currentStageHistory = history.find(h => h.stage === stageKey);
        // 若没有计划时间且没有历史记录，视为未设置
        const hasPlan = !!(startDate || endDate || (currentStageHistory && (currentStageHistory.plannedStart || currentStageHistory.plannedEnd)));
        if (!hasPlan) return '';

        if (stageKey === this.currentStage) {
            return 'in-progress';
        } else if (this.isStageCompleted(stageKey)) {
            return 'completed';
        } else {
            return 'pending';
        }
    }

    /**
     * 判断阶段是否已完成
     */
    isStageCompleted(stageKey) {
        const stageOrder = this.getStageOrder(stageKey);
        const currentOrder = this.getStageOrder(this.currentStage);
        return stageOrder < currentOrder;
    }

    /**
     * 获取阶段顺序
     */
    getStageOrder(stageKey) {
        const stage = this.stageConfig.mainStages?.find(s => s.key === stageKey);
        return stage ? stage.order : 0;
    }

    /**
     * 获取阶段负责人
     */
    getStageOwner(stageKey) {
        const history = this.stageHistory || [];
        const stageHistory = history.find(h => h.stage === stageKey);
        return stageHistory?.username || '未分配';
    }
    
    /**
     * 获取创建者信息
     */
    getCreatorInfo() {
        // 从甘特图数据中获取创建者信息
        return {
            name: this.creatorName || '未知创建者',
            id: this.creatorId || null
        };
    }
    
    /**
     * 根据文件类型获取图标
     */
    getFileIcon(fileType) {
        if (!fileType) return 'fa-file';
        
        const type = fileType.toLowerCase();
        if (type.includes('pdf')) return 'fa-file-pdf';
        if (type.includes('doc') || type.includes('docx')) return 'fa-file-word';
        if (type.includes('xls') || type.includes('xlsx')) return 'fa-file-excel';
        if (type.includes('ppt') || type.includes('pptx')) return 'fa-file-powerpoint';
        if (type.includes('txt')) return 'fa-file-alt';
        if (type.includes('zip') || type.includes('rar')) return 'fa-file-archive';
        if (type.includes('image') || type.includes('jpg') || type.includes('png') || type.includes('gif')) return 'fa-file-image';
        
        return 'fa-file';
    }

    /**
     * 获取阶段开始时间
     */
    getStageStartDate(stageKey) {
        const history = this.stageHistory || [];
        const stageHistory = history.find(h => h.stage === stageKey);
        if (stageHistory?.plannedStart) {
            return new Date(stageHistory.plannedStart);
        }
        if (stageHistory?.startDate) {
            return new Date(stageHistory.startDate);
        }
        // 不再自动生成默认时间，保留为空，待人工录入
        return null;
    }

    /**
     * 获取阶段结束时间
     */
    getStageEndDate(stageKey) {
        const history = this.stageHistory || [];
        const stageHistory = history.find(h => h.stage === stageKey);
        if (stageHistory?.plannedEnd) {
            return new Date(stageHistory.plannedEnd);
        }
        if (stageHistory?.endDate) {
            return new Date(stageHistory.endDate);
        }
        // 不再自动生成默认时间，保留为空，待人工录入
        return null;
    }

    /**
     * 获取相对日期偏移
     */
    getDateOffset(monthOffset, dayOffset) {
        const date = new Date();
        date.setMonth(date.getMonth() + monthOffset);
        date.setDate(date.getDate() + dayOffset);
        return date;
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 月份导航
        this.bindMonthNavigation();
        
        // 任务列表事件
        this.bindTaskListEvents();

        // 右侧甘特条事件
        this.bindGanttBarEvents();
        
        // 详情面板事件
        this.bindDetailsEvents();
        
        // 全局交互事件
        this.bindGlobalEvents();
        
        // 添加阶段按钮
        this.bindAddStageEvent();
    }

    // 通用确认对话框（使用标准确认组件 stageProgressConfirmDialog）
    showStandardConfirmDialog(options) {
        const dialogId = options.dialogId || 'stageProgressConfirmDialog';
        const dialog = document.getElementById(dialogId);
        if (!dialog) {
            console.error('找不到确认对话框容器:', dialogId);
            // 如果没有标准确认组件，降级为原生确认
            if (confirm(options.message || '确认执行此操作？')) {
                if (typeof options.onConfirm === 'function') options.onConfirm();
            }
            return;
        }

        const titleElement = dialog.querySelector('.message-title');
        const textElement = dialog.querySelector('.message-text');
        const iconElement = dialog.querySelector('.dialog-icon');
        const confirmBtn = dialog.querySelector('.dialog-confirm-btn');
        const cancelBtn = dialog.querySelector('.dialog-cancel-btn');

        if (titleElement) titleElement.textContent = options.title || '确认操作';
        if (textElement) textElement.innerHTML = (options.message || '').replace(/\n/g, '<br>');
        if (iconElement) {
            iconElement.className = 'dialog-icon ' + this.getIconClassByType(options.type || 'warning');
        }
        if (confirmBtn) {
            confirmBtn.textContent = options.confirmText || '确认';
            confirmBtn.className = confirmBtn.className.replace(/btn-\w+/g, '');
            confirmBtn.classList.add('btn', 'btn-' + this.getButtonColorByType(options.type || 'warning'), 'dialog-confirm-btn');
        }
        if (cancelBtn) {
            cancelBtn.textContent = options.cancelText || '取消';
        }

        const confirmHandler = () => {
            this.hideConfirmDialog(dialogId);
            if (typeof options.onConfirm === 'function') options.onConfirm();
        };
        const cancelHandler = () => {
            this.hideConfirmDialog(dialogId);
        };

        if (confirmBtn) {
            confirmBtn.replaceWith(confirmBtn.cloneNode(true));
            const newConfirmBtn = dialog.querySelector('.dialog-confirm-btn');
            newConfirmBtn.addEventListener('click', confirmHandler);
        }
        if (cancelBtn) {
            cancelBtn.replaceWith(cancelBtn.cloneNode(true));
            const newCancelBtn = dialog.querySelector('.dialog-cancel-btn');
            newCancelBtn.addEventListener('click', cancelHandler);
        }
        const overlay = dialog.querySelector('.dialog-overlay');
        if (overlay) {
            overlay.replaceWith(overlay.cloneNode(true));
            const newOverlay = dialog.querySelector('.dialog-overlay');
            newOverlay.addEventListener('click', cancelHandler);
        }

        // 显示
        this.showConfirmDialogDisplay(dialogId);
    }

    hideConfirmDialog(dialogId) {
        const dialog = document.getElementById(dialogId);
        if (!dialog) return;
        dialog.classList.remove('show');
        setTimeout(() => {
            dialog.style.display = 'none';
        }, 300);
    }

    showConfirmDialogDisplay(dialogId) {
        const dialog = document.getElementById(dialogId);
        if (!dialog) return;
        dialog.style.display = 'flex';
        setTimeout(() => dialog.classList.add('show'), 10);
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.hideConfirmDialog(dialogId);
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    getIconClassByType(type) {
        switch (type) {
            case 'danger': return 'fas fa-times-circle text-danger';
            case 'success': return 'fas fa-check-circle text-success';
            case 'info': return 'fas fa-info-circle text-info';
            case 'warning':
            default: return 'fas fa-exclamation-triangle text-warning';
        }
    }

    getButtonColorByType(type) {
        switch (type) {
            case 'danger': return 'danger';
            case 'success': return 'success';
            case 'info': return 'info';
            case 'warning':
            default: return 'warning';
        }
    }

    /**
     * 绑定右侧甘特条点击事件，点击打开对应阶段详情
     */
    bindGanttBarEvents() {
        const barsContainer = this.container.querySelector('#ganttBars');
        if (!barsContainer) return;
        barsContainer.addEventListener('click', (e) => {
            const bar = e.target.closest('.gantt-bar');
            if (!bar) return;
            const taskId = bar.dataset.taskId;
            if (!taskId) return;
            this.selectTask(taskId);
            this.jumpToTaskDate(taskId);
            this.showTaskDetails(taskId);
        });
    }

    /**
     * 绑定月份导航事件
     */
    bindMonthNavigation() {
        const prevBtn = this.container.querySelector('#prevMonth');
        const nextBtn = this.container.querySelector('#nextMonth');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.currentDate.setMonth(this.currentDate.getMonth() - 1);
                this.renderGantt();
                this.updateTodayLine();
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.currentDate.setMonth(this.currentDate.getMonth() + 1);
                this.renderGantt();
                this.updateTodayLine();
            });
        }
    }

    /**
     * 绑定任务列表事件
     */
    bindTaskListEvents() {
        const taskList = this.container.querySelector('#taskList');
        if (!taskList) return;

        taskList.addEventListener('click', (e) => {
            const taskItem = e.target.closest('.task-item');
            if (!taskItem) return;

            const taskId = taskItem.dataset.taskId;
            
            if (e.target.classList.contains('expand-icon') || e.target.closest('.expand-icon')) {
                // 展开/收起子任务
                this.toggleTaskExpansion(taskId);
            } else if (!e.target.closest('.task-actions')) {
                // 点击任务名称或任务区域：选中并打开详情
                this.selectTask(taskId);
                this.jumpToTaskDate(taskId);
                this.showTaskDetails(taskId);
            }
        });

        // 任务操作按钮事件
        taskList.addEventListener('click', (e) => {
            // 修复事件委托问题（如果点击的是图标）
            let target = e.target;
            if (target.tagName === 'I') {
                target = target.closest('button');
            }

            if (target && target.classList.contains('btn-add')) {
                e.stopPropagation();
                const taskItem = target.closest('.task-item');
                const taskId = taskItem.dataset.taskId;

                const parentTask = this.tasks[taskId];
                if (!parentTask || parentTask.type !== 'main') {
                    if (window.showTopNotification) {
                        window.showTopNotification('只能为主阶段创建子阶段', 'warning', 3000, 'topNotification');
                    } else {
                        alert('只能为主阶段创建子阶段');
                    }
                    return;
                }

                // 禁止在已完成的主阶段下新增子阶段
                if (parentTask.status === 'completed') {
                    const msg = '主阶段已完成，不能再添加子阶段';
                    if (window.showTopNotification) {
                        window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                    } else {
                        alert(msg);
                    }
                    return;
                }

                // 使用通用确认对话框
                console.log('检查showConfirmDialog函数可用性:', typeof window.showConfirmDialog); // Debug log
                if (window.showConfirmDialog) {
                    console.log('使用通用确认对话框显示创建子阶段确认'); // Debug log
                    window.showConfirmDialog({
                        title: '创建子阶段',
                        message: `确认要为"${parentTask.name}"创建子阶段吗？`,
                        type: 'info',
                        confirmText: '确认创建',
                        cancelText: '取消',
                        dialogId: 'stageProgressConfirmDialog',
                        onConfirm: () => {
                            console.log('用户确认创建子阶段，准备显示表单'); // Debug log
                            this.showCreateSubStagePanel(taskId);
                        }
                    });
                } else {
                    console.warn('showConfirmDialog函数不可用，使用降级处理'); // Debug log
                    // 降级处理
                    if (confirm(`确认要为"${parentTask.name}"创建子阶段吗？`)) {
                        console.log('用户通过原生确认对话框确认创建'); // Debug log
                        this.showCreateSubStagePanel(taskId);
                    }
                }
            } else if (target && target.classList.contains('btn-edit')) {
                e.stopPropagation();
                const taskId = target.closest('.task-item').dataset.taskId;
                console.log('Edit button clicked for task:', taskId); // Debug log
                this.editTask(taskId);
            } else if (target && target.classList.contains('btn-delete')) {
                e.stopPropagation();
                const taskId = target.closest('.task-item').dataset.taskId;
                const subTask = this.tasks[taskId];
                const parentTask = subTask && subTask.parent ? this.tasks[subTask.parent] : null;
                if ((parentTask && parentTask.status === 'completed') || (subTask && subTask.status === 'completed')) {
                    const msg = parentTask && parentTask.status === 'completed'
                        ? '主阶段已完成，不能删除子阶段'
                        : '已完成的子阶段不能删除';
                    if (window.showTopNotification) {
                        window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                    } else {
                        alert(msg);
                    }
                    return;
                }
                console.log('Delete button clicked for task:', taskId); // Debug log
                this.confirmDeleteTask(taskId);
            }
        });
    }

    /**
     * 绑定详情面板事件
     */
    bindDetailsEvents() {
        const closeBtn = this.container.querySelector('#closeDetails');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideDetails();
            });
        }
    }

    /**
     * 计算某任务的“当前位置”日期
     * 规则：
     * - 进行中且有 progress: start + (end-start)*progress
     * - 已完成: 取 endDate
     * - 待开始/计划中: 取 startDate
     * - 兜底: startDate 或 endDate 或今天
     */
    getTaskCurrentDate(task) {
        const start = task?.startDate instanceof Date ? task.startDate : (task?.startDate ? new Date(task.startDate) : null);
        const end = task?.endDate instanceof Date ? task.endDate : (task?.endDate ? new Date(task.endDate) : null);

        if (task?.status === 'completed' && end) return end;

        if (task?.status === 'in-progress' && start && end) {
            const total = end.getTime() - start.getTime();
            const ratio = (typeof task.progress === 'number' && task.progress >= 0 && task.progress <= 100)
                ? task.progress / 100
                : 0;
            const ms = start.getTime() + Math.max(0, Math.min(1, ratio)) * Math.max(0, total);
            return new Date(ms);
        }

        if (start) return start;
        if (end) return end;
        return new Date();
    }

    /**
     * 跳转到指定任务对应的日期（月）并高亮该天
     */
    jumpToTaskDate(taskId) {
        const task = this.tasks[taskId];
        if (!task) return;

        const targetDate = this.getTaskCurrentDate(task);
        if (!targetDate) return;

        // 如果目标日期不在当前月份，则切换到目标月份
        const curY = this.currentDate.getFullYear();
        const curM = this.currentDate.getMonth();
        const tgtY = targetDate.getFullYear();
        const tgtM = targetDate.getMonth();

        if (curY !== tgtY || curM !== tgtM) {
            this.currentDate = new Date(tgtY, tgtM, 1);
            this.renderGantt();
            this.updateTodayLine();
        }

        // 高亮该日期并在图表区域画一条参考线
        this.highlightDate(targetDate);
    }

    /**
     * 在当前月份中高亮某个日期并在图表区绘制参考线
     */
    highlightDate(date) {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        if (date.getFullYear() !== year || date.getMonth() !== month) return;

        // 1) 标记头部对应日
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const day = Math.min(daysInMonth, Math.max(1, date.getDate()));
        const daysContainer = this.container.querySelector('#ganttDays');
        if (daysContainer) {
            // 清除旧的选中样式
            daysContainer.querySelectorAll('.gantt-day.selected').forEach(el => el.classList.remove('selected'));
            const dayEl = daysContainer.children[day - 1];
            if (dayEl) dayEl.classList.add('selected');
        }

        // 需求调整：不再在日期或内容区绘制高亮
        const content = this.container.querySelector('.gantt-content');
        if (!content) return;
        content.querySelectorAll('.focus-column, .focus-line').forEach(el => el.remove());
    }

    /**
     * 绑定全局交互事件
     */
    bindGlobalEvents() {
        // ESC键关闭详情面板
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isDetailsVisible) {
                this.hideDetails();
            }
        });

        // 点击甘特图外部区域关闭详情面板
        document.addEventListener('click', (e) => {
            if (!this.isDetailsVisible) return;

            const clickedInsideContainer = this.container.contains(e.target);
            const clickedInOverlay = !!e.target.closest(
                '.modal, .dropdown-menu, .popover, .tooltip, .standard-confirm-dialog, .standard-invoice-preview-dialog, .offcanvas'
            );

            if (!clickedInsideContainer && !clickedInOverlay) {
                this.hideDetails();
            }
        });
    }

    /**
     * 绑定添加阶段事件（已移至任务项内部按钮）
     */
    bindAddStageEvent() {
        // 添加按钮已移至任务项内部，通过 bindTaskListEvents 处理
        // 无需额外绑定
    }

    /**
     * 渲染甘特图
     */
    renderGantt() {
        this.renderTaskList();
        this.renderGanttHeader();
        this.renderGanttBars();
    }

    /**
     * 渲染任务列表
     */
    renderTaskList() {
        const taskList = this.container.querySelector('#taskList');
        if (!taskList) return;

        let html = '';
        
        // 渲染主阶段和子阶段
        Object.entries(this.tasks).forEach(([taskId, task]) => {
            if (task.type === 'main') {
                html += this.renderMainTaskItem(taskId, task);
                
                // 渲染子任务
                const subTasks = Object.entries(this.tasks).filter(([id, t]) => t.parent === taskId);
                if (subTasks.length > 0) {
                    subTasks.forEach(([subId, subTask]) => {
                        html += this.renderSubTaskItem(subId, subTask);
                    });
                }
            }
        });

        taskList.innerHTML = html;
    }

    /**
     * 兼容旧调用：渲染任务列表别名
     * 若外部调用了 renderTasks，则等同于刷新左侧任务树
     */
    renderTasks() {
        this.renderTaskList();
    }

    /**
     * 渲染主任务项
     */
    renderMainTaskItem(taskId, task) {
        const isSelected = this.selectedTask === taskId;
        const hasSubTasks = Object.values(this.tasks).some(t => t.parent === taskId);
        const rowStyle = this.getTaskRowStyle(taskId, true);
        const statusIconSpan = this.getStatusIconForList(task.status);
        
        return `
            <div class="task-item main-stage ${isSelected ? 'selected' : ''}" 
                 data-task-id="${taskId}" 
                 data-stage="${taskId}"
                 style="${rowStyle}">
                ${hasSubTasks ? `
                    <div class="expand-icon expanded" data-expanded="true">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                ` : '<div class="expand-icon"></div>'}
                <div class="task-name">${task.name}</div>
                ${statusIconSpan}
                ${this.canEdit && task.status !== 'completed' && !['apply_storage', 'stored'].includes(taskId) ? `
                    <div class="task-actions">
                        <button type="button" class="btn btn-add" title="添加子阶段">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button type="button" class="btn btn-edit" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * 渲染子任务项
     */
    renderSubTaskItem(taskId, task) {
        const isSelected = this.selectedTask === taskId;
        const rowStyle = this.getTaskRowStyle(task.parent, false, parseInt(task.progress || 0));
        const statusIconSpan = this.getStatusIconForList(task.status);
        const parentTask = this.tasks[task.parent];
        const parentCompleted = parentTask && parentTask.status === 'completed';
        
        return `
            <div class="task-item sub-stage ${isSelected ? 'selected' : ''}" 
                 data-task-id="${taskId}" 
                 data-parent="${task.parent}"
                 style="${rowStyle}">
                <div class="expand-icon"></div>
                <div class="task-name">${task.name}</div>
                ${statusIconSpan}
                ${this.canEdit && !parentCompleted && !(parentTask && parentTask.status === 'paused') && task.status !== 'completed' ? `
                    <div class="task-actions">
                        <button type="button" class="btn btn-edit" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-delete" title="删除">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * 根据阶段颜色生成左侧行的行内样式
     */
    getTaskRowStyle(stageKey, isMain, progressOverride = null) {
        const task = isMain ? this.tasks[stageKey] : null;
        // 计算主色与浅色（与甘特条一致）
        let mainColor, lightColor;
        const palette = this.stageColors[stageKey];
        if (palette) {
            mainColor = palette.main || palette.sub || 'var(--gantt-primary-color)';
            lightColor = palette.light || this.lightenColor(mainColor, 0.55);
            if (mainColor && lightColor && mainColor.toLowerCase() === lightColor.toLowerCase()) {
                lightColor = this.lightenColor(mainColor, 0.55);
            }
        } else {
            // 兜底配色
            mainColor = 'var(--gantt-primary-color)';
            lightColor = '#e3f2fd';
        }
        const progressBase = progressOverride != null ? progressOverride : parseInt((task?.progress) || 0);
        const progress = Math.max(0, Math.min(100, isNaN(progressBase) ? 0 : progressBase));
        const bg = progress > 0 && progress < 100
            ? `linear-gradient(90deg, ${mainColor} 0%, ${mainColor} ${progress}%, ${lightColor} ${progress}%, ${lightColor} 100%)`
            : (progress >= 100 ? mainColor : lightColor);
        const textColor = '#333';
        const border = isMain ? '' : `border-left: 3px solid ${mainColor};`;
        return `background: ${bg}; color: ${textColor}; ${border}`;
    }

    getStatusIconForList(status) {
        const map = { 'in-progress': 'fa-play', 'paused': 'fa-pause', 'completed': 'fa-stop' };
        const icon = map[status];
        if (!icon) return '<span class="stage-status-icon"></span>';
        return `<span class="stage-status-icon"><i class="fas ${icon}"></i></span>`;
    }

    /** 将HEX颜色转换为半透明rgba */
    toTransparent(hex, alpha = 0.3) {
        const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
        if (!m) return 'rgba(0,0,0,' + alpha + ')';
        const r = parseInt(m[1], 16);
        const g = parseInt(m[2], 16);
        const b = parseInt(m[3], 16);
        return `rgba(${r},${g},${b},${alpha})`;
    }

    /**
     * 渲染甘特图表头
     */
    renderGanttHeader() {
        const monthSpan = this.container.querySelector('#currentMonth');
        const daysContainer = this.container.querySelector('#ganttDays');
        
        if (monthSpan) {
            monthSpan.textContent = `${this.currentDate.getFullYear()}年${this.currentDate.getMonth() + 1}月`;
        }

        if (daysContainer) {
            daysContainer.innerHTML = this.generateDayHeaders();
        }
    }

    /**
     * 生成日期表头
     */
    generateDayHeaders() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        
        let html = '';
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const isToday = date.toDateString() === today.toDateString();
            const isWeekend = date.getDay() === 0 || date.getDay() === 6;
            
            html += `
                <div class="gantt-day ${isWeekend ? 'weekend' : ''} ${isToday ? 'today' : ''}">
                    ${day}
                </div>
            `;
        }
        
        return html;
    }

    /**
     * 渲染甘特条
     */
    renderGanttBars() {
        const barsContainer = this.container.querySelector('#ganttBars');
        if (!barsContainer) return;

        let html = '';
        
        // 为每个任务创建甘特条行
        Object.entries(this.tasks).forEach(([taskId, task]) => {
            if (task.type === 'main') {
                html += this.renderGanttBarRow(taskId, task);
                
                // 子任务行
                const subTasks = Object.entries(this.tasks).filter(([id, t]) => t.parent === taskId);
                subTasks.forEach(([subId, subTask]) => {
                    html += this.renderGanttBarRow(subId, subTask);
                });
            }
        });

        barsContainer.innerHTML = html;
    }

    /**
     * 渲染甘特条行
     */
    renderGanttBarRow(taskId, task) {
        const isMainStage = task.type === 'main';
        const barHtml = this.renderGanttBar(taskId, task);
        
        return `
            <div class="gantt-bar-row ${isMainStage ? 'main-stage' : 'sub-stage'}" 
                 data-task-id="${taskId}">
                ${barHtml}
            </div>
        `;
    }

    /**
     * 渲染甘特条
     */
    renderGanttBar(taskId, task) {
        if (!task.startDate || !task.endDate) {
            return ''; // 没有时间信息的任务不显示甘特条
        }

        const { left, width, unit } = this.calculateBarPosition(task.startDate, task.endDate);
        const parentAttr = task.parent ? `data-parent="${task.parent}"` : `data-stage="${taskId}"`;

        // 生成甘特条样式
        const barStyle = this.generateGanttBarStyle(taskId, task, left, width, unit);
        const colors = this.getBarColors(taskId, task);
        const progress = Math.max(0, Math.min(100, parseInt(task.progress || 0)));

        // 为已完成任务添加实际完成时间边线标记
        let actualEndMarker = '';
        let extendedBar = '';
        let enhancedTooltip = task.name;

        if (task.status === 'completed' && task.actualEndDate) {
            // 计算实际完成时间相对于计划时间的位置
            const actualEndDate = new Date(task.actualEndDate);
            const planEndDate = new Date(task.endDate);

            if (actualEndDate <= planEndDate) {
                // 提前完成或按时完成：在甘特条内部显示实际完成边线
                const actualPosition = this.calculateBarPosition(task.startDate, actualEndDate);
                if (actualPosition.width > 0) {
                    const actualPercent = Math.min(100, (actualPosition.width / width) * 100);
                    actualEndMarker = `<div class="gantt-bar-actual-end" style="left: ${actualPercent}%;"></div>`;
                }

                // 计算节省的天数
                const savedDays = Math.ceil((planEndDate - actualEndDate) / (24 * 60 * 60 * 1000));
                enhancedTooltip = `${task.name}\n计划：${task.startDate.toLocaleDateString()} - ${planEndDate.toLocaleDateString()}\n实际：${task.startDate.toLocaleDateString()} - ${actualEndDate.toLocaleDateString()}` +
                    (savedDays > 0 ? `\n提前 ${savedDays} 天完成` : '\n按时完成');
            } else {
                // 延期完成：显示延期部分
                actualEndMarker = `<div class="gantt-bar-actual-end" style="left: 100%;"></div>`;

                const extendedPosition = this.calculateBarPosition(planEndDate, actualEndDate);
                if (extendedPosition.width > 0) {
                    const extendedPercent = (extendedPosition.width / width) * 100;
                    extendedBar = `<div class="gantt-bar-extended" style="left: 100%; width: ${extendedPercent}%; background: #ffcccc; border-radius: 0 3px 3px 0;"></div>`;
                }

                // 计算延期的天数
                const delayedDays = Math.ceil((actualEndDate - planEndDate) / (24 * 60 * 60 * 1000));
                enhancedTooltip = `${task.name}\n计划：${task.startDate.toLocaleDateString()} - ${planEndDate.toLocaleDateString()}\n实际：${task.startDate.toLocaleDateString()} - ${actualEndDate.toLocaleDateString()}\n延期 ${delayedDays} 天完成`;
            }
        }

        return `
            <div class="gantt-bar"
                 style="${barStyle}"
                 ${parentAttr}
                 data-task-id="${taskId}"
                 data-status="${task.status || 'pending'}"
                 title="${enhancedTooltip}">
                <div class="gantt-bar-fill" style="width:${progress}%; background:${colors.mainColor};"></div>
                ${actualEndMarker}
                ${extendedBar}
                <div class="gantt-bar-text">${task.name}</div>
            </div>
        `;
    }

    /**
     * 生成甘特条样式
     */
    generateGanttBarStyle(taskId, task, left, width, unit = '%') {
        // 根据阶段类型确定颜色
        let mainColor, subColor, lightColor;
        
        const stageKey = task.parent || taskId;
        // 优先使用后端传入的颜色配置
        const palette = this.stageColors[stageKey];
        if (palette) {
            const isSub = task.type === 'sub';
            // 主阶段用 main，子阶段用 sub；待开始/浅色使用 sub
            mainColor = (isSub ? (palette.sub || palette.main) : (palette.main || palette.sub || 'var(--gantt-primary-color)'));
            subColor = mainColor; // 渐变使用相同主色，避免突兀
            lightColor = palette.sub || palette.light || '#e3f2fd';
        } else {
            // 兼容旧变量
            switch(stageKey) {
                case 'research':
                    mainColor = 'var(--gantt-research-main)';
                    subColor = 'var(--gantt-research-sub)';
                    lightColor = 'var(--gantt-research-light)';
                    break;
                case 'planning':
                    mainColor = 'var(--gantt-planning-main)';
                    subColor = 'var(--gantt-planning-sub)';
                    lightColor = 'var(--gantt-planning-light)';
                    break;
                case 'development':
                    mainColor = 'var(--gantt-development-main)';
                    subColor = 'var(--gantt-development-sub)';
                    lightColor = 'var(--gantt-development-light)';
                    break;
                case 'apply_storage':
                    mainColor = 'var(--gantt-apply-main)';
                    subColor = 'var(--gantt-apply-sub)';
                    lightColor = 'var(--gantt-apply-light)';
                    break;
                case 'stored':
                    mainColor = 'var(--gantt-stored-main)';
                    subColor = 'var(--gantt-stored-sub)';
                    lightColor = 'var(--gantt-stored-light)';
                    break;
                default:
                    mainColor = 'var(--gantt-primary-color)';
                    subColor = 'var(--gantt-info-color)';
                    lightColor = '#e3f2fd';
            }
        }

        let background;
        let color = '#333';
        let border = 'none';

        const progress = Math.max(0, Math.min(100, parseInt(task.progress || 0)));

        // 使用浅色作为底色，深色用内部fill条表示，保证可视化对比明显
        if (task.status === 'pending') {
            background = lightColor;
            color = '#333';
            border = `1px solid ${mainColor}`;
        } else if (progress >= 100 || task.status === 'completed') {
            background = mainColor;
        } else {
            background = lightColor;
        }

        const u = unit;
        return `
            left: ${left}${u}; 
            width: ${width}${u}; 
            background: ${background}; 
            color: ${color}; 
            border: ${border};
        `;
    }

    /**
     * 统一计算甘特条颜色（主色/浅色）
     */
    getBarColors(taskId, task) {
        let mainColor, lightColor;
        const stageKey = task.parent || taskId;
        const palette = this.stageColors[stageKey];
        if (palette) {
            // 主色优先取 palette.main，其次 palette.sub；浅色优先取 palette.light，否则从主色自动生成浅色
            mainColor = palette.main || palette.sub || 'var(--gantt-primary-color)';
            lightColor = palette.light || this.lightenColor(mainColor, 0.55);
            // 兜底：如果最终仍相同，强制变浅
            if (mainColor && lightColor && mainColor.toLowerCase() === lightColor.toLowerCase()) {
                lightColor = this.lightenColor(mainColor, 0.55);
            }
        } else {
            switch(stageKey) {
                case 'research':
                    mainColor = 'var(--gantt-research-main)';
                    lightColor = 'var(--gantt-research-light)';
                    break;
                case 'planning':
                    mainColor = 'var(--gantt-planning-main)';
                    lightColor = 'var(--gantt-planning-light)';
                    break;
                case 'development':
                    mainColor = 'var(--gantt-development-main)';
                    lightColor = 'var(--gantt-development-light)';
                    break;
                case 'apply_storage':
                    mainColor = 'var(--gantt-apply-main)';
                    lightColor = 'var(--gantt-apply-light)';
                    break;
                case 'stored':
                    mainColor = 'var(--gantt-stored-main)';
                    lightColor = 'var(--gantt-stored-light)';
                    break;
                default:
                    mainColor = 'var(--gantt-primary-color)';
                    lightColor = '#e3f2fd';
            }
        }
        return { mainColor, lightColor };
    }

    /**
     * 生成更浅的颜色
     */
    lightenColor(hex, amount = 0.5) {
        const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
        if (!m) return '#e3f2fd';
        const r = Math.min(255, Math.round(parseInt(m[1], 16) + (255 - parseInt(m[1], 16)) * amount));
        const g = Math.min(255, Math.round(parseInt(m[2], 16) + (255 - parseInt(m[2], 16)) * amount));
        const b = Math.min(255, Math.round(parseInt(m[3], 16) + (255 - parseInt(m[3], 16)) * amount));
        const toHex = (v) => v.toString(16).padStart(2, '0');
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    }

    /**
     * 计算甘特条位置
     */
    calculateBarPosition(startDate, endDate) {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const monthStart = new Date(year, month, 1);
        const monthEnd = new Date(year, month + 1, 0);
        const daysInMonth = monthEnd.getDate();

        // 优先使用像素精确对齐到日期单元格
        const dayRects = this.getDayRects();
        if (dayRects && dayRects.length === daysInMonth) {
            const startDayIndex = (startDate.getFullYear() === year && startDate.getMonth() === month)
                ? Math.max(0, Math.min(daysInMonth - 1, startDate.getDate() - 1))
                : (startDate < monthStart ? 0 : daysInMonth - 1);
            const endDayIndex = (endDate.getFullYear() === year && endDate.getMonth() === month)
                ? Math.max(0, Math.min(daysInMonth - 1, endDate.getDate() - 1))
                : (endDate > monthEnd ? daysInMonth - 1 : 0);

            const leftPx = dayRects[startDayIndex].left;
            const rightPx = dayRects[endDayIndex].left + dayRects[endDayIndex].width; // 包含结束日整格
            const widthPx = Math.max(0, rightPx - leftPx);
            return { left: leftPx, width: widthPx, unit: 'px' };
        }

        // 退回百分比方案
        const startDay = startDate.getMonth() === month && startDate.getFullYear() === year
            ? startDate.getDate()
            : (startDate < monthStart ? 1 : daysInMonth + 1);

        const endDay = endDate.getMonth() === month && endDate.getFullYear() === year
            ? endDate.getDate()
            : (endDate > monthEnd ? daysInMonth : 0);

        const left = ((startDay - 1) / daysInMonth) * 100;
        const width = ((endDay - startDay + 1) / daysInMonth) * 100;

        return {
            left: Math.max(0, Math.min(100, left)),
            width: Math.max(0, Math.min(100 - left, width)),
            unit: '%'
        };
    }

    /**
     * 计算每一天在内容区中的像素位置和宽度
     */
    getDayRects() {
        try {
            const daysContainer = this.container.querySelector('#ganttDays');
            const content = this.container.querySelector('.gantt-content');
            if (!daysContainer || !content) return null;
            const contentRect = content.getBoundingClientRect();
            const rects = [];
            const children = Array.from(daysContainer.children);
            children.forEach((el) => {
                const r = el.getBoundingClientRect();
                rects.push({
                    left: r.left - contentRect.left + content.scrollLeft,
                    width: r.width
                });
            });
            return rects;
        } catch (_) {
            return null;
        }
    }

    /**
     * 更新今日线
     */
    updateTodayLine() {
        // 移除现有的今日线
        const existingLine = this.container.querySelector('.today-line');
        if (existingLine) {
            existingLine.remove();
        }

        // 计算今日线位置
        const today = new Date();
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        if (today.getFullYear() === year && today.getMonth() === month) {
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const todayDay = today.getDate();
            const leftPercent = ((todayDay - 1) / daysInMonth) * 100;

            const ganttContent = this.container.querySelector('.gantt-content');
            if (ganttContent) {
                const todayLine = document.createElement('div');
                todayLine.className = 'today-line';
                todayLine.style.cssText = `
                    position: absolute;
                    left: ${leftPercent}%;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background-color: #dc3545;
                    z-index: 100;
                    pointer-events: none;
                `;
                ganttContent.appendChild(todayLine);
            }
        }
    }

    /**
     * 选择任务
     */
    selectTask(taskId) {
        // 移除之前的选中状态
        this.container.querySelectorAll('.task-item.selected').forEach(item => {
            item.classList.remove('selected');
        });

        // 设置新的选中状态
        const taskItem = this.container.querySelector(`[data-task-id="${taskId}"]`);
        if (taskItem) {
            taskItem.classList.add('selected');
        }

        this.selectedTask = taskId;
    }

    /**
     * 显示任务详情
     */
    showTaskDetails(taskId) {
        console.log('showTaskDetails called with taskId:', taskId); // Debug log
        const task = this.tasks[taskId];
        if (!task) {
            console.warn('任务不存在:', taskId);
            return;
        }

        // 防止重复点击相同任务
        if (this.isDetailsVisible && this.currentDetailTaskId === taskId) {
            return;
        }

        const detailsPanel = this.container.querySelector('#ganttDetails');
        const detailsTitle = this.container.querySelector('#detailsTitle');
        const detailsContent = this.container.querySelector('#detailsContent');

        if (!detailsPanel || !detailsTitle || !detailsContent) {
            console.warn('详情面板元素不存在');
            return;
        }

        // 如果当前有其他任务详情打开，先关闭
        if (this.isDetailsVisible) {
            this.hideDetails();
            // 延迟显示新内容，等待关闭动画完成
            setTimeout(() => {
                this.showTaskDetailsImmediate(taskId, task, detailsPanel, detailsTitle, detailsContent);
            }, 320);
        } else {
            this.showTaskDetailsImmediate(taskId, task, detailsPanel, detailsTitle, detailsContent);
        }
    }

    /**
     * 立即显示任务详情（内部方法）
     */
    showTaskDetailsImmediate(taskId, task, detailsPanel, detailsTitle, detailsContent) {
        // 设置标题
        detailsTitle.textContent = `${task.name} - 详情`;

        // 生成详情内容
        detailsContent.innerHTML = this.generateTaskDetailsHtml(taskId, task, 'view');

        // 显示面板 - 使用类切换实现动画效果（确保清理行内样式，避免关闭不完全）
        detailsPanel.style.display = 'flex';
        detailsPanel.style.maxHeight = '';
        detailsPanel.style.overflow = '';
        detailsPanel.classList.add('expanded');
        this.isDetailsVisible = true;
        this.currentDetailTaskId = taskId;

        // 绑定详情面板内的事件
        this.bindDetailEvents(taskId, 'view');

        // 加载阶段记录和附件
        this.loadStageRecords(taskId);
        this.loadStageAttachments(taskId);

        console.log('显示任务详情:', taskId, task.name);
    }

    /**
     * 生成任务详情HTML
     */
    generateTaskDetailsHtml(taskId, task, mode = 'view') {
        const isMainStage = task.type === 'main';
        
        // 获取主阶段名称
        let mainStageName = '';
        if (task.type === 'sub' && task.parent) {
            const parentTask = this.tasks[task.parent];
            if (parentTask) {
                mainStageName = parentTask.name;
            }
        }

        const statusClass = task.status ? `status-${task.status}` : '';
        const statusText = task.status ? this.getStatusText(task.status) : '';
        const showProgress = (task.status === 'in-progress');
        const hasPlan = !!(task.startDate && task.endDate);
        // 隐藏申请入库和已入库阶段的控制按钮
        const stageToCheck = task.type === 'sub' ? task.parent : taskId;
        const allowStateButtons = this.canEdit && this.isCreator && hasPlan && !['apply_storage', 'stored'].includes(stageToCheck);
        const startEnabled = allowStateButtons && (!task.status || task.status === 'planned' || task.status === 'pending' || task.status === 'paused');
        const pauseEnabled = allowStateButtons && (task.status === 'in-progress');
        const completeEnabled = allowStateButtons && (task.status === 'in-progress' || task.status === 'paused');
        
        // 获取真实附件数据（从API加载）
        const attachments = task.attachments || [];
        
        return `
            <div class="details-body">
                <!-- 左栏：基本信息 -->
                <div class="details-section">
                    <h4 class="section-title">基本信息</h4>
                    ${mode === 'create' ? `
                    <div class="detail-item">
                        <span class="detail-label">阶段名称：</span>
                        <span class="detail-value">
                            <input type="text" value="${task.name || ''}" id="taskName" placeholder="输入阶段名称" data-field="name" />
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">所属主阶段：</span>
                        <span class="detail-value">
                            ${this.tasks[task.parent] ? this.tasks[task.parent].name : ''}
                            <input type="hidden" id="taskParent" data-field="parent" value="${task.parent}" />
                        </span>
                    </div>
                    ` : `
                    <div class="detail-item">
                        <span class="detail-label">阶段名称：</span>
                        <span class="detail-value">${task.name || ''}</span>
                    </div>
                    ${mainStageName ? `
                    <div class="detail-item">
                        <span class="detail-label">主阶段：</span>
                        <span class="detail-value">${mainStageName}</span>
                    </div>
                    ` : ''}
                    ${task.status ? `
                    <div class="detail-item">
                        <span class="detail-label">状态：</span>
                        <span class="detail-value">
                            <span class="status-badge ${statusClass}">${statusText}</span>
                            ${allowStateButtons && task.status !== 'completed' ? `
                            <span class="ms-3">
                                <button class="btn btn-unified btn-unified-success btn-xs" data-action="startStage" title="启动" ${startEnabled ? '' : 'disabled'}><i class="fas fa-play"></i></button>
                                <button class="btn btn-unified btn-unified-warning btn-xs" data-action="pauseStage" title="暂停" ${pauseEnabled ? '' : 'disabled'}><i class="fas fa-pause"></i></button>
                                <button class="btn btn-unified btn-unified-danger btn-xs" data-action="completeStage" title="完成" ${completeEnabled ? '' : 'disabled'}><i class="fas fa-stop"></i></button>
                            </span>
                            ` : ''}
                        </span>
                    </div>
                    ` : ''}
                    ${(!task.status && allowStateButtons) ? `
                    <div class="detail-item">
                        <span class="detail-label">阶段操作：</span>
                        <span class="detail-value">
                            <span class="text-muted">未启动</span>
                            <span class="ms-3">
                                <button class="btn btn-unified btn-unified-success btn-xs" data-action="startStage" title="启动" ${startEnabled ? '' : 'disabled'}><i class="fas fa-play"></i></button>
                                <button class="btn btn-unified btn-unified-warning btn-xs" data-action="pauseStage" title="暂停" disabled><i class="fas fa-pause"></i></button>
                                <button class="btn btn-unified btn-unified-danger btn-xs" data-action="completeStage" disabled><i class="fas fa-stop"></i></button>
                            </span>
                        </span>
                    </div>
                    ` : ''}
                    <div class="detail-item">
                        <span class="detail-label">阶段说明：</span>
                        <span class="detail-value">
                            <textarea id="taskDescription" data-field="description" rows="3" placeholder="该阶段要做的内容描述...">${task.description || ''}</textarea>
                        </span>
                    </div>
                    `}
                    <div class="detail-item">
                        <span class="detail-label">负责人：</span>
                        <span class="detail-value">
                            <span class="creator-info">
                                <i class="fas fa-user-circle me-2" style="color: #3498db;"></i>
                                ${this.getCreatorInfo().name}
                                ${task.type === 'main' ? '<small class="text-muted ms-2">(产品创建者)</small>' : ''}
                            </span>
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">计划时间：</span>
                        <span class="detail-value">
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <input type="date" value="${task.startDate ? task.startDate.toISOString().split('T')[0] : ''}" id="taskStartDate" style="flex: 1;" data-field="startDate" ${!this.canEdit ? 'readonly' : ''} />
                                <span>~</span>
                                <input type="date" value="${task.endDate ? task.endDate.toISOString().split('T')[0] : ''}" id="taskEndDate" style="flex: 1;" data-field="endDate" ${!this.canEdit ? 'readonly' : ''} />
                            </div>
                        </span>
                    </div>
                    ${showProgress && hasPlan ? `
                    <div class="detail-item">
                        <span class="detail-label">完成度：</span>
                        <span class="detail-value">
                            <div style="display:flex; gap:10px; align-items:center;">
                                <input type="range" min="0" max="100" step="1" value="${parseInt(task.progress || 0)}" data-field="progress" style="flex:1;" />
                                <span id="progressValue">${parseInt(task.progress || 0)}%</span>
                            </div>
                        </span>
                    </div>
                    ` : ''}
                    ${mode !== 'create' ? `
                    <div class="detail-item">
                        <span class="detail-label">实际时间：</span>
                        <span class="detail-value">
                            ${task.actualStartDate ? task.actualStartDate.toLocaleDateString() : '未开始'} ~
                            ${task.actualEndDate ? task.actualEndDate.toLocaleDateString() : '进行中'}
                        </span>
                    </div>
                    ${task.status === 'completed' && task.actualEndDate ? `
                    <div class="detail-item">
                        <span class="detail-label">时间对比：</span>
                        <span class="detail-value">
                            ${(() => {
                                const actualEndDate = new Date(task.actualEndDate);
                                const planEndDate = new Date(task.endDate);
                                const timeDiff = Math.ceil((actualEndDate - planEndDate) / (24 * 60 * 60 * 1000));

                                if (timeDiff < 0) {
                                    return `<span class="text-success"><i class="fas fa-check-circle me-1"></i>提前 ${Math.abs(timeDiff)} 天完成</span>`;
                                } else if (timeDiff > 0) {
                                    return `<span class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i>延期 ${timeDiff} 天完成</span>`;
                                } else {
                                    return `<span class="text-primary"><i class="fas fa-clock me-1"></i>按时完成</span>`;
                                }
                            })()}
                        </span>
                    </div>
                    ` : ''}
                    ` : ''}
                </div>
                
                <!-- 中栏：阶段记录 -->
                <div class="details-section stage-records-section">
                    <h4 class="section-title">阶段记录</h4>
                    <div class="section-scope-info">${this.getStageDisplayScope(taskId, task)}</div>
                    
                    <!-- 可滚动的历史记录区域 -->
                    <div class="stage-records-history" id="stageRecordsHistory">
                        ${this.renderStageRecordsHistory(taskId, task)}
                    </div>
                    
                    <!-- 固定的输入区域 -->
                    ${this.canEdit && this.isCreator ? `
                    <div class="stage-records-input" id="stageRecordsInput">
                        <div class="record-input-area">
                            <textarea id="newRecordContent" placeholder="输入阶段记录..." rows="3"></textarea>
                            <div class="record-input-actions">
                                ${this.renderButton('提交记录', 'primary', 'fas fa-paper-plane', 'saveStageRecord')}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
                
                <!-- 右栏：附件管理 -->
                <div class="details-section">
                    <h4 class="section-title">附件管理</h4>
                    <div class="section-scope-info">${this.getStageDisplayScope(taskId, task)}</div>
                    ${attachments && attachments.length > 0 ? `
                    <ul class="attachment-list">
                        ${attachments.map(att => `
                            <li class="attachment-item">
                                <i class="fas ${this.getFileIcon(att.file_type || att.name)}"></i>
                                <span class="attachment-name">${att.file_name || att.name}</span>
                                <span class="attachment-size text-muted">${att.file_size_mb ? att.file_size_mb + 'MB' : (att.size || '')}</span>
                                <div class="attachment-actions">
                                    <button title="下载" data-action="download" data-attachment-id="${att.id}"><i class="fas fa-download"></i></button>
                                    ${this.canEdit ? `<button title="删除" data-action="deleteAttachment" data-attachment-id="${att.id}"><i class="fas fa-trash"></i></button>` : ''}
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                    ` : `
                    <div class="no-attachments">
                        <i class="fas fa-folder-open text-muted" style="font-size: 3rem; opacity: 0.5;"></i>
                        <p class="text-muted mt-2 mb-0">暂无附件</p>
                    </div>
                    `}
                    ${this.canEdit ? `
                    <button class="btn-standard btn-info" style="margin-top: 15px; width: 100%;" data-action="uploadAttachment" data-task-id="${taskId}">
                        <i class="fas fa-upload me-1"></i> 上传附件
                    </button>
                    ` : ''}
                </div>
            </div>
            
            <!-- 操作按钮 -->
            ${this.canEdit ? `
            <div class="details-footer">
                <div>
                    ${mode === 'create' 
                        ? this.renderButton('保存新阶段', 'primary', 'fas fa-save', 'createStage')
                        : this.renderButton('保存修改', 'primary', 'fas fa-save', 'saveChanges')
                    }
                    ${this.renderButton('取消', 'secondary', 'fas fa-times', 'cancel')}
                </div>
            </div>
            ` : ''}
        `;
    }

    /**
     * 获取状态文本
     */
    getStatusText(status) {
        const statusMap = {
            'planned': '计划中',
            'in-progress': '进行中', 
            'completed': '已完成',
            'paused': '已暂停',
            'cancelled': '已取消',
            'pending': '待开始'
        };
        return statusMap[status] || status;
    }

    /**
     * 标准化按钮生成函数 - 匹配通用按钮组件样式
     */
    renderButton(text, color, icon, action) {
        // 基础类名：匹配render_button宏生成的样式
        const baseClasses = "btn btn-unified btn-unified-" + color + " min-width-md me-2 py-1 px-3 text-xs rounded-pill";
        const iconHtml = icon ? `<i class="${icon} me-1"></i>` : '';
        const textHtml = icon ? `<span class="d-none d-md-inline">${text}</span>` : text;
        
        return `
            <button type="button" class="${baseClasses}" data-action="${action}">
                ${iconHtml}${textHtml}
            </button>
        `;
    }

    /**
     * 渲染阶段记录历史区域
     */
    renderStageRecordsHistory(taskId, task) {
        const stageRecords = task.stageRecords || [];

        if (!stageRecords || stageRecords.length === 0) {
            return '<div class="no-records">暂无阶段记录</div>';
        }

        // 按创建时间倒序排序（最新的在上面）
        const sortedRecords = stageRecords.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

        return sortedRecords.map(record => `
            <div class="stage-record-item" data-record-id="${record.id}")">
                <div class="record-header">
                    <span class="record-creator">${record.creator}</span>
                    <span class="record-time">${record.createdAt}</span>
                </div>
                <div class="record-content">${record.content}</div>
                ${this.canEdit && this.isCreator ? `<span class="record-delete" title="删除" data-action="deleteStageRecord" data-record-id="${record.id}"><i class="fas fa-trash"></i></span>` : ''}
            </div>
        `).join('');
    }

    /**
     * 从API加载阶段记录
     */
    async loadStageRecords(taskId) {
        try {
            const task = this.tasks[taskId];
            if (!task) {
                console.warn('任务不存在:', taskId);
                return;
            }

            // 获取需要查询的阶段keys（支持层级化查询）
            const stageKeys = this.getStageKeysForView(taskId, task);
            const stageKeysParam = stageKeys.join(',');

            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-records?stage_keys=${stageKeysParam}`);
            const result = await response.json();

            if (result.success) {
                // 将API数据转换为前端格式
                task.stageRecords = result.records.map(record => ({
                    id: record.id,
                    content: record.content,
                    createdAt: record.created_at,
                    creator: record.creator_name,
                    stageKey: record.stage_key,  // 保存来源阶段信息
                    stageName: this.getStageNameByKey(record.stage_key)  // 获取阶段名称
                }));

                // 刷新显示
                const historyContainer = this.container.querySelector('#stageRecordsHistory');
                if (historyContainer) {
                    historyContainer.innerHTML = this.renderStageRecordsHistory(taskId, task);
                }
            } else {
                console.error('加载阶段记录失败:', result.message);
            }
        } catch (error) {
            console.error('加载阶段记录时发生错误:', error);
        }
    }

    /**
     * 获取阶段查看范围的stage keys（层级化逻辑）
     * @param {string} taskId - 当前任务ID
     * @param {object} task - 当前任务对象
     * @returns {string[]} - 需要查看的stage keys数组
     */
    getStageKeysForView(taskId, task) {
        if (task.type === 'main') {
            // 主阶段：返回自己 + 所有子阶段的keys
            const subStageKeys = this.getSubStageKeys(taskId);
            return [taskId, ...subStageKeys];
        } else {
            // 子阶段：只返回自己
            return [taskId];
        }
    }

    /**
     * 获取指定主阶段下的所有子阶段keys
     * @param {string} mainStageId - 主阶段ID
     * @returns {string[]} - 子阶段keys数组
     */
    getSubStageKeys(mainStageId) {
        return Object.keys(this.tasks).filter(key =>
            this.tasks[key].parent === mainStageId
        );
    }

    /**
     * 获取阶段显示名称（用于UI显示）
     * @param {string} taskId - 任务ID
     * @param {object} task - 任务对象
     * @returns {string} - 显示范围描述
     */
    getStageDisplayScope(taskId, task) {
        if (task.type === 'main') {
            const subStageKeys = this.getSubStageKeys(taskId);
            if (subStageKeys.length > 0) {
                return `${task.name}及其子阶段的记录和附件`;
            } else {
                return `${task.name}阶段的记录和附件`;
            }
        } else {
            return `${task.name}阶段的记录和附件`;
        }
    }

    /**
     * 根据stage key获取阶段名称
     * @param {string} stageKey - 阶段key
     * @returns {string} - 阶段名称
     */
    getStageNameByKey(stageKey) {
        const task = this.tasks[stageKey];
        return task ? task.name : stageKey;
    }

    /**
     * 从API加载阶段附件
     */
    async loadStageAttachments(taskId) {
        try {
            const task = this.tasks[taskId];
            if (!task) {
                console.warn('任务不存在:', taskId);
                return;
            }

            // 获取需要查询的阶段keys（支持层级化查询）
            const stageKeys = this.getStageKeysForView(taskId, task);
            const stageKeysParam = stageKeys.join(',');

            // 调试日志：确认查询的stage keys
            console.log('查询附件 - taskId:', taskId, 'task.type:', task.type, '查询stageKeys:', stageKeys);

            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-attachments?stage_keys=${stageKeysParam}`);
            const result = await response.json();

            // 调试日志：查看API响应
            console.log('附件API响应:', result, '返回附件数量:', result.attachments?.length || 0);

            if (result.success) {
                // 为附件添加阶段名称信息
                task.attachments = (result.attachments || []).map(attachment => ({
                    ...attachment,
                    stageName: this.getStageNameByKey(attachment.stage_key)
                }));

                // 刷新附件显示
                const detailsContent = this.container.querySelector('#detailsContent');
                if (detailsContent) {
                    // 重新生成详情内容以更新附件列表
                    detailsContent.innerHTML = this.generateTaskDetailsHtml(taskId, task, 'view');
                    this.bindDetailEvents(taskId, 'view');
                }
            } else {
                console.error('加载阶段附件失败:', result.message);
            }
        } catch (error) {
            console.error('加载阶段附件时发生错误:', error);
        }
    }

    /**
     * 绑定详情面板内的事件
     */
    bindDetailEvents(taskId, mode = 'view') {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 移除旧的事件监听器（如果存在）
        if (this.detailClickHandler) {
            detailsContent.removeEventListener('click', this.detailClickHandler);
        }

        // 创建新的事件处理函数
    this.detailClickHandler = (e) => {
        const button = e.target.closest('[data-action]');
        if (!button) return;

        // 防止点击操作按钮时冒泡到全局点击监听，导致详情面板被关闭
        e.preventDefault();
        e.stopPropagation();

        const action = button.getAttribute('data-action');
        if (button.hasAttribute('disabled')) {
            const msgMap = { startStage: '当前状态无法启动', pauseStage: '未启动的阶段不能暂停', completeStage: '未启动的阶段不能完成' };
            const msg = msgMap[action] || '操作不可用';
            if (window.showTopNotification) {
                window.showTopNotification(msg, 'warning', 2500, 'topNotification');
            } else {
                alert(msg);
            }
            return;
        }
        console.log('[Gantt] 详情面板点击:', { action, dataset: button.dataset, target: e.target });
        this.handleDetailAction(action, taskId, mode, e);
    };

        // 绑定新的事件监听器
        detailsContent.addEventListener('click', this.detailClickHandler);

        // 进度滑块百分比显示
        const progressInput = detailsContent.querySelector('input[type="range"][data-field="progress"]');
        const progressLabel = detailsContent.querySelector('#progressValue');
        if (progressInput && progressLabel) {
            progressInput.addEventListener('input', () => {
                const val = parseInt(progressInput.value) || 0;
                progressLabel.textContent = `${val}%`;
                // 实时更新本地任务进度并刷新甘特条填充
                const t = this.tasks[taskId];
                if (t) {
                    t.progress = val;
                    this.updateBarBackground(taskId);
                    // 进度修改直接持久化（防抖）
                    this.debouncedSaveProgress(taskId);
                }
            });
        }
        console.log('[Gantt] 详情面板事件已绑定');
    }

    debouncedSaveProgress(taskId, delay = 500) {
        this._progressTimers = this._progressTimers || {};
        if (this._progressTimers[taskId]) clearTimeout(this._progressTimers[taskId]);
        this._progressTimers[taskId] = setTimeout(async () => {
            const t = this.tasks[taskId];
            if (!t) return;
            try {
                const val = parseInt(t.progress || 0) || 0;
                if (t.type === 'sub') {
                    await this.updateStageToAPI(taskId, { progress: val });
                    // 子阶段进度保存后，联动父阶段进度为子阶段平均值
                    if (t.parent) this.recalcParentProgress(t.parent);
                } else if (t.type === 'main') {
                    // 主阶段进度保存使用主阶段计划API
                    await this.saveMainStagePlanToAPI(taskId, t.startDate, t.endDate);
                }
            } catch (e) {
                console.warn('保存进度失败:', e);
            }
        }, delay);
    }

    /**
     * 以子阶段平均进度更新父主阶段进度，并持久化
     */
    async recalcParentProgress(parentId) {
        const children = Object.values(this.tasks).filter(x => x.parent === parentId);
        if (!children.length) return;
        const sum = children.reduce((acc, cur) => acc + (parseInt(cur.progress || 0) || 0), 0);
        const avg = Math.round(sum / children.length);
        const parent = this.tasks[parentId];
        if (!parent) return;
        parent.progress = avg;
        this.updateBarBackground(parentId);
        try { await this.saveMainStagePlanToAPI(parentId, parent.startDate, parent.endDate); } catch (e) { console.warn('父阶段进度持久化失败:', e); }
        this.renderTaskList();
        this.renderGantt();
    }

    /**
     * 根据当前任务进度，实时刷新对应甘特条的背景填充
     */
    updateBarBackground(taskId) {
        const bar = this.container.querySelector(`.gantt-bar[data-task-id="${taskId}"]`);
        if (!bar) return;
        const task = this.tasks[taskId];
        if (!task || !task.startDate || !task.endDate) return;
        // 复用颜色与进度计算逻辑，仅更新背景与填充，不改动定位尺寸
        let mainColor, lightColor;
        const stageKey = task.parent || taskId;
        const palette = this.stageColors[stageKey];
        if (palette) {
            const isSub = task.type === 'sub';
            mainColor = (isSub ? (palette.sub || palette.main) : (palette.main || palette.sub || 'var(--gantt-primary-color)'));
            lightColor = palette.sub || palette.light || '#e3f2fd';
        } else {
            switch(stageKey) {
                case 'research':
                    mainColor = 'var(--gantt-research-main)';
                    lightColor = 'var(--gantt-research-light)';
                    break;
                case 'planning':
                    mainColor = 'var(--gantt-planning-main)';
                    lightColor = 'var(--gantt-planning-light)';
                    break;
                case 'development':
                    mainColor = 'var(--gantt-development-main)';
                    lightColor = 'var(--gantt-development-light)';
                    break;
                case 'apply_storage':
                    mainColor = 'var(--gantt-apply-main)';
                    lightColor = 'var(--gantt-apply-light)';
                    break;
                case 'stored':
                    mainColor = 'var(--gantt-stored-main)';
                    lightColor = 'var(--gantt-stored-light)';
                    break;
                default:
                    mainColor = 'var(--gantt-primary-color)';
                    lightColor = '#e3f2fd';
            }
        }
        const colors = this.getBarColors(taskId, task);
        const progress = Math.max(0, Math.min(100, parseInt(task.progress || 0)));
        // 底色统一使用浅色；已完成则用主色铺满
        bar.style.background = (progress >= 100 || task.status === 'completed') ? colors.mainColor : colors.lightColor;

        // 更新内部填充条
        let fill = bar.querySelector('.gantt-bar-fill');
        if (!fill) {
            fill = document.createElement('div');
            fill.className = 'gantt-bar-fill';
            bar.insertBefore(fill, bar.firstChild);
        }
        fill.style.width = `${progress}%`;
        fill.style.background = colors.mainColor;

        // 同步更新左侧任务树行的渐变填充（主/子阶段）
        const row = this.container.querySelector(`.task-item[data-task-id="${taskId}"]`);
        if (row) {
            const isMain = (task.type === 'main');
            const rowStyle = this.getTaskRowStyle(isMain ? taskId : task.parent, isMain, parseInt(task.progress || 0));
            row.setAttribute('style', rowStyle);
        }
    }

    /**
     * 处理详情面板操作
     */
    handleDetailAction(action, taskId, mode, evt) {
        switch (action) {
            case 'saveChanges':
                // 使用API集成版本
                if (this.csrfToken && this.apiEndpoints) {
                    this.saveTaskDetailsWithAPI(taskId);
                } else {
                    // 降级到基础版本
                    this.saveTaskDetails(taskId);
                }
                break;
            case 'createStage':
                // 使用API集成版本
                if (this.csrfToken && this.apiEndpoints) {
                    this.createNewSubStageWithAPI();
                } else {
                    // 降级到基础版本
                    this.createNewSubStage();
                }
                break;
            case 'cancel':
                this.hideDetails();
                break;
            case 'completeStage':
                {
                    const t = this.tasks[taskId];
                    if (!t) return;
                    // 确认框
                    this.showStandardConfirmDialog({
                        title: '确认完成阶段',
                        message: `确定将“${t.name}”设置为完成状态吗？`,
                        type: 'warning',
                        confirmText: '确认完成',
                        cancelText: '取消',
                        dialogId: 'stageProgressConfirmDialog',
                        onConfirm: () => this.completeStage(taskId)
                    });
                }
                break;
            case 'pauseStage':
                {
                    const t = this.tasks[taskId];
                    if (t && t.status === 'completed') {
                        const msg = '已完成的阶段不能切换为暂停状态';
                        if (window.showTopNotification) {
                            window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                        } else {
                            alert(msg);
                        }
                        return;
                    }
                    this.showStandardConfirmDialog({
                        title: '确认暂停阶段',
                        message: `确定将“${t.name}”设置为暂停状态吗？`,
                        type: 'warning',
                        confirmText: '确认暂停',
                        cancelText: '取消',
                        dialogId: 'stageProgressConfirmDialog',
                        onConfirm: () => this.pauseStage(taskId)
                    });
                }
                break;
            case 'startStage':
                {
                    const t = this.tasks[taskId];
                    if (t && t.status === 'completed') {
                        const msg = '已完成的阶段不能切换为启动状态';
                        if (window.showTopNotification) {
                            window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                        } else {
                            alert(msg);
                        }
                        return;
                    }
                    this.showStandardConfirmDialog({
                        title: '确认启动阶段',
                        message: `确定将“${t.name}”设置为进行中吗？`,
                        type: 'warning',
                        confirmText: '确认启动',
                        cancelText: '取消',
                        dialogId: 'stageProgressConfirmDialog',
                        onConfirm: () => this.startStage(taskId)
                    });
                }
                break;
            case 'deleteStage':
                this.confirmDeleteTask(taskId);
                break;
            case 'uploadAttachment':
                this.uploadAttachment(taskId);
                break;
            case 'download':
                const attachmentId = evt.target.closest('[data-attachment-id]')?.getAttribute('data-attachment-id');
                console.log('[Gantt] 执行下载动作，attachmentId=', attachmentId);
                this.downloadAttachment(attachmentId);
                break;
            case 'deleteAttachment':
                const deleteAttachmentId = evt.target.closest('[data-attachment-id]')?.getAttribute('data-attachment-id');
                this.deleteAttachment(deleteAttachmentId, taskId);
                break;
            case 'saveStageRecord':
                this.saveStageRecord(taskId);
                break;
            case 'deleteStageRecord':
                {
                    const recordId = evt.target.closest('[data-record-id]')?.getAttribute('data-record-id')
                        || evt.target.getAttribute('data-record-id');
                    if (!recordId) return;
                    const doDelete = () => this.deleteStageRecord(taskId, recordId);
                    if (window.showDeleteConfirm) {
                        window.showDeleteConfirm({
                            title: '确认删除记录',
                            message: '删除后无法恢复，确定删除此记录吗？',
                            dialogId: 'stageProgressConfirmDialog',
                            onConfirm: doDelete
                        });
                    } else {
                        if (confirm('删除后无法恢复，确定删除此记录吗？')) doDelete();
                    }
                }
                break;
        }
    }

    /** 删除阶段记录（前后端） */
    async deleteStageRecord(taskId, recordId) {
        try {
            const res = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-records/${recordId}`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': this.csrfToken || '' }
            });
            const result = await res.json();
            if (!result.success) {
                console.warn('删除记录失败:', result.message);
                return;
            }
            // 前端移除并重渲染
            const task = this.tasks[taskId];
            if (task && Array.isArray(task.stageRecords)) {
                task.stageRecords = task.stageRecords.filter(r => String(r.id) !== String(recordId));
                const historyContainer = this.container.querySelector('#stageRecordsHistory');
                if (historyContainer) historyContainer.innerHTML = this.renderStageRecordsHistory(taskId, task);
            }
        } catch (e) {
            console.error('删除阶段记录异常:', e);
        }
    }

    /**
     * 完成阶段
     */
    async completeStage(taskId) {
        const task = this.tasks[taskId];
        if (task) {
            if (!(task.status === 'in-progress' || task.status === 'paused')) {
                const msg = '未启动的阶段不能完成';
                if (window.showTopNotification) { window.showTopNotification(msg, 'warning', 2500, 'topNotification'); } else { alert(msg); }
                return;
            }
            // 持久化：子阶段调用子阶段API，主阶段仅保存计划和进度
            if (task.type === 'sub') {
                try { await this.updateStageToAPI(taskId, { status: 'completed', progress: 100 }); } catch (e) { console.warn('完成持久化失败:', e); }
            } else if (task.type === 'main') {
                try {
                    await this.saveMainStagePlanToAPI(taskId, task.startDate, task.endDate, 'completed');
                    // 主阶段完成后刷新产品状态
                    this.refreshProductStatus();
                } catch (e) {
                    console.warn('主阶段完成持久化失败:', e);
                }
            }
            task.status = 'completed';
            task.progress = 100;
            task.actualEndDate = new Date();
            // 如果是主阶段，联动所有子阶段完成
            if (task.type === 'main') {
                Object.entries(this.tasks).forEach(([id, t]) => {
                    if (t.parent === taskId) {
                        try { this.updateStageToAPI(id, { status: 'completed', progress: 100 }); } catch (e) {}
                        t.status = 'completed';
                        t.progress = 100;
                        t.actualEndDate = new Date();
                    }
                });
            } else if (task.type === 'sub' && task.parent) {
                // 如果是子阶段完成，检查其父阶段的所有子阶段是否都已完成
                const parentId = task.parent;
                const siblings = Object.values(this.tasks).filter(t => t.parent === parentId);
                const allCompleted = siblings.length > 0 && siblings.every(t => t.status === 'completed');
                if (allCompleted) {
                    const parentTask = this.tasks[parentId];
                    if (parentTask && parentTask.status !== 'completed') {
                        // 使用最后完成的子阶段的actualEndDate作为主阶段的实际完成时间
                        const latestEndDate = Math.max(...siblings.map(s => new Date(s.actualEndDate || s.endDate)));

                        try { await this.saveMainStagePlanToAPI(parentId, parentTask.startDate, parentTask.endDate, 'completed'); } catch (e) {}
                        parentTask.status = 'completed';
                        parentTask.progress = 100;
                        parentTask.actualEndDate = new Date(latestEndDate);

                        // 刷新产品状态（如果主阶段完成影响产品状态）
                        this.refreshProductStatus();
                    }
                }
            }
            this.renderTaskList();
            this.renderGantt();
            this.refreshDetailsIfOpen(taskId);
            console.log('阶段已完成:', task.name);
        }
    }

    /**
     * 暂停阶段
     */
    async pauseStage(taskId) {
        const task = this.tasks[taskId];
        if (task) {
            if (task.status !== 'in-progress') {
                const msg = '未启动的阶段不能暂停';
                if (window.showTopNotification) { window.showTopNotification(msg, 'warning', 2500, 'topNotification'); } else { alert(msg); }
                return;
            }
            if (task.type === 'sub') {
                try { await this.updateStageToAPI(taskId, { status: 'paused' }); } catch (e) { console.warn('暂停持久化失败:', e); }
            } else if (task.type === 'main') {
                try { await this.saveMainStagePlanToAPI(taskId, task.startDate, task.endDate, 'paused'); } catch (e) { console.warn('主阶段暂停持久化失败:', e); }
            }
            task.status = 'paused';
            // 主阶段暂停 -> 把所有进行中的子阶段同步暂停
            if (task.type === 'main') {
                Object.entries(this.tasks).forEach(([id, t]) => {
                    if (t.parent === taskId && t.status === 'in-progress') {
                        try { this.updateStageToAPI(id, { status: 'paused' }); } catch (e) {}
                        t.status = 'paused';
                    }
                });
            }
            this.renderTaskList();
            this.renderGantt();
            this.refreshDetailsIfOpen(taskId);
            console.log('阶段已暂停:', task.name);
        }
    }

    /** 启动阶段 */
    async startStage(taskId) {
        const task = this.tasks[taskId];
        if (task) {
            task.status = 'in-progress';
            if (!task.actualStartDate) task.actualStartDate = new Date();
            // 启动时清理实际结束时间
            if (task.actualEndDate) delete task.actualEndDate;
            if (typeof task.progress !== 'number' || isNaN(task.progress)) task.progress = 0;
            if (task.type === 'sub') {
                try { await this.updateStageToAPI(taskId, { status: 'in-progress' }); } catch (e) { console.warn('启动持久化失败:', e); }
            } else if (task.type === 'main') {
                try { await this.saveMainStagePlanToAPI(taskId, task.startDate, task.endDate, 'in-progress'); } catch (e) { console.warn('主阶段启动持久化失败:', e); }
            }
            // 子阶段启动 -> 主阶段同步启动
            if (task.type === 'sub' && task.parent) {
                const parent = this.tasks[task.parent];
                if (parent && parent.status !== 'in-progress' && parent.status !== 'completed') {
                    parent.status = 'in-progress';
                    if (!parent.actualStartDate) parent.actualStartDate = new Date();
                    this.updateBarBackground(task.parent);
                }
            }
            this.renderTaskList();
            this.renderGantt();
            this.refreshDetailsIfOpen(taskId);
            console.log('阶段已启动:', task.name);
        }
    }

    refreshDetailsIfOpen(taskId) {
        if (this.isDetailsVisible && this.currentDetailTaskId === taskId) {
            const detailsPanel = this.container.querySelector('#ganttDetails');
            const detailsTitle = this.container.querySelector('#detailsTitle');
            const detailsContent = this.container.querySelector('#detailsContent');
            const task = this.tasks[taskId];
            if (!detailsPanel || !detailsTitle || !detailsContent || !task) return;
            detailsTitle.textContent = `${task.name} - 详情`;
            detailsContent.innerHTML = this.generateTaskDetailsHtml(taskId, task, 'view');
            this.bindDetailEvents(taskId, 'view');
        }
    }

    /**
     * 上传附件
     */
    uploadAttachment(taskId) {
        // 创建文件选择对话框
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.multiple = true;
        fileInput.accept = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar,.txt,.jpg,.jpeg,.png,.gif';
        
        fileInput.onchange = async (event) => {
            const files = Array.from(event.target.files);
            if (files.length === 0) return;
            
            // 验证文件
            const maxSize = 20 * 1024 * 1024; // 20MB
            const invalidFiles = files.filter(file => file.size > maxSize);
            if (invalidFiles.length > 0) {
                if (window.showTopNotification) {
                    window.showTopNotification(`以下文件超过20MB限制：${invalidFiles.map(f => f.name).join(', ')}`, 'warning', 3000, 'topNotification');
                } else {
                    alert(`以下文件超过20MB限制：\n${invalidFiles.map(f => f.name).join('\n')}`);
                }
                return;
            }
            
            // 显示上传进度
            const progressContainer = this.showUploadProgress(files.length);
            
            try {
                let successCount = 0;
                let failCount = 0;
                
                // 逐个上传文件
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    
                    try {
                        // 更新进度
                        this.updateUploadProgress(progressContainer, i + 1, files.length, file.name);
                        
                        // 获取任务信息
                        const task = this.tasks[taskId];
                        const stageKey = task.type === 'main' ? taskId : (task.parent || taskId || 'general');

                        // 调试日志：确认stage key一致性
                        console.log('上传附件 - taskId:', taskId, 'task.id:', task.id, 'task.type:', task.type, '使用stageKey:', stageKey);
                        
                        await this.uploadAttachmentToAPI(stageKey, file);
                        successCount++;
                    } catch (error) {
                        console.error(`文件 ${file.name} 上传失败:`, error);
                        failCount++;
                    }
                }
                
                // 隐藏进度条
                this.hideUploadProgress(progressContainer);
                
                // 显示结果
                if (successCount > 0) {
                    // 刷新附件列表
                    await this.loadStageAttachments(taskId);
                    this.showTaskDetails(taskId);
                }

                if (failCount > 0) {
                    if (window.showTopNotification) {
                        window.showTopNotification(`上传完成！成功: ${successCount}个，失败: ${failCount}个`, 'warning', 3000, 'topNotification');
                    } else {
                        alert(`上传完成！成功: ${successCount}个，失败: ${failCount}个`);
                    }
                } else {
                    if (window.showTopNotification) {
                        window.showTopNotification(`全部文件上传成功！共${successCount}个文件`, 'success', 3000, 'topNotification');
                    } else {
                        alert(`全部文件上传成功！共${successCount}个文件`);
                    }
                }
                
            } catch (error) {
                this.hideUploadProgress(progressContainer);
                console.error('上传过程中发生错误:', error);
                alert('上传失败: ' + error.message);
            }
        };
        
        // 触发文件选择
        fileInput.click();
    }

    /**
     * 下载附件
     */
    downloadAttachment(attachmentId) {
        console.log('[Gantt] 开始下载附件:', attachmentId);
        const url = `/product-management/api/rd-products/${this.objectId}/stage-attachments/${attachmentId}/download`;
        console.log('[Gantt] 下载URL:', url);
        // 直接由浏览器跟随后端重定向到 Supabase 公有URL 并下载
        window.open(url, '_blank');
    }

    /**
     * 删除附件
     */
    async deleteAttachment(attachmentId, taskId) {
        // 使用通用确认对话框
        if (window.showDeleteConfirm) {
            window.showDeleteConfirm({
                title: '确认删除附件',
                message: '确定要删除这个附件吗？此操作不可恢复。',
                dialogId: 'stageProgressConfirmDialog',
                onConfirm: () => {
                    this.executeDeleteAttachment(attachmentId, taskId);
                }
            });
            return;
        }

        // 降级到原生确认框
        if (!confirm('确定要删除这个附件吗？')) {
            return;
        }

        await this.executeDeleteAttachment(attachmentId, taskId);
    }

    async executeDeleteAttachment(attachmentId, taskId) {

        if (!this.csrfToken) {
            // 尝试从DOM获取CSRF Token
            this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                             document.querySelector('input[name="csrf_token"]')?.value;
            
            if (!this.csrfToken) {
                console.warn('缺少CSRF Token，无法调用API');
                return;
            }
        }

        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-attachments/${attachmentId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            const result = await response.json();
            console.log('删除API返回结果:', result);
            
            if (response.ok) {
                // 根据云端删除状态显示详细信息
                let message;
                if (result.cloud_delete_success) {
                    message = result.message || '附件删除成功';
                } else {
                    message = `${result.message || '附件删除成功'} (警告: 云端文件删除失败)`;
                    console.warn('云端文件删除失败:', result);
                }
                
                if (window.showTopNotification) {
                    window.showTopNotification(message, 'success', 3000, 'topNotification');
                } else {
                    alert(message);
                }
                // 刷新附件列表
                await this.loadStageAttachments(taskId);
                this.showTaskDetails(taskId);
            } else {
                throw new Error(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除附件失败:', error);
            if (window.showTopNotification) {
                window.showTopNotification('删除失败: ' + error.message, 'error', 3000, 'topNotification');
            } else {
                alert('删除失败: ' + error.message);
            }
        }
    }

    /**
     * 保存阶段记录
     */
    async saveStageRecord(taskId) {
        const contentTextarea = this.container.querySelector('#newRecordContent');
        if (!contentTextarea) {
            console.error('记录输入框未找到');
            return;
        }

        const content = contentTextarea.value.trim();
        if (!content) {
            if (window.showTopNotification) {
                window.showTopNotification('请输入记录内容', 'warning', 3000, 'topNotification');
            } else {
                alert('请输入记录内容');
            }
            return;
        }

        try {
            // 获取当前任务
            const task = this.tasks[taskId];
            if (!task) {
                console.error('任务不存在:', taskId);
                return;
            }

            // 确保有CSRF Token
            if (!this.csrfToken) {
                this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                                 document.querySelector('input[name="csrf_token"]')?.value;
            }
            
            // 调用API保存记录
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-records`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken || ''
                },
                body: JSON.stringify({
                    content: content,
                    stage_key: taskId
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // 更新本地任务数据
                if (!task.stageRecords) {
                    task.stageRecords = [];
                }
                
                // 将API返回的记录转换为前端格式
                const newRecord = {
                    id: result.record.id,
                    content: result.record.content,
                    createdAt: result.record.created_at,
                    creator: result.record.creator_name
                };
                
                task.stageRecords.unshift(newRecord); // 添加到开头（最新的在上面）

                // 刷新历史记录显示
                const historyContainer = this.container.querySelector('#stageRecordsHistory');
                if (historyContainer) {
                    historyContainer.innerHTML = this.renderStageRecordsHistory(taskId, task);
                }

                // 清空输入框
                contentTextarea.value = '';

                console.log('阶段记录已保存:', newRecord);
                
                // 可选：显示成功消息
                if (result.message) {
                    // 这里可以添加toast通知或其他用户反馈
                    console.log('保存成功:', result.message);
                }
                
            } else {
                console.error('保存阶段记录失败:', result.message);
                if (window.showTopNotification) {
                    window.showTopNotification('保存失败: ' + result.message, 'error', 3000, 'topNotification');
                } else {
                    alert('保存失败: ' + result.message);
                }
            }
            
        } catch (error) {
            console.error('保存阶段记录时发生错误:', error);
            if (window.showTopNotification) {
                window.showTopNotification('保存失败: 网络错误', 'error', 3000, 'topNotification');
            } else {
                alert('保存失败: 网络错误');
            }
        }
    }

    /**
     * 创建新子阶段
     */
    createNewSubStage() {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 收集表单数据
        const formData = {};
        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value;
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value) : null;
            } else if (field === 'progress') {
                value = parseInt(value) || 0;
            }
            
            formData[field] = value;
        });

        // 验证必填字段
        if (!formData.name || !formData.parent) {
            if (window.showTopNotification) {
                window.showTopNotification('请填写阶段名称和选择主阶段', 'warning', 3000, 'topNotification');
            } else {
                alert('请填写阶段名称和选择主阶段');
            }
            return;
        }

        // 验证时间范围：不得超过主阶段跨度
        if (formData.parent) {
            const parent = this.tasks[formData.parent];
            if (parent && parent.startDate && parent.endDate) {
                const ps = new Date(parent.startDate).getTime();
                const pe = new Date(parent.endDate).getTime();
                const cs = formData.startDate ? new Date(formData.startDate).getTime() : ps;
                const ce = formData.endDate ? new Date(formData.endDate).getTime() : pe;
                if (cs < ps || ce > pe || cs > ce) {
                    const msg = '子阶段时间必须在所属主阶段范围内';
                    if (window.showTopNotification) {
                        window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                    } else { alert(msg); }
                    return;
                }
            }
        }

        // 生成新的子阶段ID
        const newTaskId = `sub-${Date.now()}`;
        
        // 创建新的子阶段任务
        const newTask = {
            id: newTaskId,
            name: formData.name,
            type: 'sub',
            parent: formData.parent,
            owner: formData.owner || '',
            startDate: formData.startDate,
            endDate: formData.endDate,
            progress: formData.progress || 0,
            status: 'planned',
            description: formData.description || '',
            attachments: [],
            createdAt: new Date().toLocaleString(),
            updatedAt: new Date().toLocaleString()
        };

        // 添加到任务列表
        this.tasks[newTaskId] = newTask;

        // 重新渲染
        this.renderTasks();
        this.renderGantt();
        
        // 保持详情面板打开，刷新显示
        this.refreshDetailsIfOpen(taskId);

        // TODO: 调用API保存到后端
        console.log('创建新子阶段:', newTask);
    }

    /**
     * 保存任务详情
     */
    saveTaskDetails(taskId) {
        const detailsContent = this.container.querySelector('#detailsContent');
        const task = this.tasks[taskId];
        
        if (!detailsContent || !task) return;

        // 收集表单数据
        const formData = {};
        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value;
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value) : null;
            } else if (field === 'progress') {
                value = parseInt(value) || 0;
            }
            
            formData[field] = value;
        });

        // 智能校正：若子阶段处于进行中且实际开始时间超出计划范围，则自动调整计划时间
        if (task.type === 'sub' && task.parent) {
            const parent = this.tasks[task.parent];
            if (parent) {
                const originalDurationDays = (task.startDate && task.endDate)
                    ? Math.max(0, Math.ceil((new Date(task.endDate) - new Date(task.startDate)) / (1000*60*60*24)))
                    : 0;
                const ps = parent.startDate ? new Date(parent.startDate).getTime() : null;
                const pe = parent.endDate ? new Date(parent.endDate).getTime() : null;
                let cs = formData.startDate ? new Date(formData.startDate).getTime() : null;
                let ce = formData.endDate ? new Date(formData.endDate).getTime() : null;

                if (task.status === 'in-progress' && task.actualStartDate) {
                    const actualStart = new Date(task.actualStartDate);
                    const asTs = actualStart.getTime();
                    const violatesParent = (ps && asTs < ps) || (pe && asTs > pe);
                    const violatesChild = (cs && ps && cs < ps) || (ce && pe && ce > pe);
                    if (violatesParent || violatesChild) {
                        const newStart = new Date(actualStart);
                        const newEnd = new Date(actualStart);
                        newEnd.setDate(newEnd.getDate() + (originalDurationDays > 0 ? originalDurationDays : 0));
                        formData.startDate = newStart;
                        formData.endDate = newEnd;
                        cs = newStart.getTime();
                        ce = newEnd.getTime();
                        if (ps && cs < ps) parent.startDate = new Date(cs);
                        if (pe && ce > pe) parent.endDate = new Date(ce);
                    }
                }

                // 最终校验
                if (parent.startDate && parent.endDate) {
                    const ps2 = new Date(parent.startDate).getTime();
                    const pe2 = new Date(parent.endDate).getTime();
                    if ((cs && cs < ps2) || (ce && ce > pe2) || (cs && ce && cs > ce)) {
                        const msg = '子阶段时间必须在所属主阶段范围内';
                        if (window.showTopNotification) {
                            window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                        } else { alert(msg); }
                        return;
                    }
                }
            }
        }

        // 更新任务数据
        Object.assign(task, formData);

        // 重新渲染甘特图
        this.renderGantt();
        
        // 隐藏详情面板
        this.hideDetails();

        // TODO: 调用API保存到后端
        console.log('保存任务详情:', taskId, formData);

        // 同步父阶段范围覆盖所有子阶段（仅对子阶段）
        if (task.type === 'sub' && task.parent) {
            this.syncParentRangeFromChildren(task.parent);
            this.renderTaskList();
            this.renderGantt();
        }
    }

    /**
     * 显示创建子阶段面板
     */
    showCreateSubStagePanel(parentStageId) {
        console.log('开始执行showCreateSubStagePanel, 父阶段ID:', parentStageId);

        const parentTask = this.tasks[parentStageId];
        if (!parentTask) {
            console.error('父阶段不存在:', parentStageId);
            if (window.showTopNotification) {
                window.showTopNotification('父阶段不存在', 'error', 3000, 'topNotification');
            }
            return;
        }

        // 禁止在已完成的主阶段下新增子阶段
        if (parentTask.status === 'completed') {
            const msg = '主阶段已完成，不能再添加子阶段';
            if (window.showTopNotification) {
                window.showTopNotification(msg, 'warning', 3000, 'topNotification');
            } else {
                alert(msg);
            }
            return;
        }
        console.log('父阶段验证通过:', parentTask.name, parentTask.type);

        if (parentTask.type !== 'main') {
            console.error('只能为主阶段创建子阶段');
            if (window.showTopNotification) {
                window.showTopNotification('只能为主阶段创建子阶段', 'warning', 3000, 'topNotification');
            }
            return;
        }

        const detailsPanel = this.container.querySelector('#ganttDetails');
        const detailsTitle = this.container.querySelector('#detailsTitle');
        const detailsContent = this.container.querySelector('#detailsContent');

        console.log('检查DOM元素:', {
            detailsPanel: !!detailsPanel,
            detailsTitle: !!detailsTitle,
            detailsContent: !!detailsContent
        });

        if (!detailsPanel || !detailsTitle || !detailsContent) {
            console.error('必需的DOM元素未找到');
            if (window.showTopNotification) {
                window.showTopNotification('界面元素未找到，请刷新页面重试', 'error', 3000, 'topNotification');
            }
            return;
        }

        // 设置标题
        detailsTitle.textContent = `为"${parentTask.name}"创建子阶段`;
        console.log('设置面板标题完成');

        // 创建临时任务数据用于表单
        const tempTask = this.createTempTask(parentStageId);
        console.log('创建临时任务数据完成:', tempTask);

        // 生成详情内容
        const detailsHtml = this.generateTaskDetailsHtml('temp-task', tempTask, 'create');
        detailsContent.innerHTML = detailsHtml;
        console.log('生成详情内容HTML完成，长度:', detailsHtml.length);

        // 显示面板 - 使用类切换实现动画效果（统一用CSS控制高度，避免行内样式残留）
        detailsPanel.style.display = 'flex';
        detailsPanel.style.maxHeight = '';
        detailsPanel.style.overflow = '';
        detailsPanel.classList.add('expanded');
        this.isDetailsVisible = true;
        console.log('面板显示状态设置完成, isDetailsVisible:', this.isDetailsVisible);

        // 绑定详情面板内的事件
        this.bindDetailEvents('temp-task', 'create');
        console.log('事件绑定完成');

        // 调试：检查面板实际状态
        console.log('========== 详情面板调试信息 ==========');
        console.log('- 面板元素存在:', !!detailsPanel);
        console.log('- 面板类名:', detailsPanel.className);
        console.log('- 面板计算样式:');
        const computedStyle = window.getComputedStyle(detailsPanel);
        console.log('  * max-height:', computedStyle.maxHeight);
        console.log('  * height:', computedStyle.height);
        console.log('  * display:', computedStyle.display);
        console.log('  * visibility:', computedStyle.visibility);
        console.log('  * opacity:', computedStyle.opacity);
        console.log('  * overflow:', computedStyle.overflow);
        console.log('  * position:', computedStyle.position);
        console.log('  * z-index:', computedStyle.zIndex);
        console.log('- 面板尺寸信息:');
        console.log('  * offsetHeight:', detailsPanel.offsetHeight);
        console.log('  * clientHeight:', detailsPanel.clientHeight);
        console.log('  * scrollHeight:', detailsPanel.scrollHeight);
        console.log('- 面板位置信息:');
        const rect = detailsPanel.getBoundingClientRect();
        console.log('  * top:', rect.top);
        console.log('  * left:', rect.left);
        console.log('  * width:', rect.width);
        console.log('  * height:', rect.height);
        console.log('- 父容器信息:');
        const parentRect = detailsPanel.parentElement.getBoundingClientRect();
        console.log('  * 父容器高度:', parentRect.height);
        console.log('  * 父容器宽度:', parentRect.width);
        console.log('========================================');

        // 检查内容区域
        const detailsContentEl = detailsPanel.querySelector('.details-content');
        if (detailsContentEl) {
            console.log('- 内容区域信息:');
            console.log('  * 内容HTML长度:', detailsContentEl.innerHTML.length);
            console.log('  * 内容高度:', detailsContentEl.offsetHeight);
            console.log('  * 内容计算样式display:', window.getComputedStyle(detailsContentEl).display);
        }

        // 调试样式已移除，问题已解决
        // detailsPanel.style.border = '3px solid red';
        // detailsPanel.style.backgroundColor = 'yellow';
        // detailsPanel.style.zIndex = '9999';
        // console.log('已添加临时调试样式（红色边框、黄色背景）');

        // 检查是否需要滚动到可见区域
        detailsPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        console.log('已滚动到面板位置');

        console.log('showCreateSubStagePanel执行完成');
    }

    /**
     * 创建临时任务数据
     */
    createTempTask(parentStageId = null) {
        const parent = parentStageId ? this.tasks[parentStageId] : null;
        // 默认使用父主阶段的计划时间范围
        const start = parent && parent.startDate ? new Date(parent.startDate) : new Date();
        const end = parent && parent.endDate ? new Date(parent.endDate) : (() => { const d=new Date(); d.setDate(d.getDate()+7); return d; })();

        return {
            name: '',
            type: 'sub',
            parent: parentStageId || 'research',
            owner: '',
            startDate: start,
            endDate: end,
            progress: 0,
            status: 'planned',
            description: '',
            attachments: []
        };
    }

    /**
     * 显示创建阶段面板（通用方法，保持向下兼容）
     */
    showCreateStagePanel() {
        const detailsPanel = this.container.querySelector('#ganttDetails');
        const detailsTitle = this.container.querySelector('#detailsTitle');
        const detailsContent = this.container.querySelector('#detailsContent');

        if (!detailsPanel || !detailsTitle || !detailsContent) return;

        // 设置标题
        detailsTitle.textContent = '创建子阶段';

        // 生成创建表单
        detailsContent.innerHTML = this.generateCreateStageHtml();

        // 显示面板
        detailsPanel.style.display = 'flex';
        this.isDetailsVisible = true;

        // 绑定创建表单事件
        this.bindCreateStageEvents();
    }

    /**
     * 生成创建子阶段HTML
     */
    generateCreateSubStageHtml(parentStageId) {
        const parentTask = this.tasks[parentStageId];
        
        return `
            <div class="gantt-form">
                <div class="row">
                    <label>所属主阶段:</label>
                    <input type="text" class="form-control" value="${parentTask.name}" readonly>
                    <input type="hidden" data-field="parent" value="${parentStageId}">
                </div>
                
                <div class="row">
                    <label>子阶段名称:</label>
                    <input type="text" class="form-control" placeholder="请输入子阶段名称" data-field="name" required>
                </div>
                
                <div class="row">
                    <label>开始时间:</label>
                    <input type="date" class="form-control" data-field="startDate" required>
                </div>
                
                <div class="row">
                    <label>结束时间:</label>
                    <input type="date" class="form-control" data-field="endDate" required>
                </div>
                
                <div class="row">
                    <label>负责人:</label>
                    <input type="text" class="form-control" placeholder="请输入负责人" data-field="owner">
                </div>
                
                <div class="row">
                    <label>描述:</label>
                    <textarea class="form-control" rows="3" placeholder="请输入阶段描述" data-field="description"></textarea>
                </div>
                
                <div class="row">
                    <div style="grid-column: 1 / -1; display: flex; gap: 10px; justify-content: flex-end; margin-top: 15px;">
                        <button type="button" class="btn btn-success btn-create">创建</button>
                        <button type="button" class="btn btn-secondary btn-cancel">取消</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 生成创建阶段HTML（通用方法，保持向下兼容）
     */
    generateCreateStageHtml() {
        const mainStages = Object.entries(this.tasks)
            .filter(([id, task]) => task.type === 'main')
            .map(([id, task]) => `<option value="${id}">${task.name}</option>`)
            .join('');

        return `
            <div class="gantt-form">
                <div class="row">
                    <label>所属主阶段:</label>
                    <select class="form-control" data-field="parent" required>
                        <option value="">请选择主阶段</option>
                        ${mainStages}
                    </select>
                </div>
                
                <div class="row">
                    <label>子阶段名称:</label>
                    <input type="text" class="form-control" placeholder="请输入子阶段名称" data-field="name" required>
                </div>
                
                <div class="row">
                    <label>开始时间:</label>
                    <input type="date" class="form-control" data-field="startDate" required>
                </div>
                
                <div class="row">
                    <label>结束时间:</label>
                    <input type="date" class="form-control" data-field="endDate" required>
                </div>
                
                <div class="row">
                    <label>负责人:</label>
                    <input type="text" class="form-control" placeholder="请输入负责人" data-field="owner">
                </div>
                
                <div class="row">
                    <label>描述:</label>
                    <textarea class="form-control" rows="3" placeholder="请输入阶段描述" data-field="description"></textarea>
                </div>
                
                <div class="row">
                    <div style="grid-column: 1 / -1; display: flex; gap: 10px; justify-content: flex-end; margin-top: 15px;">
                        <button type="button" class="btn btn-success btn-create">创建</button>
                        <button type="button" class="btn btn-secondary btn-cancel">取消</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 绑定创建子阶段事件
     */
    bindCreateSubStageEvents(parentStageId) {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 创建按钮
        const createBtn = detailsContent.querySelector('.btn-create');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.createNewSubStage(parentStageId);
            });
        }

        // 取消按钮
        const cancelBtn = detailsContent.querySelector('.btn-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hideDetails();
            });
        }
    }

    /**
     * 绑定创建阶段事件
     */
    bindCreateStageEvents() {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 创建按钮
        const createBtn = detailsContent.querySelector('.btn-create');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.createNewStage();
            });
        }

        // 取消按钮
        const cancelBtn = detailsContent.querySelector('.btn-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hideDetails();
            });
        }
    }

    /**
     * 创建新子阶段
     */
    createNewSubStage(parentStageId) {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 收集表单数据
        const formData = {};
        let isValid = true;

        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value.trim();
            
            // 验证必填字段
            if (input.hasAttribute('required') && !value) {
                input.classList.add('is-invalid');
                isValid = false;
                return;
            } else {
                input.classList.remove('is-invalid');
            }
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value) : null;
            }
            
            formData[field] = value;
        });

        if (!isValid) {
            if (window.showTopNotification) {
                window.showTopNotification('请填写所有必填字段', 'warning', 3000, 'topNotification');
            } else {
                alert('请填写所有必填字段');
            }
            return;
        }

        // 生成新的任务ID
        const newTaskId = `sub-stage-${Date.now()}`;

        // 创建新任务
        this.tasks[newTaskId] = {
            name: formData.name,
            type: 'sub',
            parent: parentStageId,
            startDate: formData.startDate,
            endDate: formData.endDate,
            owner: formData.owner,
            description: formData.description,
            status: 'pending',
            progress: 0
        };

        // 重新渲染甘特图
        this.renderGantt();
        
        // 隐藏详情面板
        this.hideDetails();

        // TODO: 调用API保存到后端
        console.log('创建新子阶段:', newTaskId, formData);
    }

    /**
     * 创建新阶段
     */
    createNewStage() {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 收集表单数据
        const formData = {};
        let isValid = true;

        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value.trim();
            
            // 验证必填字段
            if (input.hasAttribute('required') && !value) {
                input.classList.add('is-invalid');
                isValid = false;
                return;
            } else {
                input.classList.remove('is-invalid');
            }
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value) : null;
            }
            
            formData[field] = value;
        });

        if (!isValid) {
            if (window.showTopNotification) {
                window.showTopNotification('请填写所有必填字段', 'warning', 3000, 'topNotification');
            } else {
                alert('请填写所有必填字段');
            }
            return;
        }

        // 生成新的任务ID
        const newTaskId = `sub-stage-${Date.now()}`;

        // 创建新任务
        this.tasks[newTaskId] = {
            name: formData.name,
            type: 'sub',
            parent: formData.parent,
            startDate: formData.startDate,
            endDate: formData.endDate,
            owner: formData.owner,
            description: formData.description,
            status: 'pending',
            progress: 0
        };

        // 重新渲染甘特图
        this.renderGantt();
        
        // 隐藏详情面板
        this.hideDetails();

        // TODO: 调用API保存到后端
        console.log('创建新阶段:', newTaskId, formData);
    }

    /**
     * 隐藏详情面板
     */
    hideDetails() {
        const detailsPanel = this.container.querySelector('#ganttDetails');
        if (detailsPanel) {
            // 使用类切换实现收缩动画
            detailsPanel.classList.remove('expanded');
            // 清理可能的行内样式，确保完全收起
            detailsPanel.style.maxHeight = '';
            detailsPanel.style.overflow = '';
            this.isDetailsVisible = false;
            this.currentDetailTaskId = null;
            
            // 延迟清空内容，等待动画完成
            setTimeout(() => {
                const detailsContent = this.container.querySelector('#detailsContent');
                if (detailsContent && !this.isDetailsVisible) {
                    detailsContent.innerHTML = '';
                }
                // 动画结束后彻底隐藏，避免残留头部区域
                if (!this.isDetailsVisible) {
                    detailsPanel.style.display = 'none';
                }
            }, 300); // 与CSS transition时间一致
        }
    }

    /**
     * 切换任务展开状态
     */
    toggleTaskExpansion(taskId) {
        const taskItem = this.container.querySelector(`[data-task-id="${taskId}"]`);
        const expandIcon = taskItem?.querySelector('.expand-icon');
        
        if (!expandIcon || !taskItem) return;
        
        const mainStageId = taskId;
        const isExpanded = expandIcon.dataset.expanded === 'true';
        
        // 查找所有子任务元素（左侧任务树和右侧甘特条）
        const leftSubStages = this.container.querySelectorAll(`[data-parent="${mainStageId}"]`);
        const rightSubBars = this.container.querySelectorAll(`[data-task-id][data-parent="${mainStageId}"]`);
        
        if (isExpanded) {
            // 收起
            expandIcon.classList.remove('expanded');
            expandIcon.dataset.expanded = 'false';
            
            // 隐藏左侧子任务
            leftSubStages.forEach(subStage => {
                if (subStage.classList.contains('task-item')) {
                    subStage.style.display = 'none';
                }
            });
            
            // 隐藏右侧子甘特条
            rightSubBars.forEach(subBar => {
                const parentRow = subBar.closest('.gantt-bar-row');
                if (parentRow) {
                    parentRow.style.display = 'none';
                }
            });
            
        } else {
            // 展开
            expandIcon.classList.add('expanded');
            expandIcon.dataset.expanded = 'true';
            
            // 显示左侧子任务
            leftSubStages.forEach(subStage => {
                if (subStage.classList.contains('task-item')) {
                    subStage.style.display = 'flex';
                }
            });
            
            // 显示右侧子甘特条
            rightSubBars.forEach(subBar => {
                const parentRow = subBar.closest('.gantt-bar-row');
                if (parentRow) {
                    parentRow.style.display = 'flex';
                }
            });
        }
        
        console.log(`${isExpanded ? '收起' : '展开'}任务: ${taskId}`);
    }

    /**
     * 编辑任务
     */
    editTask(taskId) {
        console.log('editTask called with taskId:', taskId); // Debug log
        this.selectTask(taskId);
        // 编辑时也跳转定位到该阶段的当前位置
        this.jumpToTaskDate(taskId);
        this.showTaskDetails(taskId);
    }

    /**
     * 删除任务确认
     */
    confirmDeleteTask(taskId) {
        const task = this.tasks[taskId];
        if (!task) return;

        // 使用通用确认对话框
        if (window.showDeleteConfirm) {
            window.showDeleteConfirm({
                title: '确认删除子阶段',
                message: `确定要删除子阶段"${task.name}"吗？此操作不可恢复。`,
                dialogId: 'stageProgressConfirmDialog',
                onConfirm: async () => {
                    await this.deleteTask(taskId);
                }
            });
        } else {
            // 降级到原生确认框
            if (confirm(`确定要删除子阶段"${task.name}"吗？此操作不可恢复。`)) {
                this.deleteTask(taskId);
            }
        }
    }

    /**
     * 删除任务
     */
    async deleteTask(taskId) {
        const task = this.tasks[taskId];
        if (!task) return;

        // 不允许删除主阶段
        if (task.type === 'main') {
            if (window.showTopNotification) {
                window.showTopNotification('不能删除主阶段', 'warning', 3000, 'topNotification');
            } else {
                alert('不能删除主阶段');
            }
            return;
        }

        // 先调用后端API删除
        try {
            await this.deleteStageFromAPI(taskId);
        } catch (e) {
            console.error('后端删除失败:', e);
            throw e;
        }

        // 本地删除并刷新
        delete this.tasks[taskId];
        this.renderTaskList();
        this.renderGantt();
        this.hideDetails();
        console.log('删除任务完成:', taskId);
    }

    /**
     * API集成方法
     */

    /**
     * 调用后端API保存阶段数据
     */
    async saveStageToAPI(stageData) {
        if (!this.csrfToken) {
            console.warn('缺少CSRF Token，无法调用API');
            return;
        }

        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    object_type: this.objectType,
                    stage_data: stageData
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                console.log('阶段保存成功:', result);
                return result;
            } else {
                throw new Error(result.message || '保存失败');
            }
        } catch (error) {
            console.error('API调用失败:', error);
            if (window.showTopNotification) {
                window.showTopNotification('保存失败: ' + error.message, 'error', 3000, 'topNotification');
            } else {
                alert('保存失败: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * 调用后端API更新阶段数据
     */
    async updateStageToAPI(stageId, stageData) {
        if (!this.csrfToken) {
            console.warn('缺少CSRF Token，无法调用API');
            return;
        }

        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stages/${stageId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    object_type: this.objectType,
                    stage_data: stageData
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                console.log('阶段更新成功:', result);
                return result;
            } else {
                throw new Error(result.message || '更新失败');
            }
        } catch (error) {
            console.error('API调用失败:', error);
            if (window.showTopNotification) {
                window.showTopNotification('更新失败: ' + error.message, 'error', 3000, 'topNotification');
            } else {
                alert('更新失败: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * 调用后端API删除阶段
     */
    async deleteStageFromAPI(stageId) {
        if (!this.csrfToken) {
            console.warn('缺少CSRF Token，无法调用API');
            return;
        }

        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stages/${stageId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            const result = await response.json();
            
            if (response.ok) {
                console.log('阶段删除成功:', result);
                return result;
            } else {
                throw new Error(result.message || '删除失败');
            }
        } catch (error) {
            console.error('API调用失败:', error);
            if (window.showTopNotification) {
                window.showTopNotification('删除失败: ' + error.message, 'error', 3000, 'topNotification');
            } else {
                alert('删除失败: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * 调用后端API上传附件
     */
    async uploadAttachmentToAPI(stageId, file) {
        if (!this.csrfToken) {
            // 尝试从DOM获取CSRF Token
            this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                             document.querySelector('input[name="csrf_token"]')?.value;
            
            if (!this.csrfToken) {
                console.warn('缺少CSRF Token，无法调用API');
                return;
            }
        }

        const formData = new FormData();
        formData.append('attachment', file);
        formData.append('stage_key', stageId);

        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/stage-attachments/upload`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                console.log('附件上传成功:', result);
                return result;
            } else {
                throw new Error(result.message || '上传失败');
            }
        } catch (error) {
            console.error('附件上传失败:', error);
            if (window.showTopNotification) {
                window.showTopNotification('上传失败: ' + error.message, 'error', 3000, 'topNotification');
            } else {
                alert('上传失败: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * 更新保存任务详情方法，集成API调用
     */
    async saveTaskDetailsWithAPI(taskId) {
        const detailsContent = this.container.querySelector('#detailsContent');
        const task = this.tasks[taskId];
        
        if (!detailsContent || !task) return;

        // 收集表单数据
        const formData = {};
        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value;
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value).toISOString() : null;
            } else if (field === 'progress') {
                value = parseInt(value) || 0;
            }
            
            formData[field] = value;
        });

        // 智能校正：若子阶段处于进行中且实际开始时间超出计划范围，则自动调整计划时间
        if (task.type === 'sub' && task.parent) {
            const parent = this.tasks[task.parent];
            if (parent) {
                // 计算原计划时长（天）
                const originalDurationDays = (task.startDate && task.endDate)
                    ? Math.max(0, Math.ceil((new Date(task.endDate) - new Date(task.startDate)) / (1000*60*60*24)))
                    : 0;
                const ps = parent.startDate ? new Date(parent.startDate).getTime() : null;
                const pe = parent.endDate ? new Date(parent.endDate).getTime() : null;
                let cs = formData.startDate ? new Date(formData.startDate).getTime() : null;
                let ce = formData.endDate ? new Date(formData.endDate).getTime() : null;

                // 如果正在进行且有实际开始时间
                if (task.status === 'in-progress' && task.actualStartDate) {
                    const actualStart = new Date(task.actualStartDate);
                    const asTs = actualStart.getTime();
                    const violatesParent = (ps && asTs < ps) || (pe && asTs > pe);
                    const violatesChild = (cs && ps && cs < ps) || (ce && pe && ce > pe);

                    if (violatesParent || violatesChild) {
                        // 用实际开始时间作为新的计划开始
                        const newStart = new Date(actualStart);
                        const newEnd = new Date(actualStart);
                        newEnd.setDate(newEnd.getDate() + (originalDurationDays > 0 ? originalDurationDays : 0));

                        // 更新表单数据为新的计划值
                        formData.startDate = newStart.toISOString();
                        formData.endDate = newEnd.toISOString();
                        cs = newStart.getTime();
                        ce = newEnd.getTime();

                        // 为了避免再次触发越界校验，前端同步扩展父阶段的计划范围（仅前端会话内）
                        if (ps && cs < ps) parent.startDate = new Date(cs);
                        if (pe && ce > pe) parent.endDate = new Date(ce);
                    }
                }

                // 最终校验（若仍不在父阶段范围内，则提示）
                if (parent.startDate && parent.endDate) {
                    const ps2 = new Date(parent.startDate).getTime();
                    const pe2 = new Date(parent.endDate).getTime();
                    if ((cs && cs < ps2) || (ce && ce > pe2) || (cs && ce && cs > ce)) {
                        const msg = '子阶段时间必须在所属主阶段范围内';
                        if (window.showTopNotification) {
                            window.showTopNotification(msg, 'warning', 3000, 'topNotification');
                        } else { alert(msg); }
                        return;
                    }
                }
            }
        }

        // 准备API数据
        const stageData = {
            name: formData.name,
            parent_stage: formData.parent,
            owner: formData.owner,
            start_date: formData.startDate,
            end_date: formData.endDate,
            progress: formData.progress,
            description: formData.description,
            status: task.status
        };

        try {
            // 显示加载状态
            const saveButton = detailsContent.querySelector('[data-action="saveChanges"]');
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.textContent = '保存中...';
            }

            // 子阶段调用后端API；主阶段调用主阶段计划API
            if (task.type === 'sub') {
                await this.updateStageToAPI(taskId, stageData);
            } else if (task.type === 'main') {
                await this.saveMainStagePlanToAPI(taskId, task.startDate || formData.startDate, task.endDate || formData.endDate);
            }

            // 更新本地任务数据（确保时间为Date对象）
            task.name = formData.name ?? task.name;
            task.owner = formData.owner ?? task.owner;
            if (formData.parent) task.parent = formData.parent;
            task.startDate = formData.startDate ? new Date(formData.startDate) : null;
            task.endDate = formData.endDate ? new Date(formData.endDate) : null;
            task.progress = typeof formData.progress === 'number' ? formData.progress : (parseInt(formData.progress) || 0);
            task.description = formData.description ?? task.description;

            // 重新渲染列表与甘特条
            this.renderTaskList();
            this.renderGantt();
            
            // 同步父阶段范围覆盖所有子阶段（仅对子阶段）
            if (task.type === 'sub' && task.parent) {
                this.syncParentRangeFromChildren(task.parent);
                // 将同步后的父阶段计划写回后端
                const parent = this.tasks[task.parent];
                await this.saveMainStagePlanToAPI(task.parent, parent.startDate, parent.endDate);
                this.renderTaskList();
                this.renderGantt();
            }
            
            // 保存后保持详情面板打开，刷新内容
            this.refreshDetailsIfOpen(taskId);
        } catch (error) {
            // 恢复按钮状态
            const saveButton = detailsContent.querySelector('[data-action="saveChanges"]');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = '保存修改';
            }
        }
    }

    /**
     * 持久化主阶段计划起止时间和状态
     */
    async saveMainStagePlanToAPI(stageKey, startDate, endDate, status = null) {
        try {
            // 规范化日期，避免非法字符串
            const toISO = (d) => {
                try {
                    if (!d) return null;
                    const dt = (d instanceof Date) ? d : new Date(d);
                    if (isNaN(dt.getTime())) return null;
                    return dt.toISOString();
                } catch (_) { return null; }
            };
            const body = {
                stage_key: stageKey,
                planned_start_date: toISO(startDate),
                planned_end_date: toISO(endDate),
                progress: this.tasks[stageKey]?.progress ?? null
            };
            // 如果提供了状态参数，添加到请求体中
            if (status) {
                body.status = status;
            }
            const res = await fetch(`/product-management/api/rd-products/${this.objectId}/main-stage/plan`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(body)
            });
            const result = await res.json();
            if (!res.ok) throw new Error(result.message || '保存主阶段计划失败');
            return result;
        } catch (e) {
            console.error('保存主阶段计划失败:', e);
            if (window.showTopNotification) {
                window.showTopNotification('保存主阶段计划失败: ' + e.message, 'error', 3000, 'topNotification');
            }
            return null;
        }
    }

    /**
     * 使父阶段的计划起止覆盖所有子阶段
     */
    syncParentRangeFromChildren(parentId) {
        const parent = this.tasks[parentId];
        if (!parent) return;
        const children = Object.values(this.tasks).filter(t => t.parent === parentId);
        if (!children.length) return;
        let minStart = null;
        let maxEnd = null;
        children.forEach(ch => {
            if (ch.startDate) {
                const cs = new Date(ch.startDate);
                if (!minStart || cs < minStart) minStart = cs;
            }
            if (ch.endDate) {
                const ce = new Date(ch.endDate);
                if (!maxEnd || ce > maxEnd) maxEnd = ce;
            }
        });
        if (minStart && (!parent.startDate || minStart < new Date(parent.startDate))) {
            parent.startDate = minStart;
        }
        if (maxEnd && (!parent.endDate || maxEnd > new Date(parent.endDate))) {
            parent.endDate = maxEnd;
        }
    }

    /**
     * 更新创建新子阶段方法，集成API调用
     */
    async createNewSubStageWithAPI() {
        const detailsContent = this.container.querySelector('#detailsContent');
        if (!detailsContent) return;

        // 收集表单数据
        const formData = {};
        detailsContent.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            let value = input.value;
            
            if (field === 'startDate' || field === 'endDate') {
                value = value ? new Date(value).toISOString() : null;
            } else if (field === 'progress') {
                value = parseInt(value) || 0;
            }
            
            formData[field] = value;
        });

        // 验证必填字段
        if (!formData.name || !formData.parent) {
            if (window.showTopNotification) {
                window.showTopNotification('请填写阶段名称和选择主阶段', 'warning', 3000, 'topNotification');
            } else {
                alert('请填写阶段名称和选择主阶段');
            }
            return;
        }

        // 禁止在已完成的主阶段下新增子阶段
        const parentTaskForCreate = this.tasks[formData.parent];
        if (parentTaskForCreate && parentTaskForCreate.status === 'completed') {
            const msg = '主阶段已完成，不能再添加子阶段';
            if (window.showTopNotification) {
                window.showTopNotification(msg, 'warning', 3000, 'topNotification');
            } else {
                alert(msg);
            }
            return;
        }

        // 准备API数据
        const stageData = {
            name: formData.name,
            parent_stage: formData.parent,
            owner: formData.owner,
            start_date: formData.startDate,
            end_date: formData.endDate,
            progress: formData.progress || 0,
            description: formData.description || '',
            status: 'planned'
        };

        try {
            // 显示加载状态
            const createButton = detailsContent.querySelector('[data-action="createStage"]');
            if (createButton) {
                createButton.disabled = true;
                createButton.textContent = '创建中...';
            }

            // 调用API
            const result = await this.saveStageToAPI(stageData);

            // 生成新的子阶段ID (使用API返回的ID或生成临时ID)
            const newTaskId = result?.id || `sub-${Date.now()}`;
            
            // 创建新的子阶段任务
            const newTask = {
                id: newTaskId,
                name: formData.name,
                type: 'sub',
                parent: formData.parent,
                owner: formData.owner || '',
                startDate: formData.startDate ? new Date(formData.startDate) : null,
                endDate: formData.endDate ? new Date(formData.endDate) : null,
                progress: formData.progress || 0,
                status: 'planned',
                description: formData.description || '',
                attachments: [],
                createdAt: new Date().toLocaleString(),
                updatedAt: new Date().toLocaleString()
            };

            // 添加到任务列表
            this.tasks[newTaskId] = newTask;

            // 同步父阶段计划时间以覆盖新子阶段
            const parentTask = this.tasks[newTask.parent];
            if (parentTask) {
                const childStart = newTask.startDate ? new Date(newTask.startDate) : null;
                const childEnd = newTask.endDate ? new Date(newTask.endDate) : null;
                if (childStart) {
                    if (!parentTask.startDate || new Date(parentTask.startDate) > childStart) {
                        parentTask.startDate = new Date(childStart);
                    }
                }
                if (childEnd) {
                    if (!parentTask.endDate || new Date(parentTask.endDate) < childEnd) {
                        parentTask.endDate = new Date(childEnd);
                    }
                }
            }

            // 重新渲染
            this.renderTasks();
            this.renderGantt();
            
            // 隐藏详情面板
            this.hideDetails();

            // 显示成功提示
            if (window.showTopNotification) {
                window.showTopNotification('子阶段创建成功', 'success', 3000, 'topNotification');
            }

            console.log('子阶段创建成功:', newTask);

        } catch (error) {
            console.error('创建子阶段失败:', error);

            // 显示错误提示
            if (window.showTopNotification) {
                window.showTopNotification('创建失败: ' + (error.message || '网络错误'), 'error', 3000, 'topNotification');
            } else {
                alert('创建失败: ' + (error.message || '网络错误'));
            }

            // 恢复按钮状态
            const createButton = detailsContent.querySelector('[data-action="createStage"]');
            if (createButton) {
                createButton.disabled = false;
                createButton.textContent = '保存新阶段';
            }
        }
    }

    /**
     * 显示上传进度
     */
    showUploadProgress(totalFiles) {
        // 创建进度提示容器
        const progressContainer = document.createElement('div');
        progressContainer.className = 'upload-progress-overlay';
        progressContainer.innerHTML = `
            <div class="upload-progress-dialog">
                <div class="upload-progress-header">
                    <i class="fas fa-upload"></i>
                    <span>正在上传文件...</span>
                </div>
                <div class="upload-progress-content">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                    <div class="upload-status">
                        <span class="current-file">准备上传...</span>
                        <span class="file-count">0/${totalFiles}</span>
                    </div>
                </div>
            </div>
        `;
        
        // 添加样式
        if (!document.querySelector('#upload-progress-styles')) {
            const style = document.createElement('style');
            style.id = 'upload-progress-styles';
            style.textContent = `
                .upload-progress-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }
                .upload-progress-dialog {
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    min-width: 400px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .upload-progress-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                    font-weight: bold;
                }
                .upload-progress-header i {
                    margin-right: 8px;
                    color: #007bff;
                }
                .upload-progress-content .progress {
                    height: 10px;
                    margin-bottom: 10px;
                    background-color: #e9ecef;
                    border-radius: 5px;
                    overflow: hidden;
                }
                .upload-progress-content .progress-bar {
                    background-color: #007bff;
                    height: 100%;
                    transition: width 0.3s ease;
                }
                .upload-status {
                    display: flex;
                    justify-content: space-between;
                    font-size: 14px;
                    color: #666;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(progressContainer);
        return progressContainer;
    }

    /**
     * 更新上传进度
     */
    updateUploadProgress(container, currentIndex, totalFiles, fileName) {
        const progressBar = container.querySelector('.progress-bar');
        const currentFile = container.querySelector('.current-file');
        const fileCount = container.querySelector('.file-count');
        
        const percentage = (currentIndex / totalFiles) * 100;
        progressBar.style.width = `${percentage}%`;
        currentFile.textContent = `正在上传: ${fileName}`;
        fileCount.textContent = `${currentIndex}/${totalFiles}`;
    }

    /**
     * 隐藏上传进度
     */
    hideUploadProgress(container) {
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    }

    /**
     * 刷新产品状态显示
     * 主阶段完成后调用，更新页面上的产品状态信息
     */
    async refreshProductStatus() {
        try {
            const response = await fetch(`/product-management/api/rd-products/${this.objectId}/status`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken || ''
                },
                credentials: 'include'
            });

            if (!response.ok) {
                console.warn('获取产品状态失败:', response.status);
                return;
            }

            const result = await response.json();
            if (result.success && result.data) {
                this.updateProductStatusDisplay(result.data.status, result.data.stage_name, result.data.current_stage_key);
                console.log('产品状态已刷新:', result.data);
            }
        } catch (e) {
            console.warn('刷新产品状态失败:', e);
        }
    }

    /**
     * 更新页面上的产品状态显示
     */
    updateProductStatusDisplay(status, stageName, stageKey) {
        // 更新页面头部的产品状态显示
        const statusElements = document.querySelectorAll('.product-status, .current-stage-name, [data-field="status"]');
        statusElements.forEach(el => {
            if (el.classList.contains('product-status') || el.dataset.field === 'status') {
                el.textContent = status || stageName;
            } else if (el.classList.contains('current-stage-name')) {
                el.textContent = stageName;
            }
        });

        // 更新阶段徽章颜色（如果有相关元素）
        const statusBadges = document.querySelectorAll('.status-badge, .badge-status');
        statusBadges.forEach(badge => {
            // 移除旧的状态类
            badge.classList.remove('badge-primary', 'badge-warning', 'badge-success', 'badge-info', 'badge-danger');

            // 根据新状态添加对应的类
            if (status) {
                let badgeClass = 'badge-info'; // 默认
                if (status.includes('已') || status.includes('完成')) badgeClass = 'badge-success';
                else if (status.includes('中') || status.includes('进行')) badgeClass = 'badge-warning';
                else if (status.includes('申请')) badgeClass = 'badge-info';

                badge.classList.add(badgeClass);
                badge.textContent = status;
            }
        });

        // 触发自定义事件，通知其他组件状态已更新
        const event = new CustomEvent('productStatusUpdated', {
            detail: { status, stageName, stageKey }
        });
        document.dispatchEvent(event);
    }
}

// 自动初始化甘特图组件
document.addEventListener('DOMContentLoaded', function() {
    // 查找页面中的甘特图配置数据并自动初始化
    document.querySelectorAll('[id^="gantt-data-"]').forEach(script => {
        try {
            const data = JSON.parse(script.textContent);
            if (data.containerId) {
                console.log('自动初始化甘特图组件:', data.containerId);
                const inst = new GanttChart(data);
                // 暴露全局实例便于调试
                window.__gantt = window.__gantt || {};
                window.__gantt[data.containerId] = inst;
            }
        } catch (e) {
            console.warn('甘特图配置解析失败:', e);
        }
    });
});
