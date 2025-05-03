# Render部署指南

## 数据库连接修复

根据错误日志分析，部署在Render上的应用无法连接到数据库，因为应用使用了错误的数据库主机名 `dpg-d0a6s03uibrs73b5nelg-a`，而不是正确的主机名 `dpg-d0b1gl1r0fns73d1jc1g-a`。

### 修复步骤

1. **执行数据库配置更新脚本**

   ```bash
   python update_db_config.py
   ```

   此脚本将：
   - 查找包含旧数据库主机名的配置文件
   - 更新这些文件中的数据库主机名
   - 创建环境变量更新脚本 `update_env.sh`

2. **更新环境变量**

   ```bash
   source update_env.sh
   ```

3. **在Render管理面板中修改环境变量**

   请在Render管理面板中添加或更新以下环境变量：

   | 环境变量名称 | 值 |
   |------------|-----|
   | DATABASE_URL | postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d |
   | SQLALCHEMY_DATABASE_URI | postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d |

4. **重新部署应用**

   在Render面板中点击"Manual Deploy"按钮，选择"Clear build cache & deploy"选项。

## 验证数据库连接

部署完成后，请检查应用日志以确认数据库连接是否正常。如果日志中仍然显示数据库连接错误，请尝试以下步骤：

1. **验证数据库是否可访问**

   可以使用以下命令连接到数据库：

   ```bash
   render psql dpg-d0b1gl1r0fns73d1jc1g-a
   ```

2. **在本地测试连接**

   使用正确的连接字符串在本地测试是否可以连接到数据库：

   ```python
   import psycopg2
   conn = psycopg2.connect("postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d")
   print("Connection successful!")
   conn.close()
   ```

## 其他注意事项

- 确保您的应用有足够的权限连接到数据库
- 检查数据库防火墙设置，确保允许来自应用服务器的连接
- 如果问题仍然存在，请联系Render支持团队

## 有用的命令

在排查数据库问题时，以下命令可能有用：

```bash
# 检查数据库连接
render psql dpg-d0b1gl1r0fns73d1jc1g-a

# 查看数据库表
\dt

# 备份数据库
pg_dump -h dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com -U pma_db_sp8d_user -d pma_db_sp8d > backup.sql

# 恢复数据库
psql -h dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com -U pma_db_sp8d_user -d pma_db_sp8d < backup.sql
``` 