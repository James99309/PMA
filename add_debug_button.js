// 在用户列表页面控制台中运行此脚本，添加调试按钮
(function() {
    // 创建调试按钮容器
    const debugContainer = document.createElement('div');
    debugContainer.id = 'infiniteScrollDebug';
    debugContainer.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 15px;
        border-radius: 8px;
        z-index: 9999;
        font-family: monospace;
        font-size: 12px;
        min-width: 300px;
    `;
    
    // 状态显示
    const statusDiv = document.createElement('div');
    statusDiv.id = 'scrollStatus';
    statusDiv.style.marginBottom = '10px';
    
    // 按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = 'display: flex; gap: 5px; margin-top: 10px;';
    
    // 手动加载按钮
    const loadButton = document.createElement('button');
    loadButton.textContent = '加载更多';
    loadButton.style.cssText = `
        background: #007bff;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 11px;
    `;
    
    // 检查状态按钮
    const checkButton = document.createElement('button');
    checkButton.textContent = '检查状态';
    checkButton.style.cssText = loadButton.style.cssText;
    checkButton.style.background = '#28a745';
    
    // 滚动到底部按钮
    const scrollButton = document.createElement('button');
    scrollButton.textContent = '滚动到底';
    scrollButton.style.cssText = loadButton.style.cssText;
    scrollButton.style.background = '#ffc107';
    scrollButton.style.color = 'black';
    
    // 关闭按钮
    const closeButton = document.createElement('button');
    closeButton.textContent = '×';
    closeButton.style.cssText = `
        position: absolute;
        top: 5px;
        right: 5px;
        background: transparent;
        color: white;
        border: none;
        cursor: pointer;
        font-size: 16px;
    `;
    
    function updateStatus() {
        const state = window.debugInfiniteScroll ? window.debugInfiniteScroll.getState() : null;
        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;
        
        statusDiv.innerHTML = `
            <strong>🔄 无限滚动状态:</strong><br>
            状态: ${state ? 'OK' : 'N/A'}<br>
            已加载: ${state ? state.currentOffset : '?'}<br>
            还有更多: ${state ? state.hasMore : '?'}<br>
            正在加载: ${state ? state.isLoading : '?'}<br>
            <br>
            <strong>📏 滚动信息:</strong><br>
            当前位置: ${scrollTop}px<br>
            窗口高度: ${windowHeight}px<br>
            文档高度: ${docHeight}px<br>
            距离底部: ${docHeight - scrollTop - windowHeight}px
        `;
    }
    
    // 事件监听
    loadButton.onclick = () => {
        console.log('🚀 手动触发加载更多数据');
        if (window.debugInfiniteScroll) {
            try {
                window.debugInfiniteScroll.loadMoreData();
                updateStatus();
            } catch (error) {
                console.error('加载失败:', error);
            }
        } else {
            console.error('debugInfiniteScroll 不可用');
        }
    };
    
    checkButton.onclick = () => {
        console.log('🔍 检查滚动状态');
        if (window.debugInfiniteScroll) {
            window.debugInfiniteScroll.checkScrollPosition();
        }
        updateStatus();
    };
    
    scrollButton.onclick = () => {
        console.log('⬇️ 滚动到页面底部');
        const docHeight = document.documentElement.scrollHeight;
        const windowHeight = window.innerHeight;
        window.scrollTo({
            top: docHeight - windowHeight + 100,
            behavior: 'smooth'
        });
        setTimeout(updateStatus, 1000);
    };
    
    closeButton.onclick = () => {
        debugContainer.remove();
    };
    
    // 组装界面
    debugContainer.appendChild(closeButton);
    debugContainer.appendChild(statusDiv);
    buttonContainer.appendChild(loadButton);
    buttonContainer.appendChild(checkButton);
    buttonContainer.appendChild(scrollButton);
    debugContainer.appendChild(buttonContainer);
    
    // 添加到页面
    document.body.appendChild(debugContainer);
    
    // 初始状态更新
    updateStatus();
    
    // 定期更新状态
    const updateInterval = setInterval(() => {
        if (document.body.contains(debugContainer)) {
            updateStatus();
        } else {
            clearInterval(updateInterval);
        }
    }, 2000);
    
    console.log('✅ 无限滚动调试面板已添加到页面右上角');
    console.log('💡 你可以点击"加载更多"按钮直接测试功能');
    
})();