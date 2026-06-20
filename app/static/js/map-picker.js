/**
 * map-picker.js
 * 地图位置选择器（双引擎：高德地图 + Google Maps）
 *
 * 根据 <meta name="map-provider"> 自动选择引擎：
 * - 'amap'  → 高德地图（中国 NAS / SP8D）
 * - 'google' → Google Maps（新加坡 NAS / OVS）
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
    var CONFIG = {
        googleMapsApiKey: '',
        amapJsKey: '',
        amapSecurityKey: '',
        mapProvider: 'google', // 'amap' 或 'google'
        sdkLoadTimeout: 8000,
        defaultCenter: { lat: 31.2304, lng: 121.4737 }, // 默认上海
        defaultZoom: 15,
        reverseGeocodeApi: '/customer/api/geocode/reverse'
    };

    // 状态
    var state = {
        isOpen: false,
        map: null,
        marker: null,
        autocomplete: null,
        selectedLocation: null,
        callbacks: {},
        sdkLoaded: false,
        sdkLoadFailed: false
    };

    // ========== SDK 加载 ==========

    /**
     * 动态加载 Google Maps SDK
     */
    function loadGoogleMapsSDK() {
        return new Promise(function(resolve, reject) {
            if (window.google && window.google.maps) {
                state.sdkLoaded = true;
                resolve();
                return;
            }

            if (document.querySelector('script[src*="maps.googleapis.com"]')) {
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

            var callbackName = 'initGoogleMaps_' + Date.now();
            window[callbackName] = function() {
                delete window[callbackName];
                state.sdkLoaded = true;
                resolve();
            };

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
     * 动态加载高德地图 SDK
     */
    function loadAmapSDK() {
        return new Promise(function(resolve, reject) {
            if (window.AMap) {
                state.sdkLoaded = true;
                resolve();
                return;
            }

            // 设置安全密钥（必须在 SDK 加载前设置）
            window._AMapSecurityConfig = {
                securityJsCode: CONFIG.amapSecurityKey
            };

            if (document.querySelector('script[src*="webapi.amap.com"]')) {
                var checkInterval = setInterval(function() {
                    if (window.AMap) {
                        clearInterval(checkInterval);
                        state.sdkLoaded = true;
                        resolve();
                    }
                }, 100);

                setTimeout(function() {
                    clearInterval(checkInterval);
                    if (!window.AMap) {
                        reject(new Error('高德地图 SDK 加载超时'));
                    }
                }, CONFIG.sdkLoadTimeout);
                return;
            }

            var script = document.createElement('script');
            script.src = 'https://webapi.amap.com/maps?v=2.0&key=' + CONFIG.amapJsKey +
                         '&plugin=AMap.AutoComplete,AMap.PlaceSearch,AMap.Geocoder';
            script.async = true;

            script.onload = function() {
                state.sdkLoaded = true;
                resolve();
            };

            script.onerror = function() {
                state.sdkLoadFailed = true;
                reject(new Error('高德地图 SDK 加载失败'));
            };

            setTimeout(function() {
                if (!state.sdkLoaded) {
                    state.sdkLoadFailed = true;
                    reject(new Error('高德地图 SDK 加载超时'));
                }
            }, CONFIG.sdkLoadTimeout);

            document.head.appendChild(script);
        });
    }

    // ========== Google Maps 引擎 ==========

    function initGoogleMap(center) {
        var mapContainer = document.getElementById('mapContainer');
        var loadingEl = document.getElementById('mapLoading');

        if (!mapContainer || !window.google || !window.google.maps) {
            return;
        }

        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        var mapDiv = document.createElement('div');
        mapDiv.id = 'googleMap';
        mapDiv.style.width = '100%';
        mapDiv.style.height = '100%';
        mapContainer.appendChild(mapDiv);

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

        state.marker = new google.maps.Marker({
            position: center,
            map: state.map,
            draggable: true,
            animation: google.maps.Animation.DROP
        });

        state.marker.addListener('dragend', function() {
            var position = state.marker.getPosition();
            updateSelectedLocation(position.lat(), position.lng());
        });

        state.map.addListener('click', function(event) {
            state.marker.setPosition(event.latLng);
            updateSelectedLocation(event.latLng.lat(), event.latLng.lng());
        });

        initGoogleAutocomplete();
        updateSelectedLocation(center.lat, center.lng);
    }

    function initGoogleAutocomplete() {
        var searchInput = document.getElementById('mapSearchInput');

        if (!searchInput || !window.google || !window.google.maps || !window.google.maps.places) {
            return;
        }

        state.autocomplete = new google.maps.places.Autocomplete(searchInput, {
            types: ['geocode', 'establishment']
        });

        state.autocomplete.addListener('place_changed', function() {
            var place = state.autocomplete.getPlace();

            if (!place.geometry || !place.geometry.location) {
                return;
            }

            state.map.setCenter(place.geometry.location);
            state.map.setZoom(CONFIG.defaultZoom);
            state.marker.setPosition(place.geometry.location);

            updateSelectedLocation(
                place.geometry.location.lat(),
                place.geometry.location.lng()
            );
        });
    }

    // ========== 高德地图引擎 ==========

    function initAmapMap(center) {
        var mapContainer = document.getElementById('mapContainer');
        var loadingEl = document.getElementById('mapLoading');

        if (!mapContainer || !window.AMap) {
            return;
        }

        if (loadingEl) {
            loadingEl.style.display = 'none';
        }

        var mapDiv = document.createElement('div');
        mapDiv.id = 'amapContainer';
        mapDiv.style.width = '100%';
        mapDiv.style.height = '100%';
        mapContainer.appendChild(mapDiv);

        // 高德坐标顺序：[lng, lat]
        state.map = new AMap.Map('amapContainer', {
            center: [center.lng, center.lat],
            zoom: CONFIG.defaultZoom,
            resizeEnable: true
        });

        state.marker = new AMap.Marker({
            position: [center.lng, center.lat],
            draggable: true,
            map: state.map
        });

        // 标记拖动结束
        state.marker.on('dragend', function(e) {
            var pos = state.marker.getPosition();
            updateSelectedLocation(pos.getLat(), pos.getLng());
        });

        // 地图点击
        state.map.on('click', function(e) {
            state.marker.setPosition(e.lnglat);
            updateSelectedLocation(e.lnglat.getLat(), e.lnglat.getLng());
        });

        initAmapAutocomplete();
        updateSelectedLocation(center.lat, center.lng);

        // 如果 open() 时传了 initialQuery — 只预填搜索框 + 触发 AutoComplete 下拉,
        // 让用户主动从下拉选择(避免 PlaceSearch 拿到无关首条结果导致误定位)
        if (state.pendingInitialQuery) {
            var q = state.pendingInitialQuery;
            state.pendingInitialQuery = null;
            var input = document.getElementById('mapSearchInput');
            if (input) {
                input.value = q;
                input.focus();
                // 模拟 input 事件触发 AMap.AutoComplete 弹下拉
                input.dispatchEvent(new Event('input', { bubbles: true }));
                // 部分版本 AutoComplete 需要 keyup 才触发
                try {
                    input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: q.slice(-1) }));
                } catch (e) {}
            }
        }
    }

    function _toastNoMatch(msg) {
        if (window.ATToast) ATToast.warn('地图定位', msg);
        else console.warn('[MapPicker]', msg);
    }

    function initAmapAutocomplete() {
        var searchInput = document.getElementById('mapSearchInput');
        if (!searchInput || !window.AMap) {
            return;
        }

        var autoComplete = new AMap.AutoComplete({
            input: 'mapSearchInput'
        });

        autoComplete.on('select', function(e) {
            if (!e || !e.poi) return;

            // 情况 1:POI 自带 location(地标性建筑)→ 直接居中
            if (e.poi.location) {
                var lnglat = e.poi.location;
                state.map.setCenter(lnglat);
                state.map.setZoom(CONFIG.defaultZoom);
                state.marker.setPosition(lnglat);
                updateSelectedLocation(lnglat.getLat(), lnglat.getLng());
                return;
            }

            // 情况 2:用户选的 POI 无 location → 高德没该 POI 精确坐标
            // 不做 fallback 猜测(容易拿无关结果),直接提示让用户调整
            _toastNoMatch('“' + (e.poi.name || '') + '” 在高德无精确坐标,请微调搜索词或在地图上手动点选位置');
        });
    }

    // ========== 公共方法 ==========

    /**
     * 更新选中的位置
     */
    function updateSelectedLocation(lat, lng) {
        var addressEl = document.getElementById('selectedAddress');
        var coordsEl = document.getElementById('selectedCoords');
        var confirmBtn = document.getElementById('confirmLocationBtn');

        if (coordsEl) {
            coordsEl.textContent = lat.toFixed(6) + ', ' + lng.toFixed(6);
        }

        if (addressEl) {
            addressEl.textContent = '正在获取地址...';
        }

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

        // 从 meta 标签读取配置
        CONFIG.mapProvider = document.querySelector('meta[name="map-provider"]')?.getAttribute('content') || 'google';
        CONFIG.googleMapsApiKey = document.querySelector('meta[name="google-maps-api-key"]')?.getAttribute('content') || '';
        CONFIG.amapJsKey = document.querySelector('meta[name="amap-js-key"]')?.getAttribute('content') || '';
        CONFIG.amapSecurityKey = document.querySelector('meta[name="amap-security-key"]')?.getAttribute('content') || '';

        // 验证配置
        if (CONFIG.mapProvider === 'amap' && !CONFIG.amapJsKey) {
            console.error('未配置高德地图 API Key');
            fallbackToSimple();
            return;
        }
        if (CONFIG.mapProvider === 'google' && !CONFIG.googleMapsApiKey) {
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

        // 预填搜索框 + 自动触发查询(caller 传 options.initialQuery)
        var initialQuery = (options.initialQuery || '').trim();
        var searchInputEl = document.getElementById('mapSearchInput');
        if (searchInputEl) searchInputEl.value = initialQuery;
        if (initialQuery) {
            // 延后执行让 SDK 完成 init,然后用 PlaceSearch 直接定位首条结果
            state.pendingInitialQuery = initialQuery;
        } else {
            state.pendingInitialQuery = null;
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

            // 根据引擎加载 SDK 并初始化
            if (CONFIG.mapProvider === 'amap') {
                await loadAmapSDK();
                initAmapMap(initialLocation);
            } else {
                await loadGoogleMapsSDK();
                initGoogleMap(initialLocation);
            }

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

        // 清理地图容器
        var googleMapDiv = document.getElementById('googleMap');
        if (googleMapDiv) {
            googleMapDiv.remove();
        }
        var amapDiv = document.getElementById('amapContainer');
        if (amapDiv) {
            amapDiv.remove();
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

            if (CONFIG.mapProvider === 'amap') {
                var lnglat = [position.lng, position.lat];
                state.map.setCenter(lnglat);
                state.marker.setPosition(lnglat);
            } else {
                var latLng = new google.maps.LatLng(position.lat, position.lng);
                state.map.setCenter(latLng);
                state.marker.setPosition(latLng);
            }

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
