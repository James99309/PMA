// 在浏览器控制台中运行，检测滚动条状态
(function() {
    console.log('🔍 检测页面滚动条状态');
    
    // 检测文档和窗口高度
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const bodyHeight = document.body.scrollHeight;
    
    console.log('📏 高度信息:');
    console.log(`  窗口高度: ${windowHeight}px`);
    console.log(`  文档高度: ${documentHeight}px`);
    console.log(`  Body高度: ${bodyHeight}px`);
    console.log(`  差值: ${documentHeight - windowHeight}px`);
    
    // 检测是否有垂直滚动条
    const hasVerticalScrollbar = documentHeight > windowHeight;
    console.log(`📊 滚动条状态: ${hasVerticalScrollbar ? '✅ 有垂直滚动条' : '❌ 无垂直滚动条'}`);
    
    // 检查表格容器
    const tableContainer = document.querySelector('.table-responsive');
    if (tableContainer) {
        const containerStyle = window.getComputedStyle(tableContainer);
        const containerHeight = tableContainer.getBoundingClientRect().height;
        console.log('📋 表格容器信息:');
        console.log(`  容器高度: ${Math.round(containerHeight)}px`);
        console.log(`  min-height: ${containerStyle.minHeight}`);
        console.log(`  max-height: ${containerStyle.maxHeight}`);
        console.log(`  overflow-y: ${containerStyle.overflowY}`);
        
        // 检查容器内容高度
        const table = tableContainer.querySelector('table');
        if (table) {
            const tableHeight = table.getBoundingClientRect().height;
            console.log(`  表格内容高度: ${Math.round(tableHeight)}px`);
            
            // 计算行数
            const rows = table.querySelectorAll('tbody tr');
            console.log(`  表格行数: ${rows.length}行`);
        }
    } else {
        console.log('❌ 未找到 .table-responsive 容器');
    }
    
    // 建议的解决方案
    console.log('\n💡 解决方案建议:');
    if (!hasVerticalScrollbar) {
        console.log('1. 增加初始加载数量（从20条增加到更多）');
        console.log('2. 或者设置表格容器固定高度强制产生滚动条');
        console.log('3. 或者添加底部填充空间');
        
        // 临时测试：手动设置容器高度
        if (tableContainer) {
            console.log('\n🧪 临时测试 - 设置容器最小高度:');
            const testHeight = windowHeight - 200;
            tableContainer.style.minHeight = testHeight + 'px';
            console.log(`已设置容器最小高度为 ${testHeight}px`);
            
            setTimeout(() => {
                const newDocumentHeight = document.documentElement.scrollHeight;
                const nowHasScrollbar = newDocumentHeight > windowHeight;
                console.log(`测试结果: ${nowHasScrollbar ? '✅ 现在有滚动条了！' : '❌ 仍然没有滚动条'}`);
            }, 100);
        }
    }
    
})();