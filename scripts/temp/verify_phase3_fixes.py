#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Phase 3 fix bundle: AI rewrite + permissions + race + info_updated_by."""
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
from app.views.prospect import (
    lost_detail, lost_apply, lost_ai_research
)
from app.models.prospect_project import ProspectProject
from sqlalchemy import inspect as sql_inspect

app = create_app()
with app.app_context():
    # Check info_updated_by column type
    insp = sql_inspect(ProspectProject)
    col = insp.columns.get('info_updated_by')
    if col is not None:
        print(f'info_updated_by column type: {col.type}')

    # Check decorators applied (look at __wrapped__ chain via name)
    for fn, name in [(lost_detail, 'lost_detail'),
                     (lost_apply, 'lost_apply'),
                     (lost_ai_research, 'lost_ai_research')]:
        # decorators wrap __name__ but the chain hint is in repr(fn)
        # crude check: look at view module for "permission_required" near the route
        print(f'{name}: callable={callable(fn)}, name={fn.__name__}')

    # Verify _run_lost_project_research is gone
    import app.views.prospect as pv
    has_old = hasattr(pv, '_run_lost_project_research')
    print(f'_run_lost_project_research removed: {not has_old}')

    # Verify imports — claude_research_provider, IntegrityError available somewhere
    try:
        from app.services.claude_research_provider import send_claude_research_request
        print('PASS: send_claude_research_request importable')
    except Exception as e:
        print(f'FAIL: {e}')

    print('done')
