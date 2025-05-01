from app import db
import logging

logger = logging.getLogger(__name__)

def run_migrations():
    """运行数据库迁移"""
    logger.info("开始数据库迁移...")
    
    # 添加field_code字段到dev_product_specs表
    try:
        logger.info("检查dev_product_specs表是否存在field_code字段...")
        # 检查字段是否已存在
        result = db.session.execute("PRAGMA table_info(dev_product_specs)")
        columns = [row[1] for row in result]
        
        if 'field_code' not in columns:
            logger.info("添加field_code字段到dev_product_specs表...")
            db.session.execute("ALTER TABLE dev_product_specs ADD COLUMN field_code VARCHAR(10)")
            db.session.commit()
            logger.info("成功添加field_code字段")
            
            # 更新现有规格的编码
            logger.info("开始更新现有规格的编码...")
            
            # 获取所有规格记录
            result = db.session.execute("""
                SELECT dps.id, dps.field_name, dps.field_value, pcf.id as field_id 
                FROM dev_product_specs dps
                JOIN dev_products dp ON dps.dev_product_id = dp.id
                LEFT JOIN product_code_fields pcf ON pcf.name = dps.field_name AND pcf.subcategory_id = dp.subcategory_id
                WHERE pcf.id IS NOT NULL
            """)
            
            update_count = 0
            for row in result:
                spec_id = row[0]
                spec_value = row[2]
                field_id = row[3]
                
                if field_id and spec_value:
                    # 查找对应的选项编码
                    option_result = db.session.execute("""
                        SELECT code FROM product_code_field_options
                        WHERE field_id = :field_id AND value = :value
                    """, {"field_id": field_id, "value": spec_value})
                    
                    option_row = option_result.fetchone()
                    if option_row:
                        code = option_row[0]
                        # 更新规格记录
                        db.session.execute("""
                            UPDATE dev_product_specs
                            SET field_code = :code
                            WHERE id = :spec_id
                        """, {"code": code, "spec_id": spec_id})
                        update_count += 1
            
            db.session.commit()
            logger.info(f"已更新 {update_count} 条规格记录的编码")
        else:
            logger.info("field_code字段已存在，无需迁移")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"数据库迁移出错: {str(e)}")
        raise
    
    logger.info("数据库迁移完成") 