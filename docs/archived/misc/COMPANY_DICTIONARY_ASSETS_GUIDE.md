# 企业字典资产管理系统 - 完整指南

## 🎯 概述

企业字典资产管理系统现已完全集成到PMA系统的"企业字典"模块中。您可以为每个企业单独管理Logo、邮件签名图片和详细联系信息，所有数据存储在 `dictionaries` 表中。

## 📋 功能特性

### ✅ 已实现功能

1. **企业Logo管理**
   - 上传、预览、删除企业专属Logo
   - 支持PNG、JPG、SVG、GIF格式
   - 文件大小限制：5MB
   - 建议尺寸：240x50像素
   - Base64存储，完全兼容云部署

2. **邮件签名图片管理**
   - 上传、预览、删除邮件签名图片
   - 支持PNG、JPG、SVG、GIF格式
   - 文件大小限制：3MB
   - 建议宽度：不超过600像素

3. **企业详细信息扩展**
   - 详细地址（500字符）
   - 邮政编码
   - 企业电话、传真
   - 企业邮箱、网站地址

4. **企业列表增强显示**
   - 表格中直接显示Logo缩略图
   - 显示联系方式快览
   - 一键访问企业网站

5. **PDF报价单Logo集成**
   - 优先使用企业字典中的Logo
   - 自动回退到全局Logo
   - 无缝集成到现有PDF模板

## 🚀 使用方法

### 1. 访问企业字典管理

1. 登录PMA系统
2. 点击导航菜单中的 **"企业字典"**
3. 进入企业字典管理页面

### 2. 添加新企业

1. 点击 **"新增企业"** 按钮
2. 填写基本信息：
   - **Key（英文标识）**：系统内部标识符（必填）
   - **显示文本**：用户界面显示的企业名称（必填）
   - **厂商标记**：是否为厂商企业
3. 填写详细信息（可选）：
   - 详细地址、邮政编码
   - 企业电话、传真
   - 企业邮箱、网站地址
4. 上传企业资产（可选）：
   - 企业Logo
   - 邮件签名图片
5. 点击 **"保存"** 完成创建

### 3. 编辑现有企业

1. 在企业列表中找到目标企业
2. 点击 **"编辑"** 按钮
3. 修改需要更新的信息
4. 上传或更换Logo和邮件签名
5. 点击 **"保存"** 保存更改

### 4. Logo和邮件签名管理

#### 上传资产
1. 在编辑表单的"企业资产管理"区域
2. 点击相应的 **"上传Logo"** 或 **"上传签名"** 按钮
3. 选择本地图片文件
4. 系统自动验证文件格式和大小
5. 上传成功后立即显示预览

#### 删除资产
1. 在有资产的企业编辑界面
2. 点击 **"删除Logo"** 或 **"删除签名"** 按钮
3. 确认删除操作

## 🛠️ 技术架构

### 数据库结构

所有数据存储在 `dictionaries` 表中，企业类型记录的 `type='company'`：

```sql
-- 基础字段
id INTEGER PRIMARY KEY
type VARCHAR(50) = 'company'
key VARCHAR(50)              -- 企业英文标识
value VARCHAR(100)           -- 企业显示名称
is_active BOOLEAN           -- 是否启用
is_vendor BOOLEAN           -- 是否为厂商

-- 企业详细信息字段
address VARCHAR(500)         -- 详细地址
postal_code VARCHAR(20)      -- 邮政编码
phone VARCHAR(50)           -- 企业电话
fax VARCHAR(50)             -- 传真
email VARCHAR(100)          -- 企业邮箱
website VARCHAR(200)        -- 网站地址

-- Logo资产字段
logo_content TEXT           -- Logo的Base64内容
logo_filename VARCHAR(100)  -- Logo原始文件名
logo_type VARCHAR(50)       -- Logo文件类型
logo_size INTEGER           -- Logo文件大小（字节）

-- 邮件签名资产字段
email_signature_content TEXT     -- 邮件签名的Base64内容
email_signature_filename VARCHAR(100)  -- 邮件签名原始文件名
email_signature_type VARCHAR(50)       -- 邮件签名文件类型
email_signature_size INTEGER           -- 邮件签名文件大小（字节）
```

### API端点

新增的企业资产管理API：

- `POST /api/v1/dictionary/company/{id}/upload_asset` - 上传资产
- `POST /api/v1/dictionary/company/{id}/delete_asset` - 删除资产
- `GET /api/v1/dictionary/company/{id}/get_asset` - 获取资产

扩展的企业字典API：

- `POST /api/v1/dictionary/company/add` - 创建企业（支持详细信息）
- `POST /api/v1/dictionary/company/edit` - 编辑企业（支持详细信息）

### 模型扩展

`Dictionary` 模型新增方法：

```python
# 属性方法
@property
def logo_data_url(self)                    # 获取Logo的Data URL
def email_signature_data_url(self)         # 获取邮件签名的Data URL
def logo_size_kb(self)                     # Logo文件大小(KB)
def email_signature_size_kb(self)          # 邮件签名文件大小(KB)

# 管理方法
def update_logo(file_data, filename)       # 更新Logo
def update_email_signature(file_data, filename)  # 更新邮件签名
def clear_logo()                          # 清除Logo
def clear_email_signature()              # 清除邮件签名
```

## 📊 数据迁移

### 运行迁移脚本

**PostgreSQL数据库 (推荐)**：
```bash
# 执行PostgreSQL迁移
psql -d database_name -f add_dictionary_company_assets_fields_postgresql.sql
```

**MySQL数据库 (备用)**：
```bash
# 执行MySQL迁移
mysql -u username -p database_name < add_dictionary_company_assets_fields.sql
```

### 验证迁移

```sql
-- 验证新字段已添加
DESCRIBE dictionaries;

-- 检查企业字典数据
SELECT id, key, value, is_vendor, phone, email, 
       CASE WHEN logo_content IS NOT NULL THEN 'Yes' ELSE 'No' END as has_logo
FROM dictionaries 
WHERE type = 'company';
```

## 🎨 界面特性

### 企业列表视图

- **Logo列**：显示Logo缩略图（40x20像素）
- **联系信息列**：显示电话、邮箱、网站快览
- **响应式表格**：移动端自动调整布局

### 编辑表单

- **分区布局**：基本信息、详细信息、资产管理分别展示
- **文件预览**：上传后立即显示预览
- **进度指示**：显示上传进度
- **错误提示**：详细的错误信息反馈

### 资产管理区域

- **拖拽风格**：点击上传，直观易用
- **实时预览**：上传后立即显示
- **删除确认**：防止误操作
- **文件验证**：客户端和服务端双重验证

## 📈 PDF集成

### Logo使用优先级

1. **企业字典Logo**：优先使用企业专属Logo
2. **全局Logo**：回退到系统默认Logo
3. **文字Logo**：最终回退到文字显示

### 报价单PDF效果

- Logo显示在左上角
- 自动缩放保持比例
- 最大尺寸：150x40像素
- 支持所有主流图片格式

## 🚨 使用注意事项

### 文件要求

**企业Logo**：
- 格式：PNG、JPG、SVG、GIF
- 大小：≤ 5MB
- 建议尺寸：240x50像素
- 建议背景：透明

**邮件签名**：
- 格式：PNG、JPG、SVG、GIF
- 大小：≤ 3MB
- 建议宽度：≤ 600像素
- 建议内容：联系信息、企业标识

### 企业Key规范

- 使用英文和下划线
- 全局唯一
- 不可修改（编辑时禁止修改Key）
- 推荐格式：`company_name` 或 `company_abbr`

### 权限要求

- 需要相应的字典管理权限
- 企业资产的上传、编辑、删除操作需要权限验证
- 所有操作都会记录到系统日志

## 🔧 管理工具

### Python脚本示例

```python
from app.models.dictionary import Dictionary
from app import db

# 查找企业
company = Dictionary.query.filter_by(
    type='company',
    key='evertac_solutions'
).first()

# 检查Logo状态
if company:
    print(f"企业名称: {company.value}")
    print(f"有Logo: {'是' if company.logo_content else '否'}")
    print(f"Logo大小: {company.logo_size_kb}KB")

# 批量上传Logo
def batch_upload_logos(logo_mapping):
    """
    logo_mapping: {'company_key': '/path/to/logo.png'}
    """
    for company_key, logo_path in logo_mapping.items():
        company = Dictionary.query.filter_by(
            type='company',
            key=company_key
        ).first()
        
        if company:
            with open(logo_path, 'rb') as f:
                file_data = f.read()
            
            success = company.update_logo(file_data, os.path.basename(logo_path))
            if success:
                db.session.commit()
                print(f"✅ {company_key} Logo上传成功")
            else:
                print(f"❌ {company_key} Logo上传失败")
```

### SQL查询示例

```sql
-- 查看有Logo的企业
SELECT key, value, logo_filename, logo_size
FROM dictionaries 
WHERE type = 'company' 
  AND logo_content IS NOT NULL
ORDER BY value;

-- 统计企业资产情况
SELECT 
    COUNT(*) as total_companies,
    COUNT(logo_content) as companies_with_logo,
    COUNT(email_signature_content) as companies_with_signature,
    AVG(logo_size) as avg_logo_size
FROM dictionaries 
WHERE type = 'company' AND is_active = true;

-- 清理无效数据
UPDATE dictionaries 
SET logo_content = NULL, logo_filename = NULL, logo_type = NULL, logo_size = NULL
WHERE type = 'company' AND logo_size = 0;
```

## ✅ 测试建议

### 功能测试

1. **企业管理**
   - 创建、编辑、删除企业
   - 启用/禁用企业
   - 厂商标记设置

2. **资产管理**
   - 上传不同格式的Logo
   - 测试文件大小限制
   - 验证删除功能
   - 预览功能测试

3. **界面测试**
   - 响应式布局测试
   - 移动端兼容性
   - 表格显示效果

4. **PDF集成测试**
   - 生成报价单PDF
   - 验证Logo显示效果
   - 测试回退机制

### 性能测试

- 大文件上传性能
- 列表页面加载速度
- 数据库查询效率

## 🎉 完成状态

✅ **企业字典资产管理系统已完全集成！**

现在您可以：

1. ✅ 在企业字典中为每个企业单独上传Logo和邮件签名
2. ✅ 管理企业的详细联系信息
3. ✅ 在企业列表中直观查看Logo和联系信息
4. ✅ PDF报价单自动使用企业专属Logo
5. ✅ 享受完全兼容云部署的资产管理体验

### 🚀 立即开始

1. **运行数据库迁移**：
   ```bash
   mysql -u username -p database_name < add_dictionary_company_assets_fields.sql
   ```

2. **重启应用**加载新功能

3. **访问企业字典**：导航菜单 → 企业字典

4. **开始管理**：编辑企业 → 上传Logo → 保存

### ⚠️ 故障排除

**问题**: 访问页面时出现 `column dictionaries.address does not exist` 错误
**原因**: 数据库迁移脚本未运行
**解决**: 
```bash
# 对于PostgreSQL数据库
psql -d your_database_name -f add_dictionary_company_assets_fields_postgresql.sql

# 对于MySQL数据库  
mysql -u username -p database_name < add_dictionary_company_assets_fields.sql
```

---

**项目更新时间**: 2025-07-24  
**版本**: v2.0.0  
**状态**: ✅ 生产就绪  
**位置**: 企业字典模块（正确位置！）