/*!
 * 数据库备份管理前端脚本
 * 用于 Supabase 自动备份系统
 */

(function() {
    'use strict';

    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的大小字符串
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 格式化时间差
     * @param {Date} date - 日期对象
     * @returns {string} 格式化后的时间差字符串
     */
    function formatTimeDiff(date) {
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return '今天';
        if (days === 1) return '昨天';
        if (days < 7) return days + '天前';
        if (days < 30) return Math.floor(days / 7) + '周前';
        if (days < 365) return Math.floor(days / 30) + '个月前';
        return Math.floor(days / 365) + '年前';
    }

    /**
     * 显示Toast提示
     * @param {string} type - 类型：success, error, warning, info
     * @param {string} message - 消息内容
     */
    function showToast(type, message) {
        // 如果toastr可用，使用toastr
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
            return;
        }

        // 否则使用简单的alert
        const typeMap = {
            success: '✅ 成功',
            error: '❌ 错误',
            warning: '⚠️ 警告',
            info: 'ℹ️ 信息'
        };

        alert((typeMap[type] || '') + '\n' + message);
    }

    /**
     * 确认操作对话框
     * @param {string} message - 确认消息
     * @param {Function} onConfirm - 确认回调
     * @param {Function} onCancel - 取消回调（可选）
     */
    function confirmAction(message, onConfirm, onCancel) {
        if (confirm(message)) {
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        } else {
            if (typeof onCancel === 'function') {
                onCancel();
            }
        }
    }

    /**
     * AJAX请求包装器
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} Promise对象
     */
    function request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        };

        const mergedOptions = { ...defaultOptions, ...options };

        return fetch(url, mergedOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('Request failed:', error);
                throw error;
            });
    }

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} 节流后的函数
     */
    function throttle(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} 防抖后的函数
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 将工具函数暴露到全局
    window.BackupManager = {
        formatFileSize,
        formatTimeDiff,
        showToast,
        confirmAction,
        request,
        throttle,
        debounce
    };

    // 日志
    console.log('✅ Backup Manager utilities loaded');
})();
