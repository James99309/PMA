# 企业资产管理系统使用指南

## 🎯 概述

企业资产管理系统已成功集成到企业字典中，允许您为每个企业单独管理Logo、邮件签名图片和详细联系信息。

## 📋 功能特性

### ✅ 已实现功能

1. **企业Logo管理**
   - 支持PNG、JPG、SVG、GIF格式
   - 文件大小限制：5MB
   - 建议尺寸：240x50像素
   - Base64存储，支持云部署

2. **邮件签名图片管理**
   - 支持PNG、JPG、SVG、GIF格式
   - 文件大小限制：3MB
   - 建议宽度：不超过600像素

3. **企业详细信息扩展**
   - 详细地址（扩展字段）
   - 邮政编码
   - 企业电话、传真
   - 企业邮箱、网站地址

4. **PDF报价单Logo集成**
   - 优先使用企业专属Logo
   - 自动回退到全局Logo
   - 无缝集成到现有PDF模板

## 🚀 使用方法

### 1. 上传企业Logo

1. 进入企业编辑页面：`/customer/edit/{company_id}`
2. 在"企业资产管理"区域找到"企业Logo"
3. 点击"上传Logo"按钮选择文件
4. 系统自动验证文件格式和大小
5. 上传成功后立即显示预览

### 2. 管理邮件签名

1. 在同一页面的"邮件签名图片"区域
2. 点击"上传签名"按钮选择文件
3. 上传后可预览和删除

### 3. 更新企业信息

新增的企业信息字段包括：
- **详细地址（扩展）**：更详细的地址信息
- **邮政编码**：标准邮政编码
- **企业电话**：官方联系电话
- **传真**：传真号码
- **企业邮箱**：官方邮箱地址
- **网站地址**：企业官网

## 🛠️ 技术架构

### 数据库结构

新增字段在 `companies` 表中：

```sql
-- 企业详细信息
detailed_address VARCHAR(500)    -- 详细地址（扩展）
postal_code VARCHAR(20)          -- 邮政编码
phone VARCHAR(50)                -- 企业电话
fax VARCHAR(50)                  -- 传真
email VARCHAR(100)               -- 企业邮箱
website VARCHAR(200)             -- 网站地址

-- Logo资产
logo_content TEXT                -- Logo的Base64内容
logo_filename VARCHAR(100)       -- Logo原始文件名
logo_type VARCHAR(50)            -- Logo文件类型
logo_size INTEGER                -- Logo文件大小（字节）

-- 邮件签名资产
email_signature_content TEXT     -- 邮件签名的Base64内容
email_signature_filename VARCHAR(100)  -- 邮件签名原始文件名
email_signature_type VARCHAR(50)       -- 邮件签名文件类型
email_signature_size INTEGER           -- 邮件签名文件大小（字节）
```

### 服务层

1. **CompanyAssetService** (`app/services/company_asset_service.py`)
   - 企业资产上传、删除、获取
   - 文件验证和处理
   - 错误处理和日志记录

2. **更新的PDFGenerator** (`app/services/pdf_generator.py`)
   - 优先使用企业专属Logo
   - 自动回退机制
   - 向后兼容

### API端点

- `POST /customer/company/{id}/upload_asset` - 上传资产
- `POST /customer/company/{id}/delete_asset` - 删除资产

## 📊 数据迁移

运行数据库迁移脚本：

```bash
# 执行SQL迁移
mysql -u username -p database_name < add_company_assets_fields.sql
```

## 🔧 管理工具

### Python脚本示例

```python
from app.services.company_asset_service import CompanyAssetService

# 上传Logo
with open('/path/to/logo.png', 'rb') as f:
    file_data = f.read()

result = CompanyAssetService.upload_company_logo(
    company_id=1,
    file_data=file_data,
    filename='logo.png'
)

# 获取Logo
logo_url = CompanyAssetService.get_company_logo(company_id=1)

# 获取企业资产信息概览
info = CompanyAssetService.get_company_assets_info(company_id=1)
```

## 🎨 界面特性

### 用户体验

1. **拖拽上传**：点击即可选择文件
2. **实时预览**：上传后立即显示
3. **文件验证**：客户端和服务端双重验证
4. **进度指示**：显示上传进度
5. **错误提示**：清晰的错误信息

### 响应式设计

- 桌面端：并排显示Logo和邮件签名
- 移动端：自动调整为垂直布局
- 图片自适应：最大宽度200px，高度80px

## 📈 PDF集成效果

### Logo优先级

1. **企业专属Logo**：优先使用企业上传的Logo
2. **全局Logo**：如果企业没有Logo，使用系统默认Logo
3. **无Logo模式**：显示文字Logo（EVERTAC）

### 报价单模板

- 简洁的Excel导出风格
- Logo位置：左上角
- 自动缩放：保持比例，不超过150x40像素
- 格式兼容：支持PNG、SVG等多种格式

## 🚨 注意事项

### 文件要求

1. **Logo文件**
   - 格式：PNG、JPG、SVG、GIF
   - 大小：≤ 5MB
   - 建议尺寸：240x50像素
   - 背景：建议透明

2. **邮件签名**
   - 格式：PNG、JPG、SVG、GIF
   - 大小：≤ 3MB
   - 建议宽度：≤ 600像素

### 权限控制

- 需要 `customer.edit` 权限
- 只有企业信息编辑权限的用户可以管理资产
- 变更会记录到审计日志

### 云部署兼容

- Base64存储，无需依赖文件系统
- 适配Render等云平台
- 数据库存储，避免静态文件丢失

## ✅ 测试建议

1. **功能测试**
   - 上传不同格式的Logo
   - 测试文件大小限制
   - 验证删除功能

2. **PDF测试**
   - 生成报价单PDF
   - 验证Logo显示效果
   - 测试回退机制

3. **权限测试**
   - 不同权限用户的访问控制
   - 编辑权限验证

## 🎉 完成状态

✅ 企业Logo和邮件签名管理系统已完全集成到企业字典中！

现在您可以：
1. 为每个企业单独上传Logo
2. 管理企业详细联系信息
3. 在PDF报价单中自动使用企业专属Logo
4. 享受云部署兼容的资产管理体验

---

**项目更新时间**: 2025-07-24  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪