/**
 * 产品列表悬停图片预览功能
 * 当鼠标悬停在有图片的产品行时显示图片预览
 */

// 全局变量
let hoverPreviewContainer = null;
let hoverPreviewImg = null;
let hoverPreviewTitle = null;
let hoverPreviewLoading = null;
let hoverPreviewError = null;
let currentImageUrl = '';
let previewTimeout = null;
let hideTimeout = null;

// 配置项
const HoverPreviewConfig = {
    showDelay: 300,      // 显示延迟(毫秒)
    hideDelay: 100,      // 隐藏延迟(毫秒)
    offset: {            // 预览框偏移量
        x: 15,
        y: 10
    },
    maxRetries: 3        // 图片加载最大重试次数
};

/**
 * 初始化悬停预览功能
 */
function initializeHoverPreview() {
    // 获取DOM元素
    hoverPreviewContainer = document.getElementById('hoverPreviewContainer');
    
    if (!hoverPreviewContainer) {
        console.warn('悬停预览容器未找到');
        return;
    }
    
    hoverPreviewImg = document.getElementById('hoverPreviewImage');
    hoverPreviewTitle = document.querySelector('.hover-preview-title');
    hoverPreviewLoading = document.querySelector('.hover-preview-loading');
    hoverPreviewError = document.querySelector('.hover-preview-error');
    
    // 设置事件监听
    setupHoverEvents();
    
    console.log('✅ 悬停预览功能初始化完成');
}

/**
 * 设置悬停事件监听
 */
function setupHoverEvents() {
    // 使用事件委托处理动态内容
    document.addEventListener('mouseover', function(e) {
        const productContainer = e.target.closest('.product-name-container[data-image-url]');
        if (productContainer) {
            handleMouseEnter(e, productContainer);
        }
    });
    
    document.addEventListener('mouseout', function(e) {
        const productContainer = e.target.closest('.product-name-container[data-image-url]');
        if (productContainer) {
            handleMouseLeave(e, productContainer);
        }
    });
    
    // 预览容器自身的悬停处理
    if (hoverPreviewContainer) {
        hoverPreviewContainer.addEventListener('mouseenter', function() {
            clearTimeout(hideTimeout);
        });
        
        hoverPreviewContainer.addEventListener('mouseleave', function() {
            hideHoverPreview();
        });
    }
    
    // 监听页面滚动，隐藏预览
    window.addEventListener('scroll', function() {
        if (hoverPreviewContainer && hoverPreviewContainer.style.display !== 'none') {
            hideHoverPreview();
        }
    }, { passive: true });
}

/**
 * 处理鼠标进入事件
 */
function handleMouseEnter(event, container) {
    clearTimeout(hideTimeout);
    
    const imageUrl = container.dataset.imageUrl;
    const productName = container.dataset.productName || '产品图片';
    
    if (!imageUrl) return;
    
    // 设置延迟显示
    previewTimeout = setTimeout(() => {
        showHoverPreview(event, imageUrl, productName);
    }, HoverPreviewConfig.showDelay);
}

/**
 * 处理鼠标离开事件
 */
function handleMouseLeave(event, container) {
    clearTimeout(previewTimeout);
    
    // 检查鼠标是否移动到预览容器
    const relatedTarget = event.relatedTarget;
    if (relatedTarget && hoverPreviewContainer && 
        (hoverPreviewContainer.contains(relatedTarget) || hoverPreviewContainer === relatedTarget)) {
        return; // 鼠标移到预览容器，不隐藏
    }
    
    // 设置延迟隐藏
    hideTimeout = setTimeout(() => {
        hideHoverPreview();
    }, HoverPreviewConfig.hideDelay);
}

/**
 * 显示悬停预览
 */
function showHoverPreview(event, imageUrl, productName) {
    if (!hoverPreviewContainer || !imageUrl) return;
    
    // 设置标题
    if (hoverPreviewTitle) {
        hoverPreviewTitle.textContent = productName;
    }
    
    // 重置状态
    resetPreviewState();
    
    // 显示加载状态
    showLoading();
    
    // 计算位置
    const position = calculatePreviewPosition(event);
    hoverPreviewContainer.style.left = position.x + 'px';
    hoverPreviewContainer.style.top = position.y + 'px';
    hoverPreviewContainer.style.display = 'block';
    
    // 加载图片
    currentImageUrl = imageUrl;
    loadPreviewImage(imageUrl);
}

/**
 * 隐藏悬停预览
 */
function hideHoverPreview() {
    if (hoverPreviewContainer) {
        hoverPreviewContainer.style.display = 'none';
    }
    currentImageUrl = '';
    clearTimeout(previewTimeout);
    clearTimeout(hideTimeout);
}

/**
 * 计算预览位置
 */
function calculatePreviewPosition(event) {
    const mouseX = event.clientX;
    const mouseY = event.clientY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const previewWidth = 400;  // 预览框最大宽度
    const previewHeight = 500; // 预览框最大高度
    
    let x = mouseX + HoverPreviewConfig.offset.x;
    let y = mouseY + HoverPreviewConfig.offset.y;
    
    // 防止超出右边界
    if (x + previewWidth > windowWidth) {
        x = mouseX - previewWidth - HoverPreviewConfig.offset.x;
    }
    
    // 防止超出下边界
    if (y + previewHeight > windowHeight) {
        y = mouseY - previewHeight - HoverPreviewConfig.offset.y;
    }
    
    // 确保不超出左边界和上边界
    x = Math.max(10, x);
    y = Math.max(10, y);
    
    return { x, y };
}

/**
 * 重置预览状态
 */
function resetPreviewState() {
    if (hoverPreviewImg) {
        hoverPreviewImg.style.display = 'none';
    }
    if (hoverPreviewLoading) {
        hoverPreviewLoading.style.display = 'flex';
    }
    if (hoverPreviewError) {
        hoverPreviewError.style.display = 'none';
    }
}

/**
 * 显示加载状态
 */
function showLoading() {
    if (hoverPreviewLoading) {
        hoverPreviewLoading.style.display = 'flex';
    }
    if (hoverPreviewImg) {
        hoverPreviewImg.style.display = 'none';
    }
    if (hoverPreviewError) {
        hoverPreviewError.style.display = 'none';
    }
}

/**
 * 显示错误状态
 */
function showError() {
    if (hoverPreviewError) {
        hoverPreviewError.style.display = 'flex';
    }
    if (hoverPreviewLoading) {
        hoverPreviewLoading.style.display = 'none';
    }
    if (hoverPreviewImg) {
        hoverPreviewImg.style.display = 'none';
    }
}

/**
 * 显示图片
 */
function showImage() {
    if (hoverPreviewImg) {
        hoverPreviewImg.style.display = 'block';
    }
    if (hoverPreviewLoading) {
        hoverPreviewLoading.style.display = 'none';
    }
    if (hoverPreviewError) {
        hoverPreviewError.style.display = 'none';
    }
}

/**
 * 处理图片URL - 确保使用正确的URL格式
 */
function processImageUrl(imageUrl) {
    if (!imageUrl) return null;
    
    // 如果已经是完整URL（http或https开头），直接返回
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
        return imageUrl;
    }
    
    // 如果是Supabase相对路径，尝试构建完整URL
    if (imageUrl.includes('supabase')) {
        return imageUrl; // 已经是Supabase URL
    }
    
    // 如果是本地文件路径，尝试构建static路径
    if (!imageUrl.startsWith('/')) {
        return `/static/uploads/products/${imageUrl}`;
    }
    
    return imageUrl;
}

/**
 * 加载预览图片
 */
function loadPreviewImage(imageUrl) {
    if (!hoverPreviewImg) {
        showError();
        return;
    }
    
    // 处理图片URL
    const processedUrl = processImageUrl(imageUrl);
    if (!processedUrl) {
        console.warn('无效的图片URL:', imageUrl);
        showError();
        return;
    }
    
    // 创建新的图片对象进行预加载
    const img = new Image();
    
    img.onload = function() {
        // 检查是否还是当前请求的图片
        if (imageUrl === currentImageUrl && hoverPreviewContainer.style.display !== 'none') {
            hoverPreviewImg.src = processedUrl;
            hoverPreviewImg.alt = hoverPreviewTitle ? hoverPreviewTitle.textContent : '产品图片';
            showImage();
        }
    };
    
    img.onerror = function() {
        // 检查是否还是当前请求的图片
        if (imageUrl === currentImageUrl && hoverPreviewContainer.style.display !== 'none') {
            console.warn('图片加载失败，尝试备用路径:', processedUrl);
            
            // 如果失败，尝试其他可能的路径
            tryAlternativeImagePaths(imageUrl);
        }
    };
    
    // 设置加载超时
    setTimeout(() => {
        if (imageUrl === currentImageUrl && hoverPreviewImg && 
            hoverPreviewLoading && hoverPreviewLoading.style.display !== 'none') {
            console.warn('图片加载超时:', processedUrl);
            showError();
        }
    }, 5000);
    
    // 开始加载
    img.src = processedUrl;
}

/**
 * 尝试备用图片路径
 */
function tryAlternativeImagePaths(originalUrl) {
    const alternatives = [
        `/static/uploads/${originalUrl}`,
        `/static/product_images/${originalUrl}`,
        originalUrl // 最后尝试原始路径
    ];
    
    let currentIndex = 0;
    
    function tryNext() {
        if (currentIndex >= alternatives.length) {
            console.error('所有备用路径都加载失败:', originalUrl);
            showError();
            return;
        }
        
        const testUrl = alternatives[currentIndex++];
        const testImg = new Image();
        
        testImg.onload = function() {
            if (originalUrl === currentImageUrl && hoverPreviewContainer.style.display !== 'none') {
                hoverPreviewImg.src = testUrl;
                hoverPreviewImg.alt = hoverPreviewTitle ? hoverPreviewTitle.textContent : '产品图片';
                showImage();
                console.log('✅ 成功加载备用路径:', testUrl);
            }
        };
        
        testImg.onerror = function() {
            tryNext(); // 尝试下一个路径
        };
        
        testImg.src = testUrl;
    }
    
    tryNext();
}


/**
 * 刷新悬停预览功能（用于动态内容更新后）
 */
function refreshHoverPreview() {
    // 重新设置事件监听（如果需要）
    console.log('悬停预览功能已刷新');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initializeHoverPreview);

// 导出函数供外部调用
window.hideHoverPreview = hideHoverPreview;
window.refreshHoverPreview = refreshHoverPreview;