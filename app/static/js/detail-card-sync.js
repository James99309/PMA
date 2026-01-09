/**
 * 详情页卡片高度同步工具
 *
 * 用于将多个卡片的高度同步到参考列的高度，实现底部对齐效果。
 * 适用于 Tailwind 详情页的多列布局。
 *
 * 使用示例:
 *   DetailCardSync.init('rightSidebarColumn', ['basicInfoColumn', 'changeHistoryCard']);
 */

(function() {
    'use strict';

    const DetailCardSync = {
        referenceId: null,
        targetIds: [],
        initialized: false,

        /**
         * 初始化高度同步
         * @param {string} referenceId - 参考元素的ID（高度基准）
         * @param {string[]} targetIds - 需要同步高度的目标元素ID数组
         * @param {object} options - 可选配置
         * @param {number} options.delay - 初始化延迟时间（毫秒），默认100
         * @param {boolean} options.syncOnResize - 是否在窗口大小变化时同步，默认true
         * @param {string} options.targetSelector - 目标元素内部的选择器，如 '> div' 选择直接子元素
         */
        init: function(referenceId, targetIds, options = {}) {
            this.referenceId = referenceId;
            this.targetIds = Array.isArray(targetIds) ? targetIds : [targetIds];
            this.options = Object.assign({
                delay: 100,
                syncOnResize: true,
                targetSelector: null
            }, options);

            if (this.initialized) {
                this.sync();
                return;
            }

            const self = this;

            // 页面加载完成后同步
            if (document.readyState === 'complete') {
                setTimeout(function() { self.sync(); }, this.options.delay);
            } else {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() { self.sync(); }, self.options.delay);
                });
            }

            // 窗口大小变化时同步
            if (this.options.syncOnResize) {
                let resizeTimeout;
                window.addEventListener('resize', function() {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(function() { self.sync(); }, 50);
                });
            }

            this.initialized = true;
        },

        /**
         * 执行高度同步
         */
        sync: function() {
            const reference = document.getElementById(this.referenceId);
            if (!reference) {
                console.warn('[DetailCardSync] 参考元素未找到:', this.referenceId);
                return;
            }

            const referenceHeight = reference.offsetHeight;
            if (referenceHeight === 0) {
                console.warn('[DetailCardSync] 参考元素高度为0，跳过同步');
                return;
            }

            const self = this;
            this.targetIds.forEach(function(targetId) {
                let target = document.getElementById(targetId);

                // 如果指定了内部选择器，获取内部元素
                if (target && self.options.targetSelector) {
                    target = target.querySelector(self.options.targetSelector);
                }

                if (target) {
                    target.style.height = referenceHeight + 'px';
                }
            });
        },

        /**
         * 重置高度（移除固定高度）
         */
        reset: function() {
            const self = this;
            this.targetIds.forEach(function(targetId) {
                let target = document.getElementById(targetId);

                if (target && self.options.targetSelector) {
                    target = target.querySelector(self.options.targetSelector);
                }

                if (target) {
                    target.style.height = '';
                }
            });
        }
    };

    // 导出到全局
    window.DetailCardSync = DetailCardSync;
})();
