-- Update the specification text summary for product 86
UPDATE products SET specification = (
    SELECT string_agg(
        ps.field_name || ': ' || ps.field_value || COALESCE(' ' || sd.unit, ''),
        ', '
        ORDER BY ps.display_order
    )
    FROM product_specs ps
    LEFT JOIN (
        SELECT DISTINCT ON (name) name, unit
        FROM spec_definitions
        ORDER BY name, id
    ) sd ON sd.name = ps.field_name
    WHERE ps.product_id = 86
    AND ps.field_value IS NOT NULL AND ps.field_value != ''
) WHERE id = 86;

-- Verify
SELECT left(specification, 200) FROM products WHERE id = 86;
