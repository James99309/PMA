/**
 * 审批中心管理器
 *
 * 扩展 TwListManager，增加标签页切换功能。
 *
 * 使用示例:
 *   const manager = new ApprovalCenterManager({
 *       tableId: 'approvalTable',
 *       formId: 'approvalFilterForm',
 *       ajaxEndpoint: '/approval/tw_center_ajax',
 *       pageSize: 20,
 *       initialTab: 'created'
 *   });
 *   manager.init();
 */
class ApprovalCenterManager {
    /**
     * 构造函数
     * @param {Object} config - 配置对象
     * @param {string} config.tableId - 表格ID
     * @param {string} config.formId - 筛选表单ID
     * @param {string} config.ajaxEndpoint - AJAX加载端点
     * @param {number} [config.pageSize=20] - 每页数量
     * @param {number} [config.initialCount=0] - 初始数据数量
     * @param {string} [config.initialTab='created'] - 初始标签页
     * @param {string} [config.sortField='started_at'] - 默认排序字段
     * @param {string} [config.sortOrder='desc'] - 默认排序方向
     * @param {boolean} [config.hasMore=true] - 是否有更多数据
     * @param {Object} [config.messages] - 自定义消息文本
     */
    constructor(config) {
        this.tableId = config.tableId;
        this.formId = config.formId;
        this.ajaxEndpoint = config.ajaxEndpoint;
        this.pageSize = config.pageSize || 20;
        this.initialCount = config.initialCount || 0;
        this.currentTab = config.initialTab || 'created';
        this.sortField = config.sortField || 'started_at';
        this.sortOrder = config.sortOrder || 'desc';
        this.hasMore = config.hasMore !== false;

        // 消息文本（支持国际化）
        this.messages = Object.assign({
            loadingMore: '加载中...',
            noMoreData: '没有更多数据',
            loadError: '加载数据失败',
            noData: '暂无数据'
        }, config.messages || {});

        // 状态
        this.isLoading = false;
        this.currentOffset = this.initialCount;

        // DOM 元素缓存
        this.elements = {};

        // TwListManager 实例
        this.listManager = null;
    }

    /**
     * 初始化
     */
    init() {
        this._cacheElements();
        this._setupListManager();
        this._setupPopState();
    }

    /**
     * 缓存 DOM 元素
     * @private
     */
    _cacheElements() {
        this.elements = {
            tableBody: document.getElementById(`${this.tableId}Body`),
            tableCount: document.getElementById(`${this.tableId}Count`),
            loadingMore: document.getElementById(`${this.tableId}LoadingMore`),
            noMoreData: document.getElementById(`${this.tableId}NoMore`),
            scrollSentinel: document.getElementById(`${this.tableId}Sentinel`),
            filterForm: document.getElementById(this.formId)
        };
    }

    /**
     * 设置 TwListManager
     * @private
     */
    _setupListManager() {
        // 检查 TwListManager 是否可用
        if (typeof TwListManager !== 'undefined') {
            this.listManager = new TwListManager({
                tableId: this.tableId,
                formId: this.formId,
                ajaxEndpoint: this.ajaxEndpoint,
                pageSize: this.pageSize,
                initialCount: this.initialCount,
                sortField: this.sortField,
                sortOrder: this.sortOrder,
                infiniteScroll: this.hasMore,
                messages: this.messages
            });
            this.listManager.init();

            // 重写 loadMore 方法以添加 tab 参数
            const originalLoadMore = this.listManager.loadMore.bind(this.listManager);
            const self = this;
            this.listManager.loadMore = function() {
                if (this.isLoading || !this.hasMore) return;

                this.isLoading = true;
                this._showLoading(true);

                const url = new URL(self.ajaxEndpoint, window.location.origin);

                // 复制当前页面的筛选参数
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.forEach((value, key) => {
                    if (key !== 'old' && key !== 'ajax') {
                        url.searchParams.set(key, value);
                    }
                });

                // 添加必要参数
                url.searchParams.set('tab', self.currentTab);
                url.searchParams.set('offset', this.currentOffset);
                url.searchParams.set('limit', this.pageSize);
                url.searchParams.set('ajax', '1');

                fetch(url.toString(), {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    this._handleLoadSuccess(data);
                    // 更新统计
                    if (data.statistics) {
                        self._updateStatistics(data.statistics);
                    }
                })
                .catch(error => {
                    this._handleLoadError(error);
                });
            };
        }
    }

    /**
     * 设置浏览器前进后退监听
     * @private
     */
    _setupPopState() {
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.tab) {
                this.currentTab = event.state.tab;
                this._updateTabUI(event.state.tab);
                this.loadData();
            }
        });
    }

    /**
     * 切换标签页
     * @param {string} tabKey - 标签页键
     */
    switchTab(tabKey) {
        if (this.currentTab === tabKey) return;

        this.currentTab = tabKey;

        // 更新 URL
        const url = new URL(window.location.href);
        url.searchParams.set('tab', tabKey);
        window.history.pushState({ tab: tabKey }, '', url);

        // 重置并加载数据
        this.loadData();
    }

    /**
     * 加载数据
     */
    loadData() {
        if (this.isLoading) return;

        this.isLoading = true;
        this._showTableLoading(true);

        const url = new URL(this.ajaxEndpoint, window.location.origin);

        // 复制表单参数
        if (this.elements.filterForm) {
            const formData = new FormData(this.elements.filterForm);
            formData.forEach((value, key) => {
                url.searchParams.set(key, value);
            });
        }

        // 添加必要参数
        url.searchParams.set('tab', this.currentTab);
        url.searchParams.set('offset', '0');
        url.searchParams.set('limit', this.pageSize);
        url.searchParams.set('sort', this.sortField);
        url.searchParams.set('order', this.sortOrder);
        url.searchParams.set('ajax', '1');

        fetch(url.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            this._handleLoadDataSuccess(data);
        })
        .catch(error => {
            this._handleLoadDataError(error);
        });
    }

    /**
     * 处理数据加载成功
     * @param {Object} data - 响应数据
     * @private
     */
    _handleLoadDataSuccess(data) {
        if (data.success !== false) {
            // 更新表格内容
            if (this.elements.tableBody) {
                this.elements.tableBody.innerHTML = data.html || this._getEmptyRowHtml();
            }

            // 更新计数
            if (this.elements.tableCount) {
                this.elements.tableCount.textContent = data.total_count || 0;
            }

            // 更新统计卡片
            if (data.statistics) {
                this._updateStatistics(data.statistics);
            }

            // 更新标签页计数
            if (data.tab_counts && typeof window.updateTabCounts === 'function') {
                window.updateTabCounts(data.tab_counts);
            }

            // 更新分页状态
            if (this.listManager) {
                this.listManager.currentOffset = data.loaded_count || 0;
                this.listManager.hasMore = data.has_more || false;

                // 更新无限滚动状态
                if (!data.has_more && this.elements.noMoreData) {
                    this.elements.noMoreData.classList.remove('hidden');
                } else if (this.elements.noMoreData) {
                    this.elements.noMoreData.classList.add('hidden');
                }
            }
        }

        this._showTableLoading(false);
        this.isLoading = false;
    }

    /**
     * 处理数据加载错误
     * @param {Error} error - 错误对象
     * @private
     */
    _handleLoadDataError(error) {
        console.error(this.messages.loadError, error);
        this._showTableLoading(false);
        this.isLoading = false;
    }

    /**
     * 按字段排序
     * @param {string} field - 排序字段
     */
    sortBy(field) {
        // 切换排序方向
        if (this.sortField === field) {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortField = field;
            this.sortOrder = 'desc';
        }

        // 更新 URL 并重新加载
        const url = new URL(window.location.href);
        url.searchParams.set('sort', this.sortField);
        url.searchParams.set('order', this.sortOrder);
        window.history.pushState({ tab: this.currentTab }, '', url);

        this.loadData();
    }

    /**
     * 更新统计卡片
     * @param {Object} stats - 统计数据
     * @private
     */
    _updateStatistics(stats) {
        Object.keys(stats).forEach(key => {
            const element = document.getElementById(`stat-${key}`);
            if (element) {
                element.textContent = stats[key];
            }
        });
    }

    /**
     * 更新标签页 UI
     * @param {string} activeTab - 激活的标签页
     * @private
     */
    _updateTabUI(activeTab) {
        const tabs = document.querySelectorAll('.tw-tab-item');
        tabs.forEach(tab => {
            const tabKey = tab.dataset.tab;
            const isActive = tabKey === activeTab;

            tab.setAttribute('aria-selected', isActive ? 'true' : 'false');

            if (isActive) {
                // 激活状态：蓝色文字 + 底部蓝线
                tab.classList.remove('text-slate-500', 'dark:text-slate-400', 'border-transparent', 'hover:text-primary', 'hover:border-slate-300', 'dark:hover:border-slate-600');
                tab.classList.add('text-primary', 'border-primary');
            } else {
                // 非激活状态：灰色文字 + 透明底边
                tab.classList.add('text-slate-500', 'dark:text-slate-400', 'border-transparent', 'hover:text-primary', 'hover:border-slate-300', 'dark:hover:border-slate-600');
                tab.classList.remove('text-primary', 'border-primary');
            }

            // 更新计数徽章样式
            const badge = tab.querySelector('span.rounded-full');
            if (badge) {
                if (isActive) {
                    badge.classList.remove('bg-slate-100', 'dark:bg-slate-700', 'text-slate-500', 'dark:text-slate-400');
                    badge.classList.add('bg-primary/10', 'text-primary');
                } else {
                    badge.classList.add('bg-slate-100', 'dark:bg-slate-700', 'text-slate-500', 'dark:text-slate-400');
                    badge.classList.remove('bg-primary/10', 'text-primary');
                }
            }
        });
    }

    /**
     * 显示/隐藏表格加载状态
     * @param {boolean} show - 是否显示
     * @private
     */
    _showTableLoading(show) {
        if (this.elements.tableBody) {
            this.elements.tableBody.style.opacity = show ? '0.5' : '1';
        }
        if (this.elements.loadingMore) {
            this.elements.loadingMore.classList.toggle('hidden', !show);
        }
    }

    /**
     * 获取空行 HTML
     * @returns {string} 空行 HTML
     * @private
     */
    _getEmptyRowHtml() {
        return `<tr>
            <td colspan="8" class="p-12 text-center">
                <div class="flex flex-col items-center">
                    <span class="material-symbols-outlined text-slate-300 dark:text-slate-600 mb-3" style="font-size: 48px;">inbox</span>
                    <p class="text-slate-500 dark:text-slate-400 text-sm">${this.messages.noData}</p>
                </div>
            </td>
        </tr>`;
    }
}

// 导出到全局
window.ApprovalCenterManager = ApprovalCenterManager;
