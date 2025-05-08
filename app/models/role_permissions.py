from app import db

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    can_view = db.Column(db.Boolean, default=False)
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('role', 'module', name='uix_role_module'),)

# 初始化财务总监角色的权限
def init_finance_director_permissions():
    """
    初始化财务总监(finace_director)角色的权限，确保他们可以查看客户模块
    """
    from app import db, create_app
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    app = create_app()
    with app.app_context():
        try:
            # 检查是否已有财务总监角色的客户模块权限
            existing_perm = RolePermission.query.filter_by(
                role='finace_director', 
                module='customer'
            ).first()
            
            # 如果没有，则添加
            if not existing_perm:
                logger.info("为finace_director角色添加customer模块权限")
                perm = RolePermission(
                    role='finace_director',
                    module='customer',
                    can_view=True,  # 允许查看
                    can_create=False,
                    can_edit=False,
                    can_delete=False
                )
                db.session.add(perm)
                
                # 添加项目模块权限
                project_perm = RolePermission.query.filter_by(
                    role='finace_director', 
                    module='project'
                ).first()
                
                if not project_perm:
                    logger.info("为finace_director角色添加project模块权限")
                    project_perm = RolePermission(
                        role='finace_director',
                        module='project',
                        can_view=True,  # 允许查看
                        can_create=False,
                        can_edit=False,
                        can_delete=False
                    )
                    db.session.add(project_perm)
                
                # 添加报价模块权限
                quotation_perm = RolePermission.query.filter_by(
                    role='finace_director', 
                    module='quotation'
                ).first()
                
                if not quotation_perm:
                    logger.info("为finace_director角色添加quotation模块权限")
                    quotation_perm = RolePermission(
                        role='finace_director',
                        module='quotation',
                        can_view=True,  # 允许查看
                        can_create=False,
                        can_edit=False,
                        can_delete=False
                    )
                    db.session.add(quotation_perm)
                
                # 添加产品查看权限
                product_perm = RolePermission.query.filter_by(
                    role='finace_director', 
                    module='product'
                ).first()
                
                if not product_perm:
                    logger.info("为finace_director角色添加product模块权限")
                    product_perm = RolePermission(
                        role='finace_director',
                        module='product',
                        can_view=True,  # 允许查看
                        can_create=False,
                        can_edit=False,
                        can_delete=False
                    )
                    db.session.add(product_perm)
                
                db.session.commit()
                logger.info("已为财务总监角色添加客户、项目、报价和产品模块的查看权限")
            else:
                logger.info("finace_director角色已有权限配置，无需添加")
                
        except Exception as e:
            logger.error(f"初始化finace_director角色权限失败: {str(e)}")
            db.session.rollback()
            
# 如果直接运行此文件，则执行初始化
if __name__ == "__main__":
    init_finance_director_permissions() 