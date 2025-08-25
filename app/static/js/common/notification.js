/**
 * 通用Toast通知组件
 * 支持多种消息类型、自动消失、堆叠显示等功能
 */

class ToastNotification {
    constructor() {
        this.container = null;
        this.toasts = new Map(); // 存储活动的toast
        this.maxToasts = 5; // 最大同时显示的toast数量
        this.defaultDuration = 4000; // 默认显示时长（毫秒）
        
        this.init();
    }
    
    init() {
        // 创建toast容器
        this.createContainer();
        
        // 绑定到全局
        window.showToast = this.show.bind(this);
        window.hideToast = this.hide.bind(this);
        window.clearToasts = this.clearAll.bind(this);
    }
    
    createContainer() {
        // 检查是否已存在容器
        this.container = document.getElementById('toast-container');
        if (this.container) {
            return;
        }
        
        // 创建新容器
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        this.container.innerHTML = ''; // 确保容器为空
        
        // 添加到body
        document.body.appendChild(this.container);
    }
    
    /**
     * 显示Toast通知
     * @param {string} type - 消息类型: 'success', 'error', 'warning', 'info'
     * @param {string} message - 消息内容
     * @param {object} options - 选项配置
     */
    show(type = 'info', message = '', options = {}) {
        const config = {
            duration: options.duration || this.defaultDuration,
            closable: options.closable !== false, // 默认可关闭
            persistent: options.persistent || false, // 是否持久化显示
            id: options.id || this.generateId(),
            position: options.position || 'top-right',
            ...options
        };
        
        // 检查是否超出最大数量
        if (this.toasts.size >= this.maxToasts) {
            // 移除最旧的toast
            const oldestId = this.toasts.keys().next().value;
            this.hide(oldestId);
        }
        
        // 创建toast元素
        const toast = this.createToast(type, message, config);
        
        // 添加到容器
        this.container.appendChild(toast);
        
        // 存储引用
        this.toasts.set(config.id, {
            element: toast,
            config: config,
            createdAt: Date.now()
        });
        
        // 触发动画
        requestAnimationFrame(() => {
            toast.classList.add('toast-show');
        });
        
        // 设置自动消失
        if (!config.persistent && config.duration > 0) {
            setTimeout(() => {
                this.hide(config.id);
            }, config.duration);
        }
        
        return config.id;
    }
    
    createToast(type, message, config) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.id = `toast-${config.id}`;
        
        // 图标映射
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const icon = iconMap[type] || iconMap.info;
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="${icon}"></i>
                </div>
                <div class="toast-message">${message}</div>
                ${config.closable ? `
                    <button type="button" class="toast-close" aria-label="关闭">
                        <i class="fas fa-times"></i>
                    </button>
                ` : ''}
            </div>
        `;
        
        // 绑定关闭事件
        if (config.closable) {
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => {
                this.hide(config.id);
            });
        }
        
        // 鼠标悬停暂停自动消失
        if (!config.persistent) {
            let timeoutId = null;
            
            toast.addEventListener('mouseenter', () => {
                toast.classList.add('toast-paused');
            });
            
            toast.addEventListener('mouseleave', () => {
                toast.classList.remove('toast-paused');
            });
        }
        
        return toast;
    }
    
    /**
     * 隐藏指定的toast
     * @param {string} id - Toast ID
     */
    hide(id) {
        const toastData = this.toasts.get(id);
        if (!toastData) {
            return;
        }
        
        const { element } = toastData;
        
        // 添加消失动画
        element.classList.add('toast-hide');
        element.classList.remove('toast-show');
        
        // 动画完成后移除
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.toasts.delete(id);
        }, 300); // 匹配CSS动画时长
    }
    
    /**
     * 清空所有toast
     */
    clearAll() {
        this.toasts.forEach((_, id) => {
            this.hide(id);
        });
    }
    
    /**
     * 生成唯一ID
     */
    generateId() {
        return 'toast_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * 更新toast消息
     * @param {string} id - Toast ID
     * @param {string} newMessage - 新消息内容
     */
    updateMessage(id, newMessage) {
        const toastData = this.toasts.get(id);
        if (!toastData) {
            return false;
        }
        
        const messageElement = toastData.element.querySelector('.toast-message');
        if (messageElement) {
            messageElement.innerHTML = newMessage;
            return true;
        }
        
        return false;
    }
    
    /**
     * 检查指定类型的toast是否存在
     * @param {string} type - 消息类型
     */
    hasType(type) {
        return Array.from(this.toasts.values()).some(
            toast => toast.element.classList.contains(`toast-${type}`)
        );
    }
}

// 全局快捷方法
const createToastMethods = (notification) => {
    return {
        success: (message, options = {}) => notification.show('success', message, options),
        error: (message, options = {}) => notification.show('error', message, options),
        warning: (message, options = {}) => notification.show('warning', message, options),
        info: (message, options = {}) => notification.show('info', message, options)
    };
};

// 初始化
let toastInstance = null;

// DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        toastInstance = new ToastNotification();
        // 添加全局快捷方法
        Object.assign(window, createToastMethods(toastInstance));
    });
} else {
    // 如果DOM已加载，立即初始化
    toastInstance = new ToastNotification();
    // 添加全局快捷方法
    Object.assign(window, createToastMethods(toastInstance));
}

// 导出类（用于模块化环境）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastNotification;
}