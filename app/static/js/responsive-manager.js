/**
 * 响应式管理器 - 统一移动端响应式机制管理
 * 
 * 功能:
 * 1. 统一设备检测标准
 * 2. 实时状态同步
 * 3. 组件状态广播
 * 4. 参数同步管理
 */

class ResponsiveManager {
    // 移动端断点 - 与CSS媒体查询保持一致
    static MOBILE_BREAKPOINT = 768;
    
    // 当前设备状态
    static currentState = null;
    
    // 状态变化监听器
    static listeners = [];
    
    // 组件注册表
    static components = new Map();
    
    // 初始化标志
    static initialized = false;

    /**
     * 初始化响应式管理器
     */
    static init() {
        if (this.initialized) {
            console.warn('📱 ResponsiveManager 已经初始化');
            return;
        }

        console.log('📱 初始化 ResponsiveManager');
        
        // 设置初始状态
        this.currentState = this.isMobile() ? 'mobile' : 'desktop';
        console.log(`📱 初始设备状态: ${this.currentState} (窗口宽度: ${window.innerWidth}px)`);
        
        // 监听窗口大小变化
        this.initResizeListener();
        
        // 监听页面可见性变化（处理设备旋转等情况）
        this.initVisibilityListener();
        
        this.initialized = true;
        
        // 触发初始状态通知
        this.notifyStateChange(null, this.currentState);
    }

    /**
     * 统一的移动端检测方法
     * @returns {boolean} 是否为移动端布局
     */
    static isMobile() {
        return window.innerWidth <= this.MOBILE_BREAKPOINT;
    }

    /**
     * 获取当前设备状态
     * @returns {string} 'mobile' | 'desktop'
     */
    static getDeviceState() {
        return this.currentState;
    }

    /**
     * 检查是否为移动端状态
     * @returns {boolean}
     */
    static isMobileState() {
        return this.currentState === 'mobile';
    }

    /**
     * 初始化窗口大小变化监听
     */
    static initResizeListener() {
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            // 防抖处理，避免频繁触发
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleDeviceChange();
            }, 150);
        });
    }

    /**
     * 初始化页面可见性监听
     */
    static initVisibilityListener() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 页面重新可见时检查设备状态
                setTimeout(() => {
                    this.handleDeviceChange();
                }, 100);
            }
        });
    }

    /**
     * 处理设备状态变化
     */
    static handleDeviceChange() {
        const newState = this.isMobile() ? 'mobile' : 'desktop';
        
        if (newState !== this.currentState) {
            const oldState = this.currentState;
            this.currentState = newState;
            
            console.log(`📱↔️💻 设备状态变化: ${oldState} → ${newState} (窗口宽度: ${window.innerWidth}px)`);
            
            // 更新URL参数
            this.updateUrlParameter(newState);
            
            // 通知所有监听器
            this.notifyStateChange(oldState, newState);
        }
    }

    /**
     * 更新URL中的mobile参数
     * @param {string} deviceState 设备状态
     */
    static updateUrlParameter(deviceState) {
        try {
            const url = new URL(window.location);
            const mobileParam = deviceState === 'mobile' ? 'true' : 'false';
            
            if (url.searchParams.get('mobile') !== mobileParam) {
                url.searchParams.set('mobile', mobileParam);
                window.history.replaceState({}, '', url);
                console.log(`📱 URL参数更新: mobile=${mobileParam}`);
            }
        } catch (error) {
            console.error('❌ 更新URL参数失败:', error);
        }
    }

    /**
     * 通知状态变化
     * @param {string|null} oldState 旧状态
     * @param {string} newState 新状态
     */
    static notifyStateChange(oldState, newState) {
        console.log(`📱 通知状态变化: ${this.listeners.length} 个监听器`);
        
        this.listeners.forEach((listener, index) => {
            try {
                listener(oldState, newState, {
                    isMobile: newState === 'mobile',
                    windowWidth: window.innerWidth,
                    breakpoint: this.MOBILE_BREAKPOINT
                });
            } catch (error) {
                console.error(`❌ 监听器 ${index} 执行失败:`, error);
            }
        });
        
        // 通知注册的组件
        this.notifyComponents(oldState, newState);
    }

    /**
     * 通知注册的组件
     * @param {string|null} oldState 旧状态
     * @param {string} newState 新状态
     */
    static notifyComponents(oldState, newState) {
        this.components.forEach((component, name) => {
            try {
                if (typeof component.onDeviceStateChange === 'function') {
                    component.onDeviceStateChange(oldState, newState);
                }
            } catch (error) {
                console.error(`❌ 组件 ${name} 状态变化处理失败:`, error);
            }
        });
    }

    /**
     * 添加状态变化监听器
     * @param {Function} callback 回调函数 (oldState, newState, context) => void
     * @returns {Function} 取消监听的函数
     */
    static addStateChangeListener(callback) {
        if (typeof callback !== 'function') {
            console.error('❌ 监听器必须是函数');
            return () => {};
        }
        
        this.listeners.push(callback);
        console.log(`📱 添加状态监听器，当前共 ${this.listeners.length} 个`);
        
        // 立即调用一次当前状态
        if (this.currentState) {
            callback(null, this.currentState, {
                isMobile: this.currentState === 'mobile',
                windowWidth: window.innerWidth,
                breakpoint: this.MOBILE_BREAKPOINT
            });
        }
        
        // 返回取消监听的函数
        return () => {
            const index = this.listeners.indexOf(callback);
            if (index > -1) {
                this.listeners.splice(index, 1);
                console.log(`📱 移除状态监听器，当前共 ${this.listeners.length} 个`);
            }
        };
    }

    /**
     * 注册组件
     * @param {string} name 组件名称
     * @param {Object} component 组件对象，需要实现 onDeviceStateChange 方法
     */
    static registerComponent(name, component) {
        this.components.set(name, component);
        console.log(`📱 注册组件: ${name}`);
        
        // 立即通知当前状态
        if (this.currentState && typeof component.onDeviceStateChange === 'function') {
            try {
                component.onDeviceStateChange(null, this.currentState);
            } catch (error) {
                console.error(`❌ 组件 ${name} 初始状态通知失败:`, error);
            }
        }
    }

    /**
     * 注销组件
     * @param {string} name 组件名称
     */
    static unregisterComponent(name) {
        if (this.components.delete(name)) {
            console.log(`📱 注销组件: ${name}`);
        }
    }

    /**
     * 强制检查设备状态
     */
    static forceCheck() {
        console.log('📱 强制检查设备状态');
        this.handleDeviceChange();
    }

    /**
     * 获取调试信息
     * @returns {Object} 调试信息
     */
    static getDebugInfo() {
        return {
            currentState: this.currentState,
            windowWidth: window.innerWidth,
            breakpoint: this.MOBILE_BREAKPOINT,
            isMobile: this.isMobile(),
            listenersCount: this.listeners.length,
            componentsCount: this.components.size,
            initialized: this.initialized
        };
    }
}

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    ResponsiveManager.init();
});

// 导出到全局作用域，供其他脚本使用
window.ResponsiveManager = ResponsiveManager;

console.log('📱 ResponsiveManager 脚本加载完成');