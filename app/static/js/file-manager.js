/**
 * 文件管理器 Alpine.js 组件
 */
function fileManager() {
    return {
        // 状态
        loading: false,
        activeView: 'files',       // files / trash
        viewMode: 'list',          // list / grid
        currentFolderId: null,

        // 数据
        folderTree: [],
        folders: [],
        files: [],
        breadcrumbs: [],
        trashFiles: [],
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

        // 预览
        previewModal: { show: false, file: null, type: 'other' },

        // 扁平化文件夹列表（用于移动对话框）
        allFoldersFlat: [],

        init() {
            this.currentFolderId = window.__fileManagerInitFolderId || null;
            this.loadFolderTree();
            this.loadFiles();
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

        async deleteFolder(folderId) {
            if (!confirm('确定要删除此文件夹及其所有内容吗？')) return;
            const data = await this.api(`/files/api/folders/${folderId}`, {
                method: 'DELETE',
            });
            if (data.success) {
                this.loadFiles();
                this.loadFolderTree();
            } else {
                alert(data.message);
            }
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

        async batchDelete() {
            if (!this.selectedFiles.length) return;
            if (!confirm(`确定要删除选中的 ${this.selectedFiles.length} 个文件吗？`)) return;

            const data = await this.api('/files/api/files/delete-batch', {
                method: 'POST',
                body: JSON.stringify({ file_ids: this.selectedFiles }),
            });
            if (data.success) {
                this.selectedFiles = [];
                this.loadFiles();
            } else {
                alert(data.message);
            }
        },

        downloadFile(file) {
            const a = document.createElement('a');
            a.href = `/files/api/files/${file.id}/download`;
            a.download = file.display_name;
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

        async permanentDelete(fileId) {
            if (!confirm('永久删除后无法恢复，确定继续吗？')) return;
            const data = await this.api(`/files/api/trash/${fileId}/permanent`, { method: 'DELETE' });
            if (data.success) {
                this.loadTrash();
            }
        },

        async emptyTrash() {
            if (!confirm('确定要清空回收站吗？所有文件将被永久删除。')) return;
            const data = await this.api('/files/api/trash/empty', { method: 'POST' });
            if (data.success) {
                this.trashFiles = [];
                this.loadFiles();  // 刷新配额
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

        // ------------------------------------------------------------------
        // 右键菜单
        // ------------------------------------------------------------------
        showFileMenu(event, file) {
            this.contextMenu = {
                show: true,
                x: Math.min(event.clientX, window.innerWidth - 200),
                y: Math.min(event.clientY, window.innerHeight - 250),
                type: 'file',
                item: file,
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
        // 预览
        // ------------------------------------------------------------------
        previewFile(file) {
            const mime = file.mime_type || '';
            let type = 'other';
            if (mime.startsWith('image/')) type = 'image';
            else if (mime === 'application/pdf') type = 'pdf';

            if (type === 'other') {
                // 不支持预览的直接下载
                this.downloadFile(file);
                return;
            }

            this.previewModal = { show: true, file, type };
        },

        // ------------------------------------------------------------------
        // 辅助函数
        // ------------------------------------------------------------------
        getFileIcon(file) {
            const mime = file.mime_type || '';
            if (mime.startsWith('image/')) return 'image';
            if (mime === 'application/pdf') return 'picture_as_pdf';
            if (mime.includes('word') || mime.includes('document')) return 'description';
            if (mime.includes('sheet') || mime.includes('excel')) return 'table_chart';
            if (mime.includes('presentation') || mime.includes('powerpoint')) return 'slideshow';
            if (mime.includes('zip') || mime.includes('rar') || mime.includes('7z')) return 'folder_zip';
            return 'insert_drive_file';
        },

        getFileIconClass(file) {
            const mime = file.mime_type || '';
            if (mime.startsWith('image/')) return 'text-blue-500';
            if (mime === 'application/pdf') return 'text-red-500';
            if (mime.includes('word') || mime.includes('document')) return 'text-blue-600';
            if (mime.includes('sheet') || mime.includes('excel')) return 'text-green-600';
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
