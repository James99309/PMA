-- Migration: Add reference_price column to temp_products table
-- Date: 2025-07-24
-- Description: Add reference_price column to store pricing information for temporary products

-- Add the reference_price column
ALTER TABLE temp_products 
ADD COLUMN reference_price FLOAT;

-- Add comment to the column
COMMENT ON COLUMN temp_products.reference_price IS 'Reference price (saved unit price)';