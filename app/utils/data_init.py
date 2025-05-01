"""
数据初始化工具
用于在应用模型变更后初始化数据
"""
import logging
from app import db
from app.models.user import User, Permission
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.product import Product
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import traceback

logger = logging.getLogger(__name__)

def initialize_data_ownership():
    """为现有数据设置默认所有者"""
    try:
        # 获取管理员用户
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            logger.warning("未找到管理员用户，使用ID=1作为默认所有者")
            default_owner_id = 1
        else:
            default_owner_id = admin.id
        
        logger.info(f"开始数据所有权初始化，默认所有者ID: {default_owner_id}")
        
        # 设置公司数据所有者
        try:
            companies = Company.query.filter(Company.owner_id.is_(None)).all()
            logger.info(f"设置 {len(companies)} 个公司的所有者")
            for company in companies:
                company.owner_id = default_owner_id
        except OperationalError:
            logger.warning("公司表可能缺少owner_id列，请先运行数据库迁移")
        except Exception as e:
            logger.error(f"处理公司数据时出错: {str(e)}")
        
        # 设置联系人数据所有者
        try:
            contacts = Contact.query.filter(Contact.owner_id.is_(None)).all()
            logger.info(f"设置 {len(contacts)} 个联系人的所有者")
            for contact in contacts:
                contact.owner_id = default_owner_id
        except OperationalError:
            logger.warning("联系人表可能缺少owner_id列，请先运行数据库迁移")
        except Exception as e:
            logger.error(f"处理联系人数据时出错: {str(e)}")
        
        # 设置项目数据所有者和类型
        try:
            projects = Project.query.filter(Project.owner_id.is_(None)).all()
            logger.info(f"设置 {len(projects)} 个项目的所有者")
            for project in projects:
                project.owner_id = default_owner_id
                # 将旧的项目类型格式转换为新格式
                if not project.project_type or project.project_type not in ['normal', 'channel_follow', 'sales_focus']:
                    if project.project_type == '渠道跟进':
                        project.project_type = 'channel_follow'
                    elif project.project_type == '销售重点':
                        project.project_type = 'sales_focus'
                    else:
                        project.project_type = 'normal'
        except OperationalError:
            logger.warning("项目表可能缺少owner_id列，请先运行数据库迁移")
        except Exception as e:
            logger.error(f"处理项目数据时出错: {str(e)}")
        
        # 设置报价单数据所有者
        try:
            quotations = Quotation.query.filter(Quotation.owner_id.is_(None)).all()
            logger.info(f"设置 {len(quotations)} 个报价单的所有者")
            for quotation in quotations:
                quotation.owner_id = default_owner_id
        except OperationalError:
            logger.warning("报价单表可能缺少owner_id列，请先运行数据库迁移")
        except Exception as e:
            logger.error(f"处理报价单数据时出错: {str(e)}")
            
        # 设置产品数据所有者
        try:
            products = Product.query.filter(Product.owner_id.is_(None)).all()
            logger.info(f"设置 {len(products)} 个产品的所有者")
            for product in products:
                product.owner_id = default_owner_id
        except OperationalError:
            logger.warning("产品表可能缺少owner_id列，请先运行数据库迁移")
        except Exception as e:
            logger.error(f"处理产品数据时出错: {str(e)}")
        
        # 提交变更
        try:
            db.session.commit()
            logger.info("数据所有权初始化完成")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"数据所有权初始化失败: {str(e)}")
            return False
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"数据所有权初始化过程中发生未处理的异常: {str(e)}")
        logger.debug(traceback.format_exc())
        return False 