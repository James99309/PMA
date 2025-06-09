-- PostgreSQL 数据库结构同步语句
-- 生成时间: 2025-06-09 20:33:44.911074
-- 从本地数据库同步到云端数据库

ALTER TABLE project_rating_records ALTER COLUMN created_at TYPE timestamp without time zone;
ALTER TABLE project_rating_records ALTER COLUMN updated_at TYPE timestamp without time zone;
