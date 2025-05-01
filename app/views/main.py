from flask import Blueprint, render_template, redirect, url_for, session
import logging
from datetime import datetime
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    logger.info('Accessing index page')
    logger.info('User logged in, rendering index page')
    return render_template('index.html', now=datetime.now()) 