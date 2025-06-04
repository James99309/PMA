-- PMA云端数据库升级脚本
-- 生成时间: 2025-06-05 00:21:55.325760
-- 将云端数据库结构同步到本地版本

BEGIN;

-- 修改表: project_scoring_records
-- 修改列: project_scoring_records.created_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_scoring_records.updated_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_scoring_records.score_value
-- 本地: NUMERIC(3, 2), 可空: False
-- 云端: NUMERIC(3, 2), 可空: False
-- 修改列: project_scoring_records.auto_calculated
-- 本地: BOOLEAN, 可空: True
-- 云端: BOOLEAN, 可空: True

-- 修改表: projects
-- 修改列: projects.rating
-- 本地: INTEGER, 可空: True
-- 云端: NUMERIC(2, 1), 可空: True
ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER;

-- 修改表: project_stage_history
ALTER TABLE project_stage_history DROP COLUMN IF EXISTS user_id;
DROP INDEX IF EXISTS ix_project_stage_history_user_id;

-- 修改表: approval_process_template
-- 修改列: approval_process_template.required_fields
-- 本地: JSON, 可空: True
-- 云端: JSON, 可空: True

-- 修改表: project_total_scores
-- 修改列: project_total_scores.total_score
-- 本地: NUMERIC(3, 2), 可空: True
-- 云端: NUMERIC(3, 2), 可空: True
-- 修改列: project_total_scores.created_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_total_scores.stage_score
-- 本地: NUMERIC(3, 2), 可空: True
-- 云端: NUMERIC(3, 2), 可空: True
-- 修改列: project_total_scores.last_calculated
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_total_scores.updated_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_total_scores.quotation_score
-- 本地: NUMERIC(3, 2), 可空: True
-- 云端: NUMERIC(3, 2), 可空: True
-- 修改列: project_total_scores.manual_score
-- 本地: NUMERIC(3, 2), 可空: True
-- 云端: NUMERIC(3, 2), 可空: True
-- 修改列: project_total_scores.information_score
-- 本地: NUMERIC(3, 2), 可空: True
-- 云端: NUMERIC(3, 2), 可空: True
-- 修改列: project_total_scores.star_rating
-- 本地: NUMERIC(2, 1), 可空: True
-- 云端: NUMERIC(2, 1), 可空: True

-- 修改表: quotations
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_required_fields;
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_comments;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_at;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_by;
-- 需要添加列: quotations.confirmed_at
-- ALTER TABLE quotations ADD COLUMN confirmed_at ...;
-- 需要添加列: quotations.confirmation_badge_color
-- ALTER TABLE quotations ADD COLUMN confirmation_badge_color ...;
-- 需要添加列: quotations.product_signature
-- ALTER TABLE quotations ADD COLUMN product_signature ...;
-- 需要添加列: quotations.confirmed_by
-- ALTER TABLE quotations ADD COLUMN confirmed_by ...;
-- 需要添加列: quotations.confirmation_badge_status
-- ALTER TABLE quotations ADD COLUMN confirmation_badge_status ...;
-- 修改列: quotations.approved_stages
-- 本地: JSON, 可空: True
-- 云端: JSON, 可空: True
-- 修改列: quotations.approval_history
-- 本地: JSON, 可空: True
-- 云端: JSON, 可空: True

-- 修改表: event_registry
DROP INDEX IF EXISTS ix_event_registry_event_key;

-- 修改表: project_scoring_config
-- 修改列: project_scoring_config.created_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_scoring_config.updated_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_scoring_config.is_active
-- 本地: BOOLEAN, 可空: True
-- 云端: BOOLEAN, 可空: True
-- 修改列: project_scoring_config.score_value
-- 本地: NUMERIC(3, 2), 可空: False
-- 云端: NUMERIC(3, 2), 可空: False

-- 修改表: project_rating_records
ALTER TABLE project_rating_records DROP COLUMN IF EXISTS comment;
-- 修改列: project_rating_records.created_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_rating_records.updated_at
-- 本地: TIMESTAMP, 可空: True
-- 云端: TIMESTAMP, 可空: True
-- 修改列: project_rating_records.rating
-- 本地: INTEGER, 可空: False
-- 云端: NUMERIC(2, 1), 可空: False
ALTER TABLE project_rating_records ALTER COLUMN rating TYPE INTEGER;
DROP INDEX IF EXISTS idx_project_rating_records_created_at;
DROP INDEX IF EXISTS uq_project_rating_project_user;
DROP INDEX IF EXISTS idx_project_rating_records_project_id;
DROP INDEX IF EXISTS idx_project_rating_records_user_id;
CREATE UNIQUE INDEX uq_project_user_rating ON project_rating_records (project_id, user_id);
ALTER TABLE project_rating_records DROP CONSTRAINT IF EXISTS uq_project_rating_project_user;
ALTER TABLE project_rating_records ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


COMMIT;
