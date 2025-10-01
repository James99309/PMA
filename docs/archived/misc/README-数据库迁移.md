# SQLite到Render PostgreSQL数据库迁移指南

本指南详细说明了如何将本地SQLite数据库迁移到Render云平台的PostgreSQL数据库。我们提供了完整的工具链，包括SSL连接问题的解决方案。

## 迁移工具概述

我们开发了一套完整的工具链来处理数据迁移过程中的各种问题：

1. **一站式迁移脚本**: `render_migration.sh` - 自动执行完整迁移流程
2. **数据导出工具**: `export_sqlite_data.py` - 导出SQLite数据到JSON
3. **数据导入工具**: `import_data_to_render.py` - 将JSON数据导入PostgreSQL
4. **连接测试工具**: `connect_render_db.py` - 测试与Render数据库的连接
5. **URL修复工具**: `fix_render_db_issues.py` - 修复Render数据库URL和SSL问题

## 准备工作

迁移前请确保：

1. 已获取Render PostgreSQL数据库的连接URL
2. 已安装必要依赖：
   ```
   pip install sqlalchemy psycopg2-binary pandas
   ```
3. 本地SQLite数据库文件可访问

## 全自动迁移（推荐）

使用一站式脚本可自动处理整个迁移流程：

```bash
# 设置Render数据库URL
export RENDER_DB_URL="postgresql://user:password@host/database"

# 执行迁移脚本
./render_migration.sh
```

脚本会自动：
1. 检测和修复数据库URL格式
2. 查找并备份本地SQLite数据库
3. 测试与Render数据库的连接
4. 导出SQLite数据
5. 导入数据到Render PostgreSQL

## 手动迁移步骤

如果需要更精细的控制，可以分步执行迁移：

### 1. 导出SQLite数据

```bash
python export_sqlite_data.py --db app.db --output data_export.json
```

### 2. 测试Render数据库连接

```bash
python connect_render_db.py --disable-ssl-verify
```

### 3. 导入数据到Render

```bash
python import_data_to_render.py --json-file data_export.json --clear
```

### 4. 仅导入特定表

```bash
python import_data_to_render.py --json-file data_export.json --tables "users,permissions,products"
```

## SSL连接问题解决

如果遇到SSL连接问题，可使用以下工具：

```bash
# 修复数据库URL和SSL配置
python fix_render_db_issues.py --test --db-url "$RENDER_DB_URL"

# 测试SSL连接
python db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require
```

## 数据库URL格式说明

Render提供的数据库URL需要进行以下修正：

1. 将`postgres://`替换为`postgresql://`
2. 确保主机名包含完整域名（例如：`dpg-xxxxx.oregon-postgres.render.com`）
3. 添加SSL参数：`?sslmode=require`

正确的URL格式示例：
```
postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/database_name?sslmode=require
```

## 常见问题

### SSL连接错误

问题：`SSL connection has been closed unexpectedly`
解决：确保URL中包含`sslmode=require`参数，并且主机名正确

### 连接超时

问题：连接建立过程中超时
解决：检查网络连接，确保Render数据库服务正常运行

### 表结构不匹配

问题：列名不匹配导致导入失败
解决：使用`--tables`参数导入特定表，或修改JSON数据以匹配目标表结构

## 数据备份

迁移工具会自动创建SQLite数据库的备份，存储在`./backups/`目录下。导出的JSON数据也会保存在此目录，可用于重复导入或恢复。

## 注意事项

1. 导入时使用`--clear`参数会清空目标表，请谨慎操作
2. 大型数据库可能需要较长时间导入，请耐心等待
3. 如遇到连接中断，可重试导入过程，工具支持恢复导入

## 支持与问题反馈

如有问题，请查看日志文件：
- `db_migration.log`
- `data_import.log`

这些日志文件包含详细的错误信息和诊断数据。 

本指南详细说明了如何将本地SQLite数据库迁移到Render云平台的PostgreSQL数据库。我们提供了完整的工具链，包括SSL连接问题的解决方案。

## 迁移工具概述

我们开发了一套完整的工具链来处理数据迁移过程中的各种问题：

1. **一站式迁移脚本**: `render_migration.sh` - 自动执行完整迁移流程
2. **数据导出工具**: `export_sqlite_data.py` - 导出SQLite数据到JSON
3. **数据导入工具**: `import_data_to_render.py` - 将JSON数据导入PostgreSQL
4. **连接测试工具**: `connect_render_db.py` - 测试与Render数据库的连接
5. **URL修复工具**: `fix_render_db_issues.py` - 修复Render数据库URL和SSL问题

## 准备工作

迁移前请确保：

1. 已获取Render PostgreSQL数据库的连接URL
2. 已安装必要依赖：
   ```
   pip install sqlalchemy psycopg2-binary pandas
   ```
3. 本地SQLite数据库文件可访问

## 全自动迁移（推荐）

使用一站式脚本可自动处理整个迁移流程：

```bash
# 设置Render数据库URL
export RENDER_DB_URL="postgresql://user:password@host/database"

# 执行迁移脚本
./render_migration.sh
```

脚本会自动：
1. 检测和修复数据库URL格式
2. 查找并备份本地SQLite数据库
3. 测试与Render数据库的连接
4. 导出SQLite数据
5. 导入数据到Render PostgreSQL

## 手动迁移步骤

如果需要更精细的控制，可以分步执行迁移：

### 1. 导出SQLite数据

```bash
python export_sqlite_data.py --db app.db --output data_export.json
```

### 2. 测试Render数据库连接

```bash
python connect_render_db.py --disable-ssl-verify
```

### 3. 导入数据到Render

```bash
python import_data_to_render.py --json-file data_export.json --clear
```

### 4. 仅导入特定表

```bash
python import_data_to_render.py --json-file data_export.json --tables "users,permissions,products"
```

## SSL连接问题解决

如果遇到SSL连接问题，可使用以下工具：

```bash
# 修复数据库URL和SSL配置
python fix_render_db_issues.py --test --db-url "$RENDER_DB_URL"

# 测试SSL连接
python db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require
```

## 数据库URL格式说明

Render提供的数据库URL需要进行以下修正：

1. 将`postgres://`替换为`postgresql://`
2. 确保主机名包含完整域名（例如：`dpg-xxxxx.oregon-postgres.render.com`）
3. 添加SSL参数：`?sslmode=require`

正确的URL格式示例：
```
postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/database_name?sslmode=require
```

## 常见问题

### SSL连接错误

问题：`SSL connection has been closed unexpectedly`
解决：确保URL中包含`sslmode=require`参数，并且主机名正确

### 连接超时

问题：连接建立过程中超时
解决：检查网络连接，确保Render数据库服务正常运行

### 表结构不匹配

问题：列名不匹配导致导入失败
解决：使用`--tables`参数导入特定表，或修改JSON数据以匹配目标表结构

## 数据备份

迁移工具会自动创建SQLite数据库的备份，存储在`./backups/`目录下。导出的JSON数据也会保存在此目录，可用于重复导入或恢复。

## 注意事项

1. 导入时使用`--clear`参数会清空目标表，请谨慎操作
2. 大型数据库可能需要较长时间导入，请耐心等待
3. 如遇到连接中断，可重试导入过程，工具支持恢复导入

## 支持与问题反馈

如有问题，请查看日志文件：
- `db_migration.log`
- `data_import.log`

这些日志文件包含详细的错误信息和诊断数据。 
 
 

本指南详细说明了如何将本地SQLite数据库迁移到Render云平台的PostgreSQL数据库。我们提供了完整的工具链，包括SSL连接问题的解决方案。

## 迁移工具概述

我们开发了一套完整的工具链来处理数据迁移过程中的各种问题：

1. **一站式迁移脚本**: `render_migration.sh` - 自动执行完整迁移流程
2. **数据导出工具**: `export_sqlite_data.py` - 导出SQLite数据到JSON
3. **数据导入工具**: `import_data_to_render.py` - 将JSON数据导入PostgreSQL
4. **连接测试工具**: `connect_render_db.py` - 测试与Render数据库的连接
5. **URL修复工具**: `fix_render_db_issues.py` - 修复Render数据库URL和SSL问题

## 准备工作

迁移前请确保：

1. 已获取Render PostgreSQL数据库的连接URL
2. 已安装必要依赖：
   ```
   pip install sqlalchemy psycopg2-binary pandas
   ```
3. 本地SQLite数据库文件可访问

## 全自动迁移（推荐）

使用一站式脚本可自动处理整个迁移流程：

```bash
# 设置Render数据库URL
export RENDER_DB_URL="postgresql://user:password@host/database"

# 执行迁移脚本
./render_migration.sh
```

脚本会自动：
1. 检测和修复数据库URL格式
2. 查找并备份本地SQLite数据库
3. 测试与Render数据库的连接
4. 导出SQLite数据
5. 导入数据到Render PostgreSQL

## 手动迁移步骤

如果需要更精细的控制，可以分步执行迁移：

### 1. 导出SQLite数据

```bash
python export_sqlite_data.py --db app.db --output data_export.json
```

### 2. 测试Render数据库连接

```bash
python connect_render_db.py --disable-ssl-verify
```

### 3. 导入数据到Render

```bash
python import_data_to_render.py --json-file data_export.json --clear
```

### 4. 仅导入特定表

```bash
python import_data_to_render.py --json-file data_export.json --tables "users,permissions,products"
```

## SSL连接问题解决

如果遇到SSL连接问题，可使用以下工具：

```bash
# 修复数据库URL和SSL配置
python fix_render_db_issues.py --test --db-url "$RENDER_DB_URL"

# 测试SSL连接
python db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require
```

## 数据库URL格式说明

Render提供的数据库URL需要进行以下修正：

1. 将`postgres://`替换为`postgresql://`
2. 确保主机名包含完整域名（例如：`dpg-xxxxx.oregon-postgres.render.com`）
3. 添加SSL参数：`?sslmode=require`

正确的URL格式示例：
```
postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/database_name?sslmode=require
```

## 常见问题

### SSL连接错误

问题：`SSL connection has been closed unexpectedly`
解决：确保URL中包含`sslmode=require`参数，并且主机名正确

### 连接超时

问题：连接建立过程中超时
解决：检查网络连接，确保Render数据库服务正常运行

### 表结构不匹配

问题：列名不匹配导致导入失败
解决：使用`--tables`参数导入特定表，或修改JSON数据以匹配目标表结构

## 数据备份

迁移工具会自动创建SQLite数据库的备份，存储在`./backups/`目录下。导出的JSON数据也会保存在此目录，可用于重复导入或恢复。

## 注意事项

1. 导入时使用`--clear`参数会清空目标表，请谨慎操作
2. 大型数据库可能需要较长时间导入，请耐心等待
3. 如遇到连接中断，可重试导入过程，工具支持恢复导入

## 支持与问题反馈

如有问题，请查看日志文件：
- `db_migration.log`
- `data_import.log`

这些日志文件包含详细的错误信息和诊断数据。 

本指南详细说明了如何将本地SQLite数据库迁移到Render云平台的PostgreSQL数据库。我们提供了完整的工具链，包括SSL连接问题的解决方案。

## 迁移工具概述

我们开发了一套完整的工具链来处理数据迁移过程中的各种问题：

1. **一站式迁移脚本**: `render_migration.sh` - 自动执行完整迁移流程
2. **数据导出工具**: `export_sqlite_data.py` - 导出SQLite数据到JSON
3. **数据导入工具**: `import_data_to_render.py` - 将JSON数据导入PostgreSQL
4. **连接测试工具**: `connect_render_db.py` - 测试与Render数据库的连接
5. **URL修复工具**: `fix_render_db_issues.py` - 修复Render数据库URL和SSL问题

## 准备工作

迁移前请确保：

1. 已获取Render PostgreSQL数据库的连接URL
2. 已安装必要依赖：
   ```
   pip install sqlalchemy psycopg2-binary pandas
   ```
3. 本地SQLite数据库文件可访问

## 全自动迁移（推荐）

使用一站式脚本可自动处理整个迁移流程：

```bash
# 设置Render数据库URL
export RENDER_DB_URL="postgresql://user:password@host/database"

# 执行迁移脚本
./render_migration.sh
```

脚本会自动：
1. 检测和修复数据库URL格式
2. 查找并备份本地SQLite数据库
3. 测试与Render数据库的连接
4. 导出SQLite数据
5. 导入数据到Render PostgreSQL

## 手动迁移步骤

如果需要更精细的控制，可以分步执行迁移：

### 1. 导出SQLite数据

```bash
python export_sqlite_data.py --db app.db --output data_export.json
```

### 2. 测试Render数据库连接

```bash
python connect_render_db.py --disable-ssl-verify
```

### 3. 导入数据到Render

```bash
python import_data_to_render.py --json-file data_export.json --clear
```

### 4. 仅导入特定表

```bash
python import_data_to_render.py --json-file data_export.json --tables "users,permissions,products"
```

## SSL连接问题解决

如果遇到SSL连接问题，可使用以下工具：

```bash
# 修复数据库URL和SSL配置
python fix_render_db_issues.py --test --db-url "$RENDER_DB_URL"

# 测试SSL连接
python db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require
```

## 数据库URL格式说明

Render提供的数据库URL需要进行以下修正：

1. 将`postgres://`替换为`postgresql://`
2. 确保主机名包含完整域名（例如：`dpg-xxxxx.oregon-postgres.render.com`）
3. 添加SSL参数：`?sslmode=require`

正确的URL格式示例：
```
postgresql://username:password@dpg-xxxxx.oregon-postgres.render.com/database_name?sslmode=require
```

## 常见问题

### SSL连接错误

问题：`SSL connection has been closed unexpectedly`
解决：确保URL中包含`sslmode=require`参数，并且主机名正确

### 连接超时

问题：连接建立过程中超时
解决：检查网络连接，确保Render数据库服务正常运行

### 表结构不匹配

问题：列名不匹配导致导入失败
解决：使用`--tables`参数导入特定表，或修改JSON数据以匹配目标表结构

## 数据备份

迁移工具会自动创建SQLite数据库的备份，存储在`./backups/`目录下。导出的JSON数据也会保存在此目录，可用于重复导入或恢复。

## 注意事项

1. 导入时使用`--clear`参数会清空目标表，请谨慎操作
2. 大型数据库可能需要较长时间导入，请耐心等待
3. 如遇到连接中断，可重试导入过程，工具支持恢复导入

## 支持与问题反馈

如有问题，请查看日志文件：
- `db_migration.log`
- `data_import.log`

这些日志文件包含详细的错误信息和诊断数据。 
 
 