# 云端数据库备份信息

## 备份基本信息
- 备份时间: 2025-06-23 00:46:19
- 备份文件: pma_db_ovs_backup_20250623_004614.sql
- 数据库主机: dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com
- 数据库名称: pma_db_ovs
- 数据库版本: PostgreSQL 16.9 (Debian 16.9-1.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
- 数据库大小: 11 MB

## 表统计信息
| 表名 | 插入行数 | 更新行数 | 删除行数 |
|------|----------|----------|----------|
| action_reply | 0 | 0 | 0 |
| actions | 2 | 1 | 1 |
| affiliations | 0 | 0 | 0 |
| alembic_version | 0 | 0 | 0 |
| approval_instance | 3 | 3 | 1 |
| approval_process_template | 1 | 0 | 0 |
| approval_record | 3 | 0 | 1 |
| approval_step | 1 | 2 | 0 |
| change_logs | 27 | 0 | 0 |
| companies | 4 | 8 | 2 |
| contacts | 2 | 0 | 1 |
| dev_product_specs | 0 | 0 | 0 |
| dev_products | 0 | 0 | 0 |
| dictionaries | 6 | 0 | 0 |
| event_registry | 0 | 0 | 0 |
| feature_changes | 0 | 0 | 0 |
| inventory | 0 | 0 | 0 |
| inventory_transactions | 0 | 0 | 0 |
| permissions | 11 | 0 | 0 |
| pricing_order_approval_records | 0 | 0 | 0 |
| pricing_order_details | 0 | 0 | 0 |
| pricing_orders | 0 | 0 | 0 |
| product_categories | 0 | 0 | 0 |
| product_code_field_options | 0 | 0 | 0 |
| product_code_field_values | 0 | 0 | 0 |
| product_code_fields | 0 | 0 | 0 |
| product_codes | 0 | 0 | 0 |
| product_regions | 0 | 0 | 0 |
| product_subcategories | 0 | 0 | 0 |
| products | 70 | 70 | 0 |
| project_members | 0 | 0 | 0 |
| project_rating_records | 0 | 0 | 0 |
| project_scoring_config | 0 | 0 | 0 |
| project_scoring_records | 0 | 0 | 0 |
| project_stage_history | 8 | 0 | 4 |
| project_total_scores | 4 | 8 | 2 |
| projects | 4 | 33 | 2 |
| purchase_order_details | 0 | 0 | 0 |
| purchase_orders | 0 | 0 | 0 |
| quotation_details | 6 | 0 | 4 |
| quotations | 3 | 11 | 2 |
| role_permissions | 26 | 0 | 13 |
| settlement_details | 0 | 0 | 0 |
| settlement_order_details | 0 | 0 | 0 |
| settlement_orders | 0 | 0 | 0 |
| settlements | 0 | 0 | 0 |
| solution_manager_email_settings | 0 | 0 | 0 |
| system_metrics | 0 | 0 | 0 |
| system_settings | 2 | 0 | 0 |
| upgrade_logs | 0 | 0 | 0 |
| user_event_subscriptions | 0 | 0 | 0 |
| users | 3 | 5 | 0 |
| version_records | 1 | 0 | 0 |

## 表结构信息

### action_reply
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| action_id | integer | NO |
| parent_reply_id | integer | YES |
| content | text | NO |
| owner_id | integer | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### actions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| date | date | NO |
| contact_id | integer | YES |
| company_id | integer | YES |
| project_id | integer | YES |
| communication | text | NO |
| created_at | timestamp without time zone | YES |
| owner_id | integer | YES |

### affiliations
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| owner_id | integer | NO |
| viewer_id | integer | NO |
| created_at | double precision | YES |

### alembic_version
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| version_num | character varying | NO |

### approval_instance
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| object_id | integer | NO |
| object_type | character varying | NO |
| current_step | integer | YES |
| status | USER-DEFINED | YES |
| started_at | timestamp without time zone | YES |
| ended_at | timestamp without time zone | YES |
| process_id | integer | NO |
| created_by | integer | NO |
| template_snapshot | json | YES |
| template_version | character varying | YES |

### approval_process_template
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| name | character varying | NO |
| object_type | character varying | NO |
| is_active | boolean | YES |
| created_by | integer | NO |
| created_at | timestamp without time zone | YES |
| required_fields | json | YES |
| lock_object_on_start | boolean | YES |
| lock_reason | character varying | YES |

### approval_record
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| instance_id | integer | NO |
| step_id | integer | NO |
| approver_id | integer | NO |
| action | character varying | NO |
| comment | text | YES |
| timestamp | timestamp without time zone | YES |

### approval_step
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| process_id | integer | NO |
| step_order | integer | NO |
| approver_user_id | integer | NO |
| step_name | character varying | NO |
| send_email | boolean | YES |
| action_type | character varying | YES |
| action_params | json | YES |
| editable_fields | json | YES |
| cc_users | json | YES |
| cc_enabled | boolean | YES |

### change_logs
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| module_name | character varying | NO |
| table_name | character varying | NO |
| record_id | integer | NO |
| operation_type | character varying | NO |
| field_name | character varying | YES |
| old_value | text | YES |
| new_value | text | YES |
| user_id | integer | YES |
| user_name | character varying | YES |
| created_at | timestamp without time zone | YES |
| description | character varying | YES |
| ip_address | character varying | YES |
| user_agent | character varying | YES |
| record_info | character varying | YES |

### companies
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| company_code | character varying | NO |
| company_name | character varying | NO |
| country | character varying | YES |
| region | character varying | YES |
| address | character varying | YES |
| industry | character varying | YES |
| company_type | character varying | YES |
| status | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| notes | text | YES |
| is_deleted | boolean | YES |
| owner_id | integer | YES |
| shared_with_users | json | YES |
| share_contacts | boolean | YES |

### contacts
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| company_id | integer | NO |
| name | character varying | NO |
| department | character varying | YES |
| position | character varying | YES |
| phone | character varying | YES |
| email | character varying | YES |
| is_primary | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| notes | text | YES |
| owner_id | integer | YES |
| override_share | boolean | YES |
| shared_disabled | boolean | YES |

### dev_product_specs
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| dev_product_id | integer | YES |
| field_name | character varying | YES |
| field_value | character varying | YES |
| field_code | character varying | YES |

### dev_products
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| category_id | integer | YES |
| subcategory_id | integer | YES |
| region_id | integer | YES |
| name | character varying | YES |
| model | character varying | YES |
| status | character varying | YES |
| unit | character varying | YES |
| retail_price | double precision | YES |
| description | text | YES |
| image_path | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| owner_id | integer | YES |
| created_by | integer | YES |
| mn_code | character varying | YES |
| pdf_path | character varying | YES |
| currency | character varying | NO |

### dictionaries
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| type | character varying | NO |
| key | character varying | NO |
| value | character varying | NO |
| is_active | boolean | YES |
| sort_order | integer | YES |
| created_at | double precision | YES |
| updated_at | double precision | YES |
| is_vendor | boolean | YES |

### event_registry
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| event_key | character varying | NO |
| label_zh | character varying | NO |
| label_en | character varying | NO |
| default_enabled | boolean | YES |
| enabled | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### feature_changes
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| version_id | integer | NO |
| change_type | character varying | NO |
| module_name | character varying | YES |
| title | character varying | NO |
| description | text | YES |
| priority | character varying | YES |
| impact_level | character varying | YES |
| affected_files | text | YES |
| git_commits | text | YES |
| test_status | character varying | YES |
| test_notes | text | YES |
| developer_id | integer | YES |
| developer_name | character varying | YES |
| created_at | timestamp without time zone | YES |
| completed_at | timestamp without time zone | YES |

### inventory
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| company_id | integer | NO |
| product_id | integer | NO |
| quantity | integer | NO |
| unit | character varying | YES |
| location | character varying | YES |
| min_stock | integer | YES |
| max_stock | integer | YES |
| notes | text | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| created_by_id | integer | NO |

### inventory_transactions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| inventory_id | integer | NO |
| transaction_type | character varying | NO |
| quantity | integer | NO |
| quantity_before | integer | NO |
| quantity_after | integer | NO |
| reference_type | character varying | YES |
| reference_id | integer | YES |
| description | text | YES |
| transaction_date | timestamp without time zone | YES |
| created_by_id | integer | NO |

### permissions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| user_id | integer | NO |
| module | character varying | NO |
| can_view | boolean | YES |
| can_create | boolean | YES |
| can_edit | boolean | YES |
| can_delete | boolean | YES |

### pricing_order_approval_records
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| pricing_order_id | integer | NO |
| step_order | integer | NO |
| step_name | character varying | NO |
| approver_role | character varying | NO |
| approver_id | integer | NO |
| action | character varying | YES |
| comment | text | YES |
| approved_at | timestamp without time zone | YES |
| is_fast_approval | boolean | YES |
| fast_approval_reason | character varying | YES |

### pricing_order_details
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| pricing_order_id | integer | NO |
| product_name | character varying | NO |
| product_model | character varying | YES |
| product_desc | text | YES |
| brand | character varying | YES |
| unit | character varying | YES |
| product_mn | character varying | YES |
| market_price | double precision | NO |
| unit_price | double precision | NO |
| quantity | integer | NO |
| discount_rate | double precision | YES |
| total_price | double precision | NO |
| source_type | character varying | YES |
| source_quotation_detail_id | integer | YES |
| currency | character varying | YES |

### pricing_orders
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| order_number | character varying | NO |
| project_id | integer | NO |
| quotation_id | integer | NO |
| distributor_id | integer | YES |
| dealer_id | integer | YES |
| pricing_total_amount | double precision | YES |
| pricing_total_discount_rate | double precision | YES |
| settlement_total_amount | double precision | YES |
| settlement_total_discount_rate | double precision | YES |
| approval_flow_type | character varying | NO |
| status | character varying | YES |
| current_approval_step | integer | YES |
| approved_by | integer | YES |
| approved_at | timestamp without time zone | YES |
| created_by | integer | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| is_direct_contract | boolean | YES |
| is_factory_pickup | boolean | YES |
| currency | character varying | YES |

### product_categories
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| name | character varying | NO |
| code_letter | character varying | NO |
| description | text | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### product_code_field_options
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| field_id | integer | NO |
| value | character varying | NO |
| code | character varying | NO |
| description | text | YES |
| is_active | boolean | YES |
| position | integer | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### product_code_field_values
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| product_code_id | integer | NO |
| field_id | integer | NO |
| option_id | integer | YES |
| custom_value | character varying | YES |

### product_code_fields
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| subcategory_id | integer | NO |
| name | character varying | NO |
| code | character varying | YES |
| description | text | YES |
| field_type | character varying | NO |
| position | integer | NO |
| max_length | integer | YES |
| is_required | boolean | YES |
| use_in_code | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### product_codes
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| product_id | integer | NO |
| category_id | integer | NO |
| subcategory_id | integer | NO |
| full_code | character varying | NO |
| status | character varying | YES |
| created_by | integer | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### product_regions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| name | character varying | NO |
| code_letter | character varying | NO |
| description | text | YES |
| created_at | timestamp without time zone | YES |

### product_subcategories
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| category_id | integer | NO |
| name | character varying | NO |
| code_letter | character varying | NO |
| description | text | YES |
| display_order | integer | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### products
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| type | character varying | YES |
| category | character varying | YES |
| product_mn | character varying | YES |
| product_name | character varying | YES |
| model | character varying | YES |
| specification | text | YES |
| brand | character varying | YES |
| unit | character varying | YES |
| retail_price | numeric | YES |
| status | character varying | YES |
| image_path | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| owner_id | integer | YES |
| pdf_path | character varying | YES |
| currency | character varying | NO |

### project_members
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_id | integer | NO |
| user_id | integer | NO |
| role | character varying | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### project_rating_records
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_id | integer | NO |
| user_id | integer | NO |
| rating | integer | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### project_scoring_config
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| category | character varying | NO |
| field_name | character varying | NO |
| field_label | character varying | NO |
| score_value | numeric | NO |
| prerequisite | text | YES |
| is_active | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### project_scoring_records
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_id | integer | NO |
| category | character varying | NO |
| field_name | character varying | NO |
| score_value | numeric | NO |
| awarded_by | integer | YES |
| auto_calculated | boolean | YES |
| notes | text | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### project_stage_history
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_id | integer | NO |
| from_stage | character varying | YES |
| to_stage | character varying | NO |
| change_date | timestamp without time zone | NO |
| change_week | integer | YES |
| change_month | integer | YES |
| change_year | integer | YES |
| account_id | integer | YES |
| remarks | text | YES |
| created_at | timestamp without time zone | YES |

### project_total_scores
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_id | integer | NO |
| information_score | numeric | YES |
| quotation_score | numeric | YES |
| stage_score | numeric | YES |
| manual_score | numeric | YES |
| total_score | numeric | YES |
| star_rating | numeric | YES |
| last_calculated | timestamp without time zone | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### projects
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| project_name | character varying | NO |
| report_time | date | YES |
| project_type | character varying | YES |
| report_source | character varying | YES |
| product_situation | character varying | YES |
| end_user | character varying | YES |
| design_issues | character varying | YES |
| dealer | character varying | YES |
| contractor | character varying | YES |
| system_integrator | character varying | YES |
| current_stage | character varying | YES |
| stage_description | text | YES |
| authorization_code | character varying | YES |
| delivery_forecast | date | YES |
| quotation_customer | double precision | YES |
| authorization_status | character varying | YES |
| feedback | text | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| owner_id | integer | YES |
| is_locked | boolean | NO |
| locked_reason | character varying | YES |
| locked_by | integer | YES |
| locked_at | timestamp without time zone | YES |
| is_active | boolean | NO |
| last_activity_date | timestamp without time zone | YES |
| activity_reason | character varying | YES |
| vendor_sales_manager_id | integer | YES |
| rating | integer | YES |

### purchase_order_details
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| order_id | integer | NO |
| product_id | integer | NO |
| product_name | character varying | NO |
| product_model | character varying | YES |
| product_desc | text | YES |
| brand | character varying | YES |
| quantity | integer | NO |
| unit | character varying | YES |
| unit_price | numeric | YES |
| discount | numeric | YES |
| total_price | numeric | YES |
| received_quantity | integer | YES |
| notes | text | YES |

### purchase_orders
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| order_number | character varying | NO |
| company_id | integer | NO |
| order_type | character varying | YES |
| order_date | timestamp without time zone | YES |
| expected_date | timestamp without time zone | YES |
| status | character varying | YES |
| total_amount | numeric | YES |
| total_quantity | integer | YES |
| currency | character varying | YES |
| payment_terms | character varying | YES |
| delivery_address | text | YES |
| description | text | YES |
| created_by_id | integer | NO |
| approved_by_id | integer | YES |
| approved_at | timestamp without time zone | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### quotation_details
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| quotation_id | integer | YES |
| product_name | character varying | YES |
| product_model | character varying | YES |
| product_desc | text | YES |
| brand | character varying | YES |
| unit | character varying | YES |
| quantity | integer | YES |
| discount | double precision | YES |
| market_price | double precision | YES |
| unit_price | double precision | YES |
| total_price | double precision | YES |
| product_mn | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
| implant_subtotal | double precision | YES |
| currency | character varying | YES |
| original_market_price | double precision | YES |
| converted_market_price | double precision | YES |

### quotations
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| quotation_number | character varying | NO |
| project_id | integer | NO |
| contact_id | integer | YES |
| amount | double precision | YES |
| project_stage | character varying | YES |
| project_type | character varying | YES |
| created_at | timestamp with time zone | YES |
| updated_at | timestamp without time zone | YES |
| owner_id | integer | YES |
| approval_status | character varying | YES |
| approved_stages | json | YES |
| approval_history | json | YES |
| is_locked | boolean | YES |
| lock_reason | character varying | YES |
| locked_by | integer | YES |
| locked_at | timestamp without time zone | YES |
| confirmation_badge_status | character varying | YES |
| confirmation_badge_color | character varying | YES |
| confirmed_by | integer | YES |
| confirmed_at | timestamp without time zone | YES |
| product_signature | character varying | YES |
| implant_total_amount | double precision | YES |
| currency | character varying | NO |
| exchange_rate | numeric | NO |
| original_currency | character varying | YES |

### role_permissions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| role | character varying | NO |
| module | character varying | NO |
| can_view | boolean | YES |
| can_create | boolean | YES |
| can_edit | boolean | YES |
| can_delete | boolean | YES |
| pricing_discount_limit | double precision | YES |
| settlement_discount_limit | double precision | YES |

### settlement_details
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| settlement_id | integer | NO |
| inventory_id | integer | NO |
| product_id | integer | NO |
| quantity_settled | integer | NO |
| quantity_before | integer | NO |
| quantity_after | integer | NO |
| unit | character varying | YES |
| notes | text | YES |

### settlement_order_details
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| pricing_order_id | integer | NO |
| product_name | character varying | NO |
| product_model | character varying | YES |
| product_desc | text | YES |
| brand | character varying | YES |
| unit | character varying | YES |
| product_mn | character varying | YES |
| market_price | double precision | NO |
| unit_price | double precision | NO |
| quantity | integer | NO |
| discount_rate | double precision | YES |
| total_price | double precision | NO |
| pricing_detail_id | integer | NO |
| settlement_order_id | integer | YES |
| settlement_company_id | integer | YES |
| settlement_status | character varying | YES |
| settlement_date | timestamp without time zone | YES |
| settlement_notes | text | YES |
| currency | character varying | YES |

### settlement_orders
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| order_number | character varying | NO |
| pricing_order_id | integer | NO |
| project_id | integer | NO |
| quotation_id | integer | NO |
| distributor_id | integer | NO |
| dealer_id | integer | YES |
| total_amount | double precision | YES |
| total_discount_rate | double precision | YES |
| status | character varying | YES |
| approved_by | integer | YES |
| approved_at | timestamp without time zone | YES |
| created_by | integer | NO |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### settlements
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| settlement_number | character varying | NO |
| company_id | integer | NO |
| settlement_date | timestamp without time zone | YES |
| status | character varying | YES |
| total_items | integer | YES |
| description | text | YES |
| created_by_id | integer | NO |
| approved_by_id | integer | YES |
| approved_at | timestamp without time zone | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### solution_manager_email_settings
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| user_id | integer | NO |
| quotation_created | boolean | YES |
| quotation_updated | boolean | YES |
| project_created | boolean | YES |
| project_stage_changed | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### system_metrics
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| version_id | integer | YES |
| avg_response_time | double precision | YES |
| max_response_time | double precision | YES |
| error_rate | double precision | YES |
| active_users | integer | YES |
| total_requests | integer | YES |
| database_size | bigint | YES |
| cpu_usage | double precision | YES |
| memory_usage | double precision | YES |
| disk_usage | double precision | YES |
| recorded_at | timestamp without time zone | YES |

### system_settings
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| key | character varying | NO |
| value | text | YES |
| description | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### upgrade_logs
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| version_id | integer | NO |
| from_version | character varying | YES |
| to_version | character varying | NO |
| upgrade_date | timestamp without time zone | NO |
| upgrade_type | character varying | YES |
| status | character varying | YES |
| upgrade_notes | text | YES |
| error_message | text | YES |
| duration_seconds | integer | YES |
| operator_id | integer | YES |
| operator_name | character varying | YES |
| environment | character varying | YES |
| server_info | text | YES |

### user_event_subscriptions
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| user_id | integer | NO |
| target_user_id | integer | NO |
| event_id | integer | NO |
| enabled | boolean | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |

### users
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| username | character varying | NO |
| password_hash | character varying | NO |
| real_name | character varying | YES |
| company_name | character varying | YES |
| email | character varying | YES |
| phone | character varying | YES |
| department | character varying | YES |
| is_department_manager | boolean | YES |
| role | character varying | YES |
| is_profile_complete | boolean | YES |
| wechat_openid | character varying | YES |
| wechat_nickname | character varying | YES |
| wechat_avatar | character varying | YES |
| is_active | boolean | YES |
| created_at | double precision | YES |
| last_login | double precision | YES |
| updated_at | double precision | YES |
| language_preference | character varying | YES |

### version_records
| 字段名 | 数据类型 | 可空 |
|--------|----------|------|
| id | integer | NO |
| version_number | character varying | NO |
| version_name | character varying | YES |
| release_date | timestamp without time zone | NO |
| description | text | YES |
| is_current | boolean | YES |
| environment | character varying | YES |
| total_features | integer | YES |
| total_fixes | integer | YES |
| total_improvements | integer | YES |
| git_commit | character varying | YES |
| build_number | character varying | YES |
| created_at | timestamp without time zone | YES |
| updated_at | timestamp without time zone | YES |
