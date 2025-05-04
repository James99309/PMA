/**
 * 修复国家和地区选择器
 * 用于企业编辑页面
 */
document.addEventListener('DOMContentLoaded', function() {
    // 确保必要的元素存在
    const countrySelect = document.getElementById('country');
    const regionSelect = document.getElementById('region');
    
    if (!countrySelect || !regionSelect) {
        console.error("国家或地区选择器未找到");
        return;
    }
    
    console.log("修复脚本加载 - 修复国家/地区选择器");
    console.log("已保存的国家:", savedCountry);
    console.log("已保存的地区:", savedRegion);
    
    // 确保country_region_selector.js正确加载完成后再执行
    setTimeout(function() {
        if (typeof savedRegion !== 'undefined' && savedRegion && savedRegion.trim() !== '') {
            // 检查地区选择器中是否已有选中值
            if (!regionSelect.value || regionSelect.value === '') {
                console.log("地区未被正确选中，尝试修复...");
                
                // 强制添加一个自定义地区选项
                let customOption = document.createElement('option');
                customOption.value = savedRegion;
                customOption.text = savedRegion;
                regionSelect.appendChild(customOption);
                regionSelect.value = savedRegion;
                console.log("手动添加了地区选项:", savedRegion);
                
                // 确保地区选择器不是禁用状态
                regionSelect.disabled = false;
            } else {
                console.log("地区已正确选中:", regionSelect.value);
            }
        }
    }, 500);
}); 
 * 修复国家和地区选择器
 * 用于企业编辑页面
 */
document.addEventListener('DOMContentLoaded', function() {
    // 确保必要的元素存在
    const countrySelect = document.getElementById('country');
    const regionSelect = document.getElementById('region');
    
    if (!countrySelect || !regionSelect) {
        console.error("国家或地区选择器未找到");
        return;
    }
    
    console.log("修复脚本加载 - 修复国家/地区选择器");
    console.log("已保存的国家:", savedCountry);
    console.log("已保存的地区:", savedRegion);
    
    // 确保country_region_selector.js正确加载完成后再执行
    setTimeout(function() {
        if (typeof savedRegion !== 'undefined' && savedRegion && savedRegion.trim() !== '') {
            // 检查地区选择器中是否已有选中值
            if (!regionSelect.value || regionSelect.value === '') {
                console.log("地区未被正确选中，尝试修复...");
                
                // 强制添加一个自定义地区选项
                let customOption = document.createElement('option');
                customOption.value = savedRegion;
                customOption.text = savedRegion;
                regionSelect.appendChild(customOption);
                regionSelect.value = savedRegion;
                console.log("手动添加了地区选项:", savedRegion);
                
                // 确保地区选择器不是禁用状态
                regionSelect.disabled = false;
            } else {
                console.log("地区已正确选中:", regionSelect.value);
            }
        }
    }, 500);
}); 