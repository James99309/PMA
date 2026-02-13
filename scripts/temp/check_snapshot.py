#!/usr/bin/env python3
"""检查产品快照 vs 实际规格"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec

app = create_app()
with app.app_context():
    p = Product.query.filter(Product.product_mn == 'HYR2DI010').first()
    if not p:
        print('Product not found')
        exit()
    print('Product ID: {}, Name: {}, MN: {}'.format(p.id, p.product_name, p.product_mn))
    print('Subcategory ID: {}'.format(p.subcategory_id))

    # Check snapshot
    snapshot = p.code_definition_snapshot
    if snapshot:
        snap = json.loads(snapshot) if isinstance(snapshot, str) else snapshot
        print('\n=== Snapshot fields ({}) ==='.format(len(snap)))
        for item in snap:
            fn = item.get('field_name', '')
            fv = item.get('field_value', '')
            fc = item.get('code', '')
            print('  {}: value={}, code={}'.format(fn, repr(fv), repr(fc)))

    # Check actual specs
    specs = ProductSpec.query.filter_by(product_id=p.id).order_by(ProductSpec.display_order).all()
    print('\n=== Actual specs ({}) ==='.format(len(specs)))
    for s in specs:
        print('  {}: value={}, code={}'.format(s.field_name, repr(s.field_value), repr(s.field_code)))

    # Compare
    snap_fields = set(item.get('field_name') for item in snap) if snapshot else set()
    spec_fields = set(s.field_name for s in specs)

    in_snap_not_spec = snap_fields - spec_fields
    in_spec_not_snap = spec_fields - snap_fields

    if in_snap_not_spec:
        print('\n!!! In snapshot but NOT in actual specs:')
        for f in in_snap_not_spec:
            print('  - {}'.format(f))
    if in_spec_not_snap:
        print('\n!!! In actual specs but NOT in snapshot:')
        for f in in_spec_not_snap:
            print('  - {}'.format(f))

    # Check empty values in snapshot
    print('\n=== Snapshot fields with empty values ===')
    for item in (snap if snapshot else []):
        fv = item.get('field_value', '')
        if not fv or fv.strip() == '':
            print('  EMPTY: {}'.format(item.get('field_name')))
