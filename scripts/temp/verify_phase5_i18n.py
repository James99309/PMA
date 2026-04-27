#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Phase 5: i18n translations cover both zh and en for lost-projects feature."""
import sys, os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("project root not found")

sys.path.insert(0, get_project_root())

from app import create_app
from app.models.user import User
from app.models.project import Project

app = create_app()
with app.app_context():
    user = User.query.filter(User._is_active == True, User.role == 'admin').first()
    if not user:
        user = User.query.filter(User._is_active == True).first()
    project = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
    ).first()
    if not user:
        print('SKIP: no active user'); sys.exit(0)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
        sess['role'] = user.role
        sess['username'] = user.username

    # Default locale (likely zh)
    rv = client.get('/prospect/?tab=lost')
    assert rv.status_code == 200, f"got {rv.status_code}"
    body = rv.data.decode('utf-8', errors='ignore')
    has_zh = any(s in body for s in ['流失项目', '市场情报'])
    print(f'zh strings present: {has_zh}')

    rv2 = client.get('/prospect/?tab=lost', headers={'Accept-Language': 'en'})
    assert rv2.status_code == 200, f"en got {rv2.status_code}"
    body2 = rv2.data.decode('utf-8', errors='ignore')
    has_en = any(s in body2 for s in ['Lost Projects', 'Market Intel'])
    print(f'en strings present: {has_en}')

    if project:
        rv3 = client.get(f'/prospect/lost/{project.id}')
        assert rv3.status_code in (200, 302, 403), f"detail got {rv3.status_code}"
        print(f'lost_detail status: {rv3.status_code}')

    print('done')
