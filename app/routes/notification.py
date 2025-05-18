from flask import Blueprint

notification = Blueprint('notification', __name__, url_prefix='/notification')
 
from app.views.notification import * 