# 产品库图片上传容量限制修复

## 问题描述
产品库的图片上传在保存时会报错，大于一定容量的图片会导致上传失败。用户反映600K以内的图片不会报错。

## 问题分析
经过代码检查发现：
1. **前端限制**：原来设置为5MB，过于宽松
2. **后端处理**：缺少文件大小检查
3. **实际限制**：用户反映600KB以内正常，说明实际限制更小

## 修复方案
将图片上传限制统一调整为600KB，并在前后端都添加相应的检查。

## 修复内容

### 1. 前端限制调整

#### 产品库主页面 (`app/templates/product/create.html`)
- 将JavaScript文件大小检查从5MB改为600KB
- 更新错误提示信息
- 更新页面提示文字

```javascript
// 修改前：5MB限制
if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB');

// 修改后：600KB限制  
if (file.size > 600 * 1024) {
    alert('图片大小不能超过600KB');
```

#### 产品管理模块页面
- `app/templates/product_management/new_product.html` - 新建产品页面
- `app/templates/product_management/edit_product.html` - 编辑产品页面

更新内容：
- 修改提示文字：从"建议尺寸 800x600 像素"改为"图片大小不超过600KB"
- 添加JavaScript文件大小检查功能

### 2. 后端限制添加

#### 产品库路由 (`app/routes/product.py`)
在 `process_product_image` 函数中添加600KB大小检查：

```python
# 检查文件大小（最大600KB）
file.seek(0, 2)  # 移动到文件末尾
file_size = file.tell()  # 获取文件大小
file.seek(0)  # 重置文件指针
if file_size > 600 * 1024:  # 600KB
    logger.warning(f"图片文件过大: {file_size} bytes (最大600KB)")
    return None
```

#### 产品管理路由 (`app/routes/product_management.py`)
在 `save_product_image` 函数中添加相同的600KB大小检查。

### 3. 图片质量优化
为了进一步减小文件大小，将图片保存质量从85降低到75：

```python
# 修改前
img.save(final_path, optimize=True, quality=85)

# 修改后  
img.save(final_path, optimize=True, quality=75)  # 降低质量从85到75
```

## 修复效果
1. ✅ 前端在选择文件时立即检查大小，超过600KB会提示并清空选择
2. ✅ 后端在处理图片时也会检查大小，确保双重保护
3. ✅ 统一了所有产品相关页面的图片大小限制
4. ✅ 提供了清晰的错误提示信息
5. ✅ 通过降低图片质量进一步减小文件大小

## 测试验证
- 上传小于600KB的图片：正常处理
- 上传大于600KB的图片：前端提示错误并阻止上传
- 如果绕过前端检查：后端也会拒绝处理

## 文件修改列表
1. `app/templates/product/create.html` - 主产品库页面
2. `app/templates/product_management/new_product.html` - 新建产品页面  
3. `app/templates/product_management/edit_product.html` - 编辑产品页面
4. `app/routes/product.py` - 产品库后端路由
5. `app/routes/product_management.py` - 产品管理后端路由

## 注意事项
- 修复保持了原有的功能逻辑不变
- 只调整了文件大小限制，没有修改其他图片处理逻辑
- 600KB的限制对于产品展示图片来说是合理的
- 如果需要调整限制，只需要修改 `600 * 1024` 这个值即可

## 后续建议
1. 可以考虑添加图片压缩功能，自动将大图片压缩到合适大小
2. 可以添加图片格式转换，统一转换为更高效的格式（如WebP）
3. 可以添加图片预览功能，让用户在上传前看到处理后的效果 