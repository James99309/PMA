-- 添加分类共享图片和PDF字段
-- 执行前请先检查字段是否已存在

-- 添加 image_path 字段
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS image_path VARCHAR(500);

-- 添加 pdf_path 字段
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS pdf_path VARCHAR(500);

-- 数据迁移：从现有产品填充分类文件
-- 为每个分类设置第一个有图片的产品的图片路径
UPDATE product_categories pc
SET image_path = (
    SELECT p.image_path
    FROM products p
    WHERE p.category_id = pc.id
      AND p.is_deleted = false
      AND p.image_path IS NOT NULL
      AND p.image_path != ''
    ORDER BY p.id
    LIMIT 1
)
WHERE pc.image_path IS NULL;

-- 为每个分类设置第一个有PDF的产品的PDF路径
UPDATE product_categories pc
SET pdf_path = (
    SELECT p.pdf_path
    FROM products p
    WHERE p.category_id = pc.id
      AND p.is_deleted = false
      AND p.pdf_path IS NOT NULL
      AND p.pdf_path != ''
    ORDER BY p.id
    LIMIT 1
)
WHERE pc.pdf_path IS NULL;

-- 从研发产品填充（如果标准产品没有）
UPDATE product_categories pc
SET image_path = (
    SELECT dp.image_path
    FROM dev_products dp
    WHERE dp.category_id = pc.id
      AND dp.is_deleted = false
      AND dp.image_path IS NOT NULL
      AND dp.image_path != ''
    ORDER BY dp.id
    LIMIT 1
)
WHERE pc.image_path IS NULL;

-- 显示迁移结果
SELECT id, name,
       CASE WHEN image_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_image,
       CASE WHEN pdf_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_pdf
FROM product_categories
ORDER BY id;
