/**
 * 更新产品状态
 * @param {number} productId - 产品ID
 * @param {string} status - 目标状态：'active', 'discontinued', 或 'upcoming'
 * @param {Element} buttonElement - 点击的按钮元素
 */
function updateProductStatus(productId, status, buttonElement) {
    // 禁用按钮，显示加载状态
    const originalText = buttonElement.textContent;
    buttonElement.disabled = true;
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 更新中...';
    
    // 发送API请求
    fetch(`/api/products/${productId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 显示成功消息
            showToast('success', data.message);
            
            // 重新加载产品列表或更新UI
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            // 显示错误消息
            showToast('error', data.message || '更新状态失败');
            // 恢复按钮状态
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('更新产品状态时出错:', error);
        showToast('error', '网络错误，请稍后重试');
        // 恢复按钮状态
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
    });
}

/**
 * 显示消息提示
 * @param {string} type - 消息类型: 'success', 'error', 'info', 'warning'
 * @param {string} message - 显示的消息内容
 */
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
    `;
    
    toastContainer.appendChild(toast);
    
    // 自动消失
    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => {
            toastContainer.removeChild(toast);
            if (toastContainer.children.length === 0) {
                document.body.removeChild(toastContainer);
            }
        }, 300);
    }, 3000);
}

/**
 * 创建Toast容器
 * @returns {Element} - Toast容器元素
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
    `;
    document.body.appendChild(container);
    
    // 添加CSS样式
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                padding: 12px 15px;
                margin-bottom: 10px;
                border-radius: 4px;
                color: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                animation: toast-fade-in 0.3s ease;
                min-width: 250px;
            }
            .toast-success { background-color: #4CAF50; }
            .toast-error { background-color: #F44336; }
            .toast-info { background-color: #2196F3; }
            .toast-warning { background-color: #FF9800; }
            
            @keyframes toast-fade-in {
                from { opacity: 0; transform: translateY(-20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .toast-fade-out {
                opacity: 0;
                transform: translateY(-20px);
                transition: opacity 0.3s, transform 0.3s;
            }
        `;
        document.head.appendChild(style);
    }
    
    return container;
} 