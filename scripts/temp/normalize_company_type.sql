-- 客户企业类型归一化：旧中文值 → 英文 key
-- 解决客户列表筛选器中"用户"出现两次的问题
-- 执行日期: 2026-02-12

BEGIN;

UPDATE companies SET company_type = 'user' WHERE company_type = '用户';
UPDATE companies SET company_type = 'user' WHERE company_type = '最终用户';
UPDATE companies SET company_type = 'dealer' WHERE company_type = '经销商';
UPDATE companies SET company_type = 'integrator' WHERE company_type = '集成商';
UPDATE companies SET company_type = 'designer' WHERE company_type = '设计院';
UPDATE companies SET company_type = 'contractor' WHERE company_type = '总包商';
UPDATE companies SET company_type = 'distributor' WHERE company_type = '代理商';
UPDATE companies SET company_type = 'partner' WHERE company_type = '合作伙伴';
UPDATE companies SET company_type = 'other' WHERE company_type = '其他';

COMMIT;
