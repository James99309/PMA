/**
 * map-picker.js
 * 地图位置选择器
 *
 * 支持 Google Maps，加载失败时降级到简单定位
 *
 * 使用方式：
 * MapPicker.open({
 *     onConfirm: function(locationData) {
 *         // locationData: { lat, lng, country, region, city, district, address, formatted_address }
 *     },
 *     onCancel: function() {},
 *     initialLocation: { lat: 31.2304, lng: 121.4737 }  // 可选，默认当前位置
 * });
 */
window.MapPicker = (function() {
    'use strict';

    // 配置
    const CONFIG = {
        googleMapsApiKey: '', // 从页面获取
        sdkLoadTimeout: 5000, // SDK 加载超时时间 (ms)
        defaultCenter: { lat: 31.2304, lng: 121.4737 }, // 默认上海
        defaultZoom: 15,
        reverseGeocodeApi: '/customer/api/geocode/reverse'
    };

    // 状态
    let state = {
        isOpen: false,
        map: null,
        marker: null,
        autocomplete: null,
        selectedLocation: null,
        callbacks: {},
        sdkLoaded: false,
        sdkLoadFailed: false
    };

    /**
     * 动态加载 Google Maps SDK
     */
    function loadGoogleMapsSDK() {
        return new Promise(function(resolve, reject) {
            // 已经加载过
            if (window.google && window.google.maps) {
                state.sdkLoaded = true;
                resolve();
                return;
            }

            // 正在加载中
            if (document.querySelector('script[src*="maps.googleapis.com"]')) {
                // 等待加载完成
                var checkInterval = setInterval(function() {
                    if (window.google && window.google.maps) {
                        clearInterval(checkInterval);
                        state.sdkLoaded = true;
                        resolve();
                    }
                }, 100);

                setTimeout(function() {
                    clearInterval(checkInterval);
                    if (!window.google || !window.google.maps) {
                        reject(new Error('Google Maps SDK 加载超时'));
                    }
                }, CONFIG.sdkLoadTimeout);
                return;
            }

            // 创建回调函数
            var callbackName = 'initGoogleMaps_' + Date.now();
            window[callbackName] = function() {
                delete window[callbackName];
                state.sdkLoaded = true;
                resolve();
            };

            // 创建 script 标签
            var script = document.createElement('script');
            script.src = 'https://maps.googleapis.com/maps/api/js?key=' + CONFIG.googleMapsApiKey +
                         '&libraries=places&callback=' + callbackName + '&language=zh-CN';
            script.async = true;
            script.defer = true;

            script.onerror = function() {
                delete window[callbackName];
                state.sdkLoadFailed = true;
                reject(new Error('Google Maps SDK 加载失败'));
            };

            // 超时处理
            setTimeout(function() {
                if (!state.sdkLoaded) {
                    state.sdkLoadFailed = true;
                    reject(new Error('Google Maps SDK 加载超时'));
                }
            }, CONFIG.sdkLoadTimeout);

            document.head.appendChild(script);
        });
    }

    /**
     * 初始化地图
     */
    function initMap(center) {
        var mapContainer = document.getElementById('mapContainer');
        var loadingEl = document.getElementById('mapLoading');

        if (!mapContainer || !window.google || !window.google.maps) {
            return;
        }

        // 清空容器
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        // 创建地图 div
        var mapDiv = document.createElement('div');
        mapDiv.id = 'googleMap';
        mapDiv.style.width = '100%';
        mapDiv.style.height = '100%';
        mapContainer.appendChild(mapDiv);

        // 创建地图
        state.map = new google.maps.Map(mapDiv, {
            center: center,
            zoom: CONFIG.defaultZoom,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
            zoomControl: true,
            zoomControlOptions: {
                position: google.maps.ControlPosition.LEFT_BOTTOM
            }
        });

        // 创建标记
        state.marker = new google.maps.Marker({
            position: center,
            map: state.map,
            draggable: true,
            animation: google.maps.Animation.DROP
        });

        // 标记拖动结束事件
        state.marker.addListener('dragend', function() {
            var position = state.marker.getPosition();
            updateSelectedLocation(position.lat(), position.lng());
        });

        // 地图点击事件
        state.map.addListener('click', function(event) {
            state.marker.setPosition(event.latLng);
            updateSelectedLocation(event.latLng.lat(), event.latLng.lng());
        });

        // 初始化搜索自动完成
        initAutocomplete();

        // 设置初始位置
        updateSelectedLocation(center.lat, center.lng);
    }

    /**
     * 初始化地址搜索自动完成
     */
    function initAutocomplete() {
        var searchInput = document.getElementById('mapSearchInput');
        var suggestionsContainer = document.getElementById('mapSearchSuggestions');

        if (!searchInput || !window.google || !window.google.maps || !window.google.maps.places) {
            return;
        }

        // 创建 Autocomplete 服务
        state.autocomplete = new google.maps.places.Autocomplete(searchInput, {
            types: ['geocode', 'establishment']
        });

        // 选择地点事件
        state.autocomplete.addListener('place_changed', function() {
            var place = state.autocomplete.getPlace();

            if (!place.geometry || !place.geometry.location) {
                return;
            }

            // 移动地图和标记
            state.map.setCenter(place.geometry.location);
            state.map.setZoom(CONFIG.defaultZoom);
            state.marker.setPosition(place.geometry.location);

            // 更新选中位置
            updateSelectedLocation(
                place.geometry.location.lat(),
                place.geometry.location.lng()
            );
        });
    }

    /**
     * 更新选中的位置
     */
    function updateSelectedLocation(lat, lng) {
        var addressEl = document.getElementById('selectedAddress');
        var coordsEl = document.getElementById('selectedCoords');
        var confirmBtn = document.getElementById('confirmLocationBtn');

        // 显示坐标
        if (coordsEl) {
            coordsEl.textContent = lat.toFixed(6) + ', ' + lng.toFixed(6);
        }

        // 显示加载状态
        if (addressEl) {
            addressEl.textContent = '正在获取地址...';
        }

        // 调用后端 API 获取地址信息
        var csrfToken = document.querySelector('meta[name="csrf-token"]');
        fetch(CONFIG.reverseGeocodeApi, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken ? csrfToken.getAttribute('content') : ''
            },
            body: JSON.stringify({
                latitude: lat,
                longitude: lng
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(result) {
            if (result.success && result.data) {
                state.selectedLocation = {
                    lat: lat,
                    lng: lng,
                    country: result.data.country,
                    country_name: result.data.country_name,
                    region: result.data.region,
                    city: result.data.city,
                    district: result.data.district,
                    address: result.data.address,
                    formatted_address: result.data.formatted_address
                };

                if (addressEl) {
                    addressEl.textContent = result.data.formatted_address || '未知位置';
                }

                // 启用确认按钮
                if (confirmBtn) {
                    confirmBtn.disabled = false;
                }
            } else {
                if (addressEl) {
                    addressEl.textContent = '无法获取地址信息';
                }
                state.selectedLocation = {
                    lat: lat,
                    lng: lng
                };
            }
        })
        .catch(function(error) {
            console.error('获取地址失败:', error);
            if (addressEl) {
                addressEl.textContent = '获取地址失败';
            }
            state.selectedLocation = {
                lat: lat,
                lng: lng
            };
        });
    }

    /**
     * 获取当前位置
     */
    function getCurrentPosition() {
        return new Promise(function(resolve, reject) {
            if (!navigator.geolocation) {
                reject(new Error('浏览器不支持定位'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                function(position) {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    });
                },
                function(error) {
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        });
    }

    /**
     * 显示错误状态
     */
    function showError(message) {
        var loadingEl = document.getElementById('mapLoading');
        var errorEl = document.getElementById('mapError');
        var errorMsgEl = document.getElementById('mapErrorMessage');

        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        if (errorEl) {
            errorEl.classList.remove('hidden');
        }

        if (errorMsgEl) {
            errorMsgEl.textContent = message;
        }
    }

    /**
     * 打开地图选择器
     */
    async function open(options) {
        options = options || {};
        state.callbacks = {
            onConfirm: options.onConfirm || function() {},
            onCancel: options.onCancel || function() {}
        };

        var modal = document.getElementById('mapPickerModal');
        if (!modal) {
            console.error('地图选择器弹窗未找到');
            return;
        }

        // 获取 API Key
        CONFIG.googleMapsApiKey = document.querySelector('meta[name="google-maps-api-key"]')?.getAttribute('content') || '';

        if (!CONFIG.googleMapsApiKey) {
            console.error('未配置 Google Maps API Key');
            fallbackToSimple();
            return;
        }

        // 显示弹窗
        modal.classList.remove('hidden');
        state.isOpen = true;
        document.body.style.overflow = 'hidden';

        // 重置状态
        var confirmBtn = document.getElementById('confirmLocationBtn');
        if (confirmBtn) {
            confirmBtn.disabled = true;
        }

        var addressEl = document.getElementById('selectedAddress');
        if (addressEl) {
            addressEl.textContent = '请在地图上选择位置';
        }

        var coordsEl = document.getElementById('selectedCoords');
        if (coordsEl) {
            coordsEl.textContent = '';
        }

        try {
            // 获取初始位置
            var initialLocation = options.initialLocation || CONFIG.defaultCenter;

            try {
                var currentPos = await getCurrentPosition();
                initialLocation = currentPos;
            } catch (e) {
                console.log('无法获取当前位置，使用默认位置');
            }

            // 加载 SDK
            await loadGoogleMapsSDK();

            // 初始化地图
            initMap(initialLocation);

        } catch (error) {
            console.error('地图初始化失败:', error);
            showError(error.message || '地图加载失败');
        }
    }

    /**
     * 关闭地图选择器
     */
    function close() {
        var modal = document.getElementById('mapPickerModal');
        if (modal) {
            modal.classList.add('hidden');
        }

        state.isOpen = false;
        document.body.style.overflow = '';

        // 清理地图
        var mapDiv = document.getElementById('googleMap');
        if (mapDiv) {
            mapDiv.remove();
        }

        // 显示加载状态（为下次打开准备）
        var loadingEl = document.getElementById('mapLoading');
        var errorEl = document.getElementById('mapError');
        if (loadingEl) {
            loadingEl.style.display = 'flex';
        }
        if (errorEl) {
            errorEl.classList.add('hidden');
        }

        // 清空搜索框
        var searchInput = document.getElementById('mapSearchInput');
        if (searchInput) {
            searchInput.value = '';
        }

        state.map = null;
        state.marker = null;
        state.selectedLocation = null;
    }

    /**
     * 确认选择
     */
    function confirm() {
        if (state.selectedLocation && state.callbacks.onConfirm) {
            state.callbacks.onConfirm(state.selectedLocation);
        }
        close();
    }

    /**
     * 定位到当前位置
     */
    async function locateCurrent() {
        if (!state.map || !state.marker) {
            return;
        }

        var btn = document.getElementById('locateCurrentBtn');
        if (btn) {
            btn.disabled = true;
        }

        try {
            var position = await getCurrentPosition();
            var latLng = new google.maps.LatLng(position.lat, position.lng);

            state.map.setCenter(latLng);
            state.marker.setPosition(latLng);
            updateSelectedLocation(position.lat, position.lng);

        } catch (error) {
            console.error('定位失败:', error);
            alert('无法获取当前位置');
        } finally {
            if (btn) {
                btn.disabled = false;
            }
        }
    }

    /**
     * 降级到简单定位
     */
    function fallbackToSimple() {
        close();

        // 调用 CustomerForm 的简单定位功能
        if (window.CustomerForm && typeof window.CustomerForm.getLocation === 'function') {
            window.CustomerForm.getLocation();
        } else {
            alert('定位功能不可用');
        }
    }

    // 公开 API
    return {
        open: open,
        close: close,
        confirm: confirm,
        locateCurrent: locateCurrent,
        fallbackToSimple: fallbackToSimple
    };
})();
