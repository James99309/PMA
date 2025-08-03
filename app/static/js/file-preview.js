/**
 * 通用文件预览组件JavaScript支持
 * 支持图片预览和PDF首页预览功能
 */

// PDF.js库CDN（如果未加载则动态加载）
const PDFJS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
const PDFJS_WORKER_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// 全局配置
const FilePreviewConfig = {
    pdfRenderScale: 1.5,  // PDF渲染缩放比例
    maxRetries: 3,        // 最大重试次数
    timeoutMs: 10000      // 超时时间(毫秒)
};

/**
 * 初始化文件预览功能
 */
function initializeFilePreview() {
    // 初始化所有PDF预览
    initializePDFPreviews();
    
    // 为动态添加的内容设置监听
    setupDynamicPreviewHandlers();
}

/**
 * 初始化所有PDF预览
 */
function initializePDFPreviews() {
    const pdfContainers = document.querySelectorAll('[data-file-type="pdf"]');
    
    if (pdfContainers.length > 0) {
        loadPDFJS().then(() => {
            pdfContainers.forEach(container => {
                const fileUrl = container.dataset.fileUrl;
                if (fileUrl) {
                    renderPDFPreview(container, fileUrl);
                }
            });
        }).catch(error => {
            console.error('PDF.js加载失败:', error);
            // 显示PDF图标作为后备
            pdfContainers.forEach(container => {
                showPDFFallback(container);
            });
        });
    }
}

/**
 * 动态加载PDF.js库
 */
function loadPDFJS() {
    return new Promise((resolve, reject) => {
        // 检查是否已加载
        if (window.pdfjsLib) {
            resolve();
            return;
        }
        
        // 动态加载PDF.js
        const script = document.createElement('script');
        script.src = PDFJS_CDN;
        script.onload = () => {
            // 设置worker
            if (window.pdfjsLib) {
                window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_CDN;
                resolve();
            } else {
                reject(new Error('PDF.js加载失败'));
            }
        };
        script.onerror = () => reject(new Error('PDF.js脚本加载失败'));
        document.head.appendChild(script);
    });
}

/**
 * 渲染PDF预览
 */
function renderPDFPreview(container, pdfUrl) {
    const canvas = container.querySelector('.pdf-preview-canvas');
    const loading = container.querySelector('.pdf-loading');
    const fallback = container.querySelector('.pdf-fallback');
    
    if (!canvas || !window.pdfjsLib) {
        showPDFFallback(container);
        return;
    }
    
    // 设置超时
    const timeoutId = setTimeout(() => {
        console.warn('PDF预览加载超时:', pdfUrl);
        showPDFFallback(container);
    }, FilePreviewConfig.timeoutMs);
    
    // 加载PDF
    const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
    
    loadingTask.promise.then(pdf => {
        clearTimeout(timeoutId);
        
        // 获取第一页
        return pdf.getPage(1);
    }).then(page => {
        // 计算渲染尺寸
        const containerRect = container.getBoundingClientRect();
        const viewport = page.getViewport({ scale: 1 });
        
        // 计算适合容器的缩放比例
        const scaleX = containerRect.width / viewport.width;
        const scaleY = containerRect.height / viewport.height;
        const scale = Math.min(scaleX, scaleY, FilePreviewConfig.pdfRenderScale);
        
        const scaledViewport = page.getViewport({ scale });
        
        // 设置canvas尺寸
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        
        // 渲染PDF页面
        const renderContext = {
            canvasContext: canvas.getContext('2d'),
            viewport: scaledViewport
        };
        
        return page.render(renderContext).promise;
    }).then(() => {
        // 渲染成功，显示canvas
        loading.style.display = 'none';
        fallback.style.display = 'none';
        canvas.style.display = 'block';
    }).catch(error => {
        clearTimeout(timeoutId);
        console.error('PDF预览渲染失败:', error);
        showPDFFallback(container);
    });
}

/**
 * 显示PDF后备图标
 */
function showPDFFallback(container) {
    const loading = container.querySelector('.pdf-loading');
    const fallback = container.querySelector('.pdf-fallback');
    const canvas = container.querySelector('.pdf-preview-canvas');
    
    if (loading) loading.style.display = 'none';
    if (canvas) canvas.style.display = 'none';
    if (fallback) fallback.style.display = 'flex';
}

/**
 * 打开文件预览模态框
 */
function openFileModal(fileUrl, fileType) {
    const modal = document.getElementById('filePreviewModal');
    const modalContent = document.getElementById('modalFileContent');
    const downloadBtn = document.getElementById('modalDownloadBtn');
    
    if (!modal || !modalContent) {
        console.error('文件预览模态框未找到');
        return;
    }
    
    // 设置下载链接
    downloadBtn.href = fileUrl;
    
    // 清空内容
    modalContent.innerHTML = '';
    
    if (fileType === 'image') {
        // 显示大图
        const img = document.createElement('img');
        img.src = fileUrl;
        img.className = 'file-preview-image';
        img.style.maxWidth = '100%';
        img.style.maxHeight = '70vh';
        img.style.objectFit = 'contain';
        
        img.onerror = () => {
            modalContent.innerHTML = '<div class="text-danger"><i class="fas fa-exclamation-triangle"></i> 图片加载失败</div>';
        };
        
        modalContent.appendChild(img);
        
    } else if (fileType === 'pdf') {
        // 显示PDF预览
        modalContent.innerHTML = `
            <div class="pdf-modal-container">
                <div class="pdf-loading text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <div class="mt-2">正在加载PDF预览...</div>
                </div>
                <canvas class="pdf-preview-canvas" style="display: none;"></canvas>
                <div class="pdf-fallback text-center" style="display: none;">
                    <i class="fas fa-file-pdf fa-4x text-danger mb-3"></i>
                    <div>PDF预览不可用</div>
                    <div class="mt-2">
                        <a href="${fileUrl}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt me-1"></i>在新窗口打开
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        // 渲染PDF
        if (window.pdfjsLib) {
            renderModalPDF(modalContent, fileUrl);
        } else {
            loadPDFJS().then(() => {
                renderModalPDF(modalContent, fileUrl);
            }).catch(() => {
                showModalPDFFallback(modalContent);
            });
        }
    }
    
    // 显示模态框
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

/**
 * 在模态框中渲染PDF
 */
function renderModalPDF(modalContent, pdfUrl) {
    const canvas = modalContent.querySelector('.pdf-preview-canvas');
    const loading = modalContent.querySelector('.pdf-loading');
    const fallback = modalContent.querySelector('.pdf-fallback');
    
    const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
    
    loadingTask.promise.then(pdf => {
        return pdf.getPage(1);
    }).then(page => {
        const viewport = page.getViewport({ scale: 2 }); // 高分辨率预览
        
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        const renderContext = {
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
        };
        
        return page.render(renderContext).promise;
    }).then(() => {
        loading.style.display = 'none';
        fallback.style.display = 'none';
        canvas.style.display = 'block';
    }).catch(error => {
        console.error('模态框PDF渲染失败:', error);
        showModalPDFFallback(modalContent);
    });
}

/**
 * 显示模态框PDF后备内容
 */
function showModalPDFFallback(modalContent) {
    const loading = modalContent.querySelector('.pdf-loading');
    const fallback = modalContent.querySelector('.pdf-fallback');
    const canvas = modalContent.querySelector('.pdf-preview-canvas');
    
    if (loading) loading.style.display = 'none';
    if (canvas) canvas.style.display = 'none';
    if (fallback) fallback.style.display = 'block';
}

/**
 * 设置动态内容的预览处理器
 */
function setupDynamicPreviewHandlers() {
    // 使用事件委托处理动态添加的内容
    document.addEventListener('DOMContentLoaded', function() {
        // 监听动态内容变化
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // 检查新添加的PDF预览容器
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const pdfContainers = node.querySelectorAll ? 
                                node.querySelectorAll('[data-file-type="pdf"]') : [];
                            
                            if (pdfContainers.length > 0 && window.pdfjsLib) {
                                pdfContainers.forEach(container => {
                                    const fileUrl = container.dataset.fileUrl;
                                    if (fileUrl) {
                                        renderPDFPreview(container, fileUrl);
                                    }
                                });
                            }
                        }
                    });
                }
            });
        });
        
        // 开始观察
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

/**
 * 刷新指定容器的文件预览
 */
function refreshFilePreview(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const fileType = container.dataset.fileType;
    const fileUrl = container.dataset.fileUrl;
    
    if (fileType === 'pdf' && fileUrl) {
        if (window.pdfjsLib) {
            renderPDFPreview(container, fileUrl);
        } else {
            loadPDFJS().then(() => {
                renderPDFPreview(container, fileUrl);
            }).catch(() => {
                showPDFFallback(container);
            });
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initializeFilePreview);