-- Verify product 86: check field_code against specification_options dictionary
SELECT
    ps.field_name,
    ps.field_value,
    ps.field_code,
    so.code AS dict_code,
    CASE
        WHEN so.code IS NULL THEN 'NO_DICT'
        WHEN ps.field_code = so.code THEN 'OK'
        ELSE 'MISMATCH'
    END AS status
FROM product_specs ps
LEFT JOIN specification_dictionary sd ON sd.name = ps.field_name
LEFT JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id = 86
ORDER BY ps.display_order;

-- Summary counts
SELECT
    CASE
        WHEN so.code IS NULL THEN 'NO_DICT'
        WHEN ps.field_code = so.code THEN 'OK'
        ELSE 'MISMATCH'
    END AS status,
    COUNT(*) AS cnt
FROM product_specs ps
LEFT JOIN specification_dictionary sd ON sd.name = ps.field_name
LEFT JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id = 86
GROUP BY 1
ORDER BY 1;
