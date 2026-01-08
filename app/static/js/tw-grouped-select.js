/**
 * Tailwind 树形分组下拉选择器
 *
 * 通用组件，提供分组下拉选择 + 输入框组合功能。
 * 支持树形折叠菜单、自动展开选中项所在分组。
 *
 * 使用方式：
 * 配合 tw_grouped_select.html Jinja2 宏使用，自动初始化。
 *
 * @param {string} id - 组件唯一ID
 * @param {Array} groups - 分组数据，格式：[{key, label, items: [{value, label}]}]
 * @param {Object} labelsMap - 值到标签的映射，格式：{value: label}
 * @param {string} initialValue - 初始选中值
 * @param {string} initialContent - 初始输入内容
 * @returns {Object} Alpine.js 组件数据对象
 *
 * @example
 * // 在 Alpine.js 中使用
 * <div x-data="TwGroupedSelect('mySelect', groups, labelsMap, 'meeting', '')">
 *     ...
 * </div>
 */
function TwGroupedSelect(id, groups, labelsMap, initialValue = '', initialContent = '') {
    return {
        // 组件ID
        id: id,

        // 分组数据
        groups: groups || [],

        // 值到标签的映射
        labelsMap: labelsMap || {},

        // 当前选中的值
        selectedValue: initialValue || '',

        // 输入框内容
        inputContent: initialContent || '',

        // 下拉菜单是否显示
        showMenu: false,

        // 展开的分组key列表
        expandedGroups: [],

        /**
         * 初始化组件
         */
        init() {
            // 自动展开当前选中项所在的分组
            if (this.selectedValue) {
                this.expandGroupForValue(this.selectedValue);
            }
        },

        /**
         * 切换下拉菜单显示
         */
        toggleMenu() {
            this.showMenu = !this.showMenu;
            // 打开时自动展开当前选中项所在分组
            if (this.showMenu && this.selectedValue) {
                this.expandGroupForValue(this.selectedValue);
            }
        },

        /**
         * 切换分组展开/折叠
         * @param {string} groupKey - 分组key
         */
        toggleGroup(groupKey) {
            const index = this.expandedGroups.indexOf(groupKey);
            if (index > -1) {
                this.expandedGroups.splice(index, 1);
            } else {
                this.expandedGroups.push(groupKey);
            }
        },

        /**
         * 展开包含指定值的分组
         * @param {string} value - 选项值
         */
        expandGroupForValue(value) {
            for (const group of this.groups) {
                const found = group.items.some(item => item.value === value);
                if (found && !this.expandedGroups.includes(group.key)) {
                    this.expandedGroups.push(group.key);
                    break;
                }
            }
        },

        /**
         * 选择选项
         * @param {string} value - 选项值
         */
        selectItem(value) {
            this.selectedValue = value;
            this.showMenu = false;
            // 触发自定义事件，通知外部选择变化
            this.$dispatch('grouped-select-change', {
                id: this.id,
                value: value,
                label: this.getSelectedLabel()
            });
        },

        /**
         * 获取当前选中项的标签
         * @returns {string} 标签文本
         */
        getSelectedLabel() {
            return this.labelsMap[this.selectedValue] || this.selectedValue || '';
        },

        /**
         * 获取完整值（标签-内容）
         * @returns {string} 完整的组合值
         */
        getFullValue() {
            const label = this.getSelectedLabel();
            const content = this.inputContent.trim();
            if (!label) return content;
            if (!content) return label + '-';
            return label + '-' + content;
        },

        /**
         * 解析完整标题，分离类型和内容
         * @param {string} fullTitle - 完整标题
         * @param {string} workType - 工作类型值（用于确定前缀）
         */
        parseTitle(fullTitle, workType) {
            if (!fullTitle) {
                this.selectedValue = workType || '';
                this.inputContent = '';
                return;
            }

            this.selectedValue = workType || '';
            const label = this.labelsMap[workType] || '';
            const prefix = label + '-';

            if (label && fullTitle.startsWith(prefix)) {
                // 标题以正确的前缀开头
                this.inputContent = fullTitle.substring(prefix.length);
            } else if (fullTitle.includes('-')) {
                // 尝试从标题中推断（兼容处理）
                const parts = fullTitle.split('-');
                const firstPart = parts[0];
                // 检查第一部分是否是已知的标签
                const matchedValue = Object.keys(this.labelsMap).find(
                    key => this.labelsMap[key] === firstPart
                );
                if (matchedValue) {
                    this.selectedValue = matchedValue;
                    this.inputContent = parts.slice(1).join('-');
                } else {
                    // 无法识别，保持原样
                    this.inputContent = fullTitle;
                }
            } else {
                // 没有分隔符，整个作为内容
                this.inputContent = fullTitle;
            }
        },

        /**
         * 重置组件状态
         * @param {string} defaultValue - 默认选中值
         */
        reset(defaultValue = '') {
            this.selectedValue = defaultValue;
            this.inputContent = '';
            this.showMenu = false;
            this.expandedGroups = [];
            if (defaultValue) {
                this.expandGroupForValue(defaultValue);
            }
        },

        /**
         * 设置组件状态
         * @param {string} value - 选中值
         * @param {string} content - 输入内容
         */
        setValue(value, content) {
            this.selectedValue = value || '';
            this.inputContent = content || '';
            if (value) {
                this.expandGroupForValue(value);
            }
        }
    };
}

// 注册到全局
window.TwGroupedSelect = TwGroupedSelect;
