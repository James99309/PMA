/**
 * 通用项目搜索组件
 * 支持关键词搜索，权限过滤，分组显示（可编辑、只读、锁定）
 * 
 * @author Claude AI
 * @version 1.0.0
 */

class ProjectSearchComponent {
    constructor(config, container) {
        this.config = this.mergeConfig(config);
        this.container = container;
        this.selectedProject = null;
        this.searchTimeout = null;
        this.isSearching = false;
        this.currentResults = [];
        this.activeIndex = -1;
        
        this.init();
    }
    
    /**
     * 合并默认配置和用户配置
     */
    mergeConfig(config) {
        const defaultConfig = {
            // 基础配置
            input_id: 'projectSearch',
            input_name: 'project_search',
            dropdown_id: 'projectDropdown',
            clear_button_id: 'clearProject',
            selected_info_id: 'selectedProjectInfo',
            project_id_field: 'projectId',
            project_id_name: 'project_id',
            data_element_id: 'projectSearchConfig',
            
            // 显示配置
            label: '关联项目',
            placeholder: '输入项目名称或授权码进行搜索...',
            show_component_badge: true,
            
            // API端点配置
            api_endpoints: {
                search: '/api/v1/search/projects',
                project_detail: '/project/api/project/{id}'
            },
            
            // 搜索配置
            search_config: {
                min_length: 1,
                delay: 300,
                limit: 10,
                include_auth_code: true
            },
            
            // 权限配置
            permission_config: {
                check_edit: true,
                check_view: true,
                show_locked: true
            },
            
            // 显示配置
            display_config: {
                show_owner: true,
                show_type: true,
                show_stage: true,
                show_auth_code: true
            },
            
            // 隐藏字段配置
            hidden_fields: {
                project_stage: 'projectStage',
                project_type: 'projectType'
            },
            
            // 验证配置
            validation: {
                required: true,
                validate_on_submit: true
            }
        };
        
        return this.deepMerge(defaultConfig, config || {});
    }
    
    /**
     * 深度合并配置对象
     */
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                    result[key] = this.deepMerge(target[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }
        
        return result;
    }
    
    /**
     * 初始化组件
     */
    init() {
        this.validateConfig();
        this.initializeElements();
        this.bindEvents();
        
        console.log('✅ 项目搭索组件初始化完成');
    }
    
    /**
     * 验证配置
     */
    validateConfig() {
        const required = ['input_id', 'dropdown_id'];
        
        required.forEach(key => {
            if (!this.config[key]) {
                throw new Error(`ProjectSearchComponent: Missing required config: ${key}`);
            }
        });
        
        // 验证输入框元素是否存在
        if (!this.container.querySelector(`#${this.config.input_id}`)) {
            throw new Error(`ProjectSearchComponent: Input element not found: #${this.config.input_id}`);
        }
    }
    
    /**
     * 初始化元素引用
     */
    initializeElements() {
        
        this.input = this.container.querySelector(`#${this.config.input_id}`);
        
        this.dropdown = this.container.querySelector(`#${this.config.dropdown_id}`);
        
        this.clearBtn = this.container.querySelector(`#${this.config.clear_button_id}`);
        // 移除 selectedInfo 引用，不再显示选中项目信息
        this.projectIdField = this.container.querySelector(`#${this.config.project_id_field}`);
        
        // 检查必需元素
        if (!this.input) {
            console.error(`❌ 未找到输入框元素: #${this.config.input_id}`);
            throw new Error(`输入框元素未找到: #${this.config.input_id}`);
        }
        
        if (!this.dropdown) {
            console.error(`❌ 未找到下拉框元素: #${this.config.dropdown_id}`);
            throw new Error(`下拉框元素未找到: #${this.config.dropdown_id}`);
        }
        
        // 结果容器
        this.loadingElement = this.dropdown.querySelector('.dropdown-loading');
        this.resultsElement = this.dropdown.querySelector('.dropdown-results');
        this.noResultsElement = this.dropdown.querySelector('.no-results');
        
        // 项目列表容器
        this.projectList = this.dropdown.querySelector('.project-list');
        
        console.log('✅ 元素引用初始化完成');
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 输入框事件
        this.bindInputEvents();
        
        // 清除按钮事件
        this.bindClearEvents();
        
        // 下拉菜单事件
        this.bindDropdownEvents();
        
        // 键盘导航事件
        this.bindKeyboardEvents();
        
        // 外部点击事件
        this.bindOutsideClickEvents();
    }
    
    /**
     * 绑定输入框事件
     */
    bindInputEvents() {
        // 输入事件
        this.input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // 清除之前的搜索定时器
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            // 如果输入为空，清除选择（但不隐藏清除按钮，因为可能还有选中项目）
            if (!query && this.selectedProject) {
                // 输入框清空但还有选中项目时，清除选择
                this.clearSelection();
                this.hideDropdown();
                return;
            } else if (!query) {
                // 输入框清空且没有选中项目时，只隐藏下拉菜单
                this.hideDropdown();
                return;
            }
            
            // 如果输入长度不足，不进行搜索
            if (query.length < this.config.search_config.min_length) {
                this.hideDropdown();
                return;
            }
            
            // 设置搜索延迟
            this.searchTimeout = setTimeout(() => {
                this.searchProjects(query);
            }, this.config.search_config.delay);
        });
        
        // 获得焦点事件
        this.input.addEventListener('focus', () => {
            const query = this.input.value.trim();
            if (query.length >= this.config.search_config.min_length) {
                this.searchProjects(query);
            }
        });
        
        // 失去焦点事件（延迟隐藏，允许点击下拉项）
        this.input.addEventListener('blur', () => {
            setTimeout(() => {
                this.hideDropdown();
            }, 200);
        });
    }
    
    /**
     * 绑定清除按钮事件
     */
    bindClearEvents() {
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => {
                this.clearSelection();
                this.input.focus();
            });
        }
        
        // 移除了已选中项目信息区域的清除按钮处理
    }
    
    /**
     * 绑定下拉菜单事件
     */
    bindDropdownEvents() {
        // 使用事件委托处理项目项点击
        this.dropdown.addEventListener('click', (e) => {
            const projectItem = e.target.closest('.project-item');
            if (projectItem && !projectItem.classList.contains('locked')) {
                const projectData = JSON.parse(projectItem.dataset.project);
                this.selectProject(projectData);
            }
        });
        
        // 鼠标悬停高亮
        this.dropdown.addEventListener('mouseover', (e) => {
            const projectItem = e.target.closest('.project-item');
            if (projectItem && !projectItem.classList.contains('locked')) {
                this.highlightItem(projectItem);
            }
        });
    }
    
    /**
     * 绑定键盘导航事件
     */
    bindKeyboardEvents() {
        this.input.addEventListener('keydown', (e) => {
            if (!this.dropdown.style.display || this.dropdown.style.display === 'none') {
                return;
            }
            
            const items = this.dropdown.querySelectorAll('.project-item:not(.locked)');
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.activeIndex = Math.min(this.activeIndex + 1, items.length - 1);
                    this.highlightActiveItem(items);
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    this.activeIndex = Math.max(this.activeIndex - 1, -1);
                    this.highlightActiveItem(items);
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    if (this.activeIndex >= 0 && items[this.activeIndex]) {
                        const projectData = JSON.parse(items[this.activeIndex].dataset.project);
                        this.selectProject(projectData);
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    this.hideDropdown();
                    break;
            }
        });
    }
    
    /**
     * 绑定外部点击事件
     */
    bindOutsideClickEvents() {
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    /**
     * 搜索项目
     */
    async searchProjects(query) {
        if (this.isSearching) {
            return;
        }
        
        this.isSearching = true;
        this.showLoading();
        
        try {
            const response = await fetch(`${this.config.api_endpoints.search}?q=${encodeURIComponent(query)}&limit=${this.config.search_config.limit}`);
            const result = await response.json();
            
            if (result.success && result.data) {
                this.currentResults = result.data;
                this.showResults(result.data);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('搜索项目失败:', error);
            this.showError('搜索失败，请重试');
        } finally {
            this.isSearching = false;
            this.hideLoading();
        }
    }
    
    /**
     * 显示搜索结果
     */
    showResults(projects) {
        // 过滤项目：如果设置了不显示锁定项目，则过滤掉锁定项目
        let filteredProjects = projects;
        if (!this.config.permission_config.show_locked) {
            filteredProjects = projects.filter(project => {
                const permissionType = this.getProjectPermissionType(project);
                return permissionType !== 'locked';
            });
        }
        
        // 按权限排序：可编辑 > 只读 > 锁定
        const sortedProjects = this.sortProjectsByPermission(filteredProjects);
        
        // 获取项目列表容器
        const projectList = this.dropdown.querySelector('.project-list');
        if (!projectList) {
            console.error('未找到项目列表容器 .project-list');
            return;
        }

        // 清空现有项目
        projectList.innerHTML = '';

        // 检查是否有结果
        if (sortedProjects.length === 0) {
            this.showNoResults();
            return;
        }

        // 添加所有项目到统一列表
        sortedProjects.forEach(project => {
            const projectItem = this.createProjectItem(project, this.getProjectPermissionType(project));
            projectList.appendChild(projectItem);
        });

        // 显示结果
        this.showDropdown();
        this.hideNoResults();
        this.activeIndex = -1; // 重置活动索引
    }
    
    /**
     * 按权限排序项目：可编辑 > 只读 > 锁定
     */
    sortProjectsByPermission(projects) {
        return projects.sort((a, b) => {
            const aType = this.getProjectPermissionType(a);
            const bType = this.getProjectPermissionType(b);
            
            // 权限优先级：editable = 1, readonly = 2, locked = 3
            const priorityMap = { 'editable': 1, 'readonly': 2, 'locked': 3 };
            const aPriority = priorityMap[aType] || 3;
            const bPriority = priorityMap[bType] || 3;
            
            if (aPriority !== bPriority) {
                return aPriority - bPriority;
            }
            
            // 相同权限级别按项目名称排序
            return (a.project_name || '').localeCompare(b.project_name || '');
        });
    }
    
    /**
     * 获取项目权限类型
     */
    getProjectPermissionType(project) {
        if (project.permissions && project.permissions.edit) {
            return 'editable';
        } else if (project.permissions && project.permissions.view) {
            return 'readonly';
        } else {
            return 'locked';
        }
    }
    
    // 移除了 updateGroup 方法，因为不再使用分组显示
    
    /**
     * 创建项目项元素（专业紧凑布局）
     */
    createProjectItem(project, groupType) {
        const item = document.createElement('div');
        item.className = `project-item ${groupType}`;
        item.dataset.project = JSON.stringify(project);
        
        // 构建显示内容
        const projectName = project.project_name || '未命名项目';
        const ownerName = project.owner_name || '未知';
        const stageName = project.current_stage_display || project.current_stage || '未设置';
        const typeName = project.project_type_display || project.project_type || '未设置';
        
        // 权限图标
        let permissionIcon = '';
        let permissionClass = '';
        switch (groupType) {
            case 'editable':
                permissionIcon = 'fas fa-edit';
                permissionClass = 'editable';
                break;
            case 'readonly':
                permissionIcon = 'fas fa-eye';
                permissionClass = 'readonly';
                break;
            case 'locked':
                permissionIcon = 'fas fa-lock';
                permissionClass = 'locked';
                item.classList.add('locked');
                break;
        }
        
        // 专业紧凑布局：两行结构，上行项目名，下行元信息
        item.innerHTML = `
            <div class="project-single-line">
                <div class="project-main-section">
                    <div class="project-name">${this.escapeHtml(projectName)}</div>
                    <div class="project-meta-info">
                        <div class="meta-item">
                            <span class="meta-label">负责人</span>
                            <span class="meta-value">${this.escapeHtml(ownerName)}</span>
                        </div>
                        <div class="meta-divider"></div>
                        <div class="meta-item">
                            <span class="meta-label">阶段</span>
                            <span class="meta-value">${this.escapeHtml(stageName)}</span>
                        </div>
                        <div class="meta-divider"></div>
                        <div class="meta-item">
                            <span class="meta-label">类型</span>
                            <span class="meta-value">${this.escapeHtml(typeName)}</span>
                        </div>
                    </div>
                </div>
                <div class="permission-icon ${permissionClass}">
                    <i class="${permissionIcon}"></i>
                </div>
            </div>
        `;
        
        return item;
    }
    
    /**
     * 选择项目
     */
    selectProject(project) {
        this.selectedProject = project;
        
        // 更新输入框显示
        let displayName = project.project_name;
        if (this.config.display_config.show_auth_code && project.authorization_code) {
            displayName += ` (${project.authorization_code})`;
        }
        this.input.value = displayName;
        
        // 更新隐藏字段（只更新项目ID）
        this.updateHiddenFields(project);
        
        // 显示清除按钮
        this.showClearButton();
        
        // 隐藏下拉菜单
        this.hideDropdown();
        
        // 触发选择事件
        this.triggerSelectEvent(project);
        
        console.log('✅ 已选择项目:', project.project_name);
    }
    
    /**
     * 更新隐藏字段（只更新项目ID，其他信息在保存时从项目表获取）
     */
    updateHiddenFields(project) {
        // 只更新项目ID字段
        if (this.projectIdField) {
            this.projectIdField.value = project.id;
        }
        
        // 移除其他隐藏字段的更新，因为项目阶段、类型等信息在保存时从项目表获取
        // 这样可以确保使用最新的项目状态，而不是搜索时的快照
    }
    
    // 移除了 showSelectedProjectInfo 方法，不再显示已选中项目信息
    
    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedProject = null;
        
        // 清空输入框
        this.input.value = '';
        
        // 只清空项目ID字段
        if (this.projectIdField) {
            this.projectIdField.value = '';
        }
        
        // 不再处理已选中项目信息显示，因为已移除该区域
        
        // 隐藏清除按钮
        this.hideClearButton();
        
        // 隐藏下拉菜单
        this.hideDropdown();
        
        // 触发清除事件
        this.triggerClearEvent();
        
        console.log('✅ 已清除项目选择');
    }
    
    /**
     * 设置选中的项目（外部调用）
     */
    setSelectedProject(project) {
        this.selectProject(project);
    }
    
    /**
     * 获取选中的项目（外部调用）
     */
    getSelectedProject() {
        return this.selectedProject;
    }
    
    /**
     * 显示下拉菜单
     */
    showDropdown() {
        this.dropdown.style.display = 'block';
    }
    
    /**
     * 隐藏下拉菜单
     */
    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.activeIndex = -1;
    }
    
    /**
     * 显示加载状态
     */
    showLoading() {
        this.loadingElement.style.display = 'block';
        this.resultsElement.style.display = 'none';
        this.noResultsElement.style.display = 'none';
        this.showDropdown();
    }
    
    /**
     * 隐藏加载状态
     */
    hideLoading() {
        this.loadingElement.style.display = 'none';
        this.resultsElement.style.display = 'block';
    }
    
    /**
     * 显示无结果提示
     */
    showNoResults() {
        this.hideLoading();
        this.resultsElement.style.display = 'none';
        this.noResultsElement.style.display = 'block';
        this.showDropdown();
    }
    
    /**
     * 隐藏无结果提示
     */
    hideNoResults() {
        this.noResultsElement.style.display = 'none';
    }
    
    /**
     * 显示错误信息
     */
    showError(message) {
        this.hideLoading();
        this.noResultsElement.querySelector('.text-muted').textContent = message;
        this.showNoResults();
    }
    
    /**
     * 显示清除按钮
     */
    showClearButton() {
        if (this.clearBtn) {
            this.clearBtn.style.display = 'block';
        }
    }
    
    /**
     * 隐藏清除按钮
     */
    hideClearButton() {
        if (this.clearBtn) {
            this.clearBtn.style.display = 'none';
        }
    }
    
    /**
     * 高亮项目项
     */
    highlightItem(item) {
        // 移除所有高亮
        this.dropdown.querySelectorAll('.project-item.active').forEach(activeItem => {
            activeItem.classList.remove('active');
        });
        
        // 高亮当前项
        item.classList.add('active');
        
        // 更新活动索引
        const items = Array.from(this.dropdown.querySelectorAll('.project-item:not(.locked)'));
        this.activeIndex = items.indexOf(item);
    }
    
    /**
     * 高亮活动项目项
     */
    highlightActiveItem(items) {
        // 移除所有高亮
        items.forEach(item => item.classList.remove('active'));
        
        // 高亮当前活动项
        if (this.activeIndex >= 0 && items[this.activeIndex]) {
            items[this.activeIndex].classList.add('active');
            items[this.activeIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    /**
     * 触发选择事件
     */
    triggerSelectEvent(project) {
        const event = new CustomEvent('projectSelected', {
            detail: { project: project },
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * 触发清除事件
     */
    triggerClearEvent() {
        const event = new CustomEvent('projectCleared', {
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
    
    /**
     * HTML转义
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    /**
     * 验证选择（外部调用）
     */
    validate() {
        if (this.config.validation.required && !this.selectedProject) {
            this.input.classList.add('is-invalid');
            return false;
        }
        
        this.input.classList.remove('is-invalid');
        return true;
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        // 清除定时器
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // 移除事件监听器（由浏览器自动处理）
        
        console.log('✅ 项目搜索组件已销毁');
    }
}

// 全局工具函数
window.ProjectSearchComponent = ProjectSearchComponent;