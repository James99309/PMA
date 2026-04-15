/**
 * 文件管理器 Alpine.js 组件
 */
function fileManager() {
    return {
        // 状态
        loading: false,
        activeView: 'files',       // files / trash / archived
        viewMode: 'list',          // list / grid
        currentFolderId: null,

        // 数据
        folderTree: [],
        folders: [],
        files: [],
        breadcrumbs: [],
        trashFiles: [],
        archivedFiles: [],
        quota: { quota: 0, used: 0, remaining: 0, percent: 0 },

        // 搜索
        searchQuery: '',
        searchResults: null,

        // 选择
        selectedFiles: [],

        // UI 状态
        showNewFolderInput: false,
        newFolderName: '',
        isDragging: false,
        showMobileSidebar: false,
        showMoveModal: false,
        moveFolderTarget: null,
        uploadQueue: [],

        // 右键菜单
        contextMenu: { show: false, x: 0, y: 0, type: null, item: null },

        // 重命名
        renameModal: { show: false, type: null, item: null, name: '' },

        // 归档恢复
        restoreModal: { show: false, file: null, filename: '', targetUserId: '' },
        allUsers: [],

        // 预览
        previewModal: { show: false, file: null, type: 'other' },
        spreadsheetHtml: '',

        // 解压动画
        decompressModal: { show: false, fileName: '' },

        // 知识库
        kbTags: [],
        kbFiles: [],
        kbStats: { total: 0, ready: 0, processing: 0, error: 0 },
        kbFilterTag: null,
        kbFilterStatus: '',
        kbSearch: '',
        selectedKbFiles: [],
        kbDetailFile: null,
        showTagManageModal: false,
        showBatchKbModal: false,
        batchSelectedTags: [],
        // 批量加入 Wiki 弹窗（与单文件 wikiModal 保持一致，使用 topic 而非 kbTags）
        batchWikiModal: {
            topic: '',
            existingTopics: [],
            customTopic: false,
        },
        newTagName: '',
        kbFileStatus: {},  // maps user_file_ref_id -> {in_knowledge_base, document_id, status, tags}
        toast: { show: false, message: '', type: 'success' },

        // 扁平化文件夹列表（用于移动对话框）
        allFoldersFlat: [],

        // 拖拽移动
        dragFileId: null,
        dropTargetFolderId: null,

        init() {
            this.currentFolderId = window.__fileManagerInitFolderId || null;
            this.loadFolderTree();
            this.loadFiles();
            this.loadKbTags();
            // 监听分享成功事件
            window.addEventListener('share-to-chat-success', (e) => {
                this.showToast('success', e.detail?.message || '分享成功');
            });
        },

        // ------------------------------------------------------------------
        // API 调用
        // ------------------------------------------------------------------
        async api(url, options = {}) {
            const defaults = {
                headers: { 'Content-Type': 'application/json' },
            };
            const res = await fetch(url, { ...defaults, ...options });
            return res.json();
        },

        async loadFolderTree() {
            const data = await this.api('/files/api/folders');
            if (data.success) {
                this.folderTree = data.data;
                this.allFoldersFlat = this._flattenFolders(data.data, 0);
            }
        },

        async loadFiles() {
            this.loading = true;
            this.selectedFiles = [];
            const url = this.currentFolderId
                ? `/files/api/list?folder_id=${this.currentFolderId}`
                : '/files/api/list';
            const data = await this.api(url);
            if (data.success) {
                this.folders = data.data.folders;
                this.files = data.data.files;
                this.breadcrumbs = data.breadcrumbs;
                this.quota = data.quota;
                // 加载文件的知识库状态
                await this._loadKbStatusForFiles();
                // 加载 Wiki 状态（已编译标记 + 编译中标记）
                await this._loadWikiStatusForFiles();
                // 有 processing 状态的文件时，启动轮询
                this._startWikiPollIfNeeded();
            }
            this.loading = false;
        },

        async loadTrash() {
            const data = await this.api('/files/api/trash');
            if (data.success) {
                this.trashFiles = data.data;
            }
        },

        // ------------------------------------------------------------------
        // 导航
        // ------------------------------------------------------------------
        navigateTo(folderId) {
            this.currentFolderId = folderId;
            this.searchResults = null;
            this.searchQuery = '';
            this.loadFiles();
        },

        // ------------------------------------------------------------------
        // 文件夹操作
        // ------------------------------------------------------------------
        async createFolder() {
            if (!this.newFolderName.trim()) return;
            const data = await this.api('/files/api/folders', {
                method: 'POST',
                body: JSON.stringify({
                    name: this.newFolderName,
                    parent_id: this.currentFolderId,
                }),
            });
            if (data.success) {
                this.newFolderName = '';
                this.showNewFolderInput = false;
                this.loadFiles();
                this.loadFolderTree();
            } else {
                alert(data.message);
            }
        },

        deleteFolder(folderId) {
            openConfirmModal('fileConfirmModal', {
                title: '确认删除',
                message: '确定要删除此文件夹及其所有内容吗？文件将移入回收站。',
                onConfirm: async () => {
                    const data = await this.api(`/files/api/folders/${folderId}`, {
                        method: 'DELETE',
                    });
                    if (data.success) {
                        this.loadFiles();
                        this.loadFolderTree();
                    } else {
                        throw new Error(data.message);
                    }
                }
            });
        },

        // ------------------------------------------------------------------
        // 文件上传
        // ------------------------------------------------------------------
        async handleFileUpload(event) {
            const files = event.target.files;
            if (!files.length) return;
            await this._uploadFiles(Array.from(files));
            event.target.value = '';
        },

        async handleDrop(event) {
            this.isDragging = false;
            const files = event.dataTransfer.files;
            if (!files.length) return;
            await this._uploadFiles(Array.from(files));
        },

        async _uploadFiles(fileList) {
            for (const file of fileList) {
                const queueItem = { name: file.name, status: 'uploading' };
                this.uploadQueue.push(queueItem);

                const formData = new FormData();
                formData.append('file', file);
                if (this.currentFolderId) {
                    formData.append('folder_id', this.currentFolderId);
                }

                try {
                    const res = await fetch('/files/api/upload', {
                        method: 'POST',
                        body: formData,
                    });
                    const data = await res.json();
                    queueItem.status = data.success ? 'done' : 'error';
                    if (!data.success) {
                        console.error('上传失败:', data.message);
                    }
                } catch (e) {
                    queueItem.status = 'error';
                    console.error('上传异常:', e);
                }
            }

            // 刷新列表
            this.loadFiles();
            this.loadFolderTree();

            // 3秒后清除上传队列
            setTimeout(() => {
                this.uploadQueue = this.uploadQueue.filter(q => q.status === 'uploading');
            }, 3000);
        },

        // ------------------------------------------------------------------
        // 文件操作
        // ------------------------------------------------------------------
        async deleteFile(fileId) {
            const data = await this.api(`/files/api/files/${fileId}/delete`, { method: 'POST' });
            if (data.success) {
                this.loadFiles();
            } else {
                alert(data.message);
            }
        },

        batchDelete() {
            if (!this.selectedFiles.length) return;
            openConfirmModal('fileConfirmModal', {
                title: '确认删除',
                message: `确定要删除选中的 ${this.selectedFiles.length} 个文件吗？文件将移入回收站。`,
                onConfirm: async () => {
                    const data = await this.api('/files/api/files/delete-batch', {
                        method: 'POST',
                        body: JSON.stringify({ file_ids: this.selectedFiles }),
                    });
                    if (data.success) {
                        this.selectedFiles = [];
                        this.loadFiles();
                    } else {
                        throw new Error(data.message);
                    }
                }
            });
        },

        async downloadFile(file) {
            const fileName = this._getFileName(file);
            const downloadUrl = this._getFileUrl(file, 'download');
            if (file.is_archived) {
                this.decompressModal = { show: true, fileName };
                try {
                    const resp = await fetch(downloadUrl);
                    this.decompressModal.show = false;
                    if (!resp.ok) throw new Error('下载失败');
                    const blob = await resp.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = fileName;
                    a.click();
                    URL.revokeObjectURL(url);
                } catch (e) {
                    this.decompressModal.show = false;
                    console.error('下载归档文件失败:', e);
                }
                return;
            }
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = fileName;
            a.click();
        },

        // ------------------------------------------------------------------
        // 回收站
        // ------------------------------------------------------------------
        async restoreFile(fileId) {
            const data = await this.api(`/files/api/trash/${fileId}/restore`, { method: 'POST' });
            if (data.success) {
                this.loadTrash();
                this.loadFiles();
            }
        },

        permanentDelete(fileId) {
            openConfirmModal('fileConfirmModal', {
                title: '确认删除',
                message: '删除后将从您的文件列表中移除，确定继续吗？',
                onConfirm: async () => {
                    const data = await this.api(`/files/api/trash/${fileId}/permanent`, { method: 'DELETE' });
                    if (data.success) {
                        this.loadTrash();
                    } else {
                        throw new Error(data.message);
                    }
                }
            });
        },

        emptyTrash() {
            openConfirmModal('fileConfirmModal', {
                title: '清空回收站',
                message: '确定要清空回收站吗？所有文件将从您的文件列表中移除。',
                onConfirm: async () => {
                    const data = await this.api('/files/api/trash/empty', { method: 'POST' });
                    if (data.success) {
                        this.trashFiles = [];
                        this.loadFiles();
                    } else {
                        throw new Error(data.message);
                    }
                }
            });
        },

        // ------------------------------------------------------------------
        // 归档管理（管理员）
        // ------------------------------------------------------------------
        async loadArchived() {
            const data = await this.api('/files/api/admin/archived');
            if (data.success) {
                this.archivedFiles = data.data.items || [];
            }
        },

        async showRestoreModal(file) {
            if (this.allUsers.length === 0) {
                try {
                    const data = await this.api('/user/api/users/active');
                    if (data.success) {
                        this.allUsers = data.data || [];
                    }
                } catch (e) {
                    console.error('加载用户列表失败:', e);
                }
            }
            this.restoreModal = {
                show: true,
                file: file,
                filename: file.original_filename,
                targetUserId: '',
            };
        },

        async restoreArchived() {
            if (!this.restoreModal.targetUserId) return alert('请选择用户');
            const data = await this.api(`/files/api/admin/archived/${this.restoreModal.file.id}/restore`, {
                method: 'POST',
                body: JSON.stringify({ target_user_id: parseInt(this.restoreModal.targetUserId) }),
            });
            if (data.success) {
                this.restoreModal.show = false;
                this.loadArchived();
                this.loadFiles();
            } else {
                alert(data.message);
            }
        },

        permanentDeleteArchived(file) {
            openConfirmModal('fileConfirmModal', {
                title: '彻底删除',
                message: `确定要彻底删除「${file.original_filename}」吗？此操作不可恢复，物理文件将被永久删除。`,
                onConfirm: async () => {
                    const data = await this.api(`/files/api/admin/archived/${file.id}`, { method: 'DELETE' });
                    if (data.success) {
                        this.loadArchived();
                    } else {
                        throw new Error(data.message);
                    }
                }
            });
        },

        async compressInactive() {
            if (!confirm('确定要压缩所有不活跃文件吗？')) return;
            const data = await this.api('/files/api/admin/compress-inactive', {
                method: 'POST',
                body: JSON.stringify({ days: 90 }),
            });
            if (data.success) {
                alert(data.message);
                this.loadArchived();
            } else {
                alert(data.message);
            }
        },

        // ------------------------------------------------------------------
        // 搜索
        // ------------------------------------------------------------------
        async doSearch() {
            if (!this.searchQuery.trim()) {
                this.searchResults = null;
                return;
            }
            const data = await this.api(`/files/api/search?q=${encodeURIComponent(this.searchQuery)}`);
            if (data.success) {
                this.searchResults = data.data;
            }
        },

        // ------------------------------------------------------------------
        // 选择
        // ------------------------------------------------------------------
        toggleSelect(fileId) {
            const idx = this.selectedFiles.indexOf(fileId);
            if (idx >= 0) {
                this.selectedFiles.splice(idx, 1);
            } else {
                this.selectedFiles.push(fileId);
            }
        },

        toggleSelectAll(event) {
            if (event.target.checked) {
                this.selectedFiles = this.files.map(f => f.id);
            } else {
                this.selectedFiles = [];
            }
        },

        isAllSelected() {
            return this.files.length > 0 && this.selectedFiles.length === this.files.length;
        },

        getSelectedFileObjects() {
            return this.files.filter(f => this.selectedFiles.includes(f.id));
        },

        shareFilesToChat(files) {
            if (!files || files.length === 0) return;
            window.dispatchEvent(new CustomEvent('open-share-to-chat', {
                detail: {
                    files: files.map(f => ({
                        id: f.id,
                        display_name: f.display_name,
                        file_size: f.file_size,
                    }))
                }
            }));
        },

        // ------------------------------------------------------------------
        // 右键菜单
        // ------------------------------------------------------------------
        showFileMenu(event, file) {
            const kbStatus = this.kbFileStatus[file.id] || {};
            this.contextMenu = {
                show: true,
                x: Math.min(event.clientX, window.innerWidth - 200),
                y: Math.min(event.clientY, window.innerHeight - 300),
                type: 'file',
                item: file,
                showKbSub: false,
                selectedTags: kbStatus.tags ? kbStatus.tags.map(t => t.id) : [],
                inKb: kbStatus.in_knowledge_base || false,
                kbDocId: kbStatus.document_id || null,
            };
        },

        showFolderMenu(event, folder) {
            this.contextMenu = {
                show: true,
                x: Math.min(event.clientX, window.innerWidth - 200),
                y: Math.min(event.clientY, window.innerHeight - 200),
                type: 'folder',
                item: folder,
            };
        },

        // ------------------------------------------------------------------
        // 重命名
        // ------------------------------------------------------------------
        startRename(type, item) {
            this.renameModal = {
                show: true,
                type,
                item,
                name: type === 'file' ? item.display_name : item.name,
            };
            this.$nextTick(() => {
                const input = this.$refs.renameInput;
                if (input) { input.focus(); input.select(); }
            });
        },

        async confirmRename() {
            const { type, item, name } = this.renameModal;
            if (!name.trim()) return;

            let data;
            if (type === 'file') {
                data = await this.api(`/files/api/files/${item.id}/rename`, {
                    method: 'POST',
                    body: JSON.stringify({ name }),
                });
            } else {
                data = await this.api(`/files/api/folders/${item.id}`, {
                    method: 'PUT',
                    body: JSON.stringify({ name }),
                });
            }

            if (data.success) {
                this.renameModal.show = false;
                this.loadFiles();
                if (type === 'folder') this.loadFolderTree();
            } else {
                alert(data.message);
            }
        },

        // ------------------------------------------------------------------
        // 移动
        // ------------------------------------------------------------------
        moveToFolder(folderId) {
            this.moveFolderTarget = folderId;
        },

        async confirmMove() {
            if (this.selectedFiles.length === 0) return;
            const data = await this.api('/files/api/files/move-batch', {
                method: 'POST',
                body: JSON.stringify({
                    file_ids: this.selectedFiles,
                    folder_id: this.moveFolderTarget,
                }),
            });
            if (data.success) {
                this.showMoveModal = false;
                this.selectedFiles = [];
                this.moveFolderTarget = null;
                this.loadFiles();
            } else {
                alert(data.message);
            }
        },

        // ------------------------------------------------------------------
        // 拖拽移动文件到文件夹
        // ------------------------------------------------------------------
        onFileDragStart(event, file) {
            this.dragFileId = file.id;
            // 如果文件已选中且有多选，拖拽全部选中的
            if (this.selectedFiles.length > 0 && this.selectedFiles.includes(file.id)) {
                event.dataTransfer.setData('text/plain', JSON.stringify(this.selectedFiles));
            } else {
                event.dataTransfer.setData('text/plain', JSON.stringify([file.id]));
            }
            event.dataTransfer.effectAllowed = 'move';
        },

        onFileDragEnd() {
            this.dragFileId = null;
            this.dropTargetFolderId = null;
        },

        onFolderDragOver(event, folderId) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
            this.dropTargetFolderId = folderId;
        },

        onFolderDragLeave(folderId) {
            if (this.dropTargetFolderId === folderId) {
                this.dropTargetFolderId = null;
            }
        },

        async onFolderDrop(event, folderId) {
            event.preventDefault();
            this.dropTargetFolderId = null;

            let fileIds;
            try {
                fileIds = JSON.parse(event.dataTransfer.getData('text/plain'));
            } catch {
                return;
            }
            if (!fileIds || !fileIds.length) return;

            const data = await this.api('/files/api/files/move-batch', {
                method: 'POST',
                body: JSON.stringify({ file_ids: fileIds, folder_id: folderId }),
            });
            if (data.success) {
                this.selectedFiles = [];
                this.loadFiles();
                this.loadFolderTree();
            } else {
                alert(data.message);
            }
        },

        // 拖拽到面包屑（上级文件夹/根目录）
        async onBreadcrumbDrop(event, folderId) {
            event.preventDefault();
            let fileIds;
            try {
                fileIds = JSON.parse(event.dataTransfer.getData('text/plain'));
            } catch {
                return;
            }
            if (!fileIds || !fileIds.length) return;

            const data = await this.api('/files/api/files/move-batch', {
                method: 'POST',
                body: JSON.stringify({ file_ids: fileIds, folder_id: folderId }),
            });
            if (data.success) {
                this.selectedFiles = [];
                this.loadFiles();
                this.loadFolderTree();
            }
        },

        // ------------------------------------------------------------------
        // 预览
        // ------------------------------------------------------------------
        async previewFile(file) {
            const mime = file.mime_type || '';
            let type = 'other';
            if (mime.startsWith('image/')) type = 'image';
            else if (mime === 'application/pdf') type = 'pdf';
            else if (mime.startsWith('video/')) type = 'video';
            else if (mime.includes('sheet') || mime.includes('excel') || mime === 'text/csv') type = 'spreadsheet';

            if (type === 'other') {
                this.downloadFile(file);
                return;
            }

            const fileName = this._getFileName(file);

            // 归档文件 + 电子表格：先显示解压动画，fetch 完成后关闭
            if (file.is_archived && type === 'spreadsheet') {
                this.decompressModal = { show: true, fileName };
            }

            this.spreadsheetHtml = '';
            this.previewModal = { show: true, file, type };

            // 归档的图片/PDF/视频：显示简短解压提示（浏览器 src 加载自动处理）
            if (file.is_archived && type !== 'spreadsheet') {
                this.decompressModal = { show: true, fileName };
                setTimeout(() => { this.decompressModal.show = false; }, 1500);
            }

            if (type === 'spreadsheet') {
                await this.loadSpreadsheet(file);
                this.decompressModal.show = false;
            }
        },

        async loadSpreadsheet(file) {
            try {
                const resp = await fetch(this._getFileUrl(file, 'preview'));
                if (!resp.ok) throw new Error('Failed to fetch');
                const buf = await resp.arrayBuffer();
                const wb = XLSX.read(buf, { type: 'array' });
                const sheet = wb.Sheets[wb.SheetNames[0]];
                this.spreadsheetHtml = XLSX.utils.sheet_to_html(sheet);
            } catch (e) {
                console.error('Spreadsheet preview error:', e);
                this.spreadsheetHtml = '<p class="text-center text-slate-500 py-8">无法预览该文件</p>';
            }
        },

        // ------------------------------------------------------------------
        // 知识库
        // ------------------------------------------------------------------
        async loadKbTags() {
            const data = await this.api('/api/knowledge/tags');
            if (data.success) {
                this.kbTags = data.data;
            }
        },

        async loadKbFiles() {
            const params = new URLSearchParams();
            if (this.kbFilterTag) params.set('tag_id', this.kbFilterTag);
            if (this.kbFilterStatus) params.set('status', this.kbFilterStatus);
            params.set('per_page', '100');
            const data = await this.api(`/api/knowledge/documents?${params}`);
            if (data.success) {
                this.kbFiles = data.data;
            }
        },

        async loadKbStats() {
            const data = await this.api('/api/knowledge/stats');
            if (data.success) {
                this.kbStats = {
                    total: data.data.total_documents,
                    ready: data.data.status_counts.ready,
                    processing: data.data.status_counts.processing,
                    error: data.data.status_counts.error,
                    pending: data.data.status_counts.pending,
                };
            }
        },

        async openKbView() {
            this.activeView = 'knowledge';
            await Promise.all([this.loadKbFiles(), this.loadKbStats()]);
        },

        get filteredKbFiles() {
            let files = this.kbFiles;
            if (this.kbSearch.trim()) {
                const q = this.kbSearch.trim().toLowerCase();
                files = files.filter(f => (f.title || '').toLowerCase().includes(q));
            }
            return files;
        },

        async _loadKbStatusForFiles() {
            const fileRefIds = this.files.map(f => f.id);
            if (!fileRefIds.length) return;
            const data = await this.api('/api/knowledge/documents/file-status', {
                method: 'POST',
                body: JSON.stringify({ file_ref_ids: fileRefIds }),
            });
            if (data.success) {
                this.kbFileStatus = data.data;
            }
        },

        getKbStatusForFile(fileId) {
            return this.kbFileStatus[fileId] || { in_knowledge_base: false };
        },

        async addFilesToKb(fileRefIds, tagIds) {
            if (!fileRefIds.length || !tagIds.length) return;
            const data = await this.api('/api/knowledge/documents/add', {
                method: 'POST',
                body: JSON.stringify({ file_ref_ids: fileRefIds, tag_ids: tagIds }),
            });
            if (data.success) {
                this.showToast('success', `${data.data.length} 个文件已加入知识库`);
                await this._loadKbStatusForFiles();
                if (this.activeView === 'knowledge') {
                    await this.loadKbFiles();
                    await this.loadKbStats();
                }
            } else {
                this.showToast('error', data.message || '操作失败');
            }
            if (data.warnings && data.warnings.length) {
                console.warn('知识库添加警告:', data.warnings);
            }
            return data;
        },

        async removeFromKb(docId) {
            const data = await this.api(`/api/knowledge/documents/${docId}/remove`, {
                method: 'POST',
            });
            if (data.success) {
                this.showToast('success', data.message);
                await this._loadKbStatusForFiles();
                if (this.activeView === 'knowledge') {
                    await this.loadKbFiles();
                    await this.loadKbStats();
                }
            } else {
                this.showToast('error', data.message || '操作失败');
            }
        },

        async batchRemoveFromKb() {
            if (!this.selectedKbFiles.length) return;
            const data = await this.api('/api/knowledge/documents/batch-remove', {
                method: 'POST',
                body: JSON.stringify({ document_ids: this.selectedKbFiles }),
            });
            if (data.success) {
                this.showToast('success', data.message);
                this.selectedKbFiles = [];
                await Promise.all([this.loadKbFiles(), this.loadKbStats()]);
            } else {
                this.showToast('error', data.message || '操作失败');
            }
        },

        async reprocessDocument(docId) {
            const data = await this.api(`/api/knowledge/documents/${docId}/reprocess`, {
                method: 'POST',
            });
            if (data.success) {
                this.showToast('success', '已提交重新处理');
                if (this.kbDetailFile && this.kbDetailFile.id === docId) {
                    this.kbDetailFile = data.data;
                }
                await this.loadKbFiles();
                await this.loadKbStats();
            } else {
                this.showToast('error', data.message || '操作失败');
            }
        },

        async openKbDetail(file) {
            const data = await this.api(`/api/knowledge/documents/${file.id}`);
            if (data.success) {
                this.kbDetailFile = data.data;
            }
        },

        // ── Wiki 知识库状态 ──
        wikiModal: {
            show: false,
            step: 'input',
            file: null,
            topic: '',
            existingTopics: [],
            customTopic: false,
            resultMsg: '',
            errorMsg: '',
        },
        wikiFileStatus: {},       // { file_library_id: { in_wiki, status, raw_id, topic } }
        wikiCompilingIds: [],     // file_ref_ids 当前正在编译的

        // 加载文件的 Wiki 状态（调时机：loadFiles 完成后）
        async _loadWikiStatusForFiles() {
            const flIds = this.files.map(f => f.file_library_id).filter(Boolean);
            if (!flIds.length) return;
            try {
                const data = await this.api('/api/wiki/file-wiki-status', {
                    method: 'POST',
                    body: JSON.stringify({ file_library_ids: [...new Set(flIds)] }),
                });
                if (data.success) this.wikiFileStatus = data.data || {};
            } catch (e) { /* 静默 */ }
        },

        _startWikiPollIfNeeded() {
            if (this._wikiPollTimer) return;
            const isProcessing = (st) => st && (st.status === 'processing' || st.status === 'pending');
            const anyProcessing = () => Object.values(this.wikiFileStatus).some(isProcessing);
            if (!anyProcessing() && this.wikiCompilingIds.length === 0) return;
            this._wikiPollTimer = setInterval(async () => {
                await this._loadWikiStatusForFiles();
                // 后端已落终态(ingested/error)的文件从乐观编译列表中移除，避免自锁循环
                this.wikiCompilingIds = this.wikiCompilingIds.filter(fid => {
                    const f = this.files.find(x => x.id === fid);
                    if (!f) return false;
                    const st = this.wikiFileStatus[String(f.file_library_id)];
                    return !st || isProcessing(st);
                });
                if (!anyProcessing() && this.wikiCompilingIds.length === 0) {
                    clearInterval(this._wikiPollTimer);
                    this._wikiPollTimer = null;
                }
            }, 5000);
        },

        getWikiStatus(file) {
            return this.wikiFileStatus[String(file.file_library_id)] || { in_wiki: false };
        },

        isFileInWiki(file) {
            return this.getWikiStatus(file).in_wiki;
        },

        isFileCompiling(file) {
            if (this.wikiCompilingIds.includes(file.id)) return true;
            const ws = this.getWikiStatus(file);
            return ws.status === 'processing';
        },

        // 右键菜单: 打开 Wiki 添加弹窗
        async addContextFileToWiki() {
            const file = this.contextMenu.item;
            if (!file) return;
            let existingTopics = [];
            try {
                const res = await this.api('/api/wiki/topics');
                if (res.success && Array.isArray(res.data)) existingTopics = res.data;
            } catch (e) {}
            this.wikiModal.file = file;
            this.wikiModal.topic = '';
            this.wikiModal.existingTopics = existingTopics;
            this.wikiModal.customTopic = false;
            this.wikiModal.step = 'input';
            this.wikiModal.resultMsg = '';
            this.wikiModal.errorMsg = '';
            this.wikiModal.show = true;
        },

        // Wiki 弹窗: 确认提交（异步编译，不等待结果）
        async submitWikiAdd() {
            const m = this.wikiModal;
            if (!m.topic || !m.topic.trim()) return;
            const file = m.file;
            m.show = false;

            // 标记文件为"编译中"
            this.wikiCompilingIds.push(file.id);
            this.showToast('success', `📚 已提交 Wiki 编译，完成后会收到通知`);

            try {
                const data = await this.api('/api/wiki/raw-files/from-file-ref', {
                    method: 'POST',
                    body: JSON.stringify({
                        user_file_ref_id: file.id,
                        topic: m.topic.trim(),
                        title: file.name || file.display_name || '',
                    }),
                });
                if (!data.success) {
                    this.showToast('error', data.message || '添加失败');
                    this.wikiCompilingIds = this.wikiCompilingIds.filter(id => id !== file.id);
                }
                // 成功时：后端异步编译，等系统通知。先刷新状态
                await this._loadWikiStatusForFiles();
                this._startWikiPollIfNeeded();
            } catch (e) {
                this.showToast('error', e.message);
                this.wikiCompilingIds = this.wikiCompilingIds.filter(id => id !== file.id);
            }
        },

        // 右键菜单: 加入知识库（旧接口兼容）
        addContextFileToKb() {
            this.addContextFileToWiki();
        },

        toggleContextTag(tagId) {
            const idx = this.contextMenu.selectedTags.indexOf(tagId);
            if (idx >= 0) {
                this.contextMenu.selectedTags.splice(idx, 1);
            } else {
                this.contextMenu.selectedTags.push(tagId);
            }
        },

        // 批量加入知识库（走 Wiki topic 体系，与单文件 wikiModal 保持一致）
        async openBatchWikiModal() {
            if (!this.selectedFiles.length) return;
            let existingTopics = [];
            try {
                const res = await this.api('/api/wiki/topics');
                if (res.success && Array.isArray(res.data)) existingTopics = res.data;
            } catch (e) {}
            this.batchWikiModal.topic = '';
            this.batchWikiModal.existingTopics = existingTopics;
            this.batchWikiModal.customTopic = false;
            this.showBatchKbModal = true;
        },

        async confirmBatchKb() {
            const topic = (this.batchWikiModal.topic || '').trim();
            if (!this.selectedFiles.length || !topic) return;
            const fileIds = [...this.selectedFiles];
            this.showBatchKbModal = false;

            // 标记所有文件为"编译中"
            for (const id of fileIds) {
                if (!this.wikiCompilingIds.includes(id)) this.wikiCompilingIds.push(id);
            }
            this.showToast('success', `📚 已提交 ${fileIds.length} 个文件到 Wiki 编译，完成后会收到通知`);

            const results = await Promise.allSettled(fileIds.map(refId => {
                const file = this.files.find(f => f.id === refId);
                const title = file ? (file.name || file.display_name || '') : '';
                return this.api('/api/wiki/raw-files/from-file-ref', {
                    method: 'POST',
                    body: JSON.stringify({ user_file_ref_id: refId, topic, title }),
                });
            }));

            let okCount = 0;
            const failed = [];
            results.forEach((r, i) => {
                const refId = fileIds[i];
                if (r.status === 'fulfilled' && r.value && r.value.success) {
                    okCount += 1;
                } else {
                    failed.push(refId);
                    this.wikiCompilingIds = this.wikiCompilingIds.filter(id => id !== refId);
                }
            });

            if (failed.length) {
                const firstErr = results.find(r => r.status === 'fulfilled' && r.value && !r.value.success);
                const msg = firstErr ? firstErr.value.message : '部分文件提交失败';
                this.showToast('error', `${failed.length} 个文件失败：${msg}`);
            }

            await this._loadWikiStatusForFiles();
            this._startWikiPollIfNeeded();
            this.selectedFiles = [];
        },

        // KB 选择
        toggleSelectKb(fileId) {
            const idx = this.selectedKbFiles.indexOf(fileId);
            if (idx >= 0) {
                this.selectedKbFiles.splice(idx, 1);
            } else {
                this.selectedKbFiles.push(fileId);
            }
        },

        toggleSelectAllKb(event) {
            if (event.target.checked) {
                this.selectedKbFiles = this.filteredKbFiles.map(f => f.id);
            } else {
                this.selectedKbFiles = [];
            }
        },

        // 标签管理
        async createTag() {
            if (!this.newTagName.trim()) return;
            const data = await this.api('/api/knowledge/tags', {
                method: 'POST',
                body: JSON.stringify({ name: this.newTagName.trim() }),
            });
            if (data.success) {
                this.kbTags.push(data.data);
                this.newTagName = '';
                this.showToast('success', '标签已创建');
            } else {
                this.showToast('error', data.message || '创建失败');
            }
        },

        async updateTag(tagId, newName) {
            const data = await this.api(`/api/knowledge/tags/${tagId}`, {
                method: 'PUT',
                body: JSON.stringify({ name: newName }),
            });
            if (data.success) {
                const idx = this.kbTags.findIndex(t => t.id === tagId);
                if (idx >= 0) this.kbTags[idx] = data.data;
                this.showToast('success', '标签已更新');
            } else {
                this.showToast('error', data.message || '更新失败');
            }
        },

        async deleteTag(tagId) {
            const data = await this.api(`/api/knowledge/tags/${tagId}`, {
                method: 'DELETE',
            });
            if (data.success) {
                this.kbTags = this.kbTags.filter(t => t.id !== tagId);
                this.showToast('success', '标签已删除');
            } else {
                this.showToast('error', data.message || '删除失败');
            }
        },

        getTagName(tagId) {
            const tag = this.kbTags.find(t => t.id === tagId);
            return tag ? tag.name : '';
        },

        getTagCount(tagId) {
            return this.kbFiles.filter(f =>
                f.tags && f.tags.some(t => t.id === tagId)
            ).length;
        },

        getKbStatusLabel(status) {
            const labels = { ready: '就绪', processing: '处理中', pending: '队列中', error: '失败' };
            return labels[status] || status;
        },

        getKbStatusClass(status) {
            const classes = {
                ready: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
                processing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300',
                pending: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
                error: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300',
            };
            return classes[status] || '';
        },

        getKbDotClass(status) {
            const classes = {
                ready: 'bg-green-500',
                processing: 'bg-blue-500 pulse-dot',
                pending: 'bg-slate-400',
                error: 'bg-red-500',
            };
            return classes[status] || 'bg-slate-400';
        },

        // Toast
        showToast(type, message) {
            this.toast = { show: true, type, message };
            setTimeout(() => { this.toast.show = false; }, 2500);
        },

        // ------------------------------------------------------------------
        // 辅助函数
        // ------------------------------------------------------------------
        getFileIcon(file) {
            if (file.is_archived) return 'inventory_2';
            const mime = file.mime_type || '';
            if (mime.startsWith('image/')) return 'image';
            if (mime === 'application/pdf') return 'picture_as_pdf';
            if (mime.startsWith('video/')) return 'videocam';
            if (mime.includes('word') || mime.includes('document')) return 'description';
            if (mime.includes('sheet') || mime.includes('excel') || mime === 'text/csv') return 'table_chart';
            if (mime.includes('presentation') || mime.includes('powerpoint')) return 'slideshow';
            if (mime.includes('zip') || mime.includes('rar') || mime.includes('7z')) return 'folder_zip';
            return 'insert_drive_file';
        },

        getFileIconClass(file) {
            if (file.is_archived) return 'text-amber-500';
            const mime = file.mime_type || '';
            if (mime.startsWith('image/')) return 'text-blue-500';
            if (mime === 'application/pdf') return 'text-red-500';
            if (mime.startsWith('video/')) return 'text-purple-500';
            if (mime.includes('word') || mime.includes('document')) return 'text-blue-600';
            if (mime.includes('sheet') || mime.includes('excel') || mime === 'text/csv') return 'text-green-600';
            if (mime.includes('presentation')) return 'text-orange-500';
            return 'text-slate-400';
        },

        formatSize(bytes) {
            if (bytes == null || bytes === 0) return '0 B';
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
            return (bytes / 1073741824).toFixed(2) + ' GB';
        },

        formatDate(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            const now = new Date();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            if (d.getFullYear() === now.getFullYear()) {
                return `${month}-${day}`;
            }
            return `${d.getFullYear()}-${month}-${day}`;
        },

        // 判断是否为归档库文件（非用户引用）
        _isArchivedLib(file) {
            return file.archive_reason !== undefined && !file.display_name;
        },

        _getFileUrl(file, action) {
            if (this._isArchivedLib(file)) {
                return `/files/api/admin/archived/${file.id}/${action}`;
            }
            return `/files/api/files/${file.id}/${action}`;
        },

        _getFileName(file) {
            if (!file) return 'file';
            return file.display_name || file.original_filename || 'file';
        },

        _flattenFolders(folders, depth) {
            const result = [];
            for (const f of folders) {
                result.push({ id: f.id, name: f.name, depth });
                if (f.children && f.children.length > 0) {
                    result.push(...this._flattenFolders(f.children, depth + 1));
                }
            }
            return result;
        },
    };
}
