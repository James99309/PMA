-- OVS数据库专用迁移脚本
-- 生成时间: 2025-07-29 10:36:26
-- 目标: 将OVS数据库结构同步到本地最新版本

BEGIN;

-- 1. 创建缺失的表
-- 创建表: temp_products
CREATE TABLE temp_products (
    id integer(32,0) NOT NULL DEFAULT nextval('temp_products_id_seq'::regclass),
    product_name character varying(100) NOT NULL,
    product_model character varying(100) NOT NULL,
    product_desc text,
    brand character varying(50),
    unit character varying(20),
    category character varying(50),
    category_path character varying(200),
    created_by integer(32,0) NOT NULL,
    usage_count integer(32,0),
    last_used_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_deleted boolean,
    reference_price double precision(53),
    product_mn character varying(50)
);

-- 创建表: company_assets
CREATE TABLE company_assets (
    id integer(32,0) NOT NULL DEFAULT nextval('company_assets_id_seq'::regclass),
    asset_type character varying(50) NOT NULL,
    asset_name character varying(100) NOT NULL,
    asset_key character varying(50) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_type character varying(50) NOT NULL,
    file_size integer(32,0) NOT NULL,
    file_content text NOT NULL,
    description text,
    is_active boolean NOT NULL,
    is_default boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    created_by_id integer(32,0)
);

-- 2. 添加缺失的字段
ALTER TABLE settlement_orders ADD COLUMN settlement_status character varying(20) DEFAULT 'pending'::character varying;
ALTER TABLE approval_step ADD COLUMN is_conditional boolean DEFAULT false;
ALTER TABLE approval_step ADD COLUMN condition_config json;
ALTER TABLE approval_step ADD COLUMN branch_on_reject integer(32,0);
ALTER TABLE approval_step ADD COLUMN condition_type character varying(50);
ALTER TABLE approval_step ADD COLUMN skip_conditions json DEFAULT '[]'::json;
ALTER TABLE approval_step ADD COLUMN branch_on_approve integer(32,0);
ALTER TABLE dictionaries ADD COLUMN logo_content text;
ALTER TABLE dictionaries ADD COLUMN address character varying(500);
ALTER TABLE dictionaries ADD COLUMN logo_type character varying(50);
ALTER TABLE dictionaries ADD COLUMN email_signature_content text;
ALTER TABLE dictionaries ADD COLUMN email_signature_filename character varying(100);
ALTER TABLE dictionaries ADD COLUMN email_signature_type character varying(50);
ALTER TABLE dictionaries ADD COLUMN website character varying(200);
ALTER TABLE dictionaries ADD COLUMN logo_filename character varying(100);
ALTER TABLE dictionaries ADD COLUMN postal_code character varying(20);
ALTER TABLE dictionaries ADD COLUMN phone character varying(50);
ALTER TABLE dictionaries ADD COLUMN email_signature_size integer(32,0);
ALTER TABLE dictionaries ADD COLUMN email character varying(100);
ALTER TABLE dictionaries ADD COLUMN logo_size integer(32,0);
ALTER TABLE dictionaries ADD COLUMN fax character varying(50);
ALTER TABLE approval_process_template ADD COLUMN visual_data json;
ALTER TABLE performance_targets ADD COLUMN sales_rate integer(32,0) DEFAULT 0;
ALTER TABLE performance_targets ADD COLUMN projects_rate integer(32,0) DEFAULT 0;
ALTER TABLE performance_targets ADD COLUMN implant_rate integer(32,0) DEFAULT 0;
ALTER TABLE performance_targets ADD COLUMN customers_rate integer(32,0) DEFAULT 0;

-- 3. 创建缺失的索引
CREATE INDEX idx_dictionaries_company_email ON public.dictionaries USING btree (type, email) WHERE ((type)::text = 'company'::text);
CREATE INDEX idx_dictionaries_company_logo ON public.dictionaries USING btree (type) WHERE (logo_content IS NOT NULL);
CREATE INDEX idx_dictionaries_company_phone ON public.dictionaries USING btree (type, phone) WHERE ((type)::text = 'company'::text);
CREATE UNIQUE INDEX unique_baseline_user ON public.five_star_project_baselines USING btree (user_id);
CREATE UNIQUE INDEX unique_statistics_user_year_month ON public.performance_statistics USING btree (user_id, year, month);
CREATE INDEX idx_quotations_amount ON public.quotations USING btree (amount);
CREATE INDEX idx_quotations_created_at ON public.quotations USING btree (created_at);
CREATE INDEX idx_quotations_owner_id ON public.quotations USING btree (owner_id);
CREATE INDEX idx_quotations_project_id ON public.quotations USING btree (project_id);
CREATE INDEX idx_quotations_project_owner ON public.quotations USING btree (project_id, owner_id);
CREATE INDEX idx_quotations_updated_at ON public.quotations USING btree (updated_at);
CREATE INDEX idx_projects_current_stage ON public.projects USING btree (current_stage);
CREATE INDEX idx_projects_owner_id ON public.projects USING btree (owner_id);
CREATE INDEX idx_projects_project_type ON public.projects USING btree (project_type);
CREATE INDEX idx_projects_type_stage ON public.projects USING btree (project_type, current_stage);
CREATE INDEX idx_projects_vendor_sales_manager ON public.projects USING btree (vendor_sales_manager_id);
CREATE UNIQUE INDEX unique_user_year_month ON public.performance_targets USING btree (user_id, year, month);

-- 4. 添加缺失的约束
ALTER TABLE five_star_project_baselines ADD CONSTRAINT five_star_project_baselines_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE five_star_project_baselines ADD CONSTRAINT five_star_project_baselines_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE five_star_project_baselines ADD CONSTRAINT unique_baseline_user UNIQUE (user_id);
ALTER TABLE performance_statistics ADD CONSTRAINT performance_statistics_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (month);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (year);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (year);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (year);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (user_id);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (user_id);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (user_id);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (month);
ALTER TABLE performance_statistics ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (month);
ALTER TABLE performance_targets ADD CONSTRAINT performance_targets_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE performance_targets ADD CONSTRAINT performance_targets_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES users(id);
ALTER TABLE performance_targets ADD CONSTRAINT performance_targets_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (month);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (user_id);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (user_id);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (user_id);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (year);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (year);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (year);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (month);
ALTER TABLE performance_targets ADD CONSTRAINT unique_user_year_month UNIQUE (month);

COMMIT;

-- 验证迁移结果
SELECT '✅ OVS迁移完成，当前表数量: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';