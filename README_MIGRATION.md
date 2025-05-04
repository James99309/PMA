# Render数据库迁移指南

本项目包含了一系列用于将本地PostgreSQL数据库迁移到Render云数据库的脚本。

## 迁移脚本说明

- `update_db_config.py` - 更新数据库配置，修复连接字符串中的主机名
- `create_render_db_tables.py` - 在Render数据库中创建表结构
- `migrate_data_to_render.py` - 将本地数据迁移到Render数据库
- `fix_dev_products_fk.py` - 修复dev_products表的外键约束问题
- `render_migration_run.py` - 整合执行脚本，按顺序运行所有迁移步骤

## 推送到GitHub

按照以下步骤将迁移脚本推送到GitHub：

```bash
# 创建迁移脚本目录
mkdir -p db_migration

# 复制所有迁移脚本到该目录
cp update_db_config.py create_render_db_tables.py migrate_data_to_render.py fix_dev_products_fk.py render_migration_run.py db_migration/

# 添加到Git
git add db_migration/
git add render_db_fix_summary.md deploy_instructions.md

# 提交更改
git commit -m "添加Render数据库迁移脚本"

# 推送到GitHub
git push origin main
```

## 在Render上执行迁移

### 方法1：使用Render Shell执行

1. 登录Render控制台
2. 进入您的Web Service
3. 点击"Shell"标签
4. 执行以下命令：

```bash
cd /opt/render/project/src
python db_migration/render_migration_run.py
```

### 方法2：通过环境变量和启动命令执行

1. 登录Render控制台
2. 进入您的Web Service
3. 点击"Environment"标签
4. 设置以下环境变量：

```
DATABASE_URL=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
SQLALCHEMY_DATABASE_URI=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
```

5. 点击"Settings"标签
6. 在"Build Command"中添加：

```bash
python db_migration/render_migration_run.py
```

7. 点击"Manual Deploy"按钮，选择"Clear build cache & deploy"

## 验证迁移结果

迁移完成后，您可以通过以下方式验证：

1. 检查Render日志，确保没有错误
2. 使用psql命令连接到数据库检查表结构和数据：

```bash
render psql dpg-d0b1gl1r0fns73d1jc1g-a
```

3. 或者使用测试脚本验证连接：

```bash
python test_db_connection.py
```

## 注意事项

- 迁移过程会生成详细的日志文件 `render_migration.log`
- 如果某个步骤失败，可以单独执行对应的迁移脚本
- 请确保Render环境中安装了所有必要的Python包：
  - psycopg2-binary
  - sqlalchemy 

本项目包含了一系列用于将本地PostgreSQL数据库迁移到Render云数据库的脚本。

## 迁移脚本说明

- `update_db_config.py` - 更新数据库配置，修复连接字符串中的主机名
- `create_render_db_tables.py` - 在Render数据库中创建表结构
- `migrate_data_to_render.py` - 将本地数据迁移到Render数据库
- `fix_dev_products_fk.py` - 修复dev_products表的外键约束问题
- `render_migration_run.py` - 整合执行脚本，按顺序运行所有迁移步骤

## 推送到GitHub

按照以下步骤将迁移脚本推送到GitHub：

```bash
# 创建迁移脚本目录
mkdir -p db_migration

# 复制所有迁移脚本到该目录
cp update_db_config.py create_render_db_tables.py migrate_data_to_render.py fix_dev_products_fk.py render_migration_run.py db_migration/

# 添加到Git
git add db_migration/
git add render_db_fix_summary.md deploy_instructions.md

# 提交更改
git commit -m "添加Render数据库迁移脚本"

# 推送到GitHub
git push origin main
```

## 在Render上执行迁移

### 方法1：使用Render Shell执行

1. 登录Render控制台
2. 进入您的Web Service
3. 点击"Shell"标签
4. 执行以下命令：

```bash
cd /opt/render/project/src
python db_migration/render_migration_run.py
```

### 方法2：通过环境变量和启动命令执行

1. 登录Render控制台
2. 进入您的Web Service
3. 点击"Environment"标签
4. 设置以下环境变量：

```
DATABASE_URL=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
SQLALCHEMY_DATABASE_URI=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
```

5. 点击"Settings"标签
6. 在"Build Command"中添加：

```bash
python db_migration/render_migration_run.py
```

7. 点击"Manual Deploy"按钮，选择"Clear build cache & deploy"

## 验证迁移结果

迁移完成后，您可以通过以下方式验证：

1. 检查Render日志，确保没有错误
2. 使用psql命令连接到数据库检查表结构和数据：

```bash
render psql dpg-d0b1gl1r0fns73d1jc1g-a
```

3. 或者使用测试脚本验证连接：

```bash
python test_db_connection.py
```

## 注意事项

- 迁移过程会生成详细的日志文件 `render_migration.log`
- 如果某个步骤失败，可以单独执行对应的迁移脚本
- 请确保Render环境中安装了所有必要的Python包：
  - psycopg2-binary
  - sqlalchemy 