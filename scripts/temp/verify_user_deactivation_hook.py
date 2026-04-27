#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify recompute_projects_for_user helper updates DB correctly."""
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

from app import create_app, db
from app.models.project import Project
from app.utils.activity_tracker import recompute_projects_for_user, FROZEN_STAGES

app = create_app()
with app.app_context():
    p = Project.query.filter(
        Project.is_deleted == False,
        Project.owner_id.isnot(None),
        ~Project.current_stage.in_(FROZEN_STAGES),
    ).first()
    if not p or not p.owner:
        print('SKIP: no candidate project'); sys.exit(0)

    user = p.owner
    original_active = user.is_active
    original_status = p.activity_status
    original_reason = p.activity_reason

    try:
        user.is_active = False
        db.session.flush()
        n = recompute_projects_for_user(user.id)
        # Re-fetch from DB to confirm it was committed
        db.session.expire(p)
        db.session.refresh(p)
        assert p.activity_status == 'churned', f"got {p.activity_status}"
        assert '离职' in (p.activity_reason or ''), f"reason was {p.activity_reason!r}"
        print(f'PASS: hook flipped {n} project(s); sample reason: {p.activity_reason}')
    finally:
        # Restore original state since recompute_projects_for_user commits
        user.is_active = original_active
        p.activity_status = original_status
        p.activity_reason = original_reason
        db.session.commit()
        print('OK: state restored')
