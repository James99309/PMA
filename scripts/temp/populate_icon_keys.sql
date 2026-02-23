-- 批量填充 product_subcategories.icon_key
-- 基于 SUBCAT_ICON_MAP 关键字匹配逻辑
-- 执行前请先备份，执行后可在系统图编辑器中验证图标显示

BEGIN;

-- 室内天线
UPDATE product_subcategories SET icon_key = 'indoor_antenna'
WHERE icon_key IS NULL AND (name LIKE '%室内天线%' OR name_en ILIKE '%indoor antenna%' OR name_en ILIKE '%ceiling antenna%');

-- 全向天线
UPDATE product_subcategories SET icon_key = 'antenna_omni'
WHERE icon_key IS NULL AND (name LIKE '%全向天线%' OR name_en ILIKE '%omni%antenna%');

-- 定向天线 / 板状天线
UPDATE product_subcategories SET icon_key = 'antenna_dir'
WHERE icon_key IS NULL AND (name LIKE '%定向天线%' OR name LIKE '%板状天线%' OR name_en ILIKE '%directional%antenna%' OR name_en ILIKE '%panel%antenna%');

-- 对数天线 / 八木天线
UPDATE product_subcategories SET icon_key = 'antenna_out'
WHERE icon_key IS NULL AND (name LIKE '%对数天线%' OR name LIKE '%八木天线%' OR name_en ILIKE '%log%periodic%' OR name_en ILIKE '%yagi%');

-- 数字基站 (RRU)
UPDATE product_subcategories SET icon_key = 'rru'
WHERE icon_key IS NULL AND (name LIKE '%数字基站%' OR name_en ILIKE '%digital base%' OR name_en ILIKE '%RRU%');

-- 基站 (BBU) — 匹配含"基站"但不含"数字基站"的
UPDATE product_subcategories SET icon_key = 'bbu'
WHERE icon_key IS NULL AND (name LIKE '%基站%' OR name_en ILIKE '%base station%' OR name_en ILIKE '%BBU%');

-- 直放站 / 射频直放站 / 光纤直放站
UPDATE product_subcategories SET icon_key = 'repeater'
WHERE icon_key IS NULL AND (name LIKE '%直放站%' OR name LIKE '%放大器%' OR name_en ILIKE '%repeater%' OR name_en ILIKE '%BDA%' OR name_en ILIKE '%amplifier%');

-- 合路器 / 分合路 / 双工器
UPDATE product_subcategories SET icon_key = 'combiner'
WHERE icon_key IS NULL AND (name LIKE '%合路器%' OR name LIKE '%分合路%' OR name LIKE '%双工器%'
    OR name_en ILIKE '%combiner%' OR name_en ILIKE '%duplexer%' OR name_en ILIKE '%diplexer%');

-- 功分器 / 分路器
UPDATE product_subcategories SET icon_key = 'splitter_2'
WHERE icon_key IS NULL AND (name LIKE '%功分器%' OR name LIKE '%分路器%'
    OR name_en ILIKE '%splitter%' OR name_en ILIKE '%divider%');

-- 耦合器
UPDATE product_subcategories SET icon_key = 'coupler'
WHERE icon_key IS NULL AND (name LIKE '%耦合器%' OR name_en ILIKE '%coupler%');

-- 电源 / 供电
UPDATE product_subcategories SET icon_key = 'psu'
WHERE icon_key IS NULL AND (name LIKE '%电源%' OR name LIKE '%供电%'
    OR name_en ILIKE '%power supply%' OR name_en ILIKE '%PSU%');

-- UPS
UPDATE product_subcategories SET icon_key = 'ups'
WHERE icon_key IS NULL AND (name LIKE '%UPS%' OR name_en ILIKE '%UPS%');

-- 防雷 (SPD)
UPDATE product_subcategories SET icon_key = 'spd'
WHERE icon_key IS NULL AND (name LIKE '%防雷%' OR name LIKE '%避雷%'
    OR name_en ILIKE '%surge%' OR name_en ILIKE '%SPD%' OR name_en ILIKE '%lightning%');

-- 负载
UPDATE product_subcategories SET icon_key = 'load'
WHERE icon_key IS NULL AND (name LIKE '%负载%' OR name_en ILIKE '%load%' OR name_en ILIKE '%termination%');

-- POI
UPDATE product_subcategories SET icon_key = 'poi'
WHERE icon_key IS NULL AND (name LIKE '%POI%' OR name_en ILIKE '%POI%');

-- 查看结果
SELECT id, name, name_en, icon_key FROM product_subcategories ORDER BY category_id, display_order;

COMMIT;
