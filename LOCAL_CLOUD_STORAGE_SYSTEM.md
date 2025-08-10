# 本地/云端存储智能切换系统

## 📋 概述

PMA项目现已实现智能存储系统，能够根据运行环境自动选择本地文件系统或云端Supabase存储，确保开发环境使用本地存储，生产环境使用云端存储。

## 🎯 核心特性

### **智能环境检测**
- ✅ **本地环境指标**: 检测8个本地环境指标，包括RENDER、VERCEL环境变量、run.py文件存在等
- ✅ **阈值判定**: 当本地指标≥2个时判定为本地环境，否则为云端环境
- ✅ **强制覆盖**: 支持`FORCE_CLOUD_UPLOAD`和`FORCE_LOCAL_STORAGE`环境变量强制指定存储类型

### **多存储桶支持**
- 📁 **本地存储桶映射**: `invoice` → `invoices`, `product` → `products`, `rd_product` → `rd_products`
- ☁️ **云端存储桶映射**: `invoice` → `invoice-images`, `product` → `product-images`, `rd_product` → `rd-product-images`
- 🔄 **统一接口**: 相同的API调用，不同的底层实现

### **容错降级机制**
- 🛡️ **配置检查**: 云端模式下检查Supabase配置完整性
- 🔄 **自动降级**: API密钥无效或网络故障时自动降级到本地存储
- 📝 **详细日志**: 记录切换过程和失败原因

## 🔧 技术实现

### **核心类: SupabaseStorageClient**

```python
class SupabaseStorageClient:
    def __init__(self):
        """智能初始化存储客户端（本地/云端自动切换）"""
        self.is_local_env = self._detect_local_environment()
        self.use_local_storage = self._should_use_local_storage()
        
        if self.use_local_storage:
            self._init_local_storage()
        else:
            self._init_supabase_storage()
```

### **环境检测逻辑**

```python
def _detect_local_environment(self) -> bool:
    """检测是否为本地开发环境"""
    indicators = [
        not os.getenv('RENDER'),           # 非Render云端
        not os.getenv('VERCEL'),           # 非Vercel云端
        'localhost' in os.getenv('SERVER_NAME', ''),
        os.path.exists('./run.py'),        # 本地开发文件存在
        # ... 更多指标
    ]
    
    local_count = sum(indicators)
    return local_count >= 2  # 多数指标表明是本地环境
```

### **统一上传接口**

```python
def upload_expense_invoice(self, detail_id: int, file, filename: str) -> Optional[str]:
    """上传发票文件（支持本地/云端智能切换）"""
    if self.use_local_storage:
        return self._upload_expense_invoice_local(detail_id, file, filename, 'invoice')
    else:
        return self._upload_expense_invoice_cloud(detail_id, file, filename, 'invoice')
```

## 📁 本地存储实现

### **目录结构**
```
./storage/
├── invoices/           # 发票文件
│   ├── PMA/
│   │   ├── TRIPLE/
│   │   │   └── BX20250810/
│   │   │       └── PMA-TRIPLE-BX20250810-001-001.jpg
│   └── GENERAL/
├── products/           # 产品文件
│   └── product_123/
│       └── product_123_20250810_143052.jpg
└── rd_products/        # 研发产品文件
    └── rd_product_456/
        └── rd_product_456_20250810_143052.pdf
```

### **文件命名规范**
- **发票文件**: `{项目代码}-{客户简称}-{报销单号}-{明细序号}-{文件序号}.{扩展名}`
- **产品文件**: `product_{产品ID}_{时间戳}.{扩展名}`
- **研发文件**: `rd_product_{产品ID}_{时间戳}.{扩展名}`

### **本地文件服务**
- ✅ **访问路由**: `/storage/<path:filename>` 
- 🔒 **安全检查**: 防止目录遍历攻击
- 📄 **MIME类型**: 自动设置正确的Content-Type

## ☁️ 云端存储实现

### **多版本SDK兼容**
- ✅ **新版SDK**: 使用`UploadFileOptions`
- ✅ **旧版SDK**: 使用字典方式传递content-type
- 🔄 **HTTP备用**: SDK失败时使用HTTP API直接上传

### **上传容错机制**
```python
# 1. 尝试新版SDK
if HAS_UPLOAD_FILE_OPTIONS:
    options = UploadFileOptions(content_type=content_type)
    res = self.supabase.storage.from_(bucket).upload(path, file, options)

# 2. 尝试字典方式
res = self.supabase.storage.from_(bucket).upload(path, file, {"content-type": content_type})

# 3. 尝试最简方式
res = self.supabase.storage.from_(bucket).upload(path, file)

# 4. HTTP API备用
requests.post(upload_url, data=file_content, headers=headers)
```

## 🚀 使用方法

### **开发环境（本地存储）**
```bash
# 直接运行，自动使用本地存储
python3 run.py

# 强制使用云端存储测试
FORCE_CLOUD_UPLOAD=true python3 run.py --supabase
```

### **生产环境（云端存储）**
```yaml
# render.yaml 环境变量配置
env:
  - key: SUPABASE_URL
    value: https://iqcyimnjtnmomvfuwjzw.supabase.co
  - key: SUPABASE_KEY  
    value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  - key: RENDER
    value: true
```

### **代码使用示例**
```python
from app.utils.supabase_client import get_supabase_client

# 获取存储客户端（自动选择本地或云端）
client = get_supabase_client()

# 上传发票文件
image_url = client.upload_expense_invoice(detail_id=123, file=file_obj, filename='invoice.jpg')

# 上传产品文件
file_url = client.upload_product_file(product_id=456, file=file_obj, file_type='image', bucket_type='product')

# 上传研发文件
file_url = client.upload_product_file(product_id=789, file=file_obj, file_type='pdf', bucket_type='rd_product')
```

## ✅ 功能验证

### **环境检测测试**
```bash
# 本地环境测试
python3 -c "from app.utils.supabase_client import SupabaseStorageClient; print(SupabaseStorageClient().use_local_storage)"
# 输出: True

# 云端环境模拟
RENDER=true SUPABASE_URL=https://test.supabase.co python3 -c "..."
# 输出: False（会降级到本地）
```

### **方法可用性检查**
- ✅ `upload_expense_invoice` - 发票上传主方法
- ✅ `upload_product_file` - 产品文件上传主方法  
- ✅ `_upload_expense_invoice_local` - 本地发票上传
- ✅ `_upload_expense_invoice_cloud` - 云端发票上传
- ✅ `_upload_product_file_local` - 本地产品文件上传
- ✅ `_upload_product_file_cloud` - 云端产品文件上传
- ✅ `delete_expense_invoice` - 文件删除（支持新旧格式）

### **存储桶映射测试**
| bucket_type | 本地目录 | 云端bucket |
|------------|---------|-----------|
| invoice | invoices | invoice-images |
| product | products | product-images |
| rd_product | rd_products | rd-product-images |
| default | invoices | invoice-images |

## 🛡️ 安全特性

### **本地文件访问控制**
- 🔒 **路径验证**: 防止目录遍历攻击
- 📁 **权限检查**: 只能访问storage目录内文件
- 🚫 **404处理**: 不存在的文件返回404

### **云端存储安全**
- 🔑 **API密钥验证**: 无效密钥自动降级
- 🌐 **HTTPS传输**: 所有云端通信使用HTTPS
- 📝 **审计日志**: 记录所有上传操作

## 📊 性能优化

### **图片处理**
- 📐 **尺寸优化**: 自动缩放到最大1200x1200像素
- 🗜️ **质量压缩**: JPEG质量85%，平衡质量和大小
- 📁 **格式统一**: 所有图片转换为JPEG格式

### **文件大小限制**
- 📏 **大小限制**: 最大12MB文件上传
- ⚡ **快速验证**: 上传前检查文件大小
- 💾 **存储优化**: 压缩处理减少存储空间

## 🔄 升级路径

### **现有文件兼容性**
- ✅ **向下兼容**: 不影响现有文件访问
- 🔄 **逐步迁移**: 新文件使用新系统，旧文件保持现状
- 🗂️ **删除支持**: 支持新旧两种文件格式的删除

### **配置迁移**
- 📝 **环境变量**: 通过环境变量控制存储行为
- 🔧 **无代码修改**: 业务代码无需修改
- 📊 **监控日志**: 详细记录迁移过程

## 📝 维护说明

### **日志监控**
```bash
# 查看存储相关日志
grep "存储\|storage\|supabase" app.log

# 监控环境检测
grep "环境检测\|local\|cloud" app.log
```

### **故障排查**
1. **文件上传失败**: 检查存储目录权限和磁盘空间
2. **云端连接失败**: 验证Supabase配置和网络连接
3. **降级频繁**: 检查API密钥有效性和配额限制

### **性能监控**
- 📈 **上传成功率**: 监控上传成功/失败比例
- ⏱️ **响应时间**: 本地存储应<100ms，云端存储应<3s
- 💾 **存储使用**: 定期清理和归档旧文件

---

**版本**: 2.0  
**实现时间**: 2025-08-10  
**适用版本**: PMA v1.3.7+

**系统状态**: ✅ 完全实现并测试通过