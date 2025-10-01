# 🚨 紧急修复：云端数据库字段缺失

## 问题现象
云端运行报错：
```
(psycopg2.errors.UndefinedColumn) column projects.rating does not exist
```

## 问题原因
- 项目模型定义了 `rating` 字段，但云端数据库中缺少此字段
- SQLAlchemy 查询时会选择所有字段，导致查询失败

## 紧急解决方案

### 方法1：运行自动修复脚本（推荐）
```bash
python cloud_database_fix.py
```

### 方法2：手动执行SQL
```sql
ALTER TABLE projects 
ADD COLUMN rating INTEGER NULL 
CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));

COMMENT ON COLUMN projects.rating IS '项目评分(1-5星)，NULL表示未评分';
```

### 方法3：运行迁移脚本
```bash
python migrations/add_project_rating_field.py
```

## 验证修复
执行以下SQL确认字段已添加：
```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'rating';
```

## 修复后测试
```bash
python3 run.py --port 8080
```

应该不再出现 `projects.rating does not exist` 错误。

---

**提交版本**: 55ddd16  
**修复时间**: 2025-06-02 20:45  
**优先级**: 🔴 紧急 