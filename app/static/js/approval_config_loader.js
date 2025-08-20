/**
 * 审批配置性能优化加载器
 * 实现按需加载、懒初始化和性能优化策略
 */

class ApprovalConfigLoader {
  constructor() {
    this.modules = new Map();
    this.loadPromises = new Map();
    this.initialized = false;
    
    // 性能监控
    this.performanceMetrics = {
      loadStart: 0,
      loadEnd: 0,
      modulesLoaded: 0,
      totalModules: 4
    };
  }
  
  /**
   * 初始化加载器
   */
  async init() {
    if (this.initialized) return;
    
    console.log('🚀 ApprovalConfigLoader 开始初始化');
    this.performanceMetrics.loadStart = performance.now();
    
    // 检查必要的全局配置
    if (!window.ApprovalConfig) {
      console.error('❌ 缺少 ApprovalConfig 全局配置');
      return;
    }
    
    // 优先加载核心模块
    await this.loadCoreModules();
    
    // 根据页面功能按需加载其他模块
    await this.loadFeatureModules();
    
    this.initialized = true;
    this.performanceMetrics.loadEnd = performance.now();
    
    const loadTime = this.performanceMetrics.loadEnd - this.performanceMetrics.loadStart;
    console.log(`🎉 ApprovalConfigLoader 初始化完成 (${loadTime.toFixed(2)}ms)`);
  }
  
  /**
   * 加载核心模块
   */
  async loadCoreModules() {
    const coreModules = [
      { name: 'main', priority: 1 },
    ];
    
    for (const module of coreModules) {
      await this.loadModule(module.name);
    }
  }
  
  /**
   * 根据页面特征按需加载功能模块
   */
  async loadFeatureModules() {
    const features = this.detectPageFeatures();
    const loadPromises = [];
    
    // 并行加载需要的模块
    if (features.hasBranchSteps) {
      loadPromises.push(this.loadModule('branch'));
    }
    
    if (features.hasTemplateList) {
      loadPromises.push(this.loadModule('template'));
    }
    
    if (features.hasStepForms) {
      loadPromises.push(this.loadModule('form'));
    }
    
    // 等待所有功能模块加载完成
    await Promise.all(loadPromises);
  }
  
  /**
   * 检测页面功能特征
   */
  detectPageFeatures() {
    return {
      hasBranchSteps: document.querySelector('.branch-conditions-container, .step-branch') !== null,
      hasTemplateList: document.querySelector('#templateList, .template-list-table') !== null,
      hasStepForms: document.querySelector('#addStepModal, #editStepModal') !== null,
      hasStepList: document.querySelector('#stepList, .step-list') !== null
    };
  }
  
  /**
   * 加载单个模块
   */
  async loadModule(moduleName) {
    if (this.modules.has(moduleName)) {
      return this.modules.get(moduleName);
    }
    
    // 避免重复加载
    if (this.loadPromises.has(moduleName)) {
      return this.loadPromises.get(moduleName);
    }
    
    console.log(`📦 加载模块: ${moduleName}`);
    
    const loadPromise = this.loadModuleScript(moduleName);
    this.loadPromises.set(moduleName, loadPromise);
    
    try {
      const module = await loadPromise;
      this.modules.set(moduleName, module);
      this.performanceMetrics.modulesLoaded++;
      
      // 初始化模块
      await this.initializeModule(moduleName, module);
      
      console.log(`✅ 模块 ${moduleName} 加载完成`);
      return module;
    } catch (error) {
      console.error(`❌ 模块 ${moduleName} 加载失败:`, error);
      this.loadPromises.delete(moduleName);
      throw error;
    }
  }
  
  /**
   * 加载模块脚本
   */
  async loadModuleScript(moduleName) {
    return new Promise((resolve, reject) => {
      // 检查模块是否已经存在（模块可能已经同步加载）
      const globalName = `ApprovalConfig${this.capitalize(moduleName)}`;
      if (window[globalName]) {
        console.log(`📦 模块 ${moduleName} 已存在，跳过加载`);
        resolve(window[globalName]);
        return;
      }
      
      const script = document.createElement('script');
      script.src = `/static/js/modules/approval_config_${moduleName}.js`;
      script.async = true;
      
      script.onload = () => {
        const module = window[globalName];
        if (module) {
          resolve(module);
        } else {
          reject(new Error(`模块 ${globalName} 未正确导出`));
        }
      };
      
      script.onerror = () => {
        reject(new Error(`无法加载脚本 ${script.src}`));
      };
      
      document.head.appendChild(script);
    });
  }
  
  /**
   * 初始化模块
   */
  async initializeModule(moduleName, module) {
    const initDelay = this.getInitDelay(moduleName);
    
    return new Promise((resolve) => {
      setTimeout(() => {
        try {
          if (module && typeof module.init === 'function') {
            if (moduleName === 'main') {
              module.init(window.ApprovalConfig);
            } else {
              module.init();
            }
          }
          resolve();
        } catch (error) {
          console.error(`❌ 模块 ${moduleName} 初始化失败:`, error);
          resolve(); // 不阻塞其他模块
        }
      }, initDelay);
    });
  }
  
  /**
   * 获取模块初始化延迟
   */
  getInitDelay(moduleName) {
    const delays = {
      main: 50,
      branch: 100,
      template: 150,
      form: 200
    };
    return delays[moduleName] || 100;
  }
  
  /**
   * 字符串首字母大写
   */
  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
  
  /**
   * 获取性能指标
   */
  getPerformanceMetrics() {
    const metrics = { ...this.performanceMetrics };
    if (metrics.loadEnd && metrics.loadStart) {
      metrics.totalLoadTime = metrics.loadEnd - metrics.loadStart;
      metrics.averageModuleLoadTime = metrics.totalLoadTime / metrics.modulesLoaded;
    }
    return metrics;
  }
  
  /**
   * 预加载模块（用于提升后续页面性能）
   */
  async preloadModule(moduleName) {
    if (this.modules.has(moduleName) || this.loadPromises.has(moduleName)) {
      return;
    }
    
    console.log(`🔮 预加载模块: ${moduleName}`);
    
    // 在空闲时间预加载
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        this.loadModule(moduleName).catch(() => {
          // 预加载失败不影响正常功能
        });
      });
    } else {
      setTimeout(() => {
        this.loadModule(moduleName).catch(() => {});
      }, 1000);
    }
  }
  
  /**
   * 清理资源
   */
  cleanup() {
    this.modules.clear();
    this.loadPromises.clear();
    this.initialized = false;
    console.log('🧹 ApprovalConfigLoader 已清理');
  }
}

// 创建全局实例
window.ApprovalConfigLoader = new ApprovalConfigLoader();

// 自动初始化
document.addEventListener('DOMContentLoaded', function() {
  // 延迟初始化，让页面先渲染
  setTimeout(() => {
    window.ApprovalConfigLoader.init().catch(error => {
      console.error('❌ ApprovalConfigLoader 初始化失败:', error);
    });
  }, 100);
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
  if (window.ApprovalConfigLoader) {
    window.ApprovalConfigLoader.cleanup();
  }
});

// 性能监控（开发环境）
if (window.location.hostname === 'localhost' || window.location.hostname.includes('dev')) {
  window.addEventListener('load', function() {
    setTimeout(() => {
      if (window.ApprovalConfigLoader) {
        const metrics = window.ApprovalConfigLoader.getPerformanceMetrics();
        console.table(metrics);
      }
    }, 2000);
  });
}

console.log('📦 approval_config_loader.js 已加载');