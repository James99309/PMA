/**
 * 分类文件上传工具
 * 支持产品图片/PDF按分类共享
 *
 * 使用方法:
 * CategoryFileUpload.init({
 *     productId: 123,
 *     categoryStatusUrl: '/api/products/123/category-file-status',
 *     uploadImageUrl: '/api/products/123/upload-image',
 *     uploadPdfUrl: '/api/products/123/upload-pdf',
 *     categoryName: '分类名称',
 *     csrfToken: 'xxx',
 *     translations: { ... }  // 可选的翻译文本
 * });
 */
const CategoryFileUpload = {
    config: {
        productId: null,
        categoryStatusUrl: '',
        uploadImageUrl: '',
        uploadPdfUrl: '',
        categoryName: '',
        csrfToken: '',
        translations: {}
    },

    // 默认翻译文本
    defaultTranslations: {
        image: '图片',
        pdf: 'PDF',
        uploadImage: '上传图片',
        uploadPdf: '上传PDF',
        uploading: '上传中...',
        uploadSuccess: '上传成功！',
        uploadFailed: '上传失败',
        unknownError: '未知错误',
        uploadError: '上传过程中发生错误，请重试',
        category: '分类',
        hasShared: '已有共享',
        chooseAction: '，请选择操作方式：',
        setAsCategory: '（已设为分类共享文件）',
        updatedCategory: '（已覆盖分类共享文件）',
        productOnlyResult: '（仅用于此产品）'
    },

    /**
     * 初始化配置
     */
    init(options) {
        Object.assign(this.config, options);
        // 合并翻译
        this.config.translations = Object.assign({}, this.defaultTranslations, options.translations || {});
    },

    /**
     * 获取翻译文本
     */
    t(key) {
        return this.config.translations[key] || this.defaultTranslations[key] || key;
    },

    /**
     * 检查分类文件状态并上传
     */
    checkAndUpload(file, fileType) {
        const self = this;
        fetch(this.config.categoryStatusUrl)
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    self.uploadFile(file, fileType, null);
                    return;
                }

                const categoryFile = fileType === 'image' ? data.category_image : data.category_pdf;
                if (categoryFile) {
                    self.showConfirmModal(fileType, data.category_name, function(updateCategory) {
                        self.uploadFile(file, fileType, updateCategory);
                    });
                } else {
                    self.uploadFile(file, fileType, null);
                }
            })
            .catch(error => {
                console.error('检查分类文件状态失败:', error);
                self.uploadFile(file, fileType, null);
            });
    },

    /**
     * 显示分类文件确认弹窗
     * 使用项目标准的 render_custom_dialog 组件
     */
    showConfirmModal(fileType, categoryName, callback) {
        const self = this;
        const fileTypeName = fileType === 'image' ? this.t('image') : this.t('pdf');
        const dialogId = 'categoryFileConfirmDialog';

        // 更新对话框内容
        const content = document.getElementById('categoryFileConfirmContent');
        if (content) {
            content.innerHTML = `<p>${this.t('category')} <strong>${categoryName}</strong> ${this.t('hasShared')}${fileTypeName}${this.t('chooseAction')}</p>`;
        }

        // 绑定按钮事件
        const btnUpdateCategory = document.getElementById('btnUpdateCategory');
        const btnProductOnly = document.getElementById('btnProductOnly');

        if (btnUpdateCategory) {
            btnUpdateCategory.onclick = function() {
                closeCustomDialog(dialogId);
                callback(true);
            };
        }

        if (btnProductOnly) {
            btnProductOnly.onclick = function() {
                closeCustomDialog(dialogId);
                callback(false);
            };
        }

        // 显示对话框
        showCustomDialog(dialogId);
    },

    /**
     * 上传文件（支持分类共享）
     */
    uploadFile(file, fileType, updateCategory) {
        const self = this;
        const uploadBtn = document.getElementById(fileType === 'image' ? 'uploadImageBtn' : 'uploadPdfBtn');
        const fileInput = document.getElementById(fileType === 'image' ? 'imageFileInput' : 'pdfFileInput');
        const fileTypeName = fileType === 'image' ? this.t('image') : this.t('pdf');

        if (!uploadBtn) return;

        // 禁用按钮并显示上传状态
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${this.t('uploading')}`;

        // 创建 FormData
        const formData = new FormData();
        formData.append(fileType, file);
        formData.append('csrf_token', this.config.csrfToken);
        if (updateCategory !== null) {
            formData.append('update_category', updateCategory.toString());
        }

        // 发送上传请求
        const apiUrl = fileType === 'image' ? this.config.uploadImageUrl : this.config.uploadPdfUrl;

        fetch(apiUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let message = fileTypeName + self.t('uploadSuccess');
                if (data.set_as_category) {
                    message += self.t('setAsCategory');
                } else if (data.updated_category) {
                    message += self.t('updatedCategory');
                } else if (data.product_only) {
                    message += self.t('productOnlyResult');
                }

                // 使用showTopNotification如果存在，否则使用alert
                if (typeof showTopNotification === 'function') {
                    showTopNotification(message, 'success', 2000);
                } else {
                    alert(message);
                }
                setTimeout(() => location.reload(), 2000);
            } else if (data.need_confirm) {
                self.showConfirmModal(fileType, self.config.categoryName, function(choice) {
                    self.uploadFile(file, fileType, choice);
                });
            } else {
                alert(self.t('uploadFailed') + ': ' + (data.error || data.message || self.t('unknownError')));
            }
        })
        .catch(error => {
            console.error('上传错误:', error);
            alert(self.t('uploadError'));
        })
        .finally(() => {
            uploadBtn.disabled = false;
            const btnText = fileType === 'image' ? self.t('uploadImage') : self.t('uploadPdf');
            uploadBtn.innerHTML = `<i class="fas fa-upload me-1"></i>${btnText}`;
            if (fileInput) fileInput.value = '';
        });
    }
};
