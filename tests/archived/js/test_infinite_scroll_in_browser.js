// 在浏览器控制台中运行的无限滚动测试脚本
// 使用方法：在用户列表页面的浏览器控制台中粘贴并运行此脚本

(function() {
    console.log('🚀 开始无限滚动功能测试');
    
    // 1. 检查基础环境
    console.group('📋 环境检查');
    
    const checks = [
        { name: 'window.debugInfiniteScroll', obj: window.debugInfiniteScroll },
        { name: 'window.infiniteScrollState', obj: window.infiniteScrollState },
        { name: 'window.currentDataListConfig', obj: window.currentDataListConfig },
        { name: '.table-responsive容器', obj: document.querySelector('.table-responsive') },
        { name: '#userTableBody', obj: document.getElementById('userTableBody') }
    ];
    
    checks.forEach(check => {
        const exists = check.obj !== null && check.obj !== undefined;
        console.log(`${exists ? '✅' : '❌'} ${check.name}: ${exists ? '存在' : '不存在'}`);
        if (exists && typeof check.obj === 'object') {
            console.log(`   详情:`, check.obj);
        }
    });
    
    console.groupEnd();
    
    // 2. 检查当前状态
    if (window.debugInfiniteScroll) {
        console.group('📊 无限滚动状态');
        
        const state = window.debugInfiniteScroll.getState();
        const config = window.debugInfiniteScroll.getConfig();
        
        console.log('当前状态:', state);
        console.log('配置信息:', config);
        
        console.groupEnd();
    }
    
    // 3. 手动触发滚动检测
    console.group('🔍 手动测试');
    
    if (window.debugInfiniteScroll) {
        console.log('手动触发滚动位置检查...');
        window.debugInfiniteScroll.checkScrollPosition();
        
        setTimeout(() => {
            console.log('尝试模拟滚动到底部...');
            
            // 滚动到页面底部
            const documentHeight = document.documentElement.scrollHeight;
            const windowHeight = window.innerHeight;
            const targetScroll = documentHeight - windowHeight + 200; // 超过底部一点
            
            window.scrollTo({
                top: targetScroll,
                behavior: 'smooth'
            });
            
            setTimeout(() => {
                console.log('滚动完成，再次检查位置...');
                window.debugInfiniteScroll.checkScrollPosition();
            }, 1000);
            
        }, 2000);
        
        // 4. 提供手动操作方法
        console.log('💡 可用的调试方法:');
        console.log('  - window.debugInfiniteScroll.checkScrollPosition() // 检查滚动位置');
        console.log('  - window.debugInfiniteScroll.loadMoreData() // 强制加载更多数据');
        console.log('  - window.debugInfiniteScroll.getState() // 获取当前状态');
        console.log('  - window.debugInfiniteScroll.resetState() // 重置状态');
        
        // 5. 测试强制加载更多数据
        setTimeout(() => {
            console.log('🚀 尝试强制加载更多数据...');
            try {
                window.debugInfiniteScroll.loadMoreData();
            } catch (error) {
                console.error('强制加载失败:', error);
            }
        }, 5000);
        
    } else {
        console.error('❌ debugInfiniteScroll 不可用，无法进行手动测试');
    }
    
    console.groupEnd();
    
    // 6. 监听接下来的滚动事件
    let scrollLogCount = 0;
    const maxScrollLogs = 10;
    
    function logScrollEvent() {
        if (scrollLogCount < maxScrollLogs) {
            scrollLogCount++;
            console.log(`📜 滚动事件 #${scrollLogCount}: 位置 ${window.pageYOffset}px`);
            
            if (scrollLogCount >= maxScrollLogs) {
                console.log('⚠️ 已达到最大滚动日志数量，停止记录');
                window.removeEventListener('scroll', logScrollEvent);
            }
        }
    }
    
    window.addEventListener('scroll', logScrollEvent, { passive: true });
    
    console.log('✅ 无限滚动测试脚本初始化完成');
    console.log('   请尝试向下滚动页面，观察控制台输出');
    
})();