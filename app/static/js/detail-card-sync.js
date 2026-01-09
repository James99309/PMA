/**
 * 详情页卡片高度同步工具
 *
 * 用于将多个卡片的高度同步到参考列的高度，实现底部对齐效果。
 * 适用于 Tailwind 详情页的多列布局。
 *
 * 使用示例:
 *   DetailCardSync.init('rightSidebarColumn', ['basicInfoColumn', 'changeHistoryCard']);
 *   // 或多次调用不同配置
 *   DetailCardSync.init('rightSidebarColumn', ['changeHistoryCard']);
 *   DetailCardSync.init('rightSidebarColumn', ['basicInfoColumn'], { targetSelector: '> div' });
 */

(function() {
    'use strict';

    // 存储所有同步配置
    const syncConfigs = [];
    let resizeListenerAdded = false;

    const DetailCardSync = {
        /**
         * 初始化高度同步
         * @param {string} referenceId - 参考元素的ID（高度基准）
         * @param {string[]} targetIds - 需要同步高度的目标元素ID数组
         * @param {object} options - 可选配置
         * @param {number} options.delay - 初始化延迟时间（毫秒），默认100
         * @param {boolean} options.syncOnResize - 是否在窗口大小变化时同步，默认true
         * @param {string} options.targetSelector - 目标元素内部的选择器，如 '> div' 选择直接子元素
         */
        init: function(referenceId, targetIds, options) {
            options = options || {};
            const config = {
                referenceId: referenceId,
                targetIds: Array.isArray(targetIds) ? targetIds : [targetIds],
                options: {
                    delay: options.delay !== undefined ? options.delay : 100,
                    syncOnResize: options.syncOnResize !== undefined ? options.syncOnResize : true,
                    targetSelector: options.targetSelector || null
                }
            };

            syncConfigs.push(config);

            // 页面加载完成后同步
            if (document.readyState === 'complete') {
                setTimeout(function() {
                    DetailCardSync.syncConfig(config);
                }, config.options.delay);
            } else {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() {
                        DetailCardSync.syncConfig(config);
                    }, config.options.delay);
                });
            }

            // 添加窗口大小变化监听（只添加一次）
            if (!resizeListenerAdded && config.options.syncOnResize) {
                let resizeTimeout;
                window.addEventListener('resize', function() {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(function() {
                        DetailCardSync.syncAll();
                    }, 50);
                });
                resizeListenerAdded = true;
            }
        },

        /**
         * 执行单个配置的高度同步
         */
        syncConfig: function(config) {
            const reference = document.getElementById(config.referenceId);
            if (!reference) {
                console.warn('[DetailCardSync] 参考元素未找到:', config.referenceId);
                return;
            }

            const referenceHeight = reference.offsetHeight;
            if (referenceHeight === 0) {
                console.warn('[DetailCardSync] 参考元素高度为0，跳过同步');
                return;
            }

            config.targetIds.forEach(function(targetId) {
                let target = document.getElementById(targetId);

                // 如果指定了内部选择器，获取内部元素
                if (target && config.options.targetSelector) {
                    // 使用 :scope 前缀支持 '> div' 这样的子选择器
                    var selector = config.options.targetSelector;
                    if (selector.startsWith('>')) {
                        selector = ':scope ' + selector;
                    }
                    target = target.querySelector(selector);
                }

                if (target) {
                    target.style.height = referenceHeight + 'px';
                }
            });
        },

        /**
         * 同步所有配置
         */
        syncAll: function() {
            var self = this;
            syncConfigs.forEach(function(config) {
                self.syncConfig(config);
            });
        },

        /**
         * 手动触发同步（可用于AJAX加载后）
         */
        sync: function() {
            this.syncAll();
        },

        /**
         * 重置所有高度（移除固定高度）
         */
        reset: function() {
            syncConfigs.forEach(function(config) {
                config.targetIds.forEach(function(targetId) {
                    let target = document.getElementById(targetId);

                    if (target && config.options.targetSelector) {
                        var selector = config.options.targetSelector;
                        if (selector.startsWith('>')) {
                            selector = ':scope ' + selector;
                        }
                        target = target.querySelector(selector);
                    }

                    if (target) {
                        target.style.height = '';
                    }
                });
            });
        },

        /**
         * 清除所有配置
         */
        clear: function() {
            syncConfigs.length = 0;
        }
    };

    // 导出到全局
    window.DetailCardSync = DetailCardSync;
})();
