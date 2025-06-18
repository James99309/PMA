from flask import Blueprint, jsonify

api_v1_bp = Blueprint('api_v1', __name__)

@api_v1_bp.route('/')
def index():
    """API V1基础端点"""
    return jsonify({"message": "PMA API v1", "status": "running"})

# 导入API模块
from app.api.v1 import auth, users, permissions, affiliations, dictionary, discount_permissions 