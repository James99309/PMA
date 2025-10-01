# Render PostgreSQL 数据库迁移指南

本文档提供从SQLite数据库迁移到Render云平台PostgreSQL数据库的完整解决方案，重点解决SSL连接问题。

## 1. 迁移流程概述

数据库迁移流程主要包括以下步骤：

1. **导出SQLite数据**：将本地SQLite数据导出为JSON格式
2. **修复数据类型**：处理SQLite和PostgreSQL之间的数据类型差异
3. **配置正确的连接参数**：解决SSL连接问题
4. **导入数据**：按照表依赖关系顺序导入数据到Render

## 2. SSL连接问题解决方案

### 问题诊断

Render PostgreSQL数据库要求强制使用SSL连接，但在迁移过程中出现的主要问题：

1. SSL连接意外关闭：`SSL connection has been closed unexpectedly`
2. 证书验证失败：`SSL error: certificate verify failed`
3. SSL连接要求：`FATAL: SSL/TLS required`

### 解决方案

经过多次测试，我们发现以下解决方案可以成功连接Render PostgreSQL：

```python
conn_params = {
    'dbname': 'pma_db_08cz',
    'user': 'pma_db_08cz_user',
    'password': '********',  # 替换为实际密码
    'host': 'dpg-d0a6s03uibrs73b5nelg-a.oregon-postgres.render.com',
    'port': 5432,
    'sslmode': 'require',
    'sslrootcert': 'none'  # 关键参数，禁用证书验证
}
```

**关键配置参数**：
- `sslmode=require`: 要求使用SSL
- `sslrootcert=none`: 禁用根证书验证

### 数据库URL格式修复

PostgreSQL连接URL需要进行以下修复：

1. 将 `postgres://` 修改为 `postgresql://`
2. 确保主机名包含 `.oregon-postgres.render.com` 后缀
3. 添加 `?sslmode=require` 参数
4. 不校验SSL证书

## 3. 数据类型兼容性处理

由于SQLite和PostgreSQL之间的数据类型差异，主要需要解决以下问题：

1. **布尔值转换**：SQLite使用0/1表示布尔值，PostgreSQL使用true/false
2. **日期时间格式**：确保日期时间格式兼容
3. **外键约束**：按照正确的顺序导入数据，避免外键约束错误

特别注意以下字段的转换：
- `is_active`, `is_deleted`, `is_primary`等布尔字段
- `can_view`, `can_edit`, `can_add`, `can_delete`等权限字段

## 4. 导入顺序规划

为解决表依赖关系导致的外键约束问题，应按以下顺序导入数据：

1. `users` - 最基础的表，大多数表依赖它
2. `dictionaries` - 字典表
3. `companies` - 公司表
4. `contacts` - 联系人表
5. `permissions` - 权限表
...
21. `quotation_details` - 报价单明细表

## 5. 迁移工具和脚本说明

| 文件名 | 说明 |
|--------|------|
| `export_sqlite_data.py` | 导出SQLite数据到JSON文件 |
| `fix_export_data.py` | 修复JSON数据中的数据类型 |
| `import_to_render_ordered.py` | 按顺序导入数据到Render |
| `direct_connect.py` | 测试不同SSL参数连接Render |
| `render_migration.sh` | 一站式迁移脚本 |

## 6. 命令参考

### 导出SQLite数据
```bash
python export_sqlite_data.py app.db db_export_full.json
```

### 修复数据类型
```bash
python fix_export_data.py db_export_full.json db_export_fixed.json
```

### 导入数据到Render
```bash
python import_to_render_ordered.py "postgresql://用户名:密码@主机名/数据库名?sslmode=require" db_export_fixed.json
```

### 一站式迁移
```bash
bash render_migration.sh all
```

## 7. 常见问题排查

1. **SSL连接失败**
   - 确保使用了正确的`sslmode=require`和`sslrootcert=none`参数
   - 检查主机名是否包含完整域名

2. **数据类型错误**
   - 检查布尔字段是否已正确转换
   - 确认日期时间格式是否兼容

3. **外键约束错误**
   - 使用`SET session_replication_role = 'replica';`临时禁用外键约束
   - 按照正确的表依赖顺序导入

4. **权限问题**
   - 确保使用的数据库账号有足够的权限
   - 如果缺少权限，尝试使用备用方案，如单行插入

## 8. 迁移后验证

迁移完成后，请执行以下验证：

1. 检查关键表的记录数是否与源数据库一致
2. 验证关键业务数据是否完整
3. 测试应用程序与新数据库的连接
4. 确认应用功能是否正常

## 9. 附录：Render数据库配置

在Flask应用中配置Render PostgreSQL连接示例：

```python
# config.py
import os

class Config:
    # ...其他配置...
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    
    # 添加SSL参数
    if 'postgresql://' in SQLALCHEMY_DATABASE_URI and 'render.com' in SQLALCHEMY_DATABASE_URI:
        if '?' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?sslmode=require'
        else:
            SQLALCHEMY_DATABASE_URI += '&sslmode=require'
            
    # ...其他配置...
```

## 10. 联系支持

如果遇到其他问题，请联系系统管理员或技术支持。 

本文档提供从SQLite数据库迁移到Render云平台PostgreSQL数据库的完整解决方案，重点解决SSL连接问题。

## 1. 迁移流程概述

数据库迁移流程主要包括以下步骤：

1. **导出SQLite数据**：将本地SQLite数据导出为JSON格式
2. **修复数据类型**：处理SQLite和PostgreSQL之间的数据类型差异
3. **配置正确的连接参数**：解决SSL连接问题
4. **导入数据**：按照表依赖关系顺序导入数据到Render

## 2. SSL连接问题解决方案

### 问题诊断

Render PostgreSQL数据库要求强制使用SSL连接，但在迁移过程中出现的主要问题：

1. SSL连接意外关闭：`SSL connection has been closed unexpectedly`
2. 证书验证失败：`SSL error: certificate verify failed`
3. SSL连接要求：`FATAL: SSL/TLS required`

### 解决方案

经过多次测试，我们发现以下解决方案可以成功连接Render PostgreSQL：

```python
conn_params = {
    'dbname': 'pma_db_08cz',
    'user': 'pma_db_08cz_user',
    'password': '********',  # 替换为实际密码
    'host': 'dpg-d0a6s03uibrs73b5nelg-a.oregon-postgres.render.com',
    'port': 5432,
    'sslmode': 'require',
    'sslrootcert': 'none'  # 关键参数，禁用证书验证
}
```

**关键配置参数**：
- `sslmode=require`: 要求使用SSL
- `sslrootcert=none`: 禁用根证书验证

### 数据库URL格式修复

PostgreSQL连接URL需要进行以下修复：

1. 将 `postgres://` 修改为 `postgresql://`
2. 确保主机名包含 `.oregon-postgres.render.com` 后缀
3. 添加 `?sslmode=require` 参数
4. 不校验SSL证书

## 3. 数据类型兼容性处理

由于SQLite和PostgreSQL之间的数据类型差异，主要需要解决以下问题：

1. **布尔值转换**：SQLite使用0/1表示布尔值，PostgreSQL使用true/false
2. **日期时间格式**：确保日期时间格式兼容
3. **外键约束**：按照正确的顺序导入数据，避免外键约束错误

特别注意以下字段的转换：
- `is_active`, `is_deleted`, `is_primary`等布尔字段
- `can_view`, `can_edit`, `can_add`, `can_delete`等权限字段

## 4. 导入顺序规划

为解决表依赖关系导致的外键约束问题，应按以下顺序导入数据：

1. `users` - 最基础的表，大多数表依赖它
2. `dictionaries` - 字典表
3. `companies` - 公司表
4. `contacts` - 联系人表
5. `permissions` - 权限表
...
21. `quotation_details` - 报价单明细表

## 5. 迁移工具和脚本说明

| 文件名 | 说明 |
|--------|------|
| `export_sqlite_data.py` | 导出SQLite数据到JSON文件 |
| `fix_export_data.py` | 修复JSON数据中的数据类型 |
| `import_to_render_ordered.py` | 按顺序导入数据到Render |
| `direct_connect.py` | 测试不同SSL参数连接Render |
| `render_migration.sh` | 一站式迁移脚本 |

## 6. 命令参考

### 导出SQLite数据
```bash
python export_sqlite_data.py app.db db_export_full.json
```

### 修复数据类型
```bash
python fix_export_data.py db_export_full.json db_export_fixed.json
```

### 导入数据到Render
```bash
python import_to_render_ordered.py "postgresql://用户名:密码@主机名/数据库名?sslmode=require" db_export_fixed.json
```

### 一站式迁移
```bash
bash render_migration.sh all
```

## 7. 常见问题排查

1. **SSL连接失败**
   - 确保使用了正确的`sslmode=require`和`sslrootcert=none`参数
   - 检查主机名是否包含完整域名

2. **数据类型错误**
   - 检查布尔字段是否已正确转换
   - 确认日期时间格式是否兼容

3. **外键约束错误**
   - 使用`SET session_replication_role = 'replica';`临时禁用外键约束
   - 按照正确的表依赖顺序导入

4. **权限问题**
   - 确保使用的数据库账号有足够的权限
   - 如果缺少权限，尝试使用备用方案，如单行插入

## 8. 迁移后验证

迁移完成后，请执行以下验证：

1. 检查关键表的记录数是否与源数据库一致
2. 验证关键业务数据是否完整
3. 测试应用程序与新数据库的连接
4. 确认应用功能是否正常

## 9. 附录：Render数据库配置

在Flask应用中配置Render PostgreSQL连接示例：

```python
# config.py
import os

class Config:
    # ...其他配置...
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    
    # 添加SSL参数
    if 'postgresql://' in SQLALCHEMY_DATABASE_URI and 'render.com' in SQLALCHEMY_DATABASE_URI:
        if '?' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?sslmode=require'
        else:
            SQLALCHEMY_DATABASE_URI += '&sslmode=require'
            
    # ...其他配置...
```

## 10. 联系支持

如果遇到其他问题，请联系系统管理员或技术支持。 
 
 

本文档提供从SQLite数据库迁移到Render云平台PostgreSQL数据库的完整解决方案，重点解决SSL连接问题。

## 1. 迁移流程概述

数据库迁移流程主要包括以下步骤：

1. **导出SQLite数据**：将本地SQLite数据导出为JSON格式
2. **修复数据类型**：处理SQLite和PostgreSQL之间的数据类型差异
3. **配置正确的连接参数**：解决SSL连接问题
4. **导入数据**：按照表依赖关系顺序导入数据到Render

## 2. SSL连接问题解决方案

### 问题诊断

Render PostgreSQL数据库要求强制使用SSL连接，但在迁移过程中出现的主要问题：

1. SSL连接意外关闭：`SSL connection has been closed unexpectedly`
2. 证书验证失败：`SSL error: certificate verify failed`
3. SSL连接要求：`FATAL: SSL/TLS required`

### 解决方案

经过多次测试，我们发现以下解决方案可以成功连接Render PostgreSQL：

```python
conn_params = {
    'dbname': 'pma_db_08cz',
    'user': 'pma_db_08cz_user',
    'password': '********',  # 替换为实际密码
    'host': 'dpg-d0a6s03uibrs73b5nelg-a.oregon-postgres.render.com',
    'port': 5432,
    'sslmode': 'require',
    'sslrootcert': 'none'  # 关键参数，禁用证书验证
}
```

**关键配置参数**：
- `sslmode=require`: 要求使用SSL
- `sslrootcert=none`: 禁用根证书验证

### 数据库URL格式修复

PostgreSQL连接URL需要进行以下修复：

1. 将 `postgres://` 修改为 `postgresql://`
2. 确保主机名包含 `.oregon-postgres.render.com` 后缀
3. 添加 `?sslmode=require` 参数
4. 不校验SSL证书

## 3. 数据类型兼容性处理

由于SQLite和PostgreSQL之间的数据类型差异，主要需要解决以下问题：

1. **布尔值转换**：SQLite使用0/1表示布尔值，PostgreSQL使用true/false
2. **日期时间格式**：确保日期时间格式兼容
3. **外键约束**：按照正确的顺序导入数据，避免外键约束错误

特别注意以下字段的转换：
- `is_active`, `is_deleted`, `is_primary`等布尔字段
- `can_view`, `can_edit`, `can_add`, `can_delete`等权限字段

## 4. 导入顺序规划

为解决表依赖关系导致的外键约束问题，应按以下顺序导入数据：

1. `users` - 最基础的表，大多数表依赖它
2. `dictionaries` - 字典表
3. `companies` - 公司表
4. `contacts` - 联系人表
5. `permissions` - 权限表
...
21. `quotation_details` - 报价单明细表

## 5. 迁移工具和脚本说明

| 文件名 | 说明 |
|--------|------|
| `export_sqlite_data.py` | 导出SQLite数据到JSON文件 |
| `fix_export_data.py` | 修复JSON数据中的数据类型 |
| `import_to_render_ordered.py` | 按顺序导入数据到Render |
| `direct_connect.py` | 测试不同SSL参数连接Render |
| `render_migration.sh` | 一站式迁移脚本 |

## 6. 命令参考

### 导出SQLite数据
```bash
python export_sqlite_data.py app.db db_export_full.json
```

### 修复数据类型
```bash
python fix_export_data.py db_export_full.json db_export_fixed.json
```

### 导入数据到Render
```bash
python import_to_render_ordered.py "postgresql://用户名:密码@主机名/数据库名?sslmode=require" db_export_fixed.json
```

### 一站式迁移
```bash
bash render_migration.sh all
```

## 7. 常见问题排查

1. **SSL连接失败**
   - 确保使用了正确的`sslmode=require`和`sslrootcert=none`参数
   - 检查主机名是否包含完整域名

2. **数据类型错误**
   - 检查布尔字段是否已正确转换
   - 确认日期时间格式是否兼容

3. **外键约束错误**
   - 使用`SET session_replication_role = 'replica';`临时禁用外键约束
   - 按照正确的表依赖顺序导入

4. **权限问题**
   - 确保使用的数据库账号有足够的权限
   - 如果缺少权限，尝试使用备用方案，如单行插入

## 8. 迁移后验证

迁移完成后，请执行以下验证：

1. 检查关键表的记录数是否与源数据库一致
2. 验证关键业务数据是否完整
3. 测试应用程序与新数据库的连接
4. 确认应用功能是否正常

## 9. 附录：Render数据库配置

在Flask应用中配置Render PostgreSQL连接示例：

```python
# config.py
import os

class Config:
    # ...其他配置...
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    
    # 添加SSL参数
    if 'postgresql://' in SQLALCHEMY_DATABASE_URI and 'render.com' in SQLALCHEMY_DATABASE_URI:
        if '?' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?sslmode=require'
        else:
            SQLALCHEMY_DATABASE_URI += '&sslmode=require'
            
    # ...其他配置...
```

## 10. 联系支持

如果遇到其他问题，请联系系统管理员或技术支持。 

本文档提供从SQLite数据库迁移到Render云平台PostgreSQL数据库的完整解决方案，重点解决SSL连接问题。

## 1. 迁移流程概述

数据库迁移流程主要包括以下步骤：

1. **导出SQLite数据**：将本地SQLite数据导出为JSON格式
2. **修复数据类型**：处理SQLite和PostgreSQL之间的数据类型差异
3. **配置正确的连接参数**：解决SSL连接问题
4. **导入数据**：按照表依赖关系顺序导入数据到Render

## 2. SSL连接问题解决方案

### 问题诊断

Render PostgreSQL数据库要求强制使用SSL连接，但在迁移过程中出现的主要问题：

1. SSL连接意外关闭：`SSL connection has been closed unexpectedly`
2. 证书验证失败：`SSL error: certificate verify failed`
3. SSL连接要求：`FATAL: SSL/TLS required`

### 解决方案

经过多次测试，我们发现以下解决方案可以成功连接Render PostgreSQL：

```python
conn_params = {
    'dbname': 'pma_db_08cz',
    'user': 'pma_db_08cz_user',
    'password': '********',  # 替换为实际密码
    'host': 'dpg-d0a6s03uibrs73b5nelg-a.oregon-postgres.render.com',
    'port': 5432,
    'sslmode': 'require',
    'sslrootcert': 'none'  # 关键参数，禁用证书验证
}
```

**关键配置参数**：
- `sslmode=require`: 要求使用SSL
- `sslrootcert=none`: 禁用根证书验证

### 数据库URL格式修复

PostgreSQL连接URL需要进行以下修复：

1. 将 `postgres://` 修改为 `postgresql://`
2. 确保主机名包含 `.oregon-postgres.render.com` 后缀
3. 添加 `?sslmode=require` 参数
4. 不校验SSL证书

## 3. 数据类型兼容性处理

由于SQLite和PostgreSQL之间的数据类型差异，主要需要解决以下问题：

1. **布尔值转换**：SQLite使用0/1表示布尔值，PostgreSQL使用true/false
2. **日期时间格式**：确保日期时间格式兼容
3. **外键约束**：按照正确的顺序导入数据，避免外键约束错误

特别注意以下字段的转换：
- `is_active`, `is_deleted`, `is_primary`等布尔字段
- `can_view`, `can_edit`, `can_add`, `can_delete`等权限字段

## 4. 导入顺序规划

为解决表依赖关系导致的外键约束问题，应按以下顺序导入数据：

1. `users` - 最基础的表，大多数表依赖它
2. `dictionaries` - 字典表
3. `companies` - 公司表
4. `contacts` - 联系人表
5. `permissions` - 权限表
...
21. `quotation_details` - 报价单明细表

## 5. 迁移工具和脚本说明

| 文件名 | 说明 |
|--------|------|
| `export_sqlite_data.py` | 导出SQLite数据到JSON文件 |
| `fix_export_data.py` | 修复JSON数据中的数据类型 |
| `import_to_render_ordered.py` | 按顺序导入数据到Render |
| `direct_connect.py` | 测试不同SSL参数连接Render |
| `render_migration.sh` | 一站式迁移脚本 |

## 6. 命令参考

### 导出SQLite数据
```bash
python export_sqlite_data.py app.db db_export_full.json
```

### 修复数据类型
```bash
python fix_export_data.py db_export_full.json db_export_fixed.json
```

### 导入数据到Render
```bash
python import_to_render_ordered.py "postgresql://用户名:密码@主机名/数据库名?sslmode=require" db_export_fixed.json
```

### 一站式迁移
```bash
bash render_migration.sh all
```

## 7. 常见问题排查

1. **SSL连接失败**
   - 确保使用了正确的`sslmode=require`和`sslrootcert=none`参数
   - 检查主机名是否包含完整域名

2. **数据类型错误**
   - 检查布尔字段是否已正确转换
   - 确认日期时间格式是否兼容

3. **外键约束错误**
   - 使用`SET session_replication_role = 'replica';`临时禁用外键约束
   - 按照正确的表依赖顺序导入

4. **权限问题**
   - 确保使用的数据库账号有足够的权限
   - 如果缺少权限，尝试使用备用方案，如单行插入

## 8. 迁移后验证

迁移完成后，请执行以下验证：

1. 检查关键表的记录数是否与源数据库一致
2. 验证关键业务数据是否完整
3. 测试应用程序与新数据库的连接
4. 确认应用功能是否正常

## 9. 附录：Render数据库配置

在Flask应用中配置Render PostgreSQL连接示例：

```python
# config.py
import os

class Config:
    # ...其他配置...
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    
    # 添加SSL参数
    if 'postgresql://' in SQLALCHEMY_DATABASE_URI and 'render.com' in SQLALCHEMY_DATABASE_URI:
        if '?' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?sslmode=require'
        else:
            SQLALCHEMY_DATABASE_URI += '&sslmode=require'
            
    # ...其他配置...
```

## 10. 联系支持

如果遇到其他问题，请联系系统管理员或技术支持。 
 
 