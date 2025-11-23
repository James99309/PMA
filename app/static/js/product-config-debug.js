/**
 * 产品配置嵌套功能调试工具
 * 用于诊断嵌套配置数据收集问题
 */

(function() {
    'use strict';

    // 调试日志颜色
    const colors = {
        info: '#2196F3',
        success: '#4CAF50',
        warning: '#FF9800',
        error: '#F44336',
        data: '#9C27B0'
    };

    function log(message, type = 'info', data = null) {
        const color = colors[type] || colors.info;
        console.log(`%c[嵌套配置调试] ${message}`, `color: ${color}; font-weight: bold;`);
        if (data) {
            console.log('%c数据:', `color: ${colors.data}`, data);
        }
    }

    // 等待页面加载完成
    window.addEventListener('DOMContentLoaded', function() {
        log('调试工具已加载', 'success');

        // 添加全局调试函数
        window.debugNestedConfig = {
            // 1. 检查容器结构
            checkContainers: function() {
                log('=== 检查容器结构 ===', 'info');

                const containers = document.querySelectorAll('[id^="nested-config-"]');
                log(`找到 ${containers.length} 个嵌套配置容器`, 'info');

                containers.forEach((container, index) => {
                    const level = container.id.match(/-(\d+)$/)?.[1] || '未知';
                    const visible = container.style.display !== 'none';
                    const loaded = container.dataset.loaded === 'true';

                    console.log(`\n容器 ${index + 1}:`, {
                        id: container.id,
                        level: level,
                        visible: visible,
                        loaded: loaded,
                        childrenCount: container.children.length,
                        innerHTML: container.innerHTML.substring(0, 100) + '...'
                    });

                    // 检查容器内的配置项
                    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
                    const radios = container.querySelectorAll('input[type="radio"]');

                    if (checkboxes.length > 0) {
                        log(`  └─ 必选配置: ${checkboxes.length} 个`, 'info');
                        checkboxes.forEach(cb => {
                            console.log(`    - ${cb.dataset.productName || '未知'} (checked: ${cb.checked})`);
                        });
                    }

                    if (radios.length > 0) {
                        const groups = new Set(Array.from(radios).map(r => r.name));
                        log(`  └─ 必选互斥组: ${groups.size} 组, ${radios.length} 个选项`, 'info');
                        groups.forEach(groupName => {
                            const groupRadios = container.querySelectorAll(`input[type="radio"][name="${groupName}"]`);
                            const checked = Array.from(groupRadios).find(r => r.checked);
                            console.log(`    组 "${groupName}": 选中 "${checked ? checked.dataset.productName : '无'}"`);
                        });
                    }
                });
            },

            // 2. 模拟数据收集过程
            simulateCollection: function() {
                log('=== 模拟数据收集 ===', 'success');

                const collected = [];

                // Level 0: 必选配置
                const requiredContainer = document.getElementById('requiredConfigList');
                if (requiredContainer) {
                    log('收集 Level 0 必选配置', 'info');
                    const items = requiredContainer.querySelectorAll('.config-item-with-checkbox');
                    items.forEach(item => {
                        const checkbox = item.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            console.log(`  - ${checkbox.dataset.productName}: checked=${checkbox.checked}`);
                            if (checkbox.checked) {
                                collected.push({
                                    level: 0,
                                    type: 'required',
                                    name: checkbox.dataset.productName,
                                    id: checkbox.value,
                                    checked: true
                                });
                            }
                        }
                    });
                }

                // Level 0: 必选互斥组
                const mutualContainer = document.getElementById('requiredMutualConfigList');
                if (mutualContainer) {
                    log('收集 Level 0 必选互斥组', 'info');
                    const groups = new Set();
                    mutualContainer.querySelectorAll('input[type="radio"]').forEach(r => groups.add(r.name));

                    groups.forEach(groupName => {
                        const radios = mutualContainer.querySelectorAll(`input[type="radio"][name="${groupName}"]`);
                        radios.forEach(radio => {
                            console.log(`  - ${radio.dataset.productName}: checked=${radio.checked}`);
                            if (radio.checked) {
                                collected.push({
                                    level: 0,
                                    type: 'mutual',
                                    group: groupName,
                                    name: radio.dataset.productName,
                                    id: radio.value,
                                    checked: true
                                });

                                // 检查是否有嵌套容器
                                const nestedContainerId = `nested-config-${radio.value}-0`;
                                const nestedContainer = document.getElementById(nestedContainerId);
                                if (nestedContainer) {
                                    log(`  └─ 发现嵌套容器: ${nestedContainerId}`, 'warning');
                                    this.collectNested(nestedContainer, radio.value, 1, collected);
                                }
                            }
                        });
                    });
                }

                log('收集完成，共 ' + collected.length + ' 项', 'success', collected);
                return collected;
            },

            // 3. 递归收集嵌套配置
            collectNested: function(container, parentId, level, collected) {
                log(`收集 Level ${level} 嵌套配置 (父ID: ${parentId})`, 'info');

                // 收集必选配置
                const requiredContainerId = `${container.id}_required`;
                const requiredContainer = document.getElementById(requiredContainerId);
                if (requiredContainer) {
                    const items = requiredContainer.querySelectorAll('.config-item-with-checkbox');
                    log(`  └─ 必选配置容器 ${requiredContainerId}: ${items.length} 项`, 'info');
                    items.forEach(item => {
                        const checkbox = item.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            console.log(`    - ${checkbox.dataset.productName}: checked=${checkbox.checked}`);
                            if (checkbox.checked) {
                                collected.push({
                                    level: level,
                                    type: 'required',
                                    parentId: parentId,
                                    name: checkbox.dataset.productName,
                                    id: checkbox.value,
                                    checked: true
                                });
                            }
                        }
                    });
                }

                // 收集必选互斥组
                const mutualContainerId = `${container.id}_mutual`;
                const mutualContainer = document.getElementById(mutualContainerId);
                if (mutualContainer) {
                    const groups = new Set();
                    mutualContainer.querySelectorAll('input[type="radio"]').forEach(r => groups.add(r.name));
                    log(`  └─ 必选互斥组容器 ${mutualContainerId}: ${groups.size} 组`, 'info');

                    groups.forEach(groupName => {
                        const radios = mutualContainer.querySelectorAll(`input[type="radio"][name="${groupName}"]`);
                        radios.forEach(radio => {
                            console.log(`    - ${radio.dataset.productName}: checked=${radio.checked}`);
                            if (radio.checked) {
                                collected.push({
                                    level: level,
                                    type: 'mutual',
                                    group: groupName,
                                    parentId: parentId,
                                    name: radio.dataset.productName,
                                    id: radio.value,
                                    checked: true
                                });

                                // 递归收集更深层级
                                const deeperContainerId = `nested-config-${radio.value}-${level}`;
                                const deeperContainer = document.getElementById(deeperContainerId);
                                if (deeperContainer && level < 2) {
                                    log(`    └─ 发现更深层级容器: ${deeperContainerId}`, 'warning');
                                    this.collectNested(deeperContainer, radio.value, level + 1, collected);
                                }
                            }
                        });
                    });
                }
            },

            // 4. 检查实际的 collectNestedConfigs 方法
            inspectCollectMethod: function() {
                log('=== 检查 collectNestedConfigs 方法 ===', 'info');

                // 查找 ProductConfigModal 实例
                const modalElement = document.getElementById('productConfigModal');
                if (!modalElement) {
                    log('未找到产品配置模态框', 'error');
                    return;
                }

                log('请在确认配置时查看控制台输出', 'warning');
                log('建议在 product-config-modal.js 的 collectNestedConfigs 方法中添加断点', 'warning');
            },

            // 5. 对比预期和实际收集结果
            compareResults: function() {
                log('=== 对比预期和实际结果 ===', 'info');

                const simulated = this.simulateCollection();
                log('模拟收集结果:', 'success', simulated);

                log('请点击"确认配置"按钮，然后检查控制台中的实际收集日志', 'warning');
                log('查找以 "📦 收集嵌套配置" 开头的日志', 'warning');
            },

            // 6. 完整诊断
            diagnose: function() {
                log('\n\n', 'info');
                log('╔══════════════════════════════════════╗', 'success');
                log('║   嵌套配置完整诊断                  ║', 'success');
                log('╚══════════════════════════════════════╝', 'success');
                log('\n', 'info');

                this.checkContainers();
                log('\n', 'info');
                this.simulateCollection();
                log('\n', 'info');

                log('诊断完成！', 'success');
                log('如果发现问题，请截图控制台输出并报告', 'warning');
            }
        };

        log('调试函数已注册到 window.debugNestedConfig', 'success');
        log('可用命令:', 'info');
        console.log('  - debugNestedConfig.checkContainers()  : 检查容器结构');
        console.log('  - debugNestedConfig.simulateCollection(): 模拟数据收集');
        console.log('  - debugNestedConfig.compareResults()   : 对比预期和实际');
        console.log('  - debugNestedConfig.diagnose()         : 完整诊断');
    });
})();
