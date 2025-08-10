# Supabase多存储桶配置指南

本文档详细介绍如何在PMA项目中配置和使用多个Supabase存储桶，实现不同业务模块使用独立的文件存储。

## 🎯 架构概述

### **多存储桶设计**
在同一个Supabase项目中使用3个独立的存储桶：

| **存储桶名称** | **用途** | **对应模块** | **文件类型** |
|----------------|----------|--------------|--------------|
| `invoice-images` | 发票图片存储 | 报销管理 | PNG, JPG, HEIC, PDF |
| `product-images` | 产品库文件 | 产品管理 | JPG, PNG, PDF |
| `rd-product-images` | 研发产品库文件 | 研发产品管理 | JPG, PNG, PDF |

### **优势**
- ✅ **业务隔离**: 不同模块的文件互不干扰
- ✅ **权限管理**: 可为不同存储桶设置不同的访问策略
- ✅ **备份策略**: 可针对不同业务重要性设置备份策略
- ✅ **成本控制**: 便于统计不同模块的存储成本

## 🔧 技术实现

### **1. SupabaseStorageClient改进**

#### **多存储桶配置**
```python
# app/utils/supabase_client.py
self.bucket_config = {
    'invoice': os.getenv('SUPABASE_BUCKET_INVOICE', 'invoice-images'),
    'product': os.getenv('SUPABASE_BUCKET_PRODUCT', 'product-images'),
    'rd_product': os.getenv('SUPABASE_BUCKET_RD_PRODUCT', 'rd-product-images'),
    'default': os.getenv('SUPABASE_BUCKET', 'invoice-images')  # 向后兼容
}
```

#### **动态存储桶选择**
```python
def get_bucket_name(self, bucket_type: str = 'default') -> str:
    """根据类型获取存储桶名称"""
    return self.bucket_config.get(bucket_type, self.bucket_config['default'])
```

#### **方法签名更新**
```python
def upload_product_file(self, product_id: int, file, file_type: str, bucket_type: str = 'product') -> Optional[str]:
def delete_product_file(self, product_id: int, file_type: str, bucket_type: str = 'product') -> bool:
def upload_expense_invoice(self, detail_id: int, file, filename: str, bucket_type: str = 'invoice') -> Optional[str]:
def delete_expense_invoice(self, filename: str, bucket_type: str = 'invoice') -> bool:
```

### **2. 模块调用更新**

#### **产品管理模块**
```python
# app/routes/product.py
image_url = supabase_client.upload_product_file(
    product_id=product.id,
    file=image_file,
    file_type='image',
    bucket_type='product'  # 使用产品存储桶
)
```

#### **研发产品管理模块**
```python
# app/routes/product_management.py
image_url = supabase_client.upload_product_file(
    dev_product.id, file, 'image', 'rd_product'  # 使用研发产品存储桶
)
```

#### **发票管理模块**
```python
# app/views/expense.py (默认使用发票存储桶)
upload_expense_invoice(detail_id, file, filename)  # bucket_type='invoice'
```

## 🌐 Render云端部署配置

### **环境变量列表**

在Render控制台中配置以下环境变量：

| **变量名** | **值** | **说明** |
|------------|--------|----------|
| `SUPABASE_URL` | `https://pqzviljbpfoqvyfulakl.supabase.co` | Supabase项目URL |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Service Role Key |
| `SUPABASE_BUCKET_INVOICE` | `invoice-images` | 发票存储桶 |
| `SUPABASE_BUCKET_PRODUCT` | `product-images` | 产品存储桶 |
| `SUPABASE_BUCKET_RD_PRODUCT` | `rd-product-images` | 研发产品存储桶 |
| `SUPABASE_BUCKET` | `invoice-images` | 默认存储桶（向后兼容） |
| `FORCE_CLOUD_UPLOAD` | `true` | 强制云端上传 |

### **render.yaml配置**

```yaml
# Supabase 存储配置
- key: SUPABASE_URL
  value: https://pqzviljbpfoqvyfulakl.supabase.co
- key: SUPABASE_KEY
  value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# 多存储桶配置
- key: SUPABASE_BUCKET_INVOICE
  value: invoice-images
- key: SUPABASE_BUCKET_PRODUCT
  value: product-images
- key: SUPABASE_BUCKET_RD_PRODUCT
  value: rd-product-images
- key: SUPABASE_BUCKET
  value: invoice-images
- key: FORCE_CLOUD_UPLOAD
  value: true
```

## 📁 存储桶结构

### **invoice-images存储桶**
```
invoice-images/
└── expense_invoices/
    ├── 1/
    │   └── expense_invoice_1_*.png
    ├── 15/
    │   └── expense_invoice_15_*.heic
    └── ...（按报销明细ID组织）
```

### **product-images存储桶**
```
product-images/
├── product_1.jpg
├── product_1.pdf
├── product_2.jpg
└── ...（按产品ID命名）
```

### **rd-product-images存储桶**
```
rd-product-images/
├── product_101.jpg
├── product_101.pdf
├── product_102.jpg
└── ...（按研发产品ID命名）
```

## 🚀 部署步骤

### **1. 在Render控制台配置环境变量**

1. 登录 [Render控制台](https://dashboard.render.com)
2. 选择你的Web服务
3. 进入"Environment"标签页
4. 添加上述7个环境变量

### **2. 验证存储桶存在**

在Supabase控制台确认3个存储桶已创建：
- `invoice-images` ✅ 已存在
- `product-images` ✅ 已存在  
- `rd-product-images` ✅ 已存在

### **3. 推送代码并部署**

```bash
git add .
git commit -m "feat: implement multi-bucket Supabase storage configuration

- Add support for separate storage buckets for different modules
- invoice-images: for expense invoice files
- product-images: for product files
- rd-product-images: for R&D product files
- Update SupabaseStorageClient with bucket type parameter
- Configure Render environment variables for multi-bucket setup

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### **4. 重新部署应用**

在Render控制台点击"Manual Deploy"或等待自动部署完成。

## 🔍 测试验证

### **1. 发票上传测试**
1. 登录应用，进入报销管理
2. 创建或编辑报销单，上传发票图片
3. 检查Supabase控制台的`invoice-images`存储桶

### **2. 产品文件上传测试**
1. 进入产品管理，上传产品图片/PDF
2. 检查`product-images`存储桶

### **3. 研发产品文件上传测试**  
1. 进入研发产品管理，上传文件
2. 检查`rd-product-images`存储桶

### **4. 验证文件访问**
```bash
# 测试发票文件URL
https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/1/filename.png

# 测试产品文件URL
https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/product-images/product_1.jpg

# 测试研发产品文件URL
https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/rd-product-images/product_101.jpg
```

## 🛠️ 故障排除

### **常见问题**

#### **1. 文件上传到错误的存储桶**
**症状**: 产品图片出现在invoice-images中
**解决**: 
- 检查代码中`bucket_type`参数是否正确
- 确认环境变量配置无误

#### **2. 环境变量未生效**
**症状**: 应用仍使用旧的单存储桶配置
**解决**:
- 重新部署应用
- 检查Render控制台环境变量设置
- 查看部署日志确认变量加载

#### **3. 存储桶权限问题**
**症状**: 403 Forbidden错误
**解决**:
- 检查Supabase存储桶的公共访问策略
- 确认Service Role Key权限

### **调试命令**

```bash
# 在Render服务Shell中检查环境变量
echo "SUPABASE_BUCKET_INVOICE: $SUPABASE_BUCKET_INVOICE"
echo "SUPABASE_BUCKET_PRODUCT: $SUPABASE_BUCKET_PRODUCT"
echo "SUPABASE_BUCKET_RD_PRODUCT: $SUPABASE_BUCKET_RD_PRODUCT"

# 测试存储桶连接
curl -H "Authorization: Bearer $SUPABASE_KEY" \
  "$SUPABASE_URL/storage/v1/bucket"
```

## 📊 监控与维护

### **存储使用监控**

定期检查各存储桶的使用情况：

1. **Supabase控制台** - Storage页面查看各桶大小
2. **应用日志** - 监控上传成功/失败率
3. **成本分析** - 按存储桶统计费用

### **定期维护任务**

- **月度**: 检查存储桶大小增长趋势
- **季度**: 清理无效或重复文件
- **年度**: 评估存储成本和策略优化

## 🔮 扩展计划

### **未来可能的存储桶**

- `user-avatars`: 用户头像
- `documents`: 合同文档  
- `backups`: 数据备份文件
- `temp-files`: 临时文件（定期清理）

### **环境隔离扩展**

```bash
# 测试环境
SUPABASE_BUCKET_INVOICE=invoice-images-test
SUPABASE_BUCKET_PRODUCT=product-images-test
SUPABASE_BUCKET_RD_PRODUCT=rd-product-images-test

# 开发环境  
SUPABASE_BUCKET_INVOICE=invoice-images-dev
SUPABASE_BUCKET_PRODUCT=product-images-dev
SUPABASE_BUCKET_RD_PRODUCT=rd-product-images-dev
```

## 📝 变更日志

### **2025-08-10 v1.0**
- ✅ 初始多存储桶架构实现
- ✅ SupabaseStorageClient重构支持bucket_type参数
- ✅ 产品管理模块使用product-images存储桶
- ✅ 研发产品管理使用rd-product-images存储桶  
- ✅ 发票管理使用invoice-images存储桶
- ✅ Render部署配置更新
- ✅ 完整的配置指南和故障排除文档

### **迁移记录**
- **文件迁移**: 已完成从product-images到invoice-images的发票文件迁移（57个文件，成功率98.24%）
- **代码重构**: 所有相关调用已更新为使用新的bucket_type参数
- **配置更新**: render.yaml和环境变量配置已完成

## 🎉 总结

多存储桶配置现已完成，实现了：

1. **业务隔离**: 发票、产品、研发产品文件分别存储
2. **向后兼容**: 保持原有API的兼容性
3. **灵活配置**: 通过环境变量轻松切换不同环境
4. **易于维护**: 清晰的存储结构和完善的文档

现在你可以在Render控制台中配置相应的环境变量，享受更专业的文件存储架构！

---

**文档版本**: 1.0  
**最后更新**: 2025-08-10  
**适用项目**: PMA产品管理应用  
**部署平台**: Render + Supabase