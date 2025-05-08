from flask import Blueprint, render_template, redirect, url_for, session
import logging
from datetime import datetime
from flask_login import current_user, login_required
from app.models.project import Project
from app.utils.access_control import get_viewable_data
from app.models.quotation import Quotation
from app.models.customer import Company

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    logger.info('Accessing index page')
    logger.info('User logged in, rendering index page')
    # 查询当前用户可见的最近5个项目，按更新时间倒序
    recent_projects = get_viewable_data(Project, current_user).order_by(Project.updated_at.desc()).limit(5).all()
    # 查询当前用户可见的最近5条报价，按更新时间倒序
    recent_quotations = get_viewable_data(Quotation, current_user).order_by(Quotation.updated_at.desc()).limit(5).all()
    # 查询当前用户可见的最近5个客户，按更新时间倒序
    recent_companies = get_viewable_data(Company, current_user).order_by(Company.updated_at.desc()).limit(5).all()
    return render_template('index.html', now=datetime.now(), recent_projects=recent_projects, recent_quotations=recent_quotations, recent_companies=recent_companies) 