// 在浏览器控制台运行，检查李冬用户是否已显示
(function() {
    console.log('🔍 检查李冬用户显示状态');
    
    // 检查表格中的所有行
    const tableBody = document.getElementById('userTableBody');
    if (!tableBody) {
        console.log('❌ 未找到表格主体');
        return;
    }
    
    const rows = tableBody.querySelectorAll('tr');
    console.log(`📊 表格中共有 ${rows.length} 行数据`);
    
    // 查找李冬用户
    let lidongFound = false;
    let lidongRowNumber = 0;
    
    rows.forEach((row, index) => {
        const rowText = row.textContent.toLowerCase();
        if (rowText.includes('lidong') || rowText.includes('李冬')) {
            lidongFound = true;
            lidongRowNumber = index + 1;
            console.log(`✅ 找到李冬用户在第 ${lidongRowNumber} 行:`);
            console.log('   行内容:', row.textContent.trim());
            
            // 高亮显示这一行
            row.style.backgroundColor = '#fff3cd';
            row.style.border = '2px solid #ffc107';
            setTimeout(() => {
                row.style.backgroundColor = '';
                row.style.border = '';
            }, 3000);
        }
    });
    
    if (!lidongFound) {
        console.log('❌ 李冬用户未在表格中找到');
        console.log('📋 前10行内容预览:');
        rows.forEach((row, index) => {
            if (index < 10) {
                console.log(`   ${index + 1}. ${row.textContent.trim()}`);
            }
        });
    } else {
        console.log(`🎉 李冬用户已找到！位置：第 ${lidongRowNumber} 行`);
    }
    
    // 检查是否有筛选相关错误
    console.log('\n🔍 检查搜索功能状态:');
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        console.log(`搜索框存在: ${searchInput.value}`);
        
        // 测试搜索功能
        console.log('🧪 测试搜索李冬...');
        searchInput.value = '李冬';
        
        // 触发搜索事件
        const form = searchInput.closest('form');
        if (form) {
            console.log('找到搜索表单，准备提交...');
            // 不实际提交，只是准备
            console.log('⚠️  实际搜索可能会导致500错误，建议先解决后端问题');
        }
    } else {
        console.log('❌ 未找到搜索框');
    }
    
})();