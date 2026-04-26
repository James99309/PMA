#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Phase 2 activity rule: inactive owner / no owner → churned."""
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
from app.utils.activity_tracker import calculate_project_activity_status, FROZEN_STAGES

app = create_app()
with app.app_context():
    p = Project.query.filter(
        Project.is_deleted == False,
        Project.owner_id.isnot(None),
        ~Project.current_stage.in_(FROZEN_STAGES),
    ).first()

    if not p:
        print('SKIP: no candidate non-frozen project with owner found')
        sys.exit(0)

    original_owner = p.owner
    if original_owner is None:
        print('SKIP: project has owner_id but owner relationship returned None')
        sys.exit(0)

    original_active = original_owner.is_active
    original_owner_id = p.owner_id

    try:
        # Case 1: owner inactive
        original_owner.is_active = False
        db.session.flush()
        status, reason, _ = calculate_project_activity_status(p.id)
        assert status == 'churned', f"expected churned, got {status}"
        assert reason == '负责人已离职', f"unexpected reason: {reason!r}"
        print(f'PASS: inactive owner → churned ({reason})')

        # Case 2: no owner
        original_owner.is_active = original_active
        p.owner_id = None
        db.session.flush()
        status, reason, _ = calculate_project_activity_status(p.id)
        assert status == 'churned' and reason == '无负责人', \
            f"expected churned/无负责人, got {status}/{reason!r}"
        print(f'PASS: no owner → churned ({reason})')

    finally:
        # Roll back so DB stays clean
        db.session.rollback()
        print('OK: all changes reverted via rollback')
