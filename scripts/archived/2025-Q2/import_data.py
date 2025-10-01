import json
from sqlite_to_postgres import json_to_postgres

# 从备份的JSON加载数据
with open('db_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 导入数据到PostgreSQL
json_to_postgres(data, 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
print('数据导入完成！') 
from sqlite_to_postgres import json_to_postgres

# 从备份的JSON加载数据
with open('db_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 导入数据到PostgreSQL
json_to_postgres(data, 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
print('数据导入完成！') 