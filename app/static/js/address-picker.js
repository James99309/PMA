/**
 * address-picker.js
 * 通用地址选择器模块
 *
 * 配合 tw_address_input.html 组件使用，提供地图定位和地址填充功能
 *
 * 使用方式：
 * 1. 引入依赖：map-picker.js, address-picker.js
 * 2. 使用 tw_address_input 组件渲染输入框
 * 3. 点击定位按钮自动调用 AddressPicker.open(fieldId)
 *
 * 依赖：
 * - map-picker.js - 地图选择器
 * - tw_map_picker.html - 地图弹窗组件
 */
window.AddressPicker = (function() {
    'use strict';

    /**
     * 打开地图选择器
     * @param {string} fieldId - 地址字段ID前缀
     * @param {Object} options - 可选配置
     */
    function open(fieldId, options) {
        options = options || {};

        // 设置加载状态
        setLoading(fieldId, true);

        MapPicker.open({
            initialLocation: options.initialLocation,
            initialQuery: options.initialQuery || '',
            onConfirm: function(locationData) {
                fillAddress(fieldId, locationData);
                setLoading(fieldId, false);
                showStatus(fieldId, '定位成功', 'success');

                // 3秒后隐藏状态
                setTimeout(function() {
                    hideStatus(fieldId);
                }, 3000);

                // 回调
                if (typeof options.onConfirm === 'function') {
                    options.onConfirm(locationData);
                }
            },
            onCancel: function() {
                setLoading(fieldId, false);
                if (typeof options.onCancel === 'function') {
                    options.onCancel();
                }
            }
        });

        // 地图打开后立即取消加载状态（地图内部有自己的加载状态）
        setTimeout(function() {
            setLoading(fieldId, false);
        }, 500);
    }

    /**
     * 填充地址数据
     * @param {string} fieldId - 地址字段ID前缀
     * @param {Object} locationData - 定位数据
     */
    function fillAddress(fieldId, locationData) {
        console.log('[AddressPicker] 填充地址:', fieldId, locationData);
        console.log('[AddressPicker] 接收到的数据:', {
            country: locationData.country,
            country_name: locationData.country_name,
            region: locationData.region,
            city: locationData.city,
            formatted_address: locationData.formatted_address
        });

        // 填充显示地址（完整地址）
        var addressInput = document.getElementById(fieldId);
        if (addressInput && locationData.formatted_address) {
            addressInput.value = locationData.formatted_address;
            // 定位成功后解锁输入框，允许用户手动修正地址（如补充楼栋/楼层）
            addressInput.removeAttribute('readonly');
            addressInput.removeAttribute('onclick');
            addressInput.classList.remove('cursor-pointer');
            console.log('[AddressPicker] 显示地址:', locationData.formatted_address);
        }

        // 填充隐藏字段（结构化数据）
        var countryInput = document.getElementById(fieldId + '_country');
        console.log('[AddressPicker] 查找国家字段:', fieldId + '_country', '找到:', !!countryInput);
        if (countryInput) {
            countryInput.value = locationData.country || '';
            console.log('[AddressPicker] 设置国家:', countryInput.value);
        }

        var regionInput = document.getElementById(fieldId + '_region');
        console.log('[AddressPicker] 查找省/州字段:', fieldId + '_region', '找到:', !!regionInput);
        if (regionInput) {
            regionInput.value = locationData.region || '';
            console.log('[AddressPicker] 设置省/州:', regionInput.value);
        }

        var cityInput = document.getElementById(fieldId + '_city');
        console.log('[AddressPicker] 查找城市字段:', fieldId + '_city', '找到:', !!cityInput);
        if (cityInput) {
            cityInput.value = locationData.city || '';
            console.log('[AddressPicker] 设置城市:', cityInput.value);
        }

        // 填充坐标隐藏字段
        var latInput = document.getElementById(fieldId + '_latitude');
        if (latInput && locationData.lat != null) {
            latInput.value = locationData.lat;
        }

        var lngInput = document.getElementById(fieldId + '_longitude');
        if (lngInput && locationData.lng != null) {
            lngInput.value = locationData.lng;
        }
    }

    /**
     * 设置加载状态
     * @param {string} fieldId - 地址字段ID前缀
     * @param {boolean} loading - 是否加载中
     */
    function setLoading(fieldId, loading) {
        var btn = document.getElementById(fieldId + '_location_btn');
        var icon = document.getElementById(fieldId + '_location_icon');
        var loadingIcon = document.getElementById(fieldId + '_location_loading');

        if (btn) {
            btn.disabled = loading;
        }

        if (icon && loadingIcon) {
            if (loading) {
                icon.classList.add('hidden');
                loadingIcon.classList.remove('hidden');
            } else {
                icon.classList.remove('hidden');
                loadingIcon.classList.add('hidden');
            }
        }
    }

    /**
     * 显示状态提示
     * @param {string} fieldId - 地址字段ID前缀
     * @param {string} message - 提示消息
     * @param {string} type - 类型: 'info', 'success', 'error'
     */
    function showStatus(fieldId, message, type) {
        var statusEl = document.getElementById(fieldId + '_status');
        if (!statusEl) return;

        statusEl.textContent = message;
        statusEl.classList.remove('hidden', 'text-slate-500', 'text-green-500', 'text-red-500');

        if (type === 'success') {
            statusEl.classList.add('text-green-500');
        } else if (type === 'error') {
            statusEl.classList.add('text-red-500');
        } else {
            statusEl.classList.add('text-slate-500');
        }
    }

    /**
     * 隐藏状态提示
     * @param {string} fieldId - 地址字段ID前缀
     */
    function hideStatus(fieldId) {
        var statusEl = document.getElementById(fieldId + '_status');
        if (statusEl) {
            statusEl.classList.add('hidden');
        }
    }

    /**
     * 获取地址数据
     * @param {string} fieldId - 地址字段ID前缀
     * @returns {Object} 地址数据
     */
    function getAddressData(fieldId) {
        return {
            address: document.getElementById(fieldId)?.value || '',
            country: document.getElementById(fieldId + '_country')?.value || '',
            region: document.getElementById(fieldId + '_region')?.value || '',
            city: document.getElementById(fieldId + '_city')?.value || ''
        };
    }

    /**
     * 设置地址数据
     * @param {string} fieldId - 地址字段ID前缀
     * @param {Object} data - 地址数据
     */
    function setAddressData(fieldId, data) {
        var addressInput = document.getElementById(fieldId);
        if (addressInput && data.address) {
            addressInput.value = data.address;
        }

        var countryInput = document.getElementById(fieldId + '_country');
        if (countryInput) {
            countryInput.value = data.country || '';
        }

        var regionInput = document.getElementById(fieldId + '_region');
        if (regionInput) {
            regionInput.value = data.region || '';
        }

        var cityInput = document.getElementById(fieldId + '_city');
        if (cityInput) {
            cityInput.value = data.city || '';
        }
    }

    /**
     * 清空地址数据
     * @param {string} fieldId - 地址字段ID前缀
     */
    function clearAddress(fieldId) {
        setAddressData(fieldId, {
            address: '',
            country: '',
            region: '',
            city: ''
        });
    }

    // 公开 API
    return {
        open: open,
        fillAddress: fillAddress,
        getAddressData: getAddressData,
        setAddressData: setAddressData,
        clearAddress: clearAddress,
        setLoading: setLoading,
        showStatus: showStatus,
        hideStatus: hideStatus
    };
})();
