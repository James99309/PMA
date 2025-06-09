-- 云端数据库架构导出
-- 导出时间: 2025-06-05 10:17:44.917250
-- 数据库: dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com
-- 共 42 个表

-- 表: action_reply
-- 列数: 7
CREATE TABLE action_reply (
    id integer NOT NULL DEFAULT nextval('action_reply_id_seq'::regclass),
    action_id integer NOT NULL,
    parent_reply_id integer,
    content text NOT NULL,
    owner_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE action_reply ADD CONSTRAINT fk_action_reply_action_id FOREIGN KEY (action_id) REFERENCES actions(id);

ALTER TABLE action_reply ADD CONSTRAINT fk_action_reply_parent_reply_id FOREIGN KEY (parent_reply_id) REFERENCES action_reply(id);

ALTER TABLE action_reply ADD CONSTRAINT fk_action_reply_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

-- 表: actions
-- 列数: 8
CREATE TABLE actions (
    id integer NOT NULL DEFAULT nextval('actions_id_seq'::regclass),
    date date NOT NULL,
    contact_id integer,
    company_id integer,
    project_id integer,
    communication text NOT NULL,
    created_at timestamp without time zone,
    owner_id integer,
    PRIMARY KEY (id)
);

ALTER TABLE actions ADD CONSTRAINT fk_actions_contact_id FOREIGN KEY (contact_id) REFERENCES contacts(id);

ALTER TABLE actions ADD CONSTRAINT fk_actions_company_id FOREIGN KEY (company_id) REFERENCES companies(id);

ALTER TABLE actions ADD CONSTRAINT fk_actions_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

ALTER TABLE actions ADD CONSTRAINT fk_actions_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

-- 表: affiliations
-- 列数: 4
CREATE TABLE affiliations (
    id integer NOT NULL DEFAULT nextval('affiliations_id_seq'::regclass),
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision,
    PRIMARY KEY (id)
);

ALTER TABLE affiliations ADD CONSTRAINT fk_affiliations_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

ALTER TABLE affiliations ADD CONSTRAINT fk_affiliations_viewer_id FOREIGN KEY (viewer_id) REFERENCES users(id);

-- 表: alembic_version
-- 列数: 1
CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL,
    PRIMARY KEY (version_num)
);

-- 表: approval_instance
-- 列数: 11
CREATE TABLE approval_instance (
    id integer NOT NULL DEFAULT nextval('approval_instance_id_seq'::regclass),
    process_id integer NOT NULL,
    object_id integer NOT NULL,
    object_type character varying(50) NOT NULL,
    current_step integer,
    status USER-DEFINED,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    created_by integer NOT NULL,
    template_snapshot json,
    template_version character varying(50),
    PRIMARY KEY (id)
);

ALTER TABLE approval_instance ADD CONSTRAINT fk_approval_instance_process_id FOREIGN KEY (process_id) REFERENCES approval_process_template(id);

ALTER TABLE approval_instance ADD CONSTRAINT fk_approval_instance_created_by FOREIGN KEY (created_by) REFERENCES users(id);

-- 表: approval_process_template
-- 列数: 9
CREATE TABLE approval_process_template (
    id integer NOT NULL DEFAULT nextval('approval_process_template_id_seq'::regclass),
    name character varying(100) NOT NULL,
    object_type character varying(50) NOT NULL,
    is_active boolean,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    required_fields json,
    lock_object_on_start boolean DEFAULT true,
    lock_reason character varying(200) DEFAULT ''审批流程进行中，暂时锁定编辑'::character varying',
    PRIMARY KEY (id)
);

ALTER TABLE approval_process_template ADD CONSTRAINT fk_approval_process_template_created_by FOREIGN KEY (created_by) REFERENCES users(id);

-- 表: approval_record
-- 列数: 7
CREATE TABLE approval_record (
    id integer NOT NULL DEFAULT nextval('approval_record_id_seq'::regclass),
    instance_id integer NOT NULL,
    step_id integer NOT NULL,
    approver_id integer NOT NULL,
    action character varying(50) NOT NULL,
    comment text,
    timestamp timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE approval_record ADD CONSTRAINT fk_approval_record_instance_id FOREIGN KEY (instance_id) REFERENCES approval_instance(id);

ALTER TABLE approval_record ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES approval_step(id);

ALTER TABLE approval_record ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES users(id);

-- 表: approval_step
-- 列数: 11
CREATE TABLE approval_step (
    id integer NOT NULL DEFAULT nextval('approval_step_id_seq'::regclass),
    process_id integer NOT NULL,
    step_order integer NOT NULL,
    approver_user_id integer NOT NULL,
    step_name character varying(100) NOT NULL,
    send_email boolean,
    action_type character varying(50),
    action_params json,
    editable_fields json DEFAULT ''[]'::json',
    cc_users json DEFAULT ''[]'::json',
    cc_enabled boolean DEFAULT false,
    PRIMARY KEY (id)
);

ALTER TABLE approval_step ADD CONSTRAINT fk_approval_step_process_id FOREIGN KEY (process_id) REFERENCES approval_process_template(id);

ALTER TABLE approval_step ADD CONSTRAINT fk_approval_step_approver_user_id FOREIGN KEY (approver_user_id) REFERENCES users(id);

-- 表: change_logs
-- 列数: 15
CREATE TABLE change_logs (
    id integer NOT NULL DEFAULT nextval('change_logs_id_seq'::regclass),
    module_name character varying(50) NOT NULL,
    table_name character varying(50) NOT NULL,
    record_id integer NOT NULL,
    operation_type character varying(20) NOT NULL,
    field_name character varying(100),
    old_value text,
    new_value text,
    user_id integer,
    user_name character varying(80),
    created_at timestamp without time zone,
    record_info character varying(255),
    description character varying(255),
    ip_address character varying(45),
    user_agent character varying(255),
    PRIMARY KEY (id)
);

ALTER TABLE change_logs ADD CONSTRAINT fk_change_logs_user_id FOREIGN KEY (user_id) REFERENCES users(id);

-- 表: companies
-- 列数: 16
CREATE TABLE companies (
    id integer NOT NULL DEFAULT nextval('companies_id_seq'::regclass),
    company_code character varying(20) NOT NULL,
    company_name character varying(100) NOT NULL,
    country character varying(50),
    region character varying(50),
    address character varying(200),
    industry character varying(50),
    company_type character varying(20),
    status character varying(20),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    notes text,
    is_deleted boolean,
    owner_id integer,
    shared_with_users json,
    share_contacts boolean,
    PRIMARY KEY (id)
);

ALTER TABLE companies ADD CONSTRAINT fk_companies_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

-- 表: contacts
-- 列数: 14
CREATE TABLE contacts (
    id integer NOT NULL DEFAULT nextval('contacts_id_seq'::regclass),
    company_id integer NOT NULL,
    name character varying(50) NOT NULL,
    department character varying(50),
    position character varying(50),
    phone character varying(20),
    email character varying(100),
    is_primary boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    notes text,
    owner_id integer,
    override_share boolean,
    shared_disabled boolean,
    PRIMARY KEY (id)
);

ALTER TABLE contacts ADD CONSTRAINT fk_contacts_company_id FOREIGN KEY (company_id) REFERENCES companies(id);

ALTER TABLE contacts ADD CONSTRAINT fk_contacts_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

-- 表: dev_product_specs
-- 列数: 5
CREATE TABLE dev_product_specs (
    id integer NOT NULL DEFAULT nextval('dev_product_specs_id_seq'::regclass),
    dev_product_id integer,
    field_name character varying(100),
    field_value character varying(255),
    field_code character varying(10),
    PRIMARY KEY (id)
);

ALTER TABLE dev_product_specs ADD CONSTRAINT fk_dev_product_specs_dev_product_id FOREIGN KEY (dev_product_id) REFERENCES dev_products(id);

-- 表: dev_products
-- 列数: 17
CREATE TABLE dev_products (
    id integer NOT NULL DEFAULT nextval('dev_products_id_seq'::regclass),
    category_id integer,
    subcategory_id integer,
    region_id integer,
    name character varying(100),
    model character varying(100),
    status character varying(50),
    unit character varying(20),
    retail_price double precision,
    description text,
    image_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    created_by integer,
    mn_code character varying(20),
    pdf_path character varying(255),
    PRIMARY KEY (id)
);

ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_category_id FOREIGN KEY (category_id) REFERENCES product_categories(id);

ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_subcategory_id FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);

ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_region_id FOREIGN KEY (region_id) REFERENCES product_regions(id);

ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_created_by FOREIGN KEY (created_by) REFERENCES users(id);

-- 表: dictionaries
-- 列数: 8
CREATE TABLE dictionaries (
    id integer NOT NULL DEFAULT nextval('dictionaries_id_seq'::regclass),
    type character varying(50) NOT NULL,
    key character varying(50) NOT NULL,
    value character varying(100) NOT NULL,
    is_active boolean,
    sort_order integer,
    created_at double precision,
    updated_at double precision,
    PRIMARY KEY (id)
);

-- 表: event_registry
-- 列数: 8
CREATE TABLE event_registry (
    id integer NOT NULL DEFAULT nextval('event_registry_id_seq'::regclass),
    event_key character varying(50) NOT NULL,
    label_zh character varying(100) NOT NULL,
    label_en character varying(100) NOT NULL,
    default_enabled boolean,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

-- 表: feature_changes
-- 列数: 16
CREATE TABLE feature_changes (
    id integer NOT NULL DEFAULT nextval('feature_changes_id_seq'::regclass),
    version_id integer NOT NULL,
    change_type character varying(20) NOT NULL,
    module_name character varying(50),
    title character varying(200) NOT NULL,
    description text,
    priority character varying(20),
    impact_level character varying(20),
    affected_files text,
    git_commits text,
    test_status character varying(20),
    test_notes text,
    developer_id integer,
    developer_name character varying(50),
    created_at timestamp without time zone,
    completed_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE feature_changes ADD CONSTRAINT fk_feature_changes_version_id FOREIGN KEY (version_id) REFERENCES version_records(id);

ALTER TABLE feature_changes ADD CONSTRAINT fk_feature_changes_developer_id FOREIGN KEY (developer_id) REFERENCES users(id);

-- 表: permissions
-- 列数: 7
CREATE TABLE permissions (
    id integer NOT NULL DEFAULT nextval('permissions_id_seq'::regclass),
    user_id integer NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean,
    PRIMARY KEY (id)
);

ALTER TABLE permissions ADD CONSTRAINT fk_permissions_user_id FOREIGN KEY (user_id) REFERENCES users(id);

-- 表: product_categories
-- 列数: 6
CREATE TABLE product_categories (
    id integer NOT NULL DEFAULT nextval('product_categories_id_seq'::regclass),
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

-- 表: product_code_field_options
-- 列数: 9
CREATE TABLE product_code_field_options (
    id integer NOT NULL DEFAULT nextval('product_code_field_options_id_seq'::regclass),
    field_id integer NOT NULL,
    value character varying(100) NOT NULL,
    code character varying(10) NOT NULL,
    description text,
    is_active boolean,
    position integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE product_code_field_options ADD CONSTRAINT fk_product_code_field_options_field_id FOREIGN KEY (field_id) REFERENCES product_code_fields(id);

-- 表: product_code_field_values
-- 列数: 5
CREATE TABLE product_code_field_values (
    id integer NOT NULL DEFAULT nextval('product_code_field_values_id_seq'::regclass),
    product_code_id integer NOT NULL,
    field_id integer NOT NULL,
    option_id integer,
    custom_value character varying(100),
    PRIMARY KEY (id)
);

ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_product_code_id FOREIGN KEY (product_code_id) REFERENCES product_codes(id);

ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_field_id FOREIGN KEY (field_id) REFERENCES product_code_fields(id);

ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_option_id FOREIGN KEY (option_id) REFERENCES product_code_field_options(id);

-- 表: product_code_fields
-- 列数: 12
CREATE TABLE product_code_fields (
    id integer NOT NULL DEFAULT nextval('product_code_fields_id_seq'::regclass),
    subcategory_id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(10),
    description text,
    field_type character varying(20) NOT NULL,
    position integer NOT NULL,
    max_length integer,
    is_required boolean,
    use_in_code boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE product_code_fields ADD CONSTRAINT fk_product_code_fields_subcategory_id FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);

-- 表: product_codes
-- 列数: 9
CREATE TABLE product_codes (
    id integer NOT NULL DEFAULT nextval('product_codes_id_seq'::regclass),
    product_id integer NOT NULL,
    category_id integer NOT NULL,
    subcategory_id integer NOT NULL,
    full_code character varying(50) NOT NULL,
    status character varying(20),
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_product_id FOREIGN KEY (product_id) REFERENCES products(id);

ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_category_id FOREIGN KEY (category_id) REFERENCES product_categories(id);

ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_subcategory_id FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);

ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_created_by FOREIGN KEY (created_by) REFERENCES users(id);

-- 表: product_regions
-- 列数: 5
CREATE TABLE product_regions (
    id integer NOT NULL DEFAULT nextval('product_regions_id_seq'::regclass),
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone,
    PRIMARY KEY (id)
);

-- 表: product_subcategories
-- 列数: 8
CREATE TABLE product_subcategories (
    id integer NOT NULL DEFAULT nextval('product_subcategories_id_seq'::regclass),
    category_id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    display_order integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE product_subcategories ADD CONSTRAINT fk_product_subcategories_category_id FOREIGN KEY (category_id) REFERENCES product_categories(id);

-- 表: products
-- 列数: 16
CREATE TABLE products (
    id integer NOT NULL DEFAULT nextval('products_id_seq'::regclass),
    type character varying(50),
    category character varying(50),
    product_mn character varying(50),
    product_name character varying(100),
    model character varying(100),
    specification text,
    brand character varying(50),
    unit character varying(20),
    retail_price numeric,
    status character varying(20),
    image_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    pdf_path character varying(255),
    PRIMARY KEY (id)
);

ALTER TABLE products ADD CONSTRAINT fk_products_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

-- 表: project_members
-- 列数: 6
CREATE TABLE project_members (
    id integer NOT NULL DEFAULT nextval('project_members_id_seq'::regclass),
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE project_members ADD CONSTRAINT fk_project_members_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

ALTER TABLE project_members ADD CONSTRAINT fk_project_members_user_id FOREIGN KEY (user_id) REFERENCES users(id);

-- 表: project_rating_records
-- 列数: 6
CREATE TABLE project_rating_records (
    id integer NOT NULL DEFAULT nextval('project_rating_records_id_seq'::regclass),
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    created_at timestamp without time zone DEFAULT 'CURRENT_TIMESTAMP',
    updated_at timestamp without time zone DEFAULT 'CURRENT_TIMESTAMP',
    PRIMARY KEY (id)
);

ALTER TABLE project_rating_records ADD CONSTRAINT fk_project_rating_records_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

ALTER TABLE project_rating_records ADD CONSTRAINT fk_project_rating_records_user_id FOREIGN KEY (user_id) REFERENCES users(id);

-- 表: project_scoring_config
-- 列数: 9
CREATE TABLE project_scoring_config (
    id integer NOT NULL DEFAULT nextval('project_scoring_config_id_seq'::regclass),
    category character varying(50) NOT NULL,
    field_name character varying(100) NOT NULL,
    field_label character varying(200) NOT NULL,
    score_value numeric NOT NULL,
    prerequisite text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

-- 表: project_scoring_records
-- 列数: 10
CREATE TABLE project_scoring_records (
    id integer NOT NULL DEFAULT nextval('project_scoring_records_id_seq'::regclass),
    project_id integer NOT NULL,
    category character varying(50) NOT NULL,
    field_name character varying(100) NOT NULL,
    score_value numeric NOT NULL,
    awarded_by integer,
    auto_calculated boolean,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE project_scoring_records ADD CONSTRAINT fk_project_scoring_records_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

ALTER TABLE project_scoring_records ADD CONSTRAINT fk_project_scoring_records_awarded_by FOREIGN KEY (awarded_by) REFERENCES users(id);

-- 表: project_stage_history
-- 列数: 11
CREATE TABLE project_stage_history (
    id integer NOT NULL DEFAULT nextval('project_stage_history_id_seq'::regclass),
    project_id integer NOT NULL,
    from_stage character varying(64),
    to_stage character varying(64) NOT NULL,
    change_date timestamp without time zone NOT NULL,
    change_week integer,
    change_month integer,
    change_year integer,
    account_id integer,
    remarks text,
    created_at timestamp without time zone DEFAULT 'now()',
    PRIMARY KEY (id)
);

ALTER TABLE project_stage_history ADD CONSTRAINT fk_project_stage_history_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

-- 表: project_total_scores
-- 列数: 11
CREATE TABLE project_total_scores (
    id integer NOT NULL DEFAULT nextval('project_total_scores_id_seq'::regclass),
    project_id integer NOT NULL,
    information_score numeric,
    quotation_score numeric,
    stage_score numeric,
    manual_score numeric,
    total_score numeric,
    star_rating numeric,
    last_calculated timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE project_total_scores ADD CONSTRAINT fk_project_total_scores_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

-- 表: projects
-- 列数: 30
CREATE TABLE projects (
    id integer NOT NULL DEFAULT nextval('projects_id_seq'::regclass),
    project_name character varying(64) NOT NULL,
    report_time date,
    project_type character varying(64),
    report_source character varying(64),
    product_situation character varying(128),
    end_user character varying(128),
    design_issues character varying(128),
    dealer character varying(128),
    contractor character varying(128),
    system_integrator character varying(128),
    current_stage character varying(64),
    stage_description text,
    authorization_code character varying(64),
    delivery_forecast date,
    quotation_customer double precision,
    authorization_status character varying(20),
    feedback text,
    created_at timestamp without time zone DEFAULT 'now()',
    updated_at timestamp without time zone DEFAULT 'now()',
    owner_id integer,
    is_locked boolean NOT NULL DEFAULT false,
    locked_reason character varying(100),
    locked_by integer,
    locked_at timestamp without time zone,
    is_active boolean NOT NULL DEFAULT true,
    last_activity_date timestamp without time zone DEFAULT 'now()',
    activity_reason character varying(50),
    vendor_sales_manager_id integer,
    rating integer,
    PRIMARY KEY (id)
);

ALTER TABLE projects ADD CONSTRAINT fk_projects_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

ALTER TABLE projects ADD CONSTRAINT fk_projects_locked_by FOREIGN KEY (locked_by) REFERENCES users(id);

ALTER TABLE projects ADD CONSTRAINT fk_projects_vendor_sales_manager_id FOREIGN KEY (vendor_sales_manager_id) REFERENCES users(id);

-- 表: quotation_details
-- 列数: 15
CREATE TABLE quotation_details (
    id integer NOT NULL DEFAULT nextval('quotation_details_id_seq'::regclass),
    quotation_id integer,
    product_name character varying(100),
    product_model character varying(100),
    product_desc text,
    brand character varying(50),
    unit character varying(20),
    quantity integer,
    discount double precision,
    market_price double precision,
    unit_price double precision,
    total_price double precision,
    product_mn character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE quotation_details ADD CONSTRAINT fk_quotation_details_quotation_id FOREIGN KEY (quotation_id) REFERENCES quotations(id);

-- 表: quotations
-- 列数: 22
CREATE TABLE quotations (
    id integer NOT NULL DEFAULT nextval('quotations_id_seq'::regclass),
    quotation_number character varying(20) NOT NULL,
    project_id integer NOT NULL,
    contact_id integer,
    amount double precision,
    project_stage character varying(20),
    project_type character varying(20),
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    owner_id integer,
    approval_status character varying(50) DEFAULT ''pending'::character varying',
    approved_stages json,
    approval_history json,
    is_locked boolean DEFAULT false,
    lock_reason character varying(200),
    locked_by integer,
    locked_at timestamp without time zone,
    confirmed_at timestamp without time zone,
    confirmation_badge_color character varying(20) DEFAULT 'NULL::character varying',
    product_signature character varying(64) DEFAULT 'NULL::character varying',
    confirmed_by integer,
    confirmation_badge_status character varying(20) DEFAULT ''none'::character varying',
    PRIMARY KEY (id)
);

ALTER TABLE quotations ADD CONSTRAINT fk_quotations_project_id FOREIGN KEY (project_id) REFERENCES projects(id);

ALTER TABLE quotations ADD CONSTRAINT fk_quotations_contact_id FOREIGN KEY (contact_id) REFERENCES contacts(id);

ALTER TABLE quotations ADD CONSTRAINT fk_quotations_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);

ALTER TABLE quotations ADD CONSTRAINT fk_quotations_locked_by FOREIGN KEY (locked_by) REFERENCES users(id);

ALTER TABLE quotations ADD CONSTRAINT fk_quotations_confirmed_by FOREIGN KEY (confirmed_by) REFERENCES users(id);

-- 表: role_permissions
-- 列数: 7
CREATE TABLE role_permissions (
    id integer NOT NULL DEFAULT nextval('role_permissions_id_seq'::regclass),
    role character varying(50) NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean,
    PRIMARY KEY (id)
);

-- 表: solution_manager_email_settings
-- 列数: 8
CREATE TABLE solution_manager_email_settings (
    id integer NOT NULL DEFAULT nextval('solution_manager_email_settings_id_seq'::regclass),
    user_id integer NOT NULL,
    quotation_created boolean,
    quotation_updated boolean,
    project_created boolean,
    project_stage_changed boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE solution_manager_email_settings ADD CONSTRAINT fk_solution_manager_email_settings_user_id FOREIGN KEY (user_id) REFERENCES users(id);

-- 表: system_metrics
-- 列数: 12
CREATE TABLE system_metrics (
    id integer NOT NULL DEFAULT nextval('system_metrics_id_seq'::regclass),
    version_id integer,
    avg_response_time double precision,
    max_response_time double precision,
    error_rate double precision,
    active_users integer,
    total_requests integer,
    database_size bigint,
    cpu_usage double precision,
    memory_usage double precision,
    disk_usage double precision,
    recorded_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE system_metrics ADD CONSTRAINT fk_system_metrics_version_id FOREIGN KEY (version_id) REFERENCES version_records(id);

-- 表: system_settings
-- 列数: 6
CREATE TABLE system_settings (
    id integer NOT NULL DEFAULT nextval('system_settings_id_seq'::regclass),
    key character varying(100) NOT NULL,
    value text,
    description character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

-- 表: upgrade_logs
-- 列数: 14
CREATE TABLE upgrade_logs (
    id integer NOT NULL DEFAULT nextval('upgrade_logs_id_seq'::regclass),
    version_id integer NOT NULL,
    from_version character varying(20),
    to_version character varying(20) NOT NULL,
    upgrade_date timestamp without time zone NOT NULL,
    upgrade_type character varying(20),
    status character varying(20),
    upgrade_notes text,
    error_message text,
    duration_seconds integer,
    operator_id integer,
    operator_name character varying(50),
    environment character varying(20),
    server_info text,
    PRIMARY KEY (id)
);

ALTER TABLE upgrade_logs ADD CONSTRAINT fk_upgrade_logs_version_id FOREIGN KEY (version_id) REFERENCES version_records(id);

ALTER TABLE upgrade_logs ADD CONSTRAINT fk_upgrade_logs_operator_id FOREIGN KEY (operator_id) REFERENCES users(id);

-- 表: user_event_subscriptions
-- 列数: 7
CREATE TABLE user_event_subscriptions (
    id integer NOT NULL DEFAULT nextval('user_event_subscriptions_id_seq'::regclass),
    user_id integer NOT NULL,
    target_user_id integer NOT NULL,
    event_id integer NOT NULL,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE user_event_subscriptions ADD CONSTRAINT fk_user_event_subscriptions_user_id FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE user_event_subscriptions ADD CONSTRAINT fk_user_event_subscriptions_target_user_id FOREIGN KEY (target_user_id) REFERENCES users(id);

ALTER TABLE user_event_subscriptions ADD CONSTRAINT fk_user_event_subscriptions_event_id FOREIGN KEY (event_id) REFERENCES event_registry(id);

-- 表: users
-- 列数: 18
CREATE TABLE users (
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    username character varying(80) NOT NULL,
    password_hash character varying(256) NOT NULL,
    real_name character varying(80),
    company_name character varying(100),
    email character varying(120),
    phone character varying(20),
    department character varying(100),
    is_department_manager boolean,
    role character varying(20),
    is_profile_complete boolean,
    wechat_openid character varying(64),
    wechat_nickname character varying(64),
    wechat_avatar character varying(256),
    is_active boolean,
    created_at double precision,
    last_login double precision,
    updated_at double precision,
    PRIMARY KEY (id)
);

-- 表: version_records
-- 列数: 14
CREATE TABLE version_records (
    id integer NOT NULL DEFAULT nextval('version_records_id_seq'::regclass),
    version_number character varying(20) NOT NULL,
    version_name character varying(100),
    release_date timestamp without time zone NOT NULL,
    description text,
    is_current boolean,
    environment character varying(20),
    total_features integer,
    total_fixes integer,
    total_improvements integer,
    git_commit character varying(40),
    build_number character varying(20),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    PRIMARY KEY (id)
);

