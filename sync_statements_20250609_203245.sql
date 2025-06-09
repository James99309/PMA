-- PostgreSQL 数据库结构同步语句
-- 生成时间: 2025-06-09 20:32:45.348386
-- 从本地数据库同步到云端数据库

ALTER TABLE approval_process_template ALTER COLUMN required_fields TYPE json;
ALTER TABLE pricing_orders ALTER COLUMN is_direct_contract TYPE boolean;
ALTER TABLE pricing_orders ALTER COLUMN is_factory_pickup TYPE boolean;
ALTER TABLE project_rating_records ALTER COLUMN created_at TYPE timestamp without time zone;
ALTER TABLE project_rating_records ALTER COLUMN updated_at TYPE timestamp without time zone;
ALTER TABLE project_scoring_config ALTER COLUMN score_value TYPE numeric;
ALTER TABLE project_scoring_config ALTER COLUMN is_active TYPE boolean;
ALTER TABLE project_scoring_config ALTER COLUMN created_at TYPE timestamp without time zone;
ALTER TABLE project_scoring_config ALTER COLUMN updated_at TYPE timestamp without time zone;
ALTER TABLE project_scoring_records ALTER COLUMN score_value TYPE numeric;
ALTER TABLE project_scoring_records ALTER COLUMN auto_calculated TYPE boolean;
ALTER TABLE project_scoring_records ALTER COLUMN created_at TYPE timestamp without time zone;
ALTER TABLE project_scoring_records ALTER COLUMN updated_at TYPE timestamp without time zone;
ALTER TABLE project_total_scores ALTER COLUMN information_score TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN quotation_score TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN stage_score TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN manual_score TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN total_score TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN star_rating TYPE numeric;
ALTER TABLE project_total_scores ALTER COLUMN last_calculated TYPE timestamp without time zone;
ALTER TABLE project_total_scores ALTER COLUMN created_at TYPE timestamp without time zone;
ALTER TABLE project_total_scores ALTER COLUMN updated_at TYPE timestamp without time zone;
ALTER TABLE quotations ALTER COLUMN approved_stages TYPE json;
ALTER TABLE quotations ALTER COLUMN approval_history TYPE json;
