# Render部署中的Supabase存储配置指南

本文档介绍如何在Render云端部署中配置不同Web应用使用不同的Supabase存储位置。

## 📋 配置概述

已更新`render.yaml`文件，添加了完整的Supabase存储配置环境变量，支持多环境部署。

## 🔧 当前配置

### **Web服务环境变量**
```yaml
# Supabase 存储配置
- key: SUPABASE_URL
  value: https://pqzviljbpfoqvyfulakl.supabase.co
- key: SUPABASE_KEY  
  value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY
- key: SUPABASE_BUCKET
  value: invoice-images  
- key: FORCE_CLOUD_UPLOAD
  value: true
```

### **代码逻辑**
应用会按以下优先级使用存储桶：
1. **环境变量**: `SUPABASE_BUCKET` (云端配置)
2. **默认值**: `invoice-images` (代码硬编码)

```python
# app/utils/supabase_client.py:40
self.bucket_name = os.getenv('SUPABASE_BUCKET', 'invoice-images')
```

## 🌍 多环境部署策略

### **不同环境使用不同存储桶**

#### **生产环境 (SP8D)**
```yaml
- key: SUPABASE_BUCKET
  value: invoice-images
```

#### **测试环境 (OVS)**  
```yaml
- key: SUPABASE_BUCKET
  value: invoice-images-ovs
```

#### **开发环境**
```yaml
- key: SUPABASE_BUCKET
  value: invoice-images-dev
```

## 🚀 部署步骤

### **1. 更新render.yaml**
已完成更新，包含完整的Supabase配置。

### **2. 在Render控制台配置**
如果需要覆盖yaml中的配置：

1. 登录 [Render控制台](https://dashboard.render.com)
2. 选择你的Web服务
3. 进入"Environment"标签页  
4. 添加或修改环境变量：
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_BUCKET`
   - `FORCE_CLOUD_UPLOAD`

### **3. 重新部署**
```bash
git add render.yaml
git commit -m "Update Supabase storage config for Render deployment"  
git push origin main
```

## 📂 存储桶结构

### **当前结构**
```
invoice-images/
├── expense_invoices/
│   ├── 1/
│   │   └── expense_invoice_1_*.png
│   ├── 15/
│   │   └── expense_invoice_15_*.heic
│   └── ...（共36个子目录）
└── .emptyFolderPlaceholder
```

### **多环境建议结构**
```
# 生产环境
invoice-images/
├── expense_invoices/...

# 测试环境  
invoice-images-ovs/
├── expense_invoices/...

# 开发环境
invoice-images-dev/
├── expense_invoices/...
```

## 🔍 验证配置

### **检查环境变量**
在Render服务的Shell中运行：
```bash
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_KEY: $SUPABASE_KEY" 
echo "SUPABASE_BUCKET: $SUPABASE_BUCKET"
echo "FORCE_CLOUD_UPLOAD: $FORCE_CLOUD_UPLOAD"
```

### **测试文件上传**
1. 登录应用
2. 进入报销管理
3. 上传发票图片
4. 检查Supabase控制台中的`invoice-images`存储桶

## 🛠️ 故障排除

### **常见问题**

#### **1. 环境变量未生效**
- 检查Render控制台中的环境变量设置
- 确认服务已重新部署
- 查看部署日志

#### **2. 存储桶访问权限问题**
- 确认`SUPABASE_KEY`是Service Role Key
- 检查存储桶的访问策略设置
- 验证存储桶是否存在

#### **3. 文件上传失败**
- 检查网络连接
- 确认文件大小未超过限制
- 查看应用错误日志

### **调试命令**
```bash
# 测试Supabase连接
python debug_supabase.py

# 检查存储桶列表
curl -H "Authorization: Bearer $SUPABASE_KEY" \
  "$SUPABASE_URL/storage/v1/bucket"
```

## 📝 配置迁移记录

### **2025-08-10**
- ✅ 完成Supabase图片存储迁移：`product-images` → `invoice-images`
- ✅ 更新`render.yaml`添加Supabase环境变量配置
- ✅ 设置默认存储桶为`invoice-images`
- ✅ 迁移了57个发票文件，成功率98.24%

### **配置变更影响**
- **发票上传**: 现在将保存到`invoice-images`存储桶
- **文件路径**: 保持原有的`expense_invoices/{detail_id}/{filename}`结构
- **多环境支持**: 支持通过环境变量配置不同存储桶

## 🔐 安全注意事项

1. **密钥保护**: Service Role Key具有完全访问权限，需妥善保管
2. **环境隔离**: 不同环境使用不同的存储桶，避免数据混淆
3. **权限最小化**: 考虑为不同环境创建专用的服务密钥
4. **备份策略**: 定期备份重要的发票图片数据

## 📞 技术支持

如遇到配置问题：
1. 检查本文档的故障排除部分
2. 查看Render部署日志
3. 检查Supabase控制台
4. 联系技术支持团队

---

**文档版本**: 1.0  
**最后更新**: 2025-08-10  
**适用环境**: Render云端部署 + Supabase存储