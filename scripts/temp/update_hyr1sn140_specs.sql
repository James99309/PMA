-- ============================================================================
-- 更新 HYR1SN140 (Product 59) 规格 - 对齐 HYR1SN14A (Product 60)
--
-- 目的: 将 product 59 的旧规格替换为 product 60 的规格，仅修改工作频率
-- 执行环境: SP8D 生产数据库 (pma_synology)
-- 执行方式: docker exec pma-postgres psql -U pma -d pma_synology -f /tmp/update_hyr1sn140_specs.sql
--
-- 差异点:
--   HYR1SN14A (60): 工作频率 = TX：412-416 / RX：402-406, field_code = A
--   HYR1SN140 (59): 工作频率 = TX：420-424 / RX：410-414, field_code = 4
-- ============================================================================

BEGIN;

-- ============================================================================
-- 验证前置状态
-- ============================================================================
DO $$
DECLARE
    v_count_59 INTEGER;
    v_count_60 INTEGER;
    v_name_59 TEXT;
    v_name_60 TEXT;
BEGIN
    SELECT COUNT(*) INTO v_count_59 FROM product_specs WHERE product_id = 59;
    SELECT COUNT(*) INTO v_count_60 FROM product_specs WHERE product_id = 60;
    SELECT product_name INTO v_name_59 FROM products WHERE id = 59;
    SELECT product_name INTO v_name_60 FROM products WHERE id = 60;

    RAISE NOTICE '=== 执行前状态 ===';
    RAISE NOTICE 'Product 59 (%): % 条规格', v_name_59, v_count_59;
    RAISE NOTICE 'Product 60 (%): % 条规格', v_name_60, v_count_60;

    -- 安全检查: product 60 应有 25 条规格
    IF v_count_60 != 25 THEN
        RAISE EXCEPTION 'Product 60 规格数量异常: 期望 25, 实际 %', v_count_60;
    END IF;
END $$;

-- ============================================================================
-- Step 1: 删除 HYR1SN140 的旧规格
-- ============================================================================
DELETE FROM product_specs WHERE product_id = 59;

-- ============================================================================
-- Step 2: 从 HYR1SN14A 复制规格到 HYR1SN140（修改工作频率）
-- ============================================================================
INSERT INTO product_specs (product_id, field_name, field_name_en, field_value, field_code, include_in_description, display_order)
SELECT
    59,
    field_name,
    field_name_en,
    CASE WHEN field_name = '工作频率' THEN 'TX：420-424 / RX：410-414' ELSE field_value END,
    CASE WHEN field_name = '工作频率' THEN '4' ELSE field_code END,
    include_in_description,
    display_order
FROM product_specs
WHERE product_id = 60
ORDER BY display_order;

-- ============================================================================
-- Step 3: 更新 spec_mn（与 HYR1SN14A 一致，工作频率 use_in_code=false 不影响）
-- ============================================================================
UPDATE products
SET spec_mn = (SELECT spec_mn FROM products WHERE id = 60)
WHERE id = 59;

-- ============================================================================
-- Step 4: 更新 code_definition_snapshot
-- 从 product 60 复制快照，修改:
--   - full_code: 改为 HYR1SN140
--   - generated_at: 更新时间
--   - source: 标记为 copy_from_60
--   - code_parts 中工作频率的 field_code 和 value
-- ============================================================================
UPDATE products
SET code_definition_snapshot = (
    SELECT jsonb_set(
        jsonb_set(
            jsonb_set(
                jsonb_set(
                    code_definition_snapshot::jsonb,
                    '{full_code}', '"HYR1SN140"'
                ),
                '{source}', '"copy_from_product_60"'
            ),
            '{generated_at}', to_jsonb(to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'))
        ),
        -- 修改 code_parts 中工作频率的值
        '{code_parts}',
        (
            SELECT jsonb_agg(
                CASE
                    WHEN elem->>'field_name' = '工作频率' THEN
                        jsonb_set(
                            jsonb_set(elem, '{value}', '"TX：420-424 / RX：410-414"'),
                            '{field_code}', '"4"'
                        )
                    ELSE elem
                END
                ORDER BY (elem->>'position')::int
            )
            FROM jsonb_array_elements(code_definition_snapshot::jsonb->'code_parts') AS elem
        )
    )
    FROM products WHERE id = 60
)
WHERE id = 59;

-- ============================================================================
-- 验证结果
-- ============================================================================
DO $$
DECLARE
    v_count_59 INTEGER;
    v_count_60 INTEGER;
    v_mn_59 TEXT;
    v_mn_60 TEXT;
    v_snap_59 BOOLEAN;
    v_snap_60 BOOLEAN;
    v_freq_59 TEXT;
    v_freq_60 TEXT;
    v_code_59 TEXT;
    v_code_60 TEXT;
    v_diff_count INTEGER;
BEGIN
    -- 规格数量
    SELECT COUNT(*) INTO v_count_59 FROM product_specs WHERE product_id = 59;
    SELECT COUNT(*) INTO v_count_60 FROM product_specs WHERE product_id = 60;

    -- spec_mn
    SELECT spec_mn INTO v_mn_59 FROM products WHERE id = 59;
    SELECT spec_mn INTO v_mn_60 FROM products WHERE id = 60;

    -- 快照存在
    SELECT code_definition_snapshot IS NOT NULL INTO v_snap_59 FROM products WHERE id = 59;
    SELECT code_definition_snapshot IS NOT NULL INTO v_snap_60 FROM products WHERE id = 60;

    -- 工作频率值
    SELECT field_value, field_code INTO v_freq_59, v_code_59
    FROM product_specs WHERE product_id = 59 AND field_name = '工作频率';
    SELECT field_value, field_code INTO v_freq_60, v_code_60
    FROM product_specs WHERE product_id = 60 AND field_name = '工作频率';

    -- 除工作频率外的差异数
    SELECT COUNT(*) INTO v_diff_count
    FROM product_specs a
    FULL OUTER JOIN product_specs b
        ON a.field_name = b.field_name
        AND a.field_value = b.field_value
        AND a.field_code IS NOT DISTINCT FROM b.field_code
    WHERE a.product_id = 59 AND b.product_id = 60
        AND a.field_name != '工作频率'
        AND (a.field_value != b.field_value OR a.field_code IS DISTINCT FROM b.field_code);

    RAISE NOTICE '';
    RAISE NOTICE '=== 验证结果 ===';
    RAISE NOTICE '规格数量: Product 59 = %, Product 60 = % [%]',
        v_count_59, v_count_60,
        CASE WHEN v_count_59 = v_count_60 THEN 'OK' ELSE 'MISMATCH!' END;
    RAISE NOTICE 'spec_mn: Product 59 = %, Product 60 = % [%]',
        v_mn_59, v_mn_60,
        CASE WHEN v_mn_59 = v_mn_60 THEN 'OK' ELSE 'MISMATCH!' END;
    RAISE NOTICE '快照: Product 59 = %, Product 60 = % [%]',
        v_snap_59, v_snap_60,
        CASE WHEN v_snap_59 AND v_snap_60 THEN 'OK' ELSE 'MISSING!' END;
    RAISE NOTICE '工作频率 Product 59: % (code=%)', v_freq_59, v_code_59;
    RAISE NOTICE '工作频率 Product 60: % (code=%)', v_freq_60, v_code_60;
    RAISE NOTICE '除频率外的差异数: % [%]', v_diff_count,
        CASE WHEN v_diff_count = 0 THEN 'OK' ELSE 'HAS DIFFERENCES!' END;

    -- 最终检查
    IF v_count_59 != v_count_60 THEN
        RAISE EXCEPTION '规格数量不匹配!';
    END IF;
    IF v_freq_59 != 'TX：420-424 / RX：410-414' THEN
        RAISE EXCEPTION '工作频率值不正确: %', v_freq_59;
    END IF;
    IF v_code_59 != '4' THEN
        RAISE EXCEPTION '工作频率编码不正确: %', v_code_59;
    END IF;
END $$;

COMMIT;

-- 最终查看结果
SELECT '=== Product 59 规格列表 ===' AS info;
SELECT display_order, field_name, field_value, field_code, include_in_description
FROM product_specs WHERE product_id = 59 ORDER BY display_order;

SELECT '=== spec_mn 对比 ===' AS info;
SELECT id, product_name, spec_mn FROM products WHERE id IN (59, 60);
