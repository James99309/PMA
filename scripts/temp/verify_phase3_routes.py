#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test Phase 3 routes — list tab + apply API. Skips AI research (network)."""
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
from app.models.user import User
from app.models.prospect_claim_request import ProspectClaimRequest
from app.models.message import Message

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
with app.app_context():
    # 1. Pick a churned project (or skip)
    project = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
    ).first()
    if not project:
        print('SKIP: no churned project in DB')
        sys.exit(0)

    print(f'using churned project id={project.id} name={project.project_name!r} '
          f'owner_id={project.owner_id} stage={project.current_stage}')

    # 2. Pick a non-owner active user as applicant
    applicant = User.query.filter(
        User.id != project.owner_id,
        User._is_active == True,
    ).first()
    if not applicant:
        print('SKIP: no candidate applicant user')
        sys.exit(0)

    print(f'applicant id={applicant.id} username={applicant.username!r}')

    import time
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(applicant.id)
        sess['_fresh'] = True
        sess['role'] = applicant.role
        sess['login_time'] = time.time()

    # 3. GET /prospect/?tab=lost — should render tw_list.html with safe defaults
    rv = client.get('/prospect/?tab=lost')
    print(f'tab=lost: status={rv.status_code}')
    assert rv.status_code == 200, f"expected 200, got {rv.status_code}; body[:300]={rv.data[:300]!r}"
    print('PASS: list route returns 200')

    # 4. POST /prospect/lost/<id>/apply with empty reason → 400
    rv = client.post(f'/prospect/lost/{project.id}/apply', json={'reason': ''})
    body = rv.get_json()
    # If applicant already has perms, the perm check (400 with '已拥有') runs before reason check.
    if rv.status_code == 400 and body and '已拥有' in body.get('message', ''):
        print(f'NOTE: applicant has project permission ({body["message"]}); '
              'skipping apply tests')
        sys.exit(0)
    assert rv.status_code == 400, f"expected 400, got {rv.status_code}: {body}"
    assert '10' in body.get('message', ''), f"expected length error, got {body}"
    print(f'PASS: empty reason rejected ({body["message"]})')

    # 5. POST with valid reason → 200
    rv = client.post(f'/prospect/lost/{project.id}/apply',
                     json={'reason': '我有相关行业经验，希望能跟进'})
    body = rv.get_json()
    print(f'apply valid: status={rv.status_code}, body={body}')

    if rv.status_code == 200:
        cr = ProspectClaimRequest.query.filter_by(
            project_id=project.id, applicant_id=applicant.id
        ).first()
        assert cr, 'ClaimRequest not created'
        msgs = Message.query.filter_by(
            message_type='prospect_claim_request',
            related_object_id=project.id,
        ).all()
        assert msgs, 'Message not created'
        print(f'PASS: claim + {len(msgs)} message(s) created')

        # 6. Duplicate apply → 409
        rv2 = client.post(f'/prospect/lost/{project.id}/apply',
                          json={'reason': '再次申请测试 dedup'})
        assert rv2.status_code == 409, f"expected 409 on dup, got {rv2.status_code}"
        print('PASS: duplicate apply rejected with 409')

        # Cleanup
        for m in msgs:
            db.session.delete(m)
        db.session.delete(cr)
        db.session.commit()
        print('OK: cleaned up')
    elif rv.status_code == 400 and '已拥有' in (body or {}).get('message', ''):
        print('NOTE: applicant has project permission; skipping apply test')
    else:
        print(f'UNEXPECTED: {rv.status_code} {body}')
        sys.exit(1)
