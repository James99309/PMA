/**
 * 语言感知的国家和地区级联选择器
 * 用于客户管理模块
 */
document.addEventListener('DOMContentLoaded', function() {
  // 初始化国家选择器
  const countrySelect = document.getElementById('country');
  const regionSelect = document.getElementById('region');
  
  if (!countrySelect || !regionSelect) return;
  
  console.log("语言感知的国家地区选择器初始化开始...");
  
  let countriesData = [];
  let regionsData = {};
  
  // 从API获取语言感知的国家和地区数据
  fetch('/customer/api/countries-regions')
    .then(response => response.json())
    .then(data => {
      countriesData = data.countries;
      regionsData = data.regions;
      
      // 初始化国家选择框
      initializeCountrySelect();
      
      // 如果有保存的值，恢复选择
      if (typeof savedCountry !== 'undefined' && savedCountry) {
        countrySelect.value = savedCountry;
        updateRegions();
        
        if (typeof savedRegion !== 'undefined' && savedRegion) {
          setTimeout(() => {
            regionSelect.value = savedRegion;
          }, 100);
        }
      }
    })
    .catch(error => {
      console.error('获取国家地区数据失败:', error);
      // 降级处理：使用默认数据
      fallbackToStaticData();
    });
  
  function initializeCountrySelect() {
    // 清空国家选择框并添加提示选项
    const selectCountryText = window.i18nTexts ? window.i18nTexts.selectCountry : '请选择国家';
    countrySelect.innerHTML = `<option value="">${selectCountryText}</option>`;
    
    // 添加国家选项
    countriesData.forEach(country => {
      const option = document.createElement('option');
      option.value = country.code;
      option.textContent = country.name;
      countrySelect.appendChild(option);
    });
  }
  
  // 更新省/州选择框的函数
  function updateRegions() {
    const selectedCountryCode = countrySelect.value;
    
    console.log("更新地区，选中的国家代码:", selectedCountryCode);
    
    // 清空地区选择框
    const selectRegionText = window.i18nTexts ? window.i18nTexts.selectRegion : '请选择省/州';
    regionSelect.innerHTML = `<option value="">${selectRegionText}</option>`;
    
    if (selectedCountryCode && regionsData[selectedCountryCode]) {
      const regions = regionsData[selectedCountryCode];
      regions.forEach(region => {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
      });
      
      regionSelect.disabled = false;
    } else {
      regionSelect.disabled = true;
    }
  }
  
  // 降级处理：使用静态数据
  function fallbackToStaticData() {
    console.log("使用静态数据作为降级处理");
    
    // 基本的国家数据（中文）
    const fallbackCountries = [
      { code: "CN", name: "中国" },
      { code: "US", name: "美国" },
      { code: "JP", name: "日本" },
      { code: "DE", name: "德国" },
      { code: "GB", name: "英国" },
      { code: "CA", name: "加拿大" },
      { code: "AU", name: "澳大利亚" },
      { code: "SG", name: "新加坡" },
      { code: "MY", name: "马来西亚" },
      { code: "TH", name: "泰国" }
    ];
    
    const fallbackRegions = {
      "CN": ["北京市", "上海市", "天津市", "重庆市", "广东省", "江苏省", "浙江省", "山东省", "河南省", "四川省"],
      "US": ["California", "Texas", "New York", "Florida", "Illinois", "Pennsylvania", "Ohio"],
      "JP": ["東京都", "大阪府", "神奈川県", "愛知県", "埼玉県", "千葉県"]
    };
    
    countriesData = fallbackCountries;
    regionsData = fallbackRegions;
    
    initializeCountrySelect();
  }
  
  // 国家选择变化事件
  countrySelect.addEventListener('change', updateRegions);
});