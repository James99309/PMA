# -*- coding: utf-8 -*-
"""互动课程上传者权限测试。"""
from types import SimpleNamespace
from unittest.mock import patch

from app.models.course import InteractiveCourse


def test_course_dict_exposes_owner_id_for_template_permissions():
    from app import create_app

    app = create_app()
    with app.app_context():
        course = InteractiveCourse(key='owner-test', title='Owner Test', owner_id=42)

        assert course.to_dict()['owner_id'] == 42


def test_only_admin_uploader_can_manage_course():
    from app.views.knowledge_wiki import _can_manage_course

    course = SimpleNamespace(owner_id=42)

    with patch('app.views.knowledge_wiki.current_user', SimpleNamespace(id=42, role='admin')):
        assert _can_manage_course(course) is True
    with patch('app.views.knowledge_wiki.current_user', SimpleNamespace(id=7, role='admin')):
        assert _can_manage_course(course) is False
    with patch('app.views.knowledge_wiki.current_user', SimpleNamespace(id=42, role='sales')):
        assert _can_manage_course(course) is False
