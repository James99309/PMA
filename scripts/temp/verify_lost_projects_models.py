#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Phase 1 data model changes."""
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
from app.models.prospect_project import ProspectProject
from app.models.prospect_claim_request import ProspectClaimRequest

app = create_app()
with app.app_context():
    cols = [c.name for c in ProspectProject.__table__.columns]
    assert 'link_type' in cols, 'link_type column missing'

    n = ProspectClaimRequest.query.count()
    print(f'OK: prospect_claim_requests row count = {n}')

    uniques = [
        c.name for c in ProspectClaimRequest.__table__.constraints
        if c.__class__.__name__ == 'UniqueConstraint'
    ]
    assert 'uq_claim_project_applicant' in uniques, 'unique constraint missing'

    print('All model checks passed.')
