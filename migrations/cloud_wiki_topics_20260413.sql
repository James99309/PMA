-- Wiki Phase 2.1: knowledge_topics 主数据表（云端部署脚本）
-- 执行时机：代码部署后（db.create_all() 已创建表）
-- 幂等性：CREATE TABLE IF NOT EXISTS + INSERT ON CONFLICT DO NOTHING
--
-- 执行方式（CN NAS）:
--   cat migrations/cloud_wiki_topics_20260413.sql | \
--     ssh -p 72 james.sh@100.118.231.15 \
--     "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology"

-- ══════════════════════════════════════════════════════════════
-- 1. knowledge_topics 表（db.create_all 通常已建，这里兜底）
-- ══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS knowledge_topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_knowledge_topics_name ON knowledge_topics (name);

-- ══════════════════════════════════════════════════════════════
-- 2. 种入 8 个中文 topic（中国 NAS 专用）
--    注意：SG NAS 应使用英文 topic，不要执行本文件
-- ══════════════════════════════════════════════════════════════

INSERT INTO knowledge_topics (name, description, sort_order, created_by, created_at, updated_at)
VALUES
  ('销售营销', '销售、市场、营销相关资料', 10, 5, NOW(), NOW()),
  ('产品技术', '产品、方案、研发技术相关资料', 20, 5, NOW(), NOW()),
  ('服务支持', '售后、技术支持、服务流程相关资料', 30, 5, NOW(), NOW()),
  ('供应链',   '采购、物流、仓储相关资料',       40, 5, NOW(), NOW()),
  ('人事行政', '人事制度、绩效、员工手册、行政事务', 50, 5, NOW(), NOW()),
  ('财务',     '财务制度、预算、报销相关资料',   60, 5, NOW(), NOW()),
  ('制度规范', '公司层面制度、流程、规范汇总',   70, 5, NOW(), NOW()),
  ('行业知识', '行业趋势、竞品分析、行业标准',   80, 5, NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ══════════════════════════════════════════════════════════════
-- 验证
-- ══════════════════════════════════════════════════════════════
--   SELECT id, name, sort_order FROM knowledge_topics ORDER BY sort_order;
