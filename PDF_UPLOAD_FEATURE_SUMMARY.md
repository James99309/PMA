# 产品库PDF文件上传功能实现总结

## 功能概述

为产品库表（DevProduct）增加了PDF文件上传功能，支持在创建和编辑产品时上传PDF文件，并在产品详情页面提供下载功能。

## 实现的功能

### 1. 数据库结构更新
- 为 `dev_products` 表添加了 `pdf_path` 字段（VARCHAR(255)）
- 创建并应用了数据库迁移文件：`7dfcf037db65_add_pdf_path_field_to_dev_products_table.py`

### 2. 文件上传处理
- **文件格式限制**：仅支持 `.pdf` 格式
- **文件大小限制**：最大 2MB
- **存储位置**：`static/uploads/products/pdfs/` 目录
- **文件命名**：使用 UUID 前缀确保文件名唯一性
- **安全性**：使用 `secure_filename()` 处理文件名

### 3. 前端界面更新

#### 新建产品页面 (`new_product.html`)
- 在产品信息选项卡中添加了PDF文件上传字段
- 提供文件格式和大小限制的提示信息

#### 编辑产品页面 (`edit_product.html`)
- 添加了PDF文件上传字段
- 显示当前PDF文件信息（如果存在）
- 提供下载当前PDF文件的按钮

#### 产品详情页面 (`product_detail.html`)
- 在产品描述后添加了"产品文档"部分
- 显示PDF文件图标和文件名
- 提供下载PDF文件的按钮

### 4. 后端路由更新

#### 文件处理函数
```python
# 新增函数
def allowed_pdf_file(filename)  # 检查PDF文件格式
def check_file_size(file)       # 检查文件大小（2MB限制）
def save_product_pdf(file)      # 保存PDF文件
```

#### 路由更新
- **保存产品** (`/save`): 添加PDF文件上传处理
- **更新产品** (`/<int:id>/update`): 添加PDF文件更新处理
- **PDF下载** (`/<int:id>/download-pdf`): 新增PDF文件下载路由

### 5. 文件管理功能
- **自动目录创建**：首次上传时自动创建存储目录
- **文件替换**：编辑产品时上传新PDF会自动删除旧文件
- **文件下载**：支持以原始文件名下载PDF文件
- **错误处理**：完善的错误提示和异常处理

## 技术实现细节

### 文件上传验证
```python
def save_product_pdf(file):
    if file and allowed_pdf_file(file.filename):
        # 检查文件大小
        if not check_file_size(file):
            return None, "PDF文件大小不能超过2MB"
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 保存文件
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', 'pdfs')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        return os.path.join('uploads', 'products', 'pdfs', unique_filename), None
```

### 文件下载处理
```python
@product_management_bp.route('/<int:id>/download-pdf', methods=['GET'])
def download_pdf(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    if not dev_product.pdf_path:
        flash('该产品没有PDF文件', 'warning')
        return redirect(url_for('product_management.product_detail', id=id))
    
    pdf_file_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
    
    if not os.path.exists(pdf_file_path):
        flash('PDF文件不存在', 'danger')
        return redirect(url_for('product_management.product_detail', id=id))
    
    # 获取原始文件名
    original_filename = os.path.basename(dev_product.pdf_path)
    if '_' in original_filename:
        original_filename = '_'.join(original_filename.split('_')[1:])
    
    return send_file(
        pdf_file_path,
        as_attachment=True,
        download_name=original_filename,
        mimetype='application/pdf'
    )
```

## 使用说明

### 上传PDF文件
1. 在新建或编辑产品页面
2. 在"产品PDF文件"字段选择PDF文件
3. 确保文件大小不超过2MB
4. 保存产品

### 下载PDF文件
1. 进入产品详情页面
2. 在"产品文档"部分点击"下载PDF"按钮
3. 文件将以原始文件名下载

## 安全性考虑

1. **文件格式验证**：严格限制只能上传PDF文件
2. **文件大小限制**：防止大文件占用过多存储空间
3. **文件名安全**：使用`secure_filename()`处理文件名
4. **唯一性保证**：使用UUID前缀避免文件名冲突
5. **权限控制**：遵循现有的权限系统

## 测试验证

创建了测试脚本 `test_pdf_upload.py` 用于验证：
- 数据库连接正常
- 模型字段正确添加
- 上传目录结构
- 文件存在性检查

## 部署注意事项

1. 确保应用有写入 `static/uploads/products/pdfs/` 目录的权限
2. 定期清理无用的PDF文件（可考虑添加定时任务）
3. 在生产环境中考虑使用云存储服务
4. 监控存储空间使用情况

## 后续优化建议

1. **云存储集成**：考虑集成AWS S3或阿里云OSS
2. **文件预览**：添加PDF在线预览功能
3. **批量操作**：支持批量上传和下载
4. **版本管理**：支持PDF文件版本历史
5. **缩略图生成**：为PDF生成缩略图预览 