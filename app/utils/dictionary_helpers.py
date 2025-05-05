# app/utils/dictionary_helpers.py
# 用于从数据库dictionaries表获取字典项（如角色显示名），支持Flask g对象缓存

from flask import g
from app.models.dictionary import Dictionary
from app import db

ROLE_TYPE = 'role'


def get_role_display_name(role_key):
    """
    根据角色key从数据库字典表获取角色显示名称。
    优先从Flask g对象缓存获取，避免重复查询。
    """
    if not role_key:
        return '未知角色'
    
    # 统一小写处理
    role_key = role_key.lower()
    
    # 缓存机制
    if not hasattr(g, '_role_display_cache'):
        # 查询所有角色字典项
        role_dicts = db.session.query(Dictionary).filter_by(type=ROLE_TYPE, is_active=True).all()
        g._role_display_cache = {item.key.lower(): item.value for item in role_dicts}
    
    return g._role_display_cache.get(role_key, role_key)


def get_dictionary_value(dict_type, key):
    """
    通用方法：根据type和key获取字典项value
    """
    if not key:
        return ''
    key = key.lower()
    cache_name = f'_dict_{dict_type}_cache'
    if not hasattr(g, cache_name):
        dicts = db.session.query(Dictionary).filter_by(type=dict_type, is_active=True).all()
        setattr(g, cache_name, {item.key.lower(): item.value for item in dicts})
    cache = getattr(g, cache_name)
    return cache.get(key, key)

# TODO: 可扩展更多字典类型的获取方法 