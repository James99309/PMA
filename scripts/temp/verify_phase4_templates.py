#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Phase 4 templates render without exceptions."""
import sys
import os
import time


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
from app.models.project import Project
from app.models.user import User

app = create_app()
with app.app_context():
    project = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
    ).first()
    user = User.query.filter(
        User._is_active == True,
        User.role == 'admin',
    ).first()
    if not user:
        user = User.query.filter(User._is_active == True).first()
    if not user:
        print('SKIP: missing test user')
        sys.exit(0)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
        sess['role'] = user.role
        sess['login_time'] = time.time()

    # 1. Lost list tab renders
    rv = client.get('/prospect/?tab=lost')
    assert rv.status_code == 200, f"list?tab=lost: {rv.status_code}\n{rv.data[:500]}"
    body = rv.data.decode('utf-8', 'ignore')
    assert ('流失' in body) or ('Lost' in body), \
        "expected '流失' or 'Lost' marker in tab page"
    print('PASS: tab=lost renders (200)')

    # 2. Intel tab still works
    rv = client.get('/prospect/?tab=intel')
    assert rv.status_code == 200, f"intel: {rv.status_code}"
    print('PASS: tab=intel still renders (200)')

    # 3. Default tab (no param) still works
    rv = client.get('/prospect/')
    assert rv.status_code == 200, f"default: {rv.status_code}"
    print('PASS: default tab still renders (200)')

    # 4. Lost detail page (might redirect / 403 / 200, all valid)
    if project:
        rv = client.get(f'/prospect/lost/{project.id}')
        assert rv.status_code in (200, 302, 403), \
            f"lost detail: {rv.status_code}\n{rv.data[:500]}"
        if rv.status_code == 200:
            print('PASS: lost detail renders (200)')
        elif rv.status_code == 302:
            print(f'NOTE: lost detail redirected (likely permission/state gate)')
        else:
            print(f'NOTE: lost detail returned {rv.status_code} (permission gate)')
    else:
        print('SKIP: no churned project to test detail')

    print('done')
