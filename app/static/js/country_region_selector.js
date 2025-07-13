/**
 * 国家和地区级联选择器
 * 用于客户管理模块
 */
document.addEventListener('DOMContentLoaded', function() {
  // 初始化国家选择器
  const countrySelect = document.getElementById('country');
  const regionSelect = document.getElementById('region');
  
  if (!countrySelect || !regionSelect) return;
  
  console.log("国家地区选择器初始化开始...");
  
  // 清空国家选择框并添加提示选项
  const selectCountryText = window.i18nTexts ? window.i18nTexts.selectCountry : '请选择国家';
  countrySelect.innerHTML = `<option value="">${selectCountryText}</option>`;
  
  // 遍历国家数据并添加到选择框
  countryData.forEach(country => {
    const option = document.createElement('option');
    option.value = country.code;
    option.textContent = country.name;
    countrySelect.appendChild(option);
  });
  
  // 更新省/州选择框的函数
  function updateRegions() {
    const selectedCountryCode = countrySelect.value;
    
    console.log("更新地区，选中的国家代码:", selectedCountryCode);
    
    // 清空省/州选择框并添加提示选项
    const selectRegionText = window.i18nTexts ? window.i18nTexts.selectRegion : '请选择省/州';
    regionSelect.innerHTML = `<option value="">${selectRegionText}</option>`;
    
    // 禁用省/州选择框，直到选择了国家
    regionSelect.disabled = !selectedCountryCode;
    
    if (selectedCountryCode && regionData[selectedCountryCode]) {
      // 添加对应国家的省/州选项
      regionData[selectedCountryCode].forEach(region => {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
      });
    }
  }
  
  // 添加国家选择变化的事件监听器
  countrySelect.addEventListener('change', updateRegions);
  
  // 初始调用一次更新函数，处理可能的预选值
  updateRegions();
  
  // 如果页面上有保存的国家和省份数据，则加载它们
  setTimeout(function() {
    console.log("检查已保存的国家和地区数据...");
    
    // 检查是否存在全局变量
    if (typeof savedCountry !== 'undefined' && savedCountry) {
      console.log("已保存的国家:", savedCountry);
      console.log("已保存的地区:", savedRegion);
      
      let countryCode = null;
      let countryFound = false;
      
      // 首先尝试通过国家名称查找国家代码
      for (let i = 0; i < countryData.length; i++) {
        if (countryData[i].name === savedCountry) {
          countryCode = countryData[i].code;
          countryFound = true;
          console.log("找到匹配的国家代码:", countryCode);
          break;
        }
      }
      
      // 如果通过名称没找到，尝试通过代码查找
      if (!countryFound) {
        for (let i = 0; i < countryData.length; i++) {
          if (countryData[i].code === savedCountry) {
            countryCode = countryData[i].code;
            countryFound = true;
            console.log("通过代码找到匹配的国家:", countryCode);
            break;
          }
        }
      }
      
      if (countryFound && countryCode) {
        // 选中对应的国家
        countrySelect.value = countryCode;
        console.log("设置国家选择器值为:", countryCode);
        
        // 触发change事件以加载地区
        countrySelect.dispatchEvent(new Event('change'));
        
        // 如果有保存的省份/地区，尝试选择它
        if (typeof savedRegion !== 'undefined' && savedRegion) {
          setTimeout(function() {
            let regionFound = false;
            
            // 遍历所有选项，找到匹配的地区名称
            for (let i = 0; i < regionSelect.options.length; i++) {
              if (regionSelect.options[i].value === savedRegion || regionSelect.options[i].text === savedRegion) {
                regionSelect.selectedIndex = i;
                regionFound = true;
                console.log("找到匹配的地区选项，索引:", i);
                break;
              }
            }
            
            // 如果在选项中没有找到匹配的地区，创建一个新选项
            if (!regionFound && savedRegion) {
              console.log("未找到匹配的地区，创建自定义选项:", savedRegion);
              const customRegion = document.createElement('option');
              customRegion.value = savedRegion;
              customRegion.text = savedRegion;
              regionSelect.appendChild(customRegion);
              regionSelect.value = savedRegion;
            }
          }, 200);
        }
      } else if (savedCountry) {
        // 如果找不到预定义的国家，创建新选项
        console.log("未找到预定义国家，创建自定义选项:", savedCountry);
        const customOption = document.createElement('option');
        customOption.value = savedCountry;
        customOption.text = savedCountry;
        countrySelect.appendChild(customOption);
        countrySelect.value = savedCountry;
        
        // 启用地区选择器
        regionSelect.disabled = false;
        
        // 如果有保存的地区，添加自定义地区选项
        if (typeof savedRegion !== 'undefined' && savedRegion) {
          console.log("创建自定义地区选项:", savedRegion);
          const customRegion = document.createElement('option');
          customRegion.value = savedRegion;
          customRegion.text = savedRegion;
          regionSelect.appendChild(customRegion);
          regionSelect.value = savedRegion;
        }
      }
    }
  }, 200);
}); 