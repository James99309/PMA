function updateProvinces() {
    const country = document.getElementById('country').value;
    const provinceSelect = document.getElementById('province');
    const citySelect = document.getElementById('city');
    
    // 清空省份和城市选择框
    provinceSelect.innerHTML = '<option value="">请选择省份</option>';
    citySelect.innerHTML = '<option value="">请选择城市</option>';
    
    // 如果选择了国家，加载对应的省份
    if (country && areaData[country]) {
        const provinces = Object.keys(areaData[country]);
        provinces.forEach(province => {
            const option = document.createElement('option');
            option.value = province;
            option.textContent = province;
            provinceSelect.appendChild(option);
        });
    }
}

function updateCities() {
    const country = document.getElementById('country').value;
    const province = document.getElementById('province').value;
    const citySelect = document.getElementById('city');
    
    // 清空城市选择框
    citySelect.innerHTML = '<option value="">请选择城市</option>';
    
    // 如果选择了省份，加载对应的城市
    if (country && province && areaData[country][province]) {
        const cities = areaData[country][province];
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 获取选择框元素
    const countrySelect = document.getElementById('country');
    const provinceSelect = document.getElementById('province');
    
    // 初始化国家选择框
    countrySelect.innerHTML = '<option value="">请选择国家</option>';
    Object.keys(areaData).forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        countrySelect.appendChild(option);
    });
    
    // 添加事件监听器
    countrySelect.addEventListener('change', updateProvinces);
    provinceSelect.addEventListener('change', updateCities);
}); 