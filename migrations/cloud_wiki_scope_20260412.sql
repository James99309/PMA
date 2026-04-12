-- Wiki Phase 2: scope 权限层级迁移脚本（云端）
-- 执行时机：代码部署后（db.create_all() 已创建新表）
-- 幂等性：所有操作用 IF NOT EXISTS / DO $$ BEGIN ... EXCEPTION

-- ══════════════════════════════════════════════════════════════
-- 1. knowledge_raw_files 添加 scope 相关列
-- ══════════════════════════════════════════════════════════════

DO $$ BEGIN
    ALTER TABLE knowledge_raw_files ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'personal';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE knowledge_raw_files ADD COLUMN owner_id INTEGER REFERENCES users(id);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE knowledge_raw_files ADD COLUMN owner_department VARCHAR(100);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- 回填 owner_id = added_by（已有数据）
UPDATE knowledge_raw_files SET owner_id = added_by WHERE owner_id IS NULL;

-- 设为 NOT NULL（回填完成后）
ALTER TABLE knowledge_raw_files ALTER COLUMN owner_id SET NOT NULL;

-- 回填 owner_department（从 users 表取）
UPDATE knowledge_raw_files r
SET owner_department = u.department
FROM users u
WHERE r.owner_id = u.id AND r.owner_department IS NULL AND u.department IS NOT NULL;

-- 索引
CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_scope ON knowledge_raw_files (scope);
CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_owner_department ON knowledge_raw_files (owner_department);
CREATE INDEX IF NOT EXISTS ix_knowledge_raw_scope_dept ON knowledge_raw_files (scope, owner_department);
CREATE INDEX IF NOT EXISTS ix_knowledge_raw_scope_owner ON knowledge_raw_files (scope, owner_id);

-- ══════════════════════════════════════════════════════════════
-- 2. knowledge_wiki_articles 添加 scope 相关列
-- ══════════════════════════════════════════════════════════════

DO $$ BEGIN
    ALTER TABLE knowledge_wiki_articles ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'personal';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE knowledge_wiki_articles ADD COLUMN owner_id INTEGER REFERENCES users(id);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE knowledge_wiki_articles ADD COLUMN owner_department VARCHAR(100);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- 回填 owner_id：从关联的 raw file 继承，或用 admin (id=1) 兜底
UPDATE knowledge_wiki_articles a
SET owner_id = COALESCE(
    (SELECT r.owner_id FROM knowledge_raw_files r
     WHERE r.id = (a.source_raw_ids->0)::int LIMIT 1),
    1
)
WHERE a.owner_id IS NULL;

ALTER TABLE knowledge_wiki_articles ALTER COLUMN owner_id SET NOT NULL;

-- 回填 owner_department
UPDATE knowledge_wiki_articles a
SET owner_department = u.department
FROM users u
WHERE a.owner_id = u.id AND a.owner_department IS NULL AND u.department IS NOT NULL;

-- 索引
CREATE INDEX IF NOT EXISTS ix_knowledge_wiki_articles_scope ON knowledge_wiki_articles (scope);
CREATE INDEX IF NOT EXISTS ix_knowledge_wiki_articles_owner_department ON knowledge_wiki_articles (owner_department);
CREATE INDEX IF NOT EXISTS ix_wiki_article_scope_dept ON knowledge_wiki_articles (scope, owner_department);
CREATE INDEX IF NOT EXISTS ix_wiki_article_scope_owner ON knowledge_wiki_articles (scope, owner_id);

-- ══════════════════════════════════════════════════════════════
-- 3. knowledge_promotion_requests 补充 assigned_to 列
--    （db.create_all 可能已创建表但缺少此列）
-- ══════════════════════════════════════════════════════════════

DO $$ BEGIN
    ALTER TABLE knowledge_promotion_requests ADD COLUMN assigned_to INTEGER REFERENCES users(id);
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS ix_promotion_article ON knowledge_promotion_requests (article_id);
CREATE INDEX IF NOT EXISTS ix_promotion_status ON knowledge_promotion_requests (status);
CREATE INDEX IF NOT EXISTS ix_promotion_assigned_status ON knowledge_promotion_requests (assigned_to, status);

-- ══════════════════════════════════════════════════════════════
-- 4. knowledge_share_grants 索引（表由 create_all 创建）
-- ══════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS ix_share_grant_article ON knowledge_share_grants (article_id);
CREATE INDEX IF NOT EXISTS ix_share_grant_target ON knowledge_share_grants (grant_type, grant_target);

-- ══════════════════════════════════════════════════════════════
-- 完成
-- ══════════════════════════════════════════════════════════════
-- 验证：
--   SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_raw_files' AND column_name IN ('scope', 'owner_id', 'owner_department');
--   SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_wiki_articles' AND column_name IN ('scope', 'owner_id', 'owner_department');
--   SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_promotion_requests' AND column_name = 'assigned_to';
