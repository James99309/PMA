/**
 * 任务管理中心 - Alpine.js 组件
 *
 * 左侧任务列表 + 右侧任务详情分栏布局
 * 支持子任务CRUD、里程碑确认、跟进记录、文件上传
 */

// Alpine store for modal state (accessible from outside x-data scope)
document.addEventListener('alpine:init', () => {
    Alpine.store('taskMgmt', {
        showSubtaskModal: false,
        editingSubtask: null,
        subtaskForm: { title: '', description: '', assignee_id: '', start_date: '', due_date: '', is_milestone: false, selectedConfirmers: [] },
        showMilestoneModal: false,
        milestoneTarget: null,
        milestoneAction: '',
        milestoneComment: '',
        showPauseModal: false,
        pauseReason: '',
        allUsers: [],
        _component: null,  // reference to main component

        saveSubtaskFromModal() {
            if (this._component) this._component.saveSubtask();
        },
        submitMilestoneDecisionFromModal() {
            if (this._component) this._component.submitMilestoneDecision();
        },
        submitPauseFromModal() {
            if (this._component) this._component.pauseTask();
        },
        // 里程碑确认人多选辅助
        selectConfirmer(user) {
            if (!this.subtaskForm.selectedConfirmers.find(u => u.id === user.id)) {
                this.subtaskForm.selectedConfirmers.push(user);
            }
        },
        removeConfirmer(userId) {
            this.subtaskForm.selectedConfirmers = this.subtaskForm.selectedConfirmers.filter(u => u.id !== userId);
        },
        isConfirmerSelected(userId) {
            return this.subtaskForm.selectedConfirmers.some(u => u.id === userId);
        },
    });
});


function taskManagement() {
    return {
        // ── 列表状态 ──
        tasks: [],
        totalTasks: 0,
        loading: false,
        tab: 'all',
        sortBy: 'updated',
        search: '',
        tabs: [
            { key: 'all',     label: window.TASK_I18N?.tabs?.all     || '全部' },
            { key: 'my',      label: window.TASK_I18N?.tabs?.my      || '我负责的' },
            { key: 'created', label: window.TASK_I18N?.tabs?.created || '我创建的' },
            { key: 'shared',  label: window.TASK_I18N?.tabs?.shared  || '我参与的' },
            { key: 'review',  label: window.TASK_I18N?.tabs?.review  || '待我审核' },
        ],

        // ── 详情状态 ──
        selectedTaskId: null,
        selectedTask: null,
        detailLoading: false,
        subtasks: [],
        subtaskUpdates: {},
        expandedSubtasks: [],
        expandedTimelineGroups: [],
        taskReplies: [],
        sharedUserNames: [],

        // ── 计算属性 ──
        get completedSubtaskCount() {
            return this.subtasks.filter(s => s.status === 'completed').length;
        },

        // ── 附件 ──
        taskAttachments: [],
        attachSubtaskId: '',
        uploadingFile: false,
        uploadProgress: 0,

        // ── 子任务跟进 ──
        newUpdateContent: {},
        pendingUpdateFiles: {},
        newReplyContent: '',
        replySubtaskId: null,
        replySubtaskTitle: '',
        showMentionDrop: false,
        mentionList: [],
        mentionIdx: 0,

        // ── 用户数据 ──
        allUsers: [],
        currentUserId: null,

        // ── 初始化 ──
        async init() {
            this.currentUserId = window.CURRENT_USER_ID;
            Alpine.store('taskMgmt')._component = this;
            await this.loadUsers();

            // URL ?task_id=X&subtask_id=Y — 从待办（里程碑确认等）点击过来
            const urlParams = new URLSearchParams(window.location.search);
            const urlTaskId = urlParams.get('task_id');
            const urlSubtaskId = urlParams.get('subtask_id');
            if (urlTaskId) {
                // 切换到"待我审核"tab 并重新加载列表
                this.tab = 'review';
                await this.loadTasks();
                await this.selectTask(parseInt(urlTaskId));
                // 自动展开对应子任务
                if (urlSubtaskId) {
                    this.focusSubtask(parseInt(urlSubtaskId));
                }
                // 清理 URL 参数
                const cleaned = new URL(window.location);
                cleaned.searchParams.delete('task_id');
                cleaned.searchParams.delete('subtask_id');
                history.replaceState(null, '', cleaned.pathname + cleaned.search);
            } else {
                await this.loadTasks();
            }

            // URL ?open=<taskId> — 从导航栏下拉点击过来时自动打开该任务
            const urlOpen = urlParams.get('open');
            if (urlOpen) {
                this.selectTask(parseInt(urlOpen));
                // 清理 URL 参数避免刷新重复打开
                const cleaned = new URL(window.location);
                cleaned.searchParams.delete('open');
                history.replaceState(null, '', cleaned.pathname + cleaned.search);
            }

            // Listen for task creation/update events from tw_task_modal
            window.addEventListener('task-created', () => this.loadTasks());
            window.addEventListener('task-updated', () => {
                this.loadTasks();
                if (this.selectedTaskId) this.selectTask(this.selectedTaskId);
            });
        },

        // ══════════════════════════════════════════════════════
        // API 调用
        // ══════════════════════════════════════════════════════

        async loadTasks() {
            this.loading = true;
            try {
                const params = new URLSearchParams({
                    tab: this.tab,
                    sort: this.sortBy,
                    search: this.search,
                    per_page: '50',
                });
                const res = await fetch('/task/api/management/list?' + params);
                const data = await res.json();
                if (data.success) {
                    this.tasks = data.data;
                    this.totalTasks = data.total;
                }
            } catch (e) {
                console.error('加载任务列表失败:', e);
            } finally {
                this.loading = false;
            }
        },

        async selectTask(taskId) {
            if (this.selectedTaskId === taskId) return;
            this.selectedTaskId = taskId;
            this.detailLoading = true;
            this.subtasks = [];
            this.subtaskUpdates = {};
            this.expandedSubtasks = [];
            this.taskReplies = [];
            this.sharedUserNames = [];
            this.taskAttachments = [];

            try {
                const [taskRes, subtasksRes] = await Promise.all([
                    fetch('/task/api/' + taskId),
                    fetch('/task/api/' + taskId + '/subtasks'),
                ]);
                const taskData = await taskRes.json();
                const subtasksData = await subtasksRes.json();

                if (taskData.success) {
                    this.selectedTask = taskData.data;
                    this.taskReplies = taskData.data.replies || [];
                    this.taskAttachments = taskData.data.attachments || [];
                    // Resolve shared user names
                    const sharedIds = taskData.data.shared_with_users || [];
                    this.sharedUserNames = sharedIds.map(id => {
                        const u = this.allUsers.find(u => u.id === id);
                        return u ? (u.real_name || u.username) : ('ID:' + id);
                    });
                }
                if (subtasksData.success) {
                    this.subtasks = subtasksData.data;
                    // Pre-populate updates from inline data
                    for (const st of this.subtasks) {
                        if (st.updates) {
                            this.subtaskUpdates[st.id] = st.updates;
                        }
                    }
                }
            } catch (e) {
                console.error('加载任务详情失败:', e);
            } finally {
                this.detailLoading = false;
            }
        },

        async saveSubtask() {
            const store = Alpine.store('taskMgmt');
            const form = store.subtaskForm;
            if (!form.title.trim()) return;

            const payload = {
                title: form.title.trim(),
                description: form.description.trim() || null,
                assignee_id: form.assignee_id ? parseInt(form.assignee_id) : null,
                start_date: form.start_date || null,
                due_date: form.due_date || null,
                is_milestone: form.is_milestone,
                milestone_confirmer_ids: form.is_milestone && form.selectedConfirmers.length > 0
                    ? form.selectedConfirmers.map(u => u.id) : [],
            };

            try {
                let res;
                if (store.editingSubtask) {
                    res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks/' + store.editingSubtask.id, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                } else {
                    res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                }
                const data = await res.json();
                if (data.success) {
                    store.showSubtaskModal = false;
                    await this.refreshSubtasks();
                    await this.loadTasks(); // refresh progress in list
                }
            } catch (e) {
                console.error('保存子任务失败:', e);
            }
        },

        async deleteSubtask(subtaskId) {
            if (!confirm('确定删除此子任务？')) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks/' + subtaskId, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    await this.refreshSubtasks();
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('删除子任务失败:', e);
            }
        },

        async startSubtask(subtaskId) {
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks/' + subtaskId + '/status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'start' }),
                });
                const data = await res.json();
                if (data.success) {
                    await this.refreshSubtasks();
                } else if (data.message) {
                    alert(data.message);
                }
            } catch (e) {
                console.error('开始子任务失败:', e);
            }
        },

        async completeSubtask(subtaskId) {
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks/' + subtaskId + '/status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'complete' }),
                });
                const data = await res.json();
                if (data.success) {
                    await this.refreshSubtasks();
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('完成子任务失败:', e);
            }
        },

        async submitMilestoneDecision() {
            const store = Alpine.store('taskMgmt');
            if (!store.milestoneTarget) return;

            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks/' + store.milestoneTarget.id + '/milestone', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: store.milestoneAction,
                        comment: store.milestoneComment.trim(),
                    }),
                });
                const data = await res.json();
                if (data.success) {
                    store.showMilestoneModal = false;
                    await this.refreshSubtasks();
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('里程碑操作失败:', e);
            }
        },

        async submitTaskReview(action, comment) {
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/review', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action, comment: comment || '' }),
                });
                const data = await res.json();
                if (data.success) {
                    // 重新加载任务详情和列表
                    this.selectedTaskId = null;  // 强制刷新
                    await this.selectTask(data.data.id);
                    await this.loadTasks();
                } else {
                    alert(data.message);
                }
            } catch (e) {
                console.error('任务审核失败:', e);
            }
        },

        onReplyInput(e) {
            const val = this.newReplyContent;
            const cursor = e.target.selectionStart || val.length;
            const before = val.substring(0, cursor);
            const atIdx = before.lastIndexOf('@');
            if (atIdx >= 0 && (atIdx === 0 || before[atIdx - 1] === ' ')) {
                const query = before.substring(atIdx + 1).toLowerCase();
                this.mentionList = this.subtasks.filter(s =>
                    s.title.toLowerCase().includes(query)
                );
                this.mentionIdx = 0;
                this.showMentionDrop = this.mentionList.length > 0 || query.length === 0;
            } else {
                this.showMentionDrop = false;
            }
        },

        selectMention(st) {
            if (!st) return;
            this.replySubtaskId = st.id;
            this.replySubtaskTitle = st.title;
            // 移除输入中的 @xxx 部分
            const val = this.newReplyContent;
            const atIdx = val.lastIndexOf('@');
            if (atIdx >= 0) {
                this.newReplyContent = val.substring(0, atIdx).trimEnd();
            }
            this.showMentionDrop = false;
            this.$nextTick(() => this.$refs.replyInput && this.$refs.replyInput.focus());
        },

        async addReply() {
            const content = this.newReplyContent.trim();
            if (!content || !this.selectedTaskId) return;

            try {
                const body = { content };
                if (this.replySubtaskId) body.subtask_id = this.replySubtaskId;

                const res = await fetch('/task/api/' + this.selectedTaskId + '/replies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                const data = await res.json();
                if (data.success) {
                    this.newReplyContent = '';
                    this.replySubtaskId = null;
                    this.replySubtaskTitle = '';
                    this.taskReplies.push(data.data);
                }
            } catch (e) {
                console.error('添加讨论失败:', e);
            }
        },

        async completeTask() {
            if (!this.selectedTaskId) return;
            if (!confirm('确定完成此任务？')) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/complete', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    this.selectedTask.status = 'completed';
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('完成任务失败:', e);
            }
        },

        async pauseTask() {
            const store = Alpine.store('taskMgmt');
            const reason = (store.pauseReason || '').trim();
            if (!reason) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/pause', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason }),
                });
                const data = await res.json();
                if (data.success) {
                    store.showPauseModal = false;
                    store.pauseReason = '';
                    this.selectedTask.status = 'paused';
                    await this.loadTasks();
                    // 刷新讨论（暂停理由会记录为回复）
                    const taskRes = await fetch('/task/api/' + this.selectedTaskId);
                    const taskData = await taskRes.json();
                    if (taskData.success) this.taskReplies = taskData.data.replies || [];
                } else {
                    if (window.showToast) window.showToast(data.message, 'error');
                }
            } catch (e) {
                console.error('暂停任务失败:', e);
            }
        },

        async resumeTask() {
            if (!this.selectedTaskId) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'in_progress' }),
                });
                const data = await res.json();
                if (data.success) {
                    this.selectedTask.status = 'in_progress';
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('恢复任务失败:', e);
            }
        },

        async deleteTask() {
            if (!this.selectedTaskId) return;
            if (!confirm('确定删除此任务？此操作不可撤销。')) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    this.selectedTask = null;
                    this.selectedTaskId = null;
                    await this.loadTasks();
                }
            } catch (e) {
                console.error('删除任务失败:', e);
            }
        },

        async uploadAttachment(event) {
            const files = event.target.files;
            if (!files || files.length === 0 || !this.selectedTaskId) return;
            this.uploadingFile = true;
            this.uploadProgress = 0;
            const taskId = this.selectedTaskId;
            const self = this;

            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                if (this.attachSubtaskId) formData.append('subtask_id', this.attachSubtaskId);
                try {
                    const data = await new Promise((resolve, reject) => {
                        const xhr = new XMLHttpRequest();
                        xhr.open('POST', '/task/api/' + taskId + '/attachments');
                        xhr.upload.onprogress = (e) => {
                            if (e.lengthComputable) self.uploadProgress = Math.round((e.loaded / e.total) * 100);
                        };
                        xhr.onload = () => { try { resolve(JSON.parse(xhr.responseText)); } catch { reject(new Error('parse error')); } };
                        xhr.onerror = () => reject(new Error('network error'));
                        xhr.send(formData);
                    });
                    if (data.success) {
                        data.data.uploaded_by = data.data.uploaded_by || this.currentUserId;
                        this.taskAttachments.push(data.data);
                    }
                } catch (e) {
                    console.error('上传附件失败:', e);
                }
                this.uploadProgress = 0;
            }
            this.uploadingFile = false;
            event.target.value = '';
        },

        async deleteAttachment(attId) {
            if (!confirm('确定删除此附件？')) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/attachments/' + attId, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    this.taskAttachments = this.taskAttachments.filter(a => a.id !== attId);
                }
            } catch (e) {
                console.error('删除附件失败:', e);
            }
        },

        formatFileSize(bytes) {
            if (!bytes) return '';
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / 1048576).toFixed(1) + ' MB';
        },

        async loadUsers() {
            try {
                const res = await fetch('/user/api/users/active');
                const data = await res.json();
                if (data.success) {
                    this.allUsers = data.data;
                    Alpine.store('taskMgmt').allUsers = data.data;
                }
            } catch (e) {
                console.error('加载用户列表失败:', e);
            }
        },

        async refreshSubtasks() {
            if (!this.selectedTaskId) return;
            try {
                const res = await fetch('/task/api/' + this.selectedTaskId + '/subtasks');
                const data = await res.json();
                if (data.success) {
                    this.subtasks = data.data;
                    for (const st of this.subtasks) {
                        if (st.updates) {
                            this.subtaskUpdates[st.id] = st.updates;
                        }
                    }
                }
            } catch (e) {
                console.error('刷新子任务失败:', e);
            }
        },

        // ══════════════════════════════════════════════════════
        // UI 辅助方法
        // ══════════════════════════════════════════════════════

        subtasksByDate() {
            return [...this.subtasks].sort((a, b) => {
                const da = a.due_date || a.start_date || '';
                const db = b.due_date || b.start_date || '';
                return da.localeCompare(db);
            });
        },

        focusSubtask(id) {
            if (this.expandedSubtasks[0] === id) {
                this.expandedSubtasks = [];
                this.attachSubtaskId = '';
            } else {
                this.expandedSubtasks = [id];
                this.attachSubtaskId = id;
            }
        },

        filteredAttachments() {
            const focusId = this.expandedSubtasks[0];
            if (!focusId) return this.taskAttachments;
            return this.taskAttachments.filter(a => a.subtask_id == focusId);
        },

        filteredReplies() {
            const focusId = this.expandedSubtasks[0];
            if (!focusId) return this.taskReplies;
            return this.taskReplies.filter(r => r.subtask_id == focusId);
        },

        toggleSubtask(id) {
            const idx = this.expandedSubtasks.indexOf(id);
            if (idx >= 0) {
                this.expandedSubtasks.splice(idx, 1);
            } else {
                this.expandedSubtasks.push(id);
            }
        },

        priorityDotClass(p) {
            return {
                'urgent': 'bg-red-500',
                'high':   'bg-orange-500',
                'normal': 'bg-blue-500',
                'low':    'bg-slate-400',
            }[p] || 'bg-slate-400';
        },

        priorityBadgeClass(p) {
            return {
                'urgent': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
                'high':   'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
                'normal': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
                'low':    'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
            }[p] || 'bg-slate-100 text-slate-600';
        },

        priorityText(p) {
            return { 'urgent': '紧急', 'high': '高', 'normal': '普通', 'low': '低' }[p] || p;
        },

        statusBadgeClass(s) {
            return {
                'pending':     'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
                'in_progress': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
                'completed':   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                'delayed':     'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
                'paused':      'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
                'pending_review': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
            }[s] || 'bg-slate-100 text-slate-600';
        },

        statusText(s) {
            return {
                'pending':     '等待开始',
                'in_progress': '进行中',
                'completed':   '已完成',
                'delayed':     '已延迟',
                'paused':      '已暂停',
                'pending_review': '待审核',
            }[s] || s;
        },

        subtaskStatusIcon(st) {
            // 里程碑待确认 — 优先于 completed 判断
            if (st.is_milestone && st.milestone_status === 'pending_confirmation') {
                return '<span class="material-symbols-outlined text-base text-amber-500">hourglass_top</span>';
            }
            // 里程碑被驳回
            if (st.is_milestone && st.milestone_status === 'rejected') {
                return '<span class="material-symbols-outlined text-base text-red-500" style="font-variation-settings:\'FILL\' 1">cancel</span>';
            }
            if (st.status === 'completed') {
                return '<span class="material-symbols-outlined text-base text-green-500" style="font-variation-settings:\'FILL\' 1">check_circle</span>';
            }
            if (st.status === 'delayed') {
                return '<span class="material-symbols-outlined text-base text-red-500">warning</span>';
            }
            if (st.status === 'in_progress') {
                return '<span class="material-symbols-outlined text-base text-blue-500">play_circle</span>';
            }
            return '<span class="material-symbols-outlined text-base text-slate-400">radio_button_unchecked</span>';
        },

        milestoneStatusText(st) {
            return {
                'pending_confirmation': '等待确认',
                'confirmed': '已确认',
                'rejected': '已驳回',
            }[st.milestone_status] || '';
        },

        formatDate(d) {
            if (!d) return '';
            try {
                const dt = new Date(d);
                if (isNaN(dt.getTime())) return '';
                return (dt.getMonth() + 1) + '/' + dt.getDate();
            } catch { return ''; }
        },

        formatDateTime(dt) {
            if (!dt) return '';
            try {
                const d = new Date(dt);
                if (isNaN(d.getTime())) return '';
                const pad = n => String(n).padStart(2, '0');
                return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
            } catch { return ''; }
        },

        formatDateRange(s, e) {
            const start = this.formatDate(s);
            const end = this.formatDate(e);
            if (start && end) return start + ' - ' + end;
            if (start) return start + ' -';
            if (end) return '- ' + end;
            return '';
        },

        isOverdue(task) {
            if (!task.due_date || task.status === 'completed' || task.status === 'cancelled') return false;
            try {
                return new Date(task.due_date) < new Date();
            } catch { return false; }
        },

        renderTimeline() {
            const self = this;
            window._tlFocus = (id) => self.focusSubtask(id);
            window._tlToggleGroup = (key) => {
                const idx = self.expandedTimelineGroups.indexOf(key);
                if (idx >= 0) self.expandedTimelineGroups.splice(idx, 1);
                else self.expandedTimelineGroups.push(key);
            };

            const subs = this.subtasks
                .filter(s => s.due_date || s.start_date)
                .map(s => ({ ...s, _pos_date: s.due_date || s.start_date }));
            if (!subs.length) return '';

            let allDates = subs.map(s => new Date(s._pos_date));
            if (this.selectedTask.start_date) allDates.push(new Date(this.selectedTask.start_date));
            if (this.selectedTask.due_date) allDates.push(new Date(this.selectedTask.due_date));
            let minD = new Date(Math.min(...allDates));
            let maxD = new Date(Math.max(...allDates));
            if (maxD - minD < 86400000) {
                minD.setDate(minD.getDate() - 1);
                maxD.setDate(maxD.getDate() + 1);
            }
            const totalDays = Math.max(1, (maxD - minD) / 86400000);
            const totalMs = maxD - minD || 1;

            const fmt = (d) => { const t = new Date(d); return (t.getMonth()+1) + '/' + t.getDate(); };
            const dayKey = (d) => new Date(d).toISOString().slice(0, 10);
            const pct = (d) => ((new Date(d) - minD) / totalMs * 100);

            const now = new Date(); now.setHours(0,0,0,0);
            const showToday = now >= minD && now <= maxD;
            const todayPct = pct(now).toFixed(2);

            const dotColor = {
                completed:   'bg-green-500',
                in_progress: 'bg-blue-500',
                delayed:     'bg-red-500',
                pending:     'bg-slate-300 dark:bg-slate-500 ring-1 ring-slate-400',
                paused:      'bg-amber-400',
            };

            // 按日期分组
            const sorted = subs.map(s => ({ ...s, _pct: pct(s._pos_date) }))
                               .sort((a, b) => a._pct - b._pct);
            const groups = [];
            sorted.forEach(s => {
                const dk = dayKey(s._pos_date);
                const last = groups.length ? groups[groups.length - 1] : null;
                if (last && last.key === dk) {
                    last.items.push(s);
                } else {
                    groups.push({ key: dk, items: [s], pct: s._pct });
                }
            });

            // 展开组额外需要的百分比空间
            const SPREAD_PCT = 4; // 展开时每个节点间隔 4%
            let extraPct = 0;
            groups.forEach(g => {
                if (g.items.length > 1 && this.expandedTimelineGroups.includes(g.key)) {
                    extraPct += (g.items.length - 1) * SPREAD_PCT;
                }
            });

            // 计算最终定位：考虑展开后的偏移
            const renderNodes = []; // { s, leftPct, isGroup }
            let accOffset = 0; // 累积偏移
            const scale = 100 / (100 + extraPct); // 缩放因子

            groups.forEach(g => {
                const basePct = g.pct * scale + accOffset;

                if (g.items.length === 1) {
                    renderNodes.push({ s: g.items[0], leftPct: basePct });
                } else if (this.expandedTimelineGroups.includes(g.key)) {
                    // 展开：水平铺开
                    const count = g.items.length;
                    const totalSpread = (count - 1) * SPREAD_PCT * scale;
                    g.items.forEach((s, j) => {
                        const offset = j * SPREAD_PCT * scale;
                        renderNodes.push({ s, leftPct: basePct + offset });
                    });
                    accOffset += totalSpread;
                } else {
                    // 合并：显示为一个带 + 的节点
                    renderNodes.push({ s: g.items[0], leftPct: basePct, group: g });
                }
            });

            // 标签避让：相邻节点距离 < 8% 时交替上下
            const labelAbove = [];
            renderNodes.forEach((n, i) => {
                if (i === 0) { labelAbove.push(false); return; }
                const close = n.leftPct - renderNodes[i-1].leftPct < 8;
                labelAbove.push(close ? !labelAbove[i-1] : false);
            });

            // 渲染节点
            let dots = '';
            renderNodes.forEach((n, i) => {
                const s = n.s;
                const left = n.leftPct.toFixed(2);
                const above = labelAbove[i];

                if (n.group) {
                    // 合并节点：显示第一个节点样式 + 计数角标
                    const g = n.group;
                    const count = g.items.length;
                    const names = g.items.map(x => x.title).join(', ');
                    const tip = count + ' 个节点: ' + names + ' (' + fmt(s._pos_date) + ')';
                    const label = s.title.length > 4 ? s.title.substring(0,4) + '…' : s.title;
                    const click = 'onclick="window._tlToggleGroup(\'' + g.key + '\')"';

                    let nodeHtml;
                    if (s.is_milestone) {
                        const mColor = s.milestone_status === 'confirmed' ? 'text-green-500'
                                     : s.milestone_status === 'rejected' ? 'text-red-500'
                                     : s.milestone_status === 'pending_confirmation' ? 'text-amber-500'
                                     : 'text-blue-500';
                        nodeHtml = '<span class="text-base leading-none ' + mColor + '" style="position:absolute;top:-8px;left:50%;transform:translateX(-50%)">\u25C6</span>';
                    } else {
                        const cls = dotColor[s.status] || dotColor.pending;
                        nodeHtml = '<div class="w-2.5 h-2.5 rounded-full ' + cls + '" style="position:absolute;top:-5px;left:50%;transform:translateX(-50%)"></div>';
                    }

                    // "+" 角标
                    const badge = '<span style="position:absolute;top:-12px;left:50%;margin-left:4px;'
                        + 'font-size:9px;font-weight:700;color:#3b82f6;background:#eff6ff;border-radius:50%;'
                        + 'width:14px;height:14px;display:flex;align-items:center;justify-content:center;'
                        + 'box-shadow:0 0 0 1px #bfdbfe">+' + (count - 1) + '</span>';

                    const lTop = above ? -22 : 8;
                    const labelHtml = '<span class="text-[10px] text-slate-500 dark:text-slate-400 whitespace-nowrap" style="position:absolute;top:' + lTop + 'px;left:50%;transform:translateX(-50%)">' + label + '</span>';

                    dots += '<div class="absolute cursor-pointer" style="left:' + left + '%" title="' + tip + '" ' + click + '>'
                          + nodeHtml + badge + labelHtml + '</div>';
                } else {
                    // 普通节点
                    const label = s.title.length > 6 ? s.title.substring(0,6) + '…' : s.title;
                    const tip = s.title + ' (' + fmt(s._pos_date) + ')';
                    const click = 'onclick="window._tlFocus(' + s.id + ')"';

                    let nodeHtml;
                    if (s.is_milestone) {
                        const mColor = s.milestone_status === 'confirmed' ? 'text-green-500'
                                     : s.milestone_status === 'rejected' ? 'text-red-500'
                                     : s.milestone_status === 'pending_confirmation' ? 'text-amber-500'
                                     : 'text-blue-500';
                        nodeHtml = '<span class="text-base leading-none ' + mColor + '" style="position:absolute;top:-8px;left:50%;transform:translateX(-50%)">\u25C6</span>';
                    } else {
                        const cls = dotColor[s.status] || dotColor.pending;
                        nodeHtml = '<div class="w-2.5 h-2.5 rounded-full ' + cls + '" style="position:absolute;top:-5px;left:50%;transform:translateX(-50%)"></div>';
                    }

                    const lTop = above ? -22 : 8;
                    const labelHtml = '<span class="text-[10px] text-slate-500 dark:text-slate-400 whitespace-nowrap" style="position:absolute;top:' + lTop + 'px;left:50%;transform:translateX(-50%)">' + label + '</span>';

                    dots += '<div class="absolute cursor-pointer" style="left:' + left + '%" title="' + tip + '" ' + click + '>'
                          + nodeHtml + labelHtml + '</div>';
                }
            });

            // 今天标记
            const todayMark = showToday
                ? '<div class="absolute -translate-x-1/2 flex flex-col items-center" style="left:' + todayPct + '%">'
                  + '<div class="w-px h-3 bg-red-400" style="margin-top:-14px"></div>'
                  + '<span class="text-[9px] text-red-400 font-medium" style="margin-top:-1px">\u4ECA</span>'
                  + '</div>'
                : '';

            const hasAbove = labelAbove.some(p => p);
            const topPad = hasAbove ? 32 : 20;
            const MIN_PX_PER_DAY = 50;
            const minTrackWidth = totalDays * MIN_PX_PER_DAY * (1 + extraPct / 100);

            return '<div style="padding-top:' + topPad + 'px;padding-bottom:28px;overflow-x:auto">'
                 + '<div class="relative" style="width:100%;min-width:' + minTrackWidth + 'px">'
                 + '<div class="flex justify-between text-[10px] text-slate-400 mb-1">'
                 + '<span>' + fmt(minD) + '</span><span>' + fmt(maxD) + '</span></div>'
                 + '<div class="relative h-px bg-slate-300 dark:bg-slate-600">'
                 + dots + todayMark + '</div></div></div>';
        },

        // ══════════════════════════════════════════════════════
        // 弹窗方法
        // ══════════════════════════════════════════════════════

        openCreateModal() {
            // Dispatch event to open the existing task create modal from tw_task_modal.html
            window.dispatchEvent(new CustomEvent('open-task-create-modal', { detail: {} }));
        },

        openEditModal() {
            if (!this.selectedTask) return;
            // For editing, we dispatch the detail modal or re-open create modal with data
            // Use the existing task detail modal
            window.dispatchEvent(new CustomEvent('open-task-detail-modal', {
                detail: { taskId: this.selectedTask.id }
            }));
        },

        openSubtaskModal(st) {
            const store = Alpine.store('taskMgmt');
            if (st) {
                store.editingSubtask = st;
                // Build selectedConfirmers from milestone_reviewers
                const confirmers = (st.milestone_reviewers || []).map(r => {
                    const u = store.allUsers.find(u => u.id === r.reviewer_id);
                    return u ? { id: u.id, real_name: u.real_name, username: u.username } : { id: r.reviewer_id, real_name: r.reviewer_name || ('ID:' + r.reviewer_id), username: '' };
                });
                store.subtaskForm = {
                    title: st.title || '',
                    description: st.description || '',
                    assignee_id: st.assignee_id ? String(st.assignee_id) : '',
                    start_date: st.start_date || '',
                    due_date: st.due_date || '',
                    is_milestone: st.is_milestone || false,
                    selectedConfirmers: confirmers,
                };
            } else {
                store.editingSubtask = null;
                store.subtaskForm = {
                    title: '', description: '',
                    assignee_id: this.selectedTask?.assignee_id ? String(this.selectedTask.assignee_id) : '',
                    start_date: '', due_date: '',
                    is_milestone: false, selectedConfirmers: [],
                };
            }
            store.showSubtaskModal = true;
        },

        openMilestoneConfirmModal(st, action) {
            const store = Alpine.store('taskMgmt');
            store.milestoneTarget = st;
            store.milestoneAction = action;
            store.milestoneComment = '';
            store.showMilestoneModal = true;
        },

        handleUpdateFiles(event, subtaskId) {
            const files = Array.from(event.target.files || []);
            if (!this.pendingUpdateFiles[subtaskId]) {
                this.pendingUpdateFiles[subtaskId] = [];
            }
            this.pendingUpdateFiles[subtaskId].push(...files);
            event.target.value = '';
        },
    };
}
