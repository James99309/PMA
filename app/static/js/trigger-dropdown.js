/**
 * TriggerDropdown - 触发式下拉搜索组件
 *
 * 用于在 contenteditable 编辑器中实现 @ 提及用户、# 引用项目等功能。
 * 支持本地数据过滤和 API 搜索两种模式。
 *
 * @example
 * const dropdown = new TriggerDropdown(editorElement, {
 *     triggers: [
 *         { char: '@', type: 'user', mode: 'local', data: users, ... },
 *         { char: '#', type: 'project', mode: 'api', searchUrl: '/api/search', ... }
 *     ],
 *     onSelect: (trigger, item) => console.log('Selected:', item)
 * });
 *
 * @version 1.0.0
 * @author Claude AI
 */

class TriggerDropdown {
    /**
     * 创建 TriggerDropdown 实例
     * @param {HTMLElement} editor - contenteditable 编辑器元素
     * @param {Object} options - 配置选项
     */
    constructor(editor, options = {}) {
        this.editor = editor;
        this.options = {
            triggers: [],
            onSelect: null,
            onShow: null,
            onHide: null,
            dropdownClass: 'trigger-dropdown',
            maxHeight: 256,
            maxWidth: 320,
            zIndex: 60,
            ...options
        };

        // 状态
        this.triggers = new Map();
        this.activeDropdown = null;
        this.activeTrigger = null;
        this.triggerInfo = null;
        this.highlightedIndex = 0;
        this.items = [];
        this.isLoading = false;
        this.debounceTimer = null;

        // 初始化触发器
        this.options.triggers.forEach(t => this.addTrigger(t));

        // 绑定事件
        this._bindEvents();

        // 创建下拉框容器
        this._createDropdownContainer();
    }

    /**
     * 添加触发器配置
     * @param {Object} config - 触发器配置
     */
    addTrigger(config) {
        const trigger = {
            char: config.char,
            type: config.type || config.char,
            mode: config.mode || 'local',
            data: config.data || [],
            searchUrl: config.searchUrl || '',
            debounce: config.debounce ?? 200,
            minChars: config.minChars ?? 0,
            filterFields: config.filterFields || ['name'],
            renderItem: config.renderItem || this._defaultRenderItem.bind(this),
            tagTemplate: config.tagTemplate || this._defaultTagTemplate.bind(this),
            emptyText: config.emptyText || '未找到匹配项',
            loadingText: config.loadingText || '搜索中...',
            ...config
        };
        this.triggers.set(config.char, trigger);
    }

    /**
     * 移除触发器
     * @param {string} char - 触发字符
     */
    removeTrigger(char) {
        this.triggers.delete(char);
    }

    /**
     * 绑定事件
     * @private
     */
    _bindEvents() {
        // 输入事件
        this.editor.addEventListener('input', this._handleInput.bind(this));

        // 键盘事件
        this.editor.addEventListener('keydown', this._handleKeydown.bind(this));

        // 点击外部关闭
        document.addEventListener('click', this._handleClickOutside.bind(this));

        // 失焦时同步
        this.editor.addEventListener('blur', () => {
            // 延迟关闭，允许点击下拉框
            setTimeout(() => {
                if (!this.dropdownContainer.contains(document.activeElement)) {
                    this.hideDropdown();
                }
            }, 150);
        });
    }

    /**
     * 创建下拉框容器
     * @private
     */
    _createDropdownContainer() {
        this.dropdownContainer = document.createElement('div');
        this.dropdownContainer.className = `${this.options.dropdownClass} fixed hidden`;
        this.dropdownContainer.style.cssText = `
            z-index: ${this.options.zIndex};
            max-height: ${this.options.maxHeight}px;
            max-width: ${this.options.maxWidth}px;
        `;
        document.body.appendChild(this.dropdownContainer);
    }

    /**
     * 处理输入事件
     * @private
     */
    _handleInput(event) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return;

        const range = selection.getRangeAt(0);
        const text = this._getTextBeforeCursor(range);

        // 检查所有触发器
        for (const [char, trigger] of this.triggers) {
            const regex = new RegExp(`\\${char}([^\\s${this._escapeRegex(char)}]*)$`);
            const match = text.match(regex);

            if (match) {
                this._showDropdownFor(trigger, range, match[1]);
                return;
            }
        }

        // 没有触发，隐藏下拉框
        this.hideDropdown();
    }

    /**
     * 处理键盘事件
     * @private
     */
    _handleKeydown(event) {
        if (!this.activeTrigger) return;

        switch (event.key) {
            case 'Escape':
                event.preventDefault();
                this.hideDropdown();
                break;
            case 'ArrowDown':
                event.preventDefault();
                this._highlightNext();
                break;
            case 'ArrowUp':
                event.preventDefault();
                this._highlightPrev();
                break;
            case 'Enter':
            case 'Tab':
                if (this.items.length > 0) {
                    event.preventDefault();
                    this._selectHighlighted();
                }
                break;
        }
    }

    /**
     * 处理点击外部
     * @private
     */
    _handleClickOutside(event) {
        if (!this.dropdownContainer.contains(event.target) &&
            !this.editor.contains(event.target)) {
            this.hideDropdown();
        }
    }

    /**
     * 显示指定触发器的下拉框
     * @private
     */
    _showDropdownFor(trigger, range, query) {
        this.activeTrigger = trigger;
        this.triggerInfo = {
            trigger,
            range: range.cloneRange(),
            query
        };
        this.highlightedIndex = 0;

        // 定位下拉框
        this._positionDropdown(range);

        // 根据模式获取数据
        if (trigger.mode === 'local') {
            this._filterLocalData(trigger, query);
        } else {
            this._searchApiData(trigger, query);
        }
    }

    /**
     * 本地数据过滤
     * @private
     */
    _filterLocalData(trigger, query) {
        const lowerQuery = query.toLowerCase();

        if (!query) {
            // 空查询返回前10条
            this.items = trigger.data.slice(0, 10);
        } else {
            // 过滤匹配项
            this.items = trigger.data.filter(item => {
                return trigger.filterFields.some(field => {
                    const value = item[field];
                    return value && String(value).toLowerCase().includes(lowerQuery);
                });
            }).slice(0, 10);
        }

        this._renderDropdown();
    }

    /**
     * API 搜索数据
     * @private
     */
    _searchApiData(trigger, query) {
        // 清除之前的定时器
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // 空查询立即执行，否则防抖
        const debounceTime = query ? trigger.debounce : 0;

        this.debounceTimer = setTimeout(async () => {
            this.isLoading = true;
            this._renderDropdown();

            try {
                const url = query
                    ? `${trigger.searchUrl}?q=${encodeURIComponent(query)}&limit=10`
                    : `${trigger.searchUrl}?limit=10`;

                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    this.items = data.data || [];
                } else {
                    this.items = [];
                }
            } catch (e) {
                console.error('搜索失败:', e);
                this.items = [];
            } finally {
                this.isLoading = false;
                this.highlightedIndex = 0;
                this._renderDropdown();
            }
        }, debounceTime);
    }

    /**
     * 定位下拉框
     * @private
     */
    _positionDropdown(range) {
        const rect = range.getBoundingClientRect();

        let top = rect.bottom + 4;
        let left = rect.left;

        // 检查是否超出底部
        if (top + this.options.maxHeight > window.innerHeight) {
            top = rect.top - this.options.maxHeight - 4;
        }

        // 检查是否超出右边
        if (left + this.options.maxWidth > window.innerWidth) {
            left = window.innerWidth - this.options.maxWidth - 8;
        }

        this.dropdownContainer.style.top = `${top}px`;
        this.dropdownContainer.style.left = `${left}px`;
    }

    /**
     * 渲染下拉框
     * @private
     */
    _renderDropdown() {
        if (!this.activeTrigger) return;

        let html = '';

        if (this.isLoading) {
            html = `<div class="trigger-dropdown-loading px-3 py-4 text-sm text-slate-500 dark:text-slate-400 text-center">
                ${this.activeTrigger.loadingText}
            </div>`;
        } else if (this.items.length === 0) {
            html = `<div class="trigger-dropdown-empty px-3 py-4 text-sm text-slate-500 dark:text-slate-400 text-center">
                ${this.activeTrigger.emptyText}
            </div>`;
        } else {
            html = '<div class="trigger-dropdown-list overflow-y-auto py-1" style="max-height: ' + (this.options.maxHeight - 8) + 'px;">';
            this.items.forEach((item, index) => {
                const isHighlighted = index === this.highlightedIndex;
                const highlightClass = isHighlighted
                    ? 'bg-primary/10 text-primary'
                    : 'text-slate-900 dark:text-white hover:bg-slate-100 dark:hover:bg-slate-700';

                html += `<div class="trigger-dropdown-item px-3 py-2 cursor-pointer text-sm transition-colors ${highlightClass}"
                              data-index="${index}">
                    ${this.activeTrigger.renderItem(item, isHighlighted)}
                </div>`;
            });
            html += '</div>';
        }

        this.dropdownContainer.innerHTML = html;
        this.dropdownContainer.classList.remove('hidden');

        // 绑定点击事件
        this.dropdownContainer.querySelectorAll('.trigger-dropdown-item').forEach(el => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(el.dataset.index);
                this._selectItem(this.items[index]);
            });
            el.addEventListener('mouseenter', () => {
                this.highlightedIndex = parseInt(el.dataset.index);
                this._updateHighlight();
            });
        });

        // 触发 onShow 回调
        if (this.options.onShow) {
            this.options.onShow(this.activeTrigger);
        }
    }

    /**
     * 更新高亮状态
     * @private
     */
    _updateHighlight() {
        this.dropdownContainer.querySelectorAll('.trigger-dropdown-item').forEach((el, index) => {
            if (index === this.highlightedIndex) {
                el.classList.remove('text-slate-900', 'dark:text-white', 'hover:bg-slate-100', 'dark:hover:bg-slate-700');
                el.classList.add('bg-primary/10', 'text-primary');
            } else {
                el.classList.remove('bg-primary/10', 'text-primary');
                el.classList.add('text-slate-900', 'dark:text-white', 'hover:bg-slate-100', 'dark:hover:bg-slate-700');
            }
        });
    }

    /**
     * 高亮下一项
     * @private
     */
    _highlightNext() {
        if (this.highlightedIndex < this.items.length - 1) {
            this.highlightedIndex++;
            this._updateHighlight();
            this._scrollToHighlighted();
        }
    }

    /**
     * 高亮上一项
     * @private
     */
    _highlightPrev() {
        if (this.highlightedIndex > 0) {
            this.highlightedIndex--;
            this._updateHighlight();
            this._scrollToHighlighted();
        }
    }

    /**
     * 滚动到高亮项
     * @private
     */
    _scrollToHighlighted() {
        const list = this.dropdownContainer.querySelector('.trigger-dropdown-list');
        const item = this.dropdownContainer.querySelectorAll('.trigger-dropdown-item')[this.highlightedIndex];
        if (list && item) {
            const itemTop = item.offsetTop;
            const itemBottom = itemTop + item.offsetHeight;
            const listScrollTop = list.scrollTop;
            const listHeight = list.clientHeight;

            if (itemTop < listScrollTop) {
                list.scrollTop = itemTop;
            } else if (itemBottom > listScrollTop + listHeight) {
                list.scrollTop = itemBottom - listHeight;
            }
        }
    }

    /**
     * 选择高亮项
     * @private
     */
    _selectHighlighted() {
        if (this.items[this.highlightedIndex]) {
            this._selectItem(this.items[this.highlightedIndex]);
        }
    }

    /**
     * 选择项目
     * @private
     */
    _selectItem(item) {
        if (!this.triggerInfo || !item) return;

        const trigger = this.triggerInfo.trigger;
        const tagConfig = trigger.tagTemplate(item);

        // 插入标签
        this._insertTag(tagConfig);

        // 触发回调
        if (this.options.onSelect) {
            this.options.onSelect(trigger, item, tagConfig);
        }

        this.hideDropdown();
    }

    /**
     * 插入标签到编辑器
     * @private
     */
    _insertTag(tagConfig) {
        const editor = this.editor;
        editor.focus();

        if (!this.triggerInfo) return;

        const triggerChar = this.triggerInfo.trigger.char;
        const searchQuery = this.triggerInfo.query;
        const triggerText = triggerChar + searchQuery;

        // 遍历编辑器查找并替换触发文本
        const walker = document.createTreeWalker(
            editor,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        let found = false;

        while ((node = walker.nextNode()) && !found) {
            const text = node.textContent;
            const triggerIndex = text.lastIndexOf(triggerText);

            if (triggerIndex !== -1) {
                found = true;

                // 分割文本节点
                const beforeText = text.substring(0, triggerIndex);
                const afterText = text.substring(triggerIndex + triggerText.length);

                node.textContent = beforeText;

                // 创建标签元素
                const tag = document.createElement('span');
                tag.className = `trigger-tag ${tagConfig.class || ''}`;
                tag.contentEditable = 'false';
                tag.textContent = tagConfig.text;

                // 存储数据
                if (tagConfig.data) {
                    Object.keys(tagConfig.data).forEach(key => {
                        tag.dataset[key] = tagConfig.data[key];
                    });
                }

                // 创建后续文本和空格
                const space = document.createTextNode('\u00A0');
                const afterNode = document.createTextNode(afterText);

                // 插入节点
                if (node.nextSibling) {
                    node.parentNode.insertBefore(tag, node.nextSibling);
                    node.parentNode.insertBefore(space, tag.nextSibling);
                    if (afterText) {
                        node.parentNode.insertBefore(afterNode, space.nextSibling);
                    }
                } else {
                    node.parentNode.appendChild(tag);
                    node.parentNode.appendChild(space);
                    if (afterText) {
                        node.parentNode.appendChild(afterNode);
                    }
                }

                // 移动光标到空格后
                const selection = window.getSelection();
                const newRange = document.createRange();
                newRange.setStartAfter(space);
                newRange.collapse(true);
                selection.removeAllRanges();
                selection.addRange(newRange);
            }
        }
    }

    /**
     * 隐藏下拉框
     */
    hideDropdown() {
        this.dropdownContainer.classList.add('hidden');
        this.dropdownContainer.innerHTML = '';
        this.activeTrigger = null;
        this.triggerInfo = null;
        this.items = [];
        this.highlightedIndex = 0;

        if (this.options.onHide) {
            this.options.onHide();
        }
    }

    /**
     * 获取光标前的文本
     * @private
     */
    _getTextBeforeCursor(range) {
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(this.editor);
        preCaretRange.setEnd(range.startContainer, range.startOffset);

        const fragment = preCaretRange.cloneContents();
        const div = document.createElement('div');
        div.appendChild(fragment);
        return div.textContent || '';
    }

    /**
     * 转义正则特殊字符
     * @private
     */
    _escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * 默认列表项渲染
     * @private
     */
    _defaultRenderItem(item, isHighlighted) {
        return `<span>${item.name || item.text || JSON.stringify(item)}</span>`;
    }

    /**
     * 默认标签模板
     * @private
     */
    _defaultTagTemplate(item) {
        return {
            text: item.name || item.text || '',
            class: 'trigger-tag-default',
            data: { id: item.id }
        };
    }

    /**
     * 获取编辑器内容（存储格式）
     * @param {Object} formatConfig - 格式配置 { user: '@[{name}|user:{id}]', project: '#[{name}|project:{id}]' }
     * @returns {string}
     */
    getValue(formatConfig = {}) {
        const div = document.createElement('div');
        div.innerHTML = this.editor.innerHTML;

        // 替换标签为存储格式
        div.querySelectorAll('.trigger-tag').forEach(tag => {
            const type = tag.dataset.type;
            const id = tag.dataset.id;
            const name = tag.dataset.name;

            let format = formatConfig[type];
            if (!format) {
                // 默认格式
                const char = this._getCharByType(type);
                format = `${char}[{name}|${type}:{id}]`;
            }

            const marker = format
                .replace('{name}', name)
                .replace('{id}', id);
            tag.replaceWith(marker);
        });

        // 处理换行和 HTML
        let text = div.innerHTML
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<div>/gi, '\n')
            .replace(/<\/div>/gi, '')
            .replace(/<p>/gi, '\n')
            .replace(/<\/p>/gi, '')
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/<[^>]+>/g, '');

        return text.trim();
    }

    /**
     * 根据类型获取触发字符
     * @private
     */
    _getCharByType(type) {
        for (const [char, trigger] of this.triggers) {
            if (trigger.type === type) return char;
        }
        return '';
    }

    /**
     * 设置编辑器内容（从存储格式解析）
     * @param {string} text - 存储格式的文本
     * @param {Object} parseConfig - 解析配置
     */
    setValue(text, parseConfig = {}) {
        if (!text) {
            this.editor.innerHTML = '';
            return;
        }

        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // 解析各种标签格式
        for (const [char, trigger] of this.triggers) {
            const regex = new RegExp(
                `\\${char}\\[([^\\]|]+)\\|${trigger.type}:(\\d+)\\]`,
                'g'
            );
            html = html.replace(regex, (match, name, id) => {
                const tagConfig = trigger.tagTemplate({ id, name, [trigger.filterFields[0]]: name });
                return `<span class="trigger-tag ${tagConfig.class || ''}" contenteditable="false" data-type="${trigger.type}" data-id="${id}" data-name="${name}">${tagConfig.text}</span>`;
            });
        }

        // 处理换行
        html = html.replace(/\n/g, '<br>');

        this.editor.innerHTML = html;
    }

    /**
     * 获取所有引用的 ID
     * @returns {Object} - { user: [1, 2], project: [3, 4] }
     */
    getMentions() {
        const mentions = {};

        this.editor.querySelectorAll('.trigger-tag').forEach(tag => {
            const type = tag.dataset.type;
            const id = parseInt(tag.dataset.id);

            if (!mentions[type]) {
                mentions[type] = [];
            }
            if (!mentions[type].includes(id)) {
                mentions[type].push(id);
            }
        });

        return mentions;
    }

    /**
     * 销毁实例
     */
    destroy() {
        // 移除事件监听
        this.editor.removeEventListener('input', this._handleInput);
        this.editor.removeEventListener('keydown', this._handleKeydown);
        document.removeEventListener('click', this._handleClickOutside);

        // 移除下拉框
        if (this.dropdownContainer && this.dropdownContainer.parentNode) {
            this.dropdownContainer.parentNode.removeChild(this.dropdownContainer);
        }

        // 清除定时器
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
    }
}

// 导出到全局
window.TriggerDropdown = TriggerDropdown;
