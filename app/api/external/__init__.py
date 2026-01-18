"""
外部 API 模块
用于提供给外部系统调用的 API 端点
"""
from flask import Blueprint

external_api_bp = Blueprint('external_api', __name__, url_prefix='/api/external')

from . import employees  # noqa
