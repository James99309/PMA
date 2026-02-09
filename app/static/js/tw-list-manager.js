/**
 * Tailwind 列表管理器
 *
 * 通用的列表页面管理类，提供排序、无限滚动、筛选等功能。
 *
 * 使用示例:
 *   const listManager = new TwListManager({
 *       tableId: 'projectTable',
 *       formId: 'filterForm',
 *       ajaxEndpoint: '/project/ajax',
 *       pageSize: 30,
 *       initialCount: 30
 *   });
 *   listManager.init();
 */
class TwListManager {
    /**
     * 构造函数
     * @param {Object} config - 配置对象
     * @param {string} config.tableId - 表格ID
     * @param {string} config.formId - 筛选表单ID
     * @param {string} config.ajaxEndpoint - AJAX加载端点
     * @param {number} [config.pageSize=30] - 每页数量
     * @param {number} [config.initialCount=0] - 初始数据数量
     * @param {string} [config.sortField='updated_at'] - 默认排序字段
     * @param {string} [config.sortOrder='desc'] - 默认排序方向
     * @param {boolean} [config.infiniteScroll=true] - 是否启用无限滚动
     * @param {Object} [config.messages] - 自定义消息文本
     */
    constructor(config) {
        this.tableId = config.tableId;
        this.formId = config.formId;
        this.ajaxEndpoint = config.ajaxEndpoint;
        this.pageSize = config.pageSize || 30;
        this.initialCount = config.initialCount || 0;
        this.sortField = config.sortField || 'updated_at';
        this.sortOrder = config.sortOrder || 'desc';
        this.infiniteScrollEnabled = config.infiniteScroll !== false;
        this.extraParams = config.extraParams || {};

        // 消息文本（支持国际化）
        this.messages = Object.assign({
            loadingMore: '加载中...',
            noMoreData: '没有更多数据',
            loadError: '加载数据失败'
        }, config.messages || {});

        // 状态
        this.isLoading = false;
        this.hasMore = true;
        this.currentOffset = this.initialCount;

        // DOM 元素缓存
        this.elements = {};
    }

    /**
     * 初始化
     */
    init() {
        this._cacheElements();
        this._setupSorting();

        if (this.infiniteScrollEnabled) {
            this._setupInfiniteScroll();
        }

        // 检查初始数据是否已经少于一页
        if (this.initialCount < this.pageSize) {
            this.hasMore = false;
            if (this.initialCount > 0 && this.elements.noMoreData) {
                this.elements.noMoreData.classList.remove('hidden');
            }
        }
    }

    /**
     * 缓存 DOM 元素
     * @private
     */
    _cacheElements() {
        this.elements = {
            tableBody: document.getElementById(`${this.tableId}Body`),
            loadingMore: document.getElementById(`${this.tableId}LoadingMore`),
            noMoreData: document.getElementById(`${this.tableId}NoMore`),
            scrollSentinel: document.getElementById(`${this.tableId}Sentinel`),
            filterForm: document.getElementById(this.formId)
        };
    }

    /**
     * 设置排序功能
     * @private
     */
    _setupSorting() {
        // 将排序函数暴露到全局
        window[`sort${this._capitalize(this.tableId)}`] = (field) => {
            this.sortBy(field);
        };
    }

    /**
     * 设置无限滚动
     * @private
     */
    _setupInfiniteScroll() {
        // 优先使用表格自身的滚动容器（tw_data_table 生成的 {tableId}Scroll）
        const scrollContainer = document.getElementById(`${this.tableId}Scroll`);
        if (scrollContainer) {
            scrollContainer.addEventListener('scroll', () => {
                if (this.isLoading || !this.hasMore) return;
                const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
                if (scrollTop + clientHeight >= scrollHeight - 100) {
                    this.loadMore();
                }
            });
            return;
        }

        // 回退：使用 IntersectionObserver 观察哨兵元素
        if (!this.elements.scrollSentinel) {
            console.warn(`TwListManager: Scroll sentinel not found for ${this.tableId}`);
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !this.isLoading && this.hasMore) {
                this.loadMore();
            }
        }, { threshold: 0.1 });

        observer.observe(this.elements.scrollSentinel);
    }

    /**
     * 按字段排序
     * @param {string} field - 排序字段
     */
    sortBy(field) {
        const url = new URL(window.location.href);
        const currentSort = url.searchParams.get('sort');
        const currentOrder = url.searchParams.get('order') || 'desc';

        url.searchParams.set('sort', field);
        if (currentSort === field) {
            url.searchParams.set('order', currentOrder === 'asc' ? 'desc' : 'asc');
        } else {
            url.searchParams.set('order', 'desc');
        }

        window.location.href = url.toString();
    }

    /**
     * 加载更多数据
     */
    loadMore() {
        if (this.isLoading || !this.hasMore) return;

        this.isLoading = true;
        this._showLoading(true);

        // 构建请求URL
        const url = new URL(this.ajaxEndpoint, window.location.origin);

        // 复制当前页面的筛选参数
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.forEach((value, key) => {
            if (key !== 'old' && key !== 'ajax') {
                url.searchParams.set(key, value);
            }
        });

        url.searchParams.set('offset', this.currentOffset);
        url.searchParams.set('limit', this.pageSize);
        url.searchParams.set('ajax', '1');

        fetch(url.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            this._handleLoadSuccess(data);
        })
        .catch(error => {
            this._handleLoadError(error);
        });
    }

    /**
     * 处理加载成功
     * @param {Object} data - 响应数据
     * @private
     */
    _handleLoadSuccess(data) {
        if (data.html && this.elements.tableBody) {
            this.elements.tableBody.insertAdjacentHTML('beforeend', data.html);
        }

        this.hasMore = data.has_more;
        this.currentOffset = data.offset || (this.currentOffset + this.pageSize);

        this._showLoading(false);

        if (!this.hasMore && this.elements.noMoreData) {
            this.elements.noMoreData.classList.remove('hidden');
        }

        this.isLoading = false;
    }

    /**
     * 处理加载错误
     * @param {Error} error - 错误对象
     * @private
     */
    _handleLoadError(error) {
        console.error(this.messages.loadError, error);
        this._showLoading(false);
        this.isLoading = false;
    }

    /**
     * 显示/隐藏加载状态
     * @param {boolean} show - 是否显示
     * @private
     */
    _showLoading(show) {
        if (this.elements.loadingMore) {
            this.elements.loadingMore.classList.toggle('hidden', !show);
        }
        if (this.elements.noMoreData) {
            this.elements.noMoreData.classList.add('hidden');
        }
    }

    /**
     * 重置列表
     * 用于筛选条件变化后重新加载
     */
    reset() {
        this.currentOffset = 0;
        this.hasMore = true;
        this.isLoading = false;

        if (this.elements.tableBody) {
            this.elements.tableBody.innerHTML = '';
        }

        this.loadMore();
    }

    /**
     * 设置额外参数
     * @param {Object} params - 额外参数对象
     */
    setExtraParams(params) {
        this.extraParams = params || {};
    }

    /**
     * 重新加载列表（清空并重新请求）
     */
    reload() {
        this.currentOffset = 0;
        this.hasMore = true;
        this.isLoading = false;

        if (this.elements.tableBody) {
            this.elements.tableBody.innerHTML = '';
        }
        if (this.elements.noMoreData) {
            this.elements.noMoreData.classList.add('hidden');
        }

        this._loadData();
    }

    /**
     * 内部加载数据方法（使用 extraParams）
     * @private
     */
    _loadData() {
        if (this.isLoading) return;

        this.isLoading = true;
        this._showLoading(true);

        // 构建请求URL
        const url = new URL(this.ajaxEndpoint, window.location.origin);

        // 1. 先添加表单筛选值（排除与 extraParams 冲突的字段）
        if (this.elements.filterForm) {
            const formData = new FormData(this.elements.filterForm);
            // exclude_owner=1 时排除 owner_id（避免条件冲突）
            const excludeFields = this.extraParams.exclude_owner === '1' ? ['owner_id'] : [];
            formData.forEach((value, key) => {
                if (value && !excludeFields.includes(key)) {
                    url.searchParams.set(key, value);
                }
            });
        }

        // 2. 再添加 extraParams（会覆盖表单中的同名参数）
        Object.keys(this.extraParams).forEach(key => {
            url.searchParams.set(key, this.extraParams[key]);
        });

        // 添加排序参数
        url.searchParams.set('sort', this.sortField);
        url.searchParams.set('order', this.sortOrder);
        url.searchParams.set('offset', this.currentOffset);
        url.searchParams.set('limit', this.pageSize);
        url.searchParams.set('ajax', '1');

        fetch(url.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            this._handleLoadSuccess(data);
        })
        .catch(error => {
            this._handleLoadError(error);
        });
    }

    /**
     * 刷新列表
     * 保持当前数据，重新加载所有已加载的数据
     */
    refresh() {
        const totalLoaded = this.currentOffset;
        this.currentOffset = 0;
        this.hasMore = true;

        if (this.elements.tableBody) {
            this.elements.tableBody.innerHTML = '';
        }

        // 加载之前已加载的所有数据
        const loadPromise = new Promise((resolve) => {
            const loadBatch = () => {
                if (this.currentOffset >= totalLoaded) {
                    resolve();
                    return;
                }
                this.loadMore();
                setTimeout(loadBatch, 100);
            };
            loadBatch();
        });

        return loadPromise;
    }

    /**
     * 首字母大写
     * @param {string} str - 输入字符串
     * @returns {string} 首字母大写的字符串
     * @private
     */
    _capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

/**
 * 快速初始化函数
 * @param {Object} config - 配置对象
 * @returns {TwListManager} 列表管理器实例
 */
function initTwListManager(config) {
    const manager = new TwListManager(config);
    manager.init();
    return manager;
}

// 导出到全局
window.TwListManager = TwListManager;
window.initTwListManager = initTwListManager;
