-- 清空现有评分配置数据
DELETE FROM project_scoring_config;

-- 插入评分配置数据
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'design_consultant', '设计顾问', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'general_contractor', '总承包', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'project_category', '项目分类', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'project_stage', '项目阶段', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'system_integrator', '集成商', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('information', 'user_info', '用户信息', 0.10, '法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('manual', 'supervisor_award', '上级奖励', 0.50, '手动评分', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('quotation', 'approved_quotation', '审核通过的报价单', 0.50, '必须经由解决方案经理审批流程通过', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('stage', 'awarded', '中标', 1.00, '无', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('stage', 'final_pricing', '批价', 1.50, '无', true, NOW(), NOW());
INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) VALUES ('stage', 'tender', '招投标', 0.50, '无', true, NOW(), NOW());