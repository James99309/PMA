-- pma_db_ovs数据库结构同步SQL
-- 生成时间: 2025-06-27 19:22:39
-- 源数据库: postgresql://nijie@localhost:5432/pma_local
-- 目标数据库: pma_db_ovs

CREATE TABLE five_star_project_baselines (
  id integer(32,0) NOT NULL DEFAULT nextval('five_star_project_baselines_id_seq'::regclass),
  user_id integer(32,0) NOT NULL,
  baseline_year integer(32,0) NOT NULL,
  baseline_month integer(32,0) NOT NULL,
  baseline_count integer(32,0),
  created_at timestamp without time zone,
  created_by integer(32,0),
  PRIMARY KEY (id)
);

CREATE TABLE performance_statistics (
  id integer(32,0) NOT NULL DEFAULT nextval('performance_statistics_id_seq'::regclass),
  user_id integer(32,0) NOT NULL,
  year integer(32,0) NOT NULL,
  month integer(32,0) NOT NULL,
  implant_amount_actual double precision(53),
  sales_amount_actual double precision(53),
  new_customers_actual integer(32,0),
  new_projects_actual integer(32,0),
  five_star_projects_actual integer(32,0),
  industry_statistics json,
  calculated_at timestamp without time zone,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

CREATE TABLE performance_targets (
  id integer(32,0) NOT NULL DEFAULT nextval('performance_targets_id_seq'::regclass),
  user_id integer(32,0) NOT NULL,
  year integer(32,0) NOT NULL,
  month integer(32,0) NOT NULL,
  implant_amount_target double precision(53),
  sales_amount_target double precision(53),
  new_customers_target integer(32,0),
  new_projects_target integer(32,0),
  five_star_projects_target integer(32,0),
  display_currency character varying(10),
  created_by integer(32,0) NOT NULL,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  updated_by integer(32,0),
  PRIMARY KEY (id)
);

ALTER TABLE approval_step ADD COLUMN approver_type character varying(20) DEFAULT 'user'::character varying;

ALTER TABLE approval_step ADD COLUMN description text;

ALTER TABLE projects ADD COLUMN industry character varying(50);

