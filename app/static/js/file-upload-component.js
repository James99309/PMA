/**
 * 通用文件上传组件
 *
 * 用途：提供统一的文件上传功能，支持图片和PDF
 * 使用场景：日志附件、报销发票等
 *
 * 使用方法：
 * 1. 在页面中引入此脚本
 * 2. 使用 Jinja 宏 render_file_upload() 渲染 HTML
 * 3. 调用 FileUploadComponent.init() 初始化
 *
 * 依赖：
 * - Material Symbols 图标
 * - Tailwind CSS
 */

class FileUploadComponent {
    /**
     * 初始化文件上传组件
     * @param {string|HTMLElement} container - 容器ID或元素
     * @param {Object} options - 配置选项
     */
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        if (!this.container) {
            console.error('FileUploadComponent: Container not found');
            return;
        }

        // 从 data 属性读取配置
        this.entityType = options.entityType || this.container.dataset.entityType;
        this.entityId = options.entityId || this.container.dataset.entityId;
        this.uploadApi = options.uploadApi || this.container.dataset.uploadApi;
        this.deleteApi = options.deleteApi || this.container.dataset.deleteApi;
        this.previewApi = options.previewApi || this.container.dataset.previewApi;
        this.acceptTypes = options.acceptTypes || this.container.dataset.acceptTypes || 'image/*,.pdf';
        this.maxFileSize = parseInt(options.maxFileSize ?? this.container.dataset.maxFileSize ?? 0);
        this.maxFiles = parseInt(options.maxFiles || this.container.dataset.maxFiles || 10);
        this.readonly = (options.readonly || this.container.dataset.readonly) === 'true';
        this.compact = (options.compact || this.container.dataset.compact) === 'true';

        // 预览回调（紧凑模式点击图标时调用）
        this.onPreview = options.onPreview || null;

        // 新建模式（无 entityId）
        this.isNewMode = this.container.classList.contains('file-upload-new') || !this.entityId;
        this.pendingFiles = []; // 新建模式下的待上传文件

        // 回调函数
        this.onUploadSuccess = options.onUploadSuccess || null;
        this.onUploadError = options.onUploadError || null;
        this.onDeleteSuccess = options.onDeleteSuccess || null;
        this.onDeleteError = options.onDeleteError || null;
        this.onFilesChange = options.onFilesChange || null;

        // 获取元素引用
        this.fileInput = this.container.querySelector('.file-upload-input');
        this.fileList = this.container.querySelector('.file-list');
        this.progressEl = this.container.querySelector('.upload-progress');
        this.progressText = this.container.querySelector('.upload-progress-text');
        this.progressBar = this.container.querySelector('.upload-progress-bar');
        this.progressPercent = this.container.querySelector('.upload-progress-percent');
        this.errorEl = this.container.querySelector('.upload-error');
        this.errorText = this.container.querySelector('.upload-error-text');

        // 绑定事件
        this.bindEvents();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 文件选择事件
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // 文件列表的删除和预览事件（事件委托）
        if (this.fileList) {
            this.fileList.addEventListener('click', (e) => this.handleFileListClick(e));
        }
    }

    /**
     * 处理文件选择
     * @param {Event} e
     */
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        if (!files.length) return;

        // 清除之前的错误
        this.hideError();

        // 验证文件
        const validFiles = [];
        for (const file of files) {
            const validation = this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                this.showError(validation.error);
                break;
            }
        }

        // 检查文件数量限制
        const currentCount = this.isNewMode
            ? this.pendingFiles.length
            : this.fileList.querySelectorAll('.file-item').length;

        if (currentCount + validFiles.length > this.maxFiles) {
            this.showError(`最多只能上传 ${this.maxFiles} 个文件`);
            e.target.value = '';
            return;
        }

        if (validFiles.length === 0) {
            e.target.value = '';
            return;
        }

        // 根据模式处理文件
        if (this.isNewMode) {
            // 新建模式：添加到待上传列表
            this.addPendingFiles(validFiles);
        } else {
            // 编辑模式：立即上传
            this.uploadFiles(validFiles);
        }

        // 清空 input
        e.target.value = '';
    }

    /**
     * 验证单个文件
     * @param {File} file
     * @returns {{valid: boolean, error?: string}}
     */
    validateFile(file) {
        // 检查文件大小（maxFileSize=0 表示不限制）
        if (this.maxFileSize > 0 && file.size > this.maxFileSize) {
            const maxSizeMB = (this.maxFileSize / 1024 / 1024).toFixed(1);
            return { valid: false, error: `文件 "${file.name}" 大小超过 ${maxSizeMB}MB 限制` };
        }

        // 检查文件类型
        const acceptList = this.acceptTypes.split(',').map(t => t.trim());
        const fileType = file.type;
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();

        let typeValid = false;
        for (const accept of acceptList) {
            if (accept === '*/*') {
                typeValid = true;
                break;
            }
            if (accept.startsWith('.')) {
                // 检查扩展名
                if (fileExt === accept.toLowerCase()) {
                    typeValid = true;
                    break;
                }
            } else if (accept.endsWith('/*')) {
                // 检查 MIME 类型前缀（如 image/*）
                const typePrefix = accept.replace('/*', '');
                if (fileType.startsWith(typePrefix)) {
                    typeValid = true;
                    break;
                }
            } else {
                // 检查完整 MIME 类型
                if (fileType === accept) {
                    typeValid = true;
                    break;
                }
            }
        }

        if (!typeValid) {
            return { valid: false, error: `文件 "${file.name}" 类型不支持，仅支持图片和PDF` };
        }

        return { valid: true };
    }

    /**
     * 上传文件（编辑模式）
     * @param {File[]} files
     */
    async uploadFiles(files) {
        if (!this.uploadApi) {
            this.showError('上传接口未配置');
            return;
        }

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const label = files.length > 1 ? `上传中 (${i + 1}/${files.length})` : '上传中';
            this.showProgress(label);

            try {
                const CHUNK_THRESHOLD = 50 * 1024 * 1024; // 50MB
                const uploadFn = file.size > CHUNK_THRESHOLD
                    ? this.uploadChunked.bind(this)
                    : this.uploadSingleFile.bind(this);
                const result = await uploadFn(file, (pct) => {
                    this.updateProgress(pct);
                });
                if (result.success) {
                    this.addFileItem(result.data);
                    if (this.onUploadSuccess) {
                        this.onUploadSuccess(result.data);
                    }
                } else {
                    this.showError(result.message || '上传失败');
                    if (this.onUploadError) {
                        this.onUploadError(result.message);
                    }
                    break;
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.showError('上传失败：网络错误，请重试');
                if (this.onUploadError) {
                    this.onUploadError(error.message);
                }
                break;
            }
        }

        this.hideProgress();
    }

    /**
     * 上传单个文件（使用 XHR 支持进度事件）
     * @param {File} file
     * @param {Function} onProgress - 进度回调 (percent: 0-100)
     * @returns {Promise<Object>}
     */
    uploadSingleFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress(Math.round((e.loaded / e.total) * 100));
                }
            });

            xhr.addEventListener('load', () => {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch {
                    reject(new Error(`服务器返回异常 (${xhr.status})`));
                }
            });

            xhr.addEventListener('error', () => reject(new Error('网络连接失败')));
            xhr.addEventListener('timeout', () => reject(new Error('上传超时')));

            xhr.open('POST', this.uploadApi);
            xhr.withCredentials = true;
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
            xhr.timeout = 120000;
            xhr.send(formData);
        });
    }

    /**
     * 分片上传大文件（>50MB），绕过 Cloudflare 100MB 限制
     * @param {File} file
     * @param {Function} onProgress
     */
    async uploadChunked(file, onProgress) {
        const CHUNK_SIZE = 50 * 1024 * 1024; // 50MB
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = crypto.randomUUID();
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        const chunkApi = this.uploadApi.replace('/upload', '/upload/chunk');

        for (let i = 0; i < totalChunks; i++) {
            const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
            const formData = new FormData();
            formData.append('file', chunk, file.name);
            formData.append('upload_id', uploadId);
            formData.append('chunk_index', i);
            formData.append('total_chunks', totalChunks);
            formData.append('filename', file.name);
            if (this.folderId) formData.append('folder_id', this.folderId);

            const result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.addEventListener('load', () => {
                    try { resolve(JSON.parse(xhr.responseText)); }
                    catch { reject(new Error(`服务器返回异常 (${xhr.status})`)); }
                });
                xhr.addEventListener('error', () => reject(new Error('网络连接失败')));
                xhr.timeout = 300000; // 300s per chunk
                xhr.addEventListener('timeout', () => reject(new Error('分片上传超时')));
                xhr.open('POST', chunkApi);
                xhr.withCredentials = true;
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
                xhr.send(formData);
            });

            if (!result.success && !result.pending) {
                return result; // 出错提前返回
            }

            if (onProgress) onProgress(Math.round((i + 1) / totalChunks * 100));

            if (result.success) return result; // 最后一片，合并完成
        }
    }

    /**
     * 添加文件项到列表
     * @param {Object} fileData - {filename, url, size, type, index}
     */
    addFileItem(fileData) {
        const index = fileData.index !== undefined ? fileData.index : this.fileList.children.length;
        const isPdf = fileData.type && fileData.type.toLowerCase().includes('pdf');
        let itemHtml;

        if (this.compact) {
            // 紧凑模式：圆形图标按钮
            itemHtml = `
                <div class="file-item file-uploaded inline-flex items-center group"
                     data-index="${index}"
                     data-filename="${this.escapeHtml(fileData.filename)}"
                     data-type="${fileData.type || ''}">
                    <button type="button"
                            class="file-preview-btn inline-flex items-center justify-center w-8 h-8 rounded-full
                                   bg-slate-100 dark:bg-slate-700
                                   hover:bg-slate-200 dark:hover:bg-slate-600
                                   transition-all hover:scale-110"
                            title="点击预览: ${this.escapeHtml(fileData.filename)}">
                        <span class="material-symbols-outlined text-lg ${isPdf ? 'text-red-500' : 'text-primary'}">
                            ${isPdf ? 'picture_as_pdf' : 'image'}
                        </span>
                    </button>
                    ${!this.readonly ? `
                    <button type="button"
                            class="file-delete-btn -ml-2 opacity-0 group-hover:opacity-100
                                   inline-flex items-center justify-center w-4 h-4 rounded-full
                                   bg-red-500 text-white text-xs
                                   hover:bg-red-600 transition-all"
                            title="删除">
                        <span class="material-symbols-outlined" style="font-size: 12px;">close</span>
                    </button>
                    ` : ''}
                </div>
            `;
        } else {
            // 完整模式：带文件名
            itemHtml = `
                <div class="file-item inline-flex items-center gap-1 px-2 py-1
                            bg-slate-100 dark:bg-slate-700 rounded text-sm
                            hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                     data-index="${index}"
                     data-filename="${this.escapeHtml(fileData.filename)}"
                     data-type="${fileData.type || ''}">
                    <button type="button"
                            class="file-preview-btn inline-flex items-center gap-1 hover:text-primary transition-colors"
                            title="点击预览: ${this.escapeHtml(fileData.filename)}">
                        <span class="material-symbols-outlined text-base ${isPdf ? 'text-red-500' : 'text-primary'}">
                            ${isPdf ? 'picture_as_pdf' : 'image'}
                        </span>
                        <span class="truncate max-w-[100px]" title="${this.escapeHtml(fileData.filename)}">
                            ${this.escapeHtml(fileData.filename)}
                        </span>
                    </button>
                    ${!this.readonly ? `
                    <button type="button"
                            class="file-delete-btn text-slate-400 hover:text-red-500 transition-colors ml-1"
                            title="删除">
                        <span class="material-symbols-outlined text-base">close</span>
                    </button>
                    ` : ''}
                </div>
            `;
        }

        this.fileList.insertAdjacentHTML('beforeend', itemHtml);
    }

    /**
     * 添加待上传文件（新建模式）
     * @param {File[]} files
     */
    addPendingFiles(files) {
        for (const file of files) {
            const index = this.pendingFiles.length;
            this.pendingFiles.push(file);

            const isPdf = file.type && file.type.toLowerCase().includes('pdf');
            let itemHtml;

            if (this.compact) {
                // 紧凑模式：圆形图标按钮
                itemHtml = `
                    <div class="file-item file-pending inline-flex items-center group"
                         data-index="${index}"
                         data-filename="${this.escapeHtml(file.name)}"
                         data-type="${file.type}"
                         data-size="${file.size}">
                        <button type="button"
                                class="file-preview-btn inline-flex items-center justify-center w-8 h-8 rounded-full
                                       bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800
                                       hover:bg-blue-100 dark:hover:bg-blue-900/50
                                       transition-all hover:scale-110"
                                title="${this.escapeHtml(file.name)} (待上传)">
                            <span class="material-symbols-outlined text-lg ${isPdf ? 'text-red-500' : 'text-primary'}">
                                ${isPdf ? 'picture_as_pdf' : 'image'}
                            </span>
                        </button>
                        <button type="button"
                                class="file-remove-btn -ml-2 opacity-0 group-hover:opacity-100
                                       inline-flex items-center justify-center w-4 h-4 rounded-full
                                       bg-red-500 text-white text-xs
                                       hover:bg-red-600 transition-all"
                                title="移除">
                            <span class="material-symbols-outlined" style="font-size: 12px;">close</span>
                        </button>
                    </div>
                `;
            } else {
                // 完整模式：带文件名
                itemHtml = `
                    <div class="file-item file-pending inline-flex items-center gap-1 px-2 py-1
                                bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800
                                rounded text-sm transition-colors"
                         data-index="${index}"
                         data-filename="${this.escapeHtml(file.name)}"
                         data-type="${file.type}"
                         data-size="${file.size}">
                        <span class="inline-flex items-center gap-1">
                            <span class="material-symbols-outlined text-base ${isPdf ? 'text-red-500' : 'text-primary'}">
                                ${isPdf ? 'picture_as_pdf' : 'image'}
                            </span>
                            <span class="truncate max-w-[100px]" title="${this.escapeHtml(file.name)}">
                                ${this.escapeHtml(file.name)}
                            </span>
                        </span>
                        <span class="text-xs text-blue-500 dark:text-blue-400 ml-1">(待上传)</span>
                        <button type="button"
                                class="file-remove-btn text-slate-400 hover:text-red-500 transition-colors ml-1"
                                title="移除">
                            <span class="material-symbols-outlined text-base">close</span>
                        </button>
                    </div>
                `;
            }
            this.fileList.insertAdjacentHTML('beforeend', itemHtml);
        }

        if (this.onFilesChange) {
            this.onFilesChange(this.pendingFiles);
        }
    }

    /**
     * 处理文件列表点击事件
     * @param {Event} e
     */
    handleFileListClick(e) {
        const deleteBtn = e.target.closest('.file-delete-btn');
        const removeBtn = e.target.closest('.file-remove-btn');
        const previewBtn = e.target.closest('.file-preview-btn');
        const fileItem = e.target.closest('.file-item');

        if (!fileItem) return;

        const index = parseInt(fileItem.dataset.index);

        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            this.deleteFile(index, fileItem);
        } else if (removeBtn) {
            e.preventDefault();
            e.stopPropagation();
            this.removePendingFile(index, fileItem);
        } else if (previewBtn) {
            e.preventDefault();
            e.stopPropagation();
            this.previewFile(index, fileItem);
        }
    }

    /**
     * 删除已上传的文件
     * @param {number} index
     * @param {HTMLElement} fileItem
     */
    async deleteFile(index, fileItem) {
        if (!this.deleteApi) {
            this.showError('删除接口未配置');
            return;
        }

        const filename = fileItem.dataset.filename;
        if (!confirm(`确定要删除文件 "${filename}" 吗？`)) {
            return;
        }

        try {
            const deleteUrl = this.deleteApi.replace('{index}', index);
            // 获取 CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

            const response = await fetch(deleteUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            const result = await response.json();

            if (result.success) {
                fileItem.remove();
                // 更新其他文件项的索引
                this.updateFileIndices();
                if (this.onDeleteSuccess) {
                    this.onDeleteSuccess(index);
                }
            } else {
                this.showError(result.message || '删除失败');
                if (this.onDeleteError) {
                    this.onDeleteError(result.message);
                }
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showError('删除失败：' + error.message);
            if (this.onDeleteError) {
                this.onDeleteError(error.message);
            }
        }
    }

    /**
     * 移除待上传的文件（新建模式）
     * @param {number} index
     * @param {HTMLElement} fileItem
     */
    removePendingFile(index, fileItem) {
        // 从待上传列表移除
        this.pendingFiles.splice(index, 1);
        fileItem.remove();

        // 更新剩余项的索引
        this.updatePendingFileIndices();

        if (this.onFilesChange) {
            this.onFilesChange(this.pendingFiles);
        }
    }

    /**
     * 更新已上传文件项的索引
     */
    updateFileIndices() {
        const items = this.fileList.querySelectorAll('.file-item:not(.file-pending)');
        items.forEach((item, idx) => {
            item.dataset.index = idx;
        });
    }

    /**
     * 更新待上传文件项的索引
     */
    updatePendingFileIndices() {
        const items = this.fileList.querySelectorAll('.file-item.file-pending');
        items.forEach((item, idx) => {
            item.dataset.index = idx;
        });
    }

    /**
     * 预览文件
     * @param {number} index
     * @param {HTMLElement} fileItem
     */
    previewFile(index, fileItem) {
        const filename = fileItem.dataset.filename;
        const fileType = fileItem.dataset.type;

        // 如果是待上传文件，使用本地预览
        if (fileItem.classList.contains('file-pending')) {
            const file = this.pendingFiles[index];
            if (file) {
                const url = URL.createObjectURL(file);
                // 如果有自定义预览回调，使用它
                if (this.onPreview) {
                    this.onPreview(url, filename);
                } else {
                    FileUploadComponent.showPreviewModal(url, filename, fileType, true);
                }
            }
            return;
        }

        // 已上传文件，使用 API 预览
        if (!this.previewApi) {
            this.showError('预览接口未配置');
            return;
        }

        const previewUrl = this.previewApi.replace('{index}', index);

        // 如果有自定义预览回调，使用它
        if (this.onPreview) {
            this.onPreview(previewUrl, filename);
        } else {
            FileUploadComponent.showPreviewModal(previewUrl, filename, fileType);
        }
    }

    /**
     * 显示上传进度（重置进度条到0）
     * @param {string} text
     */
    showProgress(text) {
        if (this.progressEl) {
            this.progressEl.classList.remove('hidden');
            if (this.progressText) {
                this.progressText.textContent = text;
            }
            this.updateProgress(0);
        }
    }

    /**
     * 更新进度条百分比
     * @param {number} percent - 0 to 100
     */
    updateProgress(percent) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percent}%`;
        }
        if (this.progressPercent) {
            this.progressPercent.textContent = `${percent}%`;
        }
    }

    /**
     * 隐藏上传进度
     */
    hideProgress() {
        if (this.progressEl) {
            this.progressEl.classList.add('hidden');
            this.updateProgress(0);
        }
    }

    /**
     * 显示错误信息
     * @param {string} message
     */
    showError(message) {
        if (this.errorEl) {
            this.errorEl.classList.remove('hidden');
            if (this.errorText) {
                this.errorText.textContent = message;
            }
        }
        // 3秒后自动隐藏
        setTimeout(() => this.hideError(), 5000);
    }

    /**
     * 隐藏错误信息
     */
    hideError() {
        if (this.errorEl) {
            this.errorEl.classList.add('hidden');
        }
    }

    /**
     * HTML 转义
     * @param {string} str
     * @returns {string}
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * 获取待上传的文件列表（新建模式）
     * @returns {File[]}
     */
    getPendingFiles() {
        return this.pendingFiles;
    }

    /**
     * 清空待上传文件列表
     */
    clearPendingFiles() {
        this.pendingFiles = [];
        const pendingItems = this.fileList.querySelectorAll('.file-pending');
        pendingItems.forEach(item => item.remove());
    }

    /**
     * 设置 entity ID（用于新建后切换到编辑模式）
     * @param {number|string} entityId
     */
    setEntityId(entityId) {
        this.entityId = entityId;
        this.container.dataset.entityId = entityId;
        this.isNewMode = false;
    }

    /**
     * 批量上传待上传文件（新建后调用）
     * @param {string} uploadApi - 上传API路径
     * @returns {Promise<Object[]>}
     */
    async uploadPendingFiles(uploadApi) {
        if (!this.pendingFiles.length) {
            return [];
        }

        this.uploadApi = uploadApi || this.uploadApi;
        const results = [];

        for (let i = 0; i < this.pendingFiles.length; i++) {
            const file = this.pendingFiles[i];
            const label = this.pendingFiles.length > 1
                ? `上传附件 (${i + 1}/${this.pendingFiles.length})`
                : '上传附件中';
            this.showProgress(label);

            try {
                const result = await this.uploadSingleFile(file, (pct) => {
                    this.updateProgress(pct);
                });
                results.push(result);

                if (!result.success) {
                    this.showError(result.message || '上传附件失败');
                    break;
                }
            } catch (error) {
                console.error('Upload pending file error:', error);
                this.showError('上传失败：网络错误，请重试');
                results.push({ success: false, message: error.message });
                break;
            }
        }

        this.hideProgress();
        return results;
    }

    // ==================== 静态方法 ====================

    /**
     * 初始化页面上所有的文件上传组件
     * @param {Object} options - 额外配置选项
     * @returns {FileUploadComponent[]}
     */
    static initAll(options = {}) {
        const containers = document.querySelectorAll('.file-upload-component');
        const instances = [];

        containers.forEach(container => {
            const instance = new FileUploadComponent(container, options);
            container._fileUploadInstance = instance;
            instances.push(instance);
        });

        return instances;
    }

    /**
     * 获取容器的组件实例
     * @param {string|HTMLElement} container
     * @returns {FileUploadComponent|null}
     */
    static getInstance(container) {
        const el = typeof container === 'string'
            ? document.getElementById(container)
            : container;
        return el ? el._fileUploadInstance : null;
    }

    /**
     * 显示预览模态框
     * @param {string} url
     * @param {string} filename
     * @param {string} fileType
     * @param {boolean} isLocalFile - 是否为本地文件（blob URL）
     */
    static showPreviewModal(url, filename, fileType, isLocalFile = false) {
        let modal = document.getElementById('filePreviewModal');

        // 如果模态框不存在，创建一个
        if (!modal) {
            modal = FileUploadComponent.createPreviewModal();
            document.body.appendChild(modal);
        }

        const titleEl = modal.querySelector('#filePreviewModalTitle');
        const imageEl = modal.querySelector('.file-preview-image');
        const pdfEl = modal.querySelector('.file-preview-pdf');
        const loadingEl = modal.querySelector('.file-preview-loading');
        const errorEl = modal.querySelector('.file-preview-error');
        const downloadBtn = modal.querySelector('.file-download-btn');
        const filenameEl = modal.querySelector('.file-preview-filename');
        const closeBtn = modal.querySelector('.file-preview-close-btn');
        const backdrop = modal.querySelector('.file-preview-backdrop');

        // 重置状态
        imageEl.classList.add('hidden');
        pdfEl.classList.add('hidden');
        errorEl.classList.add('hidden');
        loadingEl.classList.remove('hidden');

        // 设置标题和文件名
        if (titleEl) titleEl.textContent = filename;
        if (filenameEl) filenameEl.textContent = filename;

        // 设置下载链接
        if (downloadBtn) {
            downloadBtn.href = url;
            downloadBtn.download = filename;
            // 本地文件隐藏下载按钮
            downloadBtn.style.display = isLocalFile ? 'none' : '';
        }

        // 显示模态框
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        // 绑定关闭事件
        const closeModal = () => {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
            imageEl.src = '';
            pdfEl.src = '';
            // 释放 blob URL
            if (isLocalFile && url.startsWith('blob:')) {
                URL.revokeObjectURL(url);
            }
        };

        closeBtn.onclick = closeModal;
        backdrop.onclick = closeModal;

        // ESC 关闭
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        // 根据文件类型显示预览
        const isPdf = fileType && fileType.toLowerCase().includes('pdf');

        if (isPdf) {
            // PDF 预览
            pdfEl.onload = () => {
                loadingEl.classList.add('hidden');
                pdfEl.classList.remove('hidden');
            };
            pdfEl.onerror = () => {
                loadingEl.classList.add('hidden');
                errorEl.classList.remove('hidden');
            };
            pdfEl.src = url;
        } else {
            // 图片预览
            imageEl.onload = () => {
                loadingEl.classList.add('hidden');
                imageEl.classList.remove('hidden');
            };
            imageEl.onerror = () => {
                loadingEl.classList.add('hidden');
                errorEl.classList.remove('hidden');
            };
            imageEl.src = url;
            imageEl.alt = filename;
        }
    }

    /**
     * 创建预览模态框
     * @returns {HTMLElement}
     */
    static createPreviewModal() {
        const modal = document.createElement('div');
        modal.id = 'filePreviewModal';
        modal.className = 'fixed inset-0 z-50 hidden overflow-y-auto';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');

        modal.innerHTML = `
            <div class="file-preview-backdrop fixed inset-0 bg-black/60 transition-opacity"></div>
            <div class="flex min-h-full items-center justify-center p-4">
                <div class="file-preview-content relative w-full max-w-4xl transform overflow-hidden rounded-xl
                            bg-white dark:bg-slate-800 shadow-2xl transition-all">
                    <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
                        <h3 id="filePreviewModalTitle" class="text-lg font-medium text-slate-900 dark:text-slate-100 truncate pr-4">
                            文件预览
                        </h3>
                        <div class="flex items-center gap-2">
                            <a href="#"
                               class="file-download-btn inline-flex items-center gap-1 px-3 py-1.5 rounded-lg
                                      text-sm font-medium text-slate-700 dark:text-slate-300
                                      bg-slate-100 dark:bg-slate-700
                                      hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                               download>
                                <span class="material-symbols-outlined" style="font-size: 18px;">download</span>
                                <span>下载</span>
                            </a>
                            <button type="button"
                                    class="file-preview-close-btn rounded-lg p-1.5
                                           text-slate-400 hover:text-slate-600 dark:hover:text-slate-300
                                           hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                                <span class="material-symbols-outlined" style="font-size: 24px;">close</span>
                            </button>
                        </div>
                    </div>
                    <div class="file-preview-body p-4 max-h-[70vh] overflow-auto flex items-center justify-center bg-slate-50 dark:bg-slate-900">
                        <img class="file-preview-image hidden max-w-full max-h-[60vh] object-contain rounded" src="" alt="">
                        <iframe class="file-preview-pdf hidden w-full h-[60vh] rounded border-0" src=""></iframe>
                        <div class="file-preview-loading flex flex-col items-center gap-3 text-slate-400">
                            <span class="material-symbols-outlined animate-spin" style="font-size: 48px;">progress_activity</span>
                            <span>加载中...</span>
                        </div>
                        <div class="file-preview-error hidden flex flex-col items-center gap-3 text-red-400">
                            <span class="material-symbols-outlined" style="font-size: 48px;">error</span>
                            <span class="file-preview-error-text">加载失败</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between px-4 py-2 border-t border-slate-200 dark:border-slate-700
                                text-xs text-slate-500 dark:text-slate-400">
                        <span class="file-preview-filename truncate"></span>
                        <span class="file-preview-size"></span>
                    </div>
                </div>
            </div>
        `;

        return modal;
    }
}

// 全局导出
window.FileUploadComponent = FileUploadComponent;
