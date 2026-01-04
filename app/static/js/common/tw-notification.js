/**
 * Tailwind 风格通知组件
 * 使用 Material Symbols 图标，支持暗色模式
 *
 * 用法:
 *   showNotification('保存成功', 'success');
 *   showNotification('操作失败', 'error');
 *   showNotification('请注意', 'warning');
 *   showNotification('提示信息', 'info');
 *   showToast('保存成功', 'success');  // 别名，兼容旧代码
 *
 * 参数:
 *   message: 消息内容
 *   type: 'success' | 'error' | 'warning' | 'info' (默认 'info')
 *   duration: 显示时长毫秒数 (默认 3000，设为 0 则不自动消失)
 */
(function() {
    'use strict';

    const typeStyles = {
        success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border-green-200 dark:border-green-800',
        error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800',
        warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800',
        info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800'
    };

    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };

    /**
     * 显示通知
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型: 'success', 'error', 'warning', 'info'
     * @param {number} duration - 显示时长(毫秒)，默认3000，设为0则不自动消失
     */
    function showNotification(message, type = 'info', duration = 3000) {
        // 移除已有的通知
        const existing = document.getElementById('twNotification');
        if (existing) {
            existing.remove();
        }

        // 创建通知元素
        const notification = document.createElement('div');
        notification.id = 'twNotification';
        notification.className = `fixed top-4 left-1/2 -translate-x-1/2 z-[9999] flex items-center gap-2 px-4 py-3 rounded-lg border shadow-lg transition-all duration-300 ${typeStyles[type] || typeStyles.info}`;
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -20px)';
        notification.innerHTML = `
            <span class="material-symbols-outlined text-xl">${icons[type] || icons.info}</span>
            <span class="text-sm font-medium">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 opacity-60 hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined text-lg">close</span>
            </button>
        `;

        document.body.appendChild(notification);

        // 触发进入动画
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translate(-50%, 0)';
        });

        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.style.opacity = '0';
                    notification.style.transform = 'translate(-50%, -20px)';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
    }

    // 绑定到全局，同时提供两个函数名以兼容不同页面的调用方式
    window.showNotification = showNotification;
    window.showToast = showNotification;

    // 添加 TwNotification 对象兼容新页面调用方式
    window.TwNotification = {
        show: showNotification
    };

})();
