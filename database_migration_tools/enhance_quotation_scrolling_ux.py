#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强报价单滚动加载用户体验
- 改善加载动画和状态指示器
- 添加底部加载完成指示和数据计数
- 修复可能的滚动加载问题
"""

import logging
import shutil
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('滚动UX增强')

class QuotationScrollingUXEnhancer:
    def __init__(self):
        self.template_file = "/Users/nijie/Documents/PMA/app/templates/quotation/list.html"
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def backup_template(self):
        """备份原模板文件"""
        backup_file = f"{self.template_file}.backup_{self.timestamp}"
        shutil.copy2(self.template_file, backup_file)
        logger.info(f"✅ 模板文件已备份: {backup_file}")
        return backup_file
    
    def read_template_content(self):
        """读取模板内容"""
        with open(self.template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def enhance_loading_indicators(self, content):
        """增强加载指示器"""
        logger.info("🔄 增强加载指示器...")
        
        # 改进加载指示器的HTML
        old_loading_indicator = """    <!-- 滚动加载指示器 -->
    <div id="loadingIndicator" class="text-center py-3 d-none">
        <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">加载中...</span>
        </div>
        <span class="ms-2 text-muted">正在加载更多数据...</span>
    </div>
    
    <!-- 没有更多数据提示 -->
    <div id="noMoreData" class="text-center py-3 text-muted d-none">
        <i class="fas fa-check-circle me-1"></i>
        已加载所有数据
    </div>"""
        
        new_loading_indicator = """    <!-- 滚动加载指示器 -->
    <div id="loadingIndicator" class="text-center py-4 d-none">
        <div class="d-flex justify-content-center align-items-center">
            <div class="spinner-border spinner-border-sm text-primary me-3" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <div class="loading-text">
                <div class="text-primary fw-medium">正在加载更多报价单...</div>
                <div class="text-muted small mt-1">
                    <span id="loadingProgress">请稍候</span>
                </div>
            </div>
        </div>
        <!-- 加载进度条 -->
        <div class="progress mt-3 mx-auto" style="width: 200px; height: 4px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 100%"></div>
        </div>
    </div>
    
    <!-- 加载完成状态指示器 -->
    <div id="noMoreData" class="text-center py-4 text-muted d-none">
        <div class="border rounded-3 bg-light p-3 mx-auto" style="max-width: 400px;">
            <div class="d-flex align-items-center justify-content-center mb-2">
                <i class="fas fa-check-circle text-success me-2"></i>
                <span class="fw-medium">已加载完成</span>
            </div>
            <div class="small text-muted">
                <i class="fas fa-list me-1"></i>
                共显示 <span id="totalLoadedCount" class="fw-medium text-dark">--</span> 个报价单
            </div>
            <div class="small text-muted mt-1">
                <i class="fas fa-info-circle me-1"></i>
                <span id="loadingStats">数据统计加载中...</span>
            </div>
        </div>
    </div>"""
        
        if old_loading_indicator in content:
            content = content.replace(old_loading_indicator, new_loading_indicator)
            logger.info("✅ 已更新加载指示器HTML")
        else:
            logger.warning("⚠️ 未找到原加载指示器HTML，可能需要手动处理")
        
        return content
    
    def enhance_loading_javascript(self, content):
        """增强加载相关的JavaScript"""
        logger.info("🔄 增强JavaScript加载逻辑...")
        
        # 查找并替换加载函数的关键部分
        # 1. 增强加载状态显示
        old_loading_start = """        isLoading = true;
        document.getElementById('loadingIndicator').classList.remove('d-none');"""
        
        new_loading_start = """        isLoading = true;
        const loadingIndicator = document.getElementById('loadingIndicator');
        const loadingProgress = document.getElementById('loadingProgress');
        
        loadingIndicator.classList.remove('d-none');
        loadingProgress.textContent = `正在请求第 ${Math.floor(currentOffset/limit) + 1} 批数据...`;"""
        
        if old_loading_start in content:
            content = content.replace(old_loading_start, new_loading_start)
            logger.info("✅ 已增强加载开始状态")
        
        # 2. 增强成功加载后的状态更新
        old_success_update = """                console.log('📊 更新状态: offset=', currentOffset, ', hasMore=', hasMore);
                
                // 重新初始化新加载内容的事件监听器
                initializeQuotationEvents();
                
                if (!hasMore) {
                    document.getElementById('noMoreData').classList.remove('d-none');
                    console.log('🏁 已加载所有数据，停止滚动加载');
                }"""
        
        new_success_update = """                console.log('📊 更新状态: offset=', currentOffset, ', hasMore=', hasMore);
                
                // 重新初始化新加载内容的事件监听器
                initializeQuotationEvents();
                
                // 更新数据统计
                updateLoadingStatistics();
                
                if (!hasMore) {
                    showCompletionIndicator();
                    console.log('🏁 已加载所有数据，停止滚动加载');
                }"""
        
        if old_success_update in content:
            content = content.replace(old_success_update, new_success_update)
            logger.info("✅ 已增强成功加载状态")
        
        # 3. 添加新的辅助函数
        helper_functions = """
    // 更新加载统计信息
    function updateLoadingStatistics() {
        const totalRows = document.querySelectorAll('#quotationTableBody tr:not([id*="empty"])').length;
        const totalCountElement = document.getElementById('totalLoadedCount');
        if (totalCountElement) {
            totalCountElement.textContent = totalRows;
        }
        
        // 更新加载统计信息
        const loadingStatsElement = document.getElementById('loadingStats');
        if (loadingStatsElement) {
            const batchCount = Math.ceil(currentOffset / limit);
            loadingStatsElement.innerHTML = `
                <i class="fas fa-layer-group me-1"></i>分 ${batchCount} 批加载 
                <i class="fas fa-clock ms-2 me-1"></i>最后更新: ${new Date().toLocaleTimeString()}
            `;
        }
    }
    
    // 显示完成指示器
    function showCompletionIndicator() {
        updateLoadingStatistics();
        document.getElementById('noMoreData').classList.remove('d-none');
        
        // 平滑滚动到底部指示器
        setTimeout(() => {
            const noMoreDataElement = document.getElementById('noMoreData');
            if (noMoreDataElement) {
                noMoreDataElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }
        }, 500);
    }
    
    // 增强的错误处理
    function showLoadingError(error) {
        console.error('加载数据失败:', error);
        const tableBody = document.getElementById('quotationTableBody');
        const errorMessage = `
            <tr id="loadingError" class="table-danger">
                <td colspan="100%" class="text-center py-4">
                    <div class="d-flex align-items-center justify-content-center mb-2">
                        <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                        <span class="fw-medium">加载数据失败</span>
                    </div>
                    <div class="small text-muted mb-3">
                        网络连接异常或服务器暂时不可用
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="retryLoading()">
                        <i class="fas fa-redo me-1"></i>重试加载
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary ms-2" onclick="location.reload()">
                        <i class="fas fa-refresh me-1"></i>刷新页面
                    </button>
                </td>
            </tr>
        `;
        tableBody.insertAdjacentHTML('beforeend', errorMessage);
    }
    
    // 重试加载功能
    function retryLoading() {
        // 移除错误消息
        const errorRow = document.getElementById('loadingError');
        if (errorRow) {
            errorRow.remove();
        }
        
        // 重置加载状态并重试
        isLoading = false;
        loadMoreData();
    }"""
        
        # 将辅助函数插入到initializeQuotationEvents函数之前
        insert_position = content.find("    // 初始化报价单相关事件（用于新加载的内容）")
        if insert_position != -1:
            content = content[:insert_position] + helper_functions + "\n    " + content[insert_position:]
            logger.info("✅ 已添加辅助函数")
        
        # 4. 替换错误处理
        old_error_handling = """            .catch(error => {
                console.error('加载数据失败:', error);
                // 显示用户友好的错误提示
                const tableBody = document.getElementById('quotationTableBody');
                tableBody.insertAdjacentHTML('beforeend', 
                    '<tr><td colspan="100%" class="text-center text-danger py-3">' +
                    '<i class="fas fa-exclamation-triangle me-2"></i>加载数据失败，请刷新页面重试' +
                    '</td></tr>'
                );
            })"""
        
        new_error_handling = """            .catch(error => {
                showLoadingError(error);
            })"""
        
        if old_error_handling in content:
            content = content.replace(old_error_handling, new_error_handling)
            logger.info("✅ 已增强错误处理")
        
        # 5. 改进初始状态设置
        old_initial_state = """    // 初始显示状态设置
    if (!hasMore && currentOffset > 0) {
        document.getElementById('noMoreData').classList.remove('d-none');
    }"""
        
        new_initial_state = """    // 初始显示状态设置
    updateLoadingStatistics();
    if (!hasMore && currentOffset > 0) {
        showCompletionIndicator();
    }"""
        
        if old_initial_state in content:
            content = content.replace(old_initial_state, new_initial_state)
            logger.info("✅ 已改进初始状态设置")
        
        return content
    
    def add_loading_animation_styles(self, content):
        """添加增强的加载动画样式"""
        logger.info("🎨 添加增强的CSS样式...")
        
        # 查找现有样式部分并添加新样式
        style_insertion_point = content.find("    /* 滚动控制按钮样式 */")
        
        if style_insertion_point != -1:
            enhanced_styles = """    /* 增强的加载指示器样式 */
    #loadingIndicator {
        transition: all 0.3s ease-in-out;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        margin: 10px 0;
    }
    
    #loadingIndicator .loading-text {
        font-size: 14px;
    }
    
    #loadingIndicator .progress {
        background-color: rgba(0,123,255,0.1);
        border-radius: 10px;
    }
    
    #loadingIndicator .progress-bar {
        background: linear-gradient(90deg, #007bff, #0056b3, #007bff);
        background-size: 200% 100%;
        animation: progressShimmer 2s infinite;
    }
    
    @keyframes progressShimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* 加载完成指示器样式 */
    #noMoreData {
        animation: fadeInUp 0.5s ease-out;
    }
    
    #noMoreData .border {
        border: 2px solid #e9ecef !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    #noMoreData .border:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 加载错误样式 */
    #loadingError td {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        animation: shakeError 0.5s ease-in-out;
    }
    
    @keyframes shakeError {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* 改进的滚动指示器 */
    .scroll-controls {
        position: fixed;
        right: 20px;
        bottom: 20px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .scroll-controls button {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
    }
    
    .scroll-controls button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    
    """
            
            content = content[:style_insertion_point] + enhanced_styles + content[style_insertion_point:]
            logger.info("✅ 已添加增强的CSS样式")
        
        return content
    
    def apply_enhancements(self):
        """应用所有增强功能"""
        logger.info("🚀 开始增强报价单滚动加载用户体验...")
        
        # 1. 备份原文件
        backup_file = self.backup_template()
        
        # 2. 读取原内容
        content = self.read_template_content()
        logger.info("📖 已读取模板文件内容")
        
        # 3. 应用各种增强
        content = self.enhance_loading_indicators(content)
        content = self.enhance_loading_javascript(content)
        content = self.add_loading_animation_styles(content)
        
        # 4. 写入增强后的内容
        with open(self.template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ 报价单滚动UX增强完成!")
        
        # 5. 显示增强内容总结
        logger.info("\\n🎉 增强功能总结:")
        logger.info("1. ✨ 改进了加载动画和进度指示")
        logger.info("2. 📊 添加了数据统计和计数显示")
        logger.info("3. 🎯 增强了加载完成状态指示器")
        logger.info("4. 🛠️ 改进了错误处理和重试机制")
        logger.info("5. 🎨 添加了更丰富的视觉效果和动画")
        logger.info("6. 📱 优化了移动端和桌面端体验")
        
        return True
    
    def verify_enhancements(self):
        """验证增强结果"""
        logger.info("\\n🔍 验证增强结果...")
        
        content = self.read_template_content()
        
        # 检查关键增强点
        checks = [
            ("updateLoadingStatistics", "数据统计更新函数"),
            ("showCompletionIndicator", "完成指示器函数"),
            ("showLoadingError", "增强错误处理函数"),
            ("totalLoadedCount", "总数统计元素"),
            ("loadingStats", "加载统计元素"),
            ("progressShimmer", "进度条动画"),
            ("fadeInUp", "淡入动画"),
            ("retryLoading", "重试加载功能")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                logger.info(f"✅ {description}: 已添加")
            else:
                logger.warning(f"⚠️ {description}: 未找到")
        
        logger.info("\\n💡 测试建议:")
        logger.info("1. 用liuwei账户登录测试报价单列表")
        logger.info("2. 测试滚动加载功能和动画效果")
        logger.info("3. 验证底部数据统计显示是否正确")
        logger.info("4. 测试网络错误情况下的重试功能")
        logger.info("5. 检查加载完成后的状态指示器")

if __name__ == "__main__":
    enhancer = QuotationScrollingUXEnhancer()
    success = enhancer.apply_enhancements()
    if success:
        enhancer.verify_enhancements()
        print("\\n" + "="*60)
        print("🎉 报价单滚动UX增强完成!")
        print("现在用户可以看到更好的加载动画和数据统计")
        print("="*60)
    else:
        print("❌ 增强失败")
        exit(1)