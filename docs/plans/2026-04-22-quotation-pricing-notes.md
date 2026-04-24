# Quotation & Pricing Order Notes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add per-row item notes to quotation and pricing order detail lines, plus fix overall notes persistence on both models.

**Architecture:** 4 new DB columns (Quotation.notes, QuotationDetail.item_note, PricingOrder.notes, PricingOrderDetail.item_note). Quotation already sends `notes` to backend but the field doesn't exist in the model — fix that first. Per-row notes use a custom sub-row UI injected below each `<tr>` in the editable tables; the note UI is independent of `tw_editable_table` to avoid touching the protected component.

**Tech Stack:** Flask/SQLAlchemy models, Alembic migration, Jinja2 templates, vanilla JS

---

## Task 1: Add DB columns + migration

**Files:**
- Modify: `app/models/quotation.py` — Quotation class (line ~111) and QuotationDetail class (line ~469)
- Modify: `app/models/pricing_order.py` — PricingOrder class (line ~79) and PricingOrderDetail class (line ~396)
- Create: `migrations/versions/notes_fields_20260422.py`

**Step 1: Add `notes` to Quotation model**

In `app/models/quotation.py`, after `currency = db.Column(...)` (around line 111), add:

```python
notes = db.Column(db.Text, nullable=True, comment='报价单备注')
```

**Step 2: Add `item_note` to QuotationDetail model**

In `app/models/quotation.py`, after `currency = db.Column(...)` in the QuotationDetail class (around line 469), add:

```python
item_note = db.Column(db.Text, nullable=True, comment='明细行备注')
```

**Step 3: Add `notes` to PricingOrder model**

In `app/models/pricing_order.py`, after `currency = Column(...)` (around line 79), add:

```python
notes = Column(Text, nullable=True, comment='批价单备注')
```

**Step 4: Add `item_note` to PricingOrderDetail model**

In `app/models/pricing_order.py`, after `product_mn = Column(...)` in PricingOrderDetail class (around line 393), add:

```python
item_note = Column(Text, nullable=True, comment='明细行备注')
```

**Step 5: Create migration**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add notes fields to quotation and pricing order"
```

Review the generated file in `migrations/versions/` to confirm it adds 4 columns:
- `quotations.notes`
- `quotation_details.item_note`
- `pricing_orders.notes`
- `pricing_order_details.item_note`

**Step 6: Apply migration**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

**Step 7: Commit**

```bash
git add app/models/quotation.py app/models/pricing_order.py migrations/versions/
git commit -m "feat(notes): add notes and item_note columns to quotation and pricing order models"
```

---

## Task 2: Fix quotation overall notes saving (backend)

**Files:**
- Modify: `app/views/quotation.py` — `save_quotation()` at line ~3728

**Step 1: Save `notes` in `save_quotation()`**

In `save_quotation()`, after the line `quotation.currency = data.get('currency', ...)` (line ~3730), add:

```python
quotation.notes = data.get('notes', '') or ''
```

**Step 2: Include `notes` in `quotation_details_json` context**

In the `details_for_edit` loop (around line 3416), the quotation object itself is already passed to the template. Verify that `_quotation_modal_fields.html` (line ~159) reads `quotation.notes` correctly:

```html
{{ quotation.notes if quotation else '' }}
```

This already exists — now the field exists in the model, so it will work.

**Step 3: Commit**

```bash
git add app/views/quotation.py
git commit -m "fix(notes): save quotation.notes to database in save_quotation"
```

---

## Task 3: Fix quotation item_note saving (backend)

**Files:**
- Modify: `app/views/quotation.py` — `process_quotation_details()` at line ~1051 and `details_for_edit` at line ~3416

**Step 1: Save `item_note` in `process_quotation_details()`**

In `process_quotation_details()`, find the `QuotationDetail(...)` constructor call (line ~1051). Add `item_note`:

```python
new_detail = QuotationDetail(
    quotation_id=quotation_id,
    product_name=product_name,
    ...
    pending_product_creation=pending_product_creation,
    item_note=detail.get('item_note', '') or ''  # ADD THIS LINE
)
```

**Step 2: Include `item_note` in `details_for_edit` JSON**

In the `details_for_edit` loop (line ~3416), add to `detail_data` dict:

```python
'item_note': str(getattr(detail, 'item_note', '') or ''),
```

**Step 3: Commit**

```bash
git add app/views/quotation.py
git commit -m "feat(notes): save and load item_note for quotation detail lines"
```

---

## Task 4: Copy notes when creating pricing order from quotation (backend)

**Files:**
- Modify: `app/services/pricing_order_service.py`
  - `copy_quotation_details_to_pricing()` at line 639
  - Find where `PricingOrder` is created from a quotation and add `notes` copy

**Step 1: Copy `item_note` in `copy_quotation_details_to_pricing()`**

In the `PricingOrderDetail(...)` constructor call (line ~655), add:

```python
pricing_detail = PricingOrderDetail(
    pricing_order_id=pricing_order.id,
    ...
    currency=qd.currency or quotation.currency,
    item_note=qd.item_note or ''  # ADD THIS LINE
)
```

**Step 2: Copy quotation `notes` to pricing order `notes`**

After the `copy_quotation_details_to_pricing()` function call in `pricing_order_service.py` (around line 518, inside the creation flow), add:

```python
pricing_order.notes = quotation.notes or ''
```

Find the exact location: search for `PricingOrderService.copy_quotation_details_to_pricing(quotation, pricing_order)` (line ~518) and add the notes copy on the next line.

**Step 3: Commit**

```bash
git add app/services/pricing_order_service.py
git commit -m "feat(notes): copy notes and item_note from quotation to pricing order on creation"
```

---

## Task 5: Save item_note and notes updates for pricing order (backend)

**Files:**
- Modify: `app/routes/pricing_order_routes.py` — `update_pricing_detail()` at line 450
- Modify: `app/services/pricing_order_service.py` — `update_pricing_detail()` at line 701
- Add endpoint: `app/routes/pricing_order_routes.py` — new `update_pricing_notes()` route

**Step 1: Add `item_note` to `update_pricing_detail()` route**

In `update_pricing_detail()` route (line ~466), extract `item_note`:

```python
data = request.get_json()
detail_id = data.get('detail_id')
quantity = data.get('quantity')
discount_rate = data.get('discount_rate')
unit_price = data.get('unit_price')
item_note = data.get('item_note')  # ADD THIS
```

Pass it to the service:

```python
success, error = PricingOrderService.update_pricing_detail(
    order_id, detail_id, quantity=quantity, discount_rate=discount_rate,
    unit_price=unit_price, item_note=item_note  # ADD item_note
)
```

**Step 2: Add `item_note` to `PricingOrderService.update_pricing_detail()`**

In `app/services/pricing_order_service.py`, `update_pricing_detail()` (line ~701):

```python
def update_pricing_detail(pricing_order_id, detail_id, quantity=None, discount_rate=None, unit_price=None, item_note=None):
```

Inside the function, after existing field updates, add:

```python
if item_note is not None:
    pricing_detail.item_note = item_note
```

**Step 3: Add `update_pricing_notes` route**

After the existing `update_pricing_detail` route in `pricing_order_routes.py`, add:

```python
@pricing_order_bp.route('/<int:order_id>/update_notes', methods=['POST'])
@login_required
def update_pricing_notes(order_id):
    """更新批价单整体备注"""
    pricing_order = PricingOrder.query.get_or_404(order_id)
    (can_edit_pricing, *_) = check_pricing_edit_permission(pricing_order, current_user)
    if not can_edit_pricing:
        return jsonify({'success': False, 'message': '没有权限编辑批价单'})
    data = request.get_json()
    pricing_order.notes = data.get('notes', '') or ''
    db.session.commit()
    return jsonify({'success': True})
```

**Step 4: Return `item_note` in existing API responses**

In `update_pricing_detail()` route response, make sure the returned pricing detail data includes `item_note`. In the `updated_detail` serialization (around line 486+), add:
```python
'item_note': updated_detail.item_note or '',
```

Also, find where pricing order details are serialized to JSON for the modal load and include `item_note`.

**Step 5: Commit**

```bash
git add app/routes/pricing_order_routes.py app/services/pricing_order_service.py
git commit -m "feat(notes): add item_note and notes save endpoints for pricing order"
```

---

## Task 6: Quotation view — item note UI on read-only rows (frontend)

**Files:**
- Modify: `app/templates/quotation/tw_quotation_detail.html` — read-only detail rows (around line 310)

**Context:** The read-only product table (view mode) renders rows at line 236-342 using a Jinja2 loop over `quotation.details`. Each main `<tr>` is followed by config sub-rows. We need to add a note sub-row after each main row when `detail.item_note` has content.

**Step 1: Add note sub-row after each main product row**

Find the main product row rendering (around line 308-314):
```html
<tr class="..." data-detail-id="{{ detail.id }}">
    <td ...>{{ loop.index }}</td>
    <td ...>{{ detail.product_name or '-' }}</td>
    ...
</tr>
```

After this `</tr>` (and before any config sub-rows loop), add:

```html
{% if detail.item_note %}
<tr class="bg-slate-50 dark:bg-slate-800/50" data-note-row-for="{{ detail.id }}">
    <td></td>
    <td colspan="{{ product_columns|length }}" class="px-3 pb-2 pt-0">
        <p class="text-xs text-slate-500 dark:text-slate-400 whitespace-pre-wrap leading-relaxed">{{ detail.item_note }}</p>
    </td>
</tr>
{% endif %}
```

**Step 2: Verify it renders correctly**

Start the app and open a quotation that has item notes (add some via the edit modal after Task 7 is done). Confirm the note row appears below the product row, not inside any column.

**Step 3: Commit**

```bash
git add app/templates/quotation/tw_quotation_detail.html
git commit -m "feat(notes): show item_note sub-row in quotation read-only view"
```

---

## Task 7: Quotation edit modal — item note UI in editable table (frontend)

**Files:**
- Modify: `app/templates/quotation/tw_quotation_detail.html`
  - `productData` mapping (line ~999) — add `item_note` field
  - `collectFormData()` (line ~1160) — merge notes into details
  - After `EditableTable.setData()` call (line ~1025) — inject note rows

**Strategy:** Keep a module-level `notesByItemId = {}` object. After `EditableTable.setData()` renders rows, inject a custom `<tr class="note-sub-row">` after each main data row. When the note textarea changes, update `notesByItemId`. When `collectFormData()` builds `details`, merge `item_note` from `notesByItemId` by matching `item_id`.

**Step 1: Add `item_note` to `productData` mapping (line ~999)**

```javascript
const productData = existingDetails.map(function(detail) {
    return {
        item_id: detail.item_id || detail.id,
        ...
        quantity_synced: detail.quantity_synced,
        item_note: detail.item_note || ''  // ADD THIS
    };
});
```

**Step 2: Add note row injection function**

In the quotation JS section, add a module-level variable and helper function (place near the top of the edit modal JS, before `collectFormData`):

```javascript
// Tracks item notes by item_id (populated on modal open, updated on user edit)
var _quotationNotesByItemId = {};

function _injectQuotationNoteRows(tableData) {
    const tbody = document.getElementById('quotationProductTableBody');
    if (!tbody) return;

    // Remove existing note rows first
    tbody.querySelectorAll('tr.quotation-note-row').forEach(r => r.remove());

    // Build a map: item_id -> item_note from tableData
    tableData.forEach(function(d) {
        if (d.item_note) {
            _quotationNotesByItemId[d.item_id] = d.item_note;
        }
    });

    // For each main row in the tbody, insert a note row after it
    const mainRows = tbody.querySelectorAll('tr[data-row-id]');
    mainRows.forEach(function(mainRow) {
        const rowId = mainRow.getAttribute('data-row-id');
        // Find item_id for this row_id from EditableTable
        const instance = window.EditableTable && window.EditableTable.instances && window.EditableTable.instances['quotationProductTable'];
        if (!instance) return;
        const rowObj = instance.rows.find(r => String(r.id) === String(rowId));
        if (!rowObj) return;
        const itemId = rowObj.data.item_id;
        const note = _quotationNotesByItemId[itemId] || '';

        // Only inject if has note OR use a collapse approach
        const colCount = mainRow.querySelectorAll('td').length;
        const noteRow = document.createElement('tr');
        noteRow.className = 'quotation-note-row';
        noteRow.setAttribute('data-note-for-item-id', itemId || '');
        noteRow.setAttribute('data-note-for-row-id', rowId);
        if (!note) noteRow.style.display = 'none';

        noteRow.innerHTML = `
            <td></td>
            <td colspan="${colCount - 1}" class="px-3 pb-2 pt-0">
                <textarea
                    class="w-full text-xs text-slate-500 dark:text-slate-400 bg-transparent border-0 border-b border-slate-200 dark:border-slate-700 resize-none focus:outline-none focus:border-slate-400 placeholder-slate-300"
                    rows="1"
                    placeholder="{{ _('输入此行备注...') }}"
                    data-note-item-id="${itemId || ''}"
                >${_escapeHtml(note)}</textarea>
            </td>
        `;

        // Auto-resize textarea
        const textarea = noteRow.querySelector('textarea');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
            _quotationNotesByItemId[itemId] = this.value;
        });

        mainRow.insertAdjacentElement('afterend', noteRow);
    });
}

function _escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str || ''));
    return d.innerHTML;
}

function _toggleQuotationNoteRow(itemId, show) {
    const noteRow = document.querySelector(`tr.quotation-note-row[data-note-for-item-id="${itemId}"]`);
    if (!noteRow) return;
    noteRow.style.display = show ? '' : 'none';
    if (show) {
        const ta = noteRow.querySelector('textarea');
        if (ta) { ta.focus(); ta.style.height = 'auto'; ta.style.height = ta.scrollHeight + 'px'; }
    }
}
```

**Step 3: Call `_injectQuotationNoteRows` after `EditableTable.setData()`**

After line ~1025 `window.EditableTable.setData('quotationProductTable', productData)`:

```javascript
window.EditableTable.setData('quotationProductTable', productData);
_injectQuotationNoteRows(productData);  // ADD THIS
```

Also call it after `window.EditableTable.addRow('quotationProductTable')` (line ~1033) with empty data.

**Step 4: Add chevron toggle to product name cell**

The product name cell is rendered by `tw_editable_table`. We need to inject a chevron below the product name in each row. Add this inside `_injectQuotationNoteRows`, after the note row is inserted:

```javascript
// Inject chevron below product name in the main row
const productNameCell = mainRow.querySelector('td[data-col-key="product_name"], td:nth-child(2)');
if (productNameCell && !productNameCell.querySelector('.note-toggle-chevron')) {
    const chevron = document.createElement('div');
    chevron.className = 'note-toggle-chevron text-xs text-slate-400 cursor-pointer hover:text-slate-600 mt-0.5 select-none';
    chevron.style.lineHeight = '1';
    const hasNote = !!note;
    chevron.innerHTML = hasNote
        ? `<span class="flex items-center gap-1">▾ <span class="truncate max-w-32">${_escapeHtml(note.substring(0, 30))}${note.length > 30 ? '...' : ''}</span></span>`
        : '';
    chevron.setAttribute('data-toggle-item-id', itemId || '');
    chevron.addEventListener('click', function(e) {
        e.stopPropagation();
        const id = this.getAttribute('data-toggle-item-id');
        const noteRowEl = document.querySelector(`tr.quotation-note-row[data-note-for-item-id="${id}"]`);
        const isHidden = !noteRowEl || noteRowEl.style.display === 'none';
        _toggleQuotationNoteRow(id, isHidden);
        // Update chevron text after toggle
        if (isHidden) {
            this.innerHTML = `<span class="flex items-center gap-1">▴ <span class="text-slate-500">{{ _('编辑备注') }}</span></span>`;
        } else {
            const currentNote = _quotationNotesByItemId[id] || '';
            this.innerHTML = currentNote
                ? `<span class="flex items-center gap-1">▾ <span class="truncate max-w-32">${_escapeHtml(currentNote.substring(0, 30))}${currentNote.length > 30 ? '...' : ''}</span></span>`
                : '';
        }
    });
    productNameCell.appendChild(chevron);
}
```

**Step 5: Update chevron preview when note changes**

In the textarea `input` event listener (from Step 2), also update the chevron preview:

```javascript
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
    _quotationNotesByItemId[itemId] = this.value;
    // Update chevron preview
    const chevron = document.querySelector(`.note-toggle-chevron[data-toggle-item-id="${itemId}"]`);
    if (chevron) {
        const val = this.value;
        chevron.innerHTML = val
            ? `<span class="flex items-center gap-1">▴ <span class="truncate max-w-32">${_escapeHtml(val.substring(0, 30))}${val.length > 30 ? '...' : ''}</span></span>`
            : `<span class="flex items-center gap-1">▾ <span class="text-slate-400">{{ _('添加备注') }}</span></span>`;
    }
});
```

**Step 6: Merge `item_note` into `collectFormData()` details**

In `collectFormData()` (line ~1168), after `details = window.EditableTable.getData('quotationProductTable')`, add:

```javascript
// Merge item_note values into each detail
details.forEach(function(d) {
    const itemId = d.item_id;
    d.item_note = _quotationNotesByItemId[itemId] || '';
});
```

**Step 7: Reset notes on modal close**

Find where the quotation edit modal is closed/reset and add:

```javascript
_quotationNotesByItemId = {};
```

**Step 8: Commit**

```bash
git add app/templates/quotation/tw_quotation_detail.html
git commit -m "feat(notes): add item_note chevron expand UI to quotation edit modal table"
```

---

## Task 8: Pricing order modal — item note UI + overall notes (frontend)

**Files:**
- Modify: `app/templates/components/tw_pricing_order_modal.html`
  - `renderPricingDetails()` at line ~1625 — add `item_note` to tableData + inject note rows
  - `onDetailChange()` at line ~1665 — handle `item_note` changes
  - Save flow (line ~1503) — include `item_note` in `update_pricing_detail` call
  - Add overall notes save call

**Step 1: Add `item_note` to `tableData` in `renderPricingDetails()`**

```javascript
return {
    id: d.id,
    item_id: d.id,
    product_name: d.product_name || '-',
    ...
    product_mn: d.product_mn || '-',
    item_note: d.item_note || ''  // ADD THIS
};
```

**Step 2: Add note row injection after `EditableTable.setData`**

Use the same pattern as Task 7 but for the pricing order modal. Add a module-level `_pricingNotesByDetailId = {}` and `_injectPricingNoteRows(tableData)` function (same logic as quotation, but for `pricingDetailTableBody` and detail `id` instead of `item_id`).

After `window.EditableTable.setData('pricingDetailTable', tableData)` (line ~1655):

```javascript
window.EditableTable.setData('pricingDetailTable', tableData);
window.EditableTable.setReadonly('pricingDetailTable', !canEdit);
_injectPricingNoteRows(tableData);  // ADD THIS
```

**Step 3: Track `item_note` in `pendingChanges`**

The pricing order uses a `pendingChanges.details` object keyed by detail ID. When a note textarea changes, add to pending changes:

```javascript
// Inside _injectPricingNoteRows, textarea input listener:
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
    const detailId = this.getAttribute('data-note-detail-id');
    _pricingNotesByDetailId[detailId] = this.value;
    // Mark as dirty and add to pendingChanges
    state.isDirty = true;
    if (!state.pendingChanges.details[detailId]) {
        state.pendingChanges.details[detailId] = {};
    }
    state.pendingChanges.details[detailId].item_note = this.value;
});
```

**Step 4: Include `item_note` in `update_pricing_detail` API call**

In the save flow (line ~1506), the body already sends `discount_rate`, `unit_price`, `quantity`. Add `item_note`:

```javascript
body: JSON.stringify({
    detail_id: parseInt(detailId),
    discount_rate: changes.discount_rate,
    unit_price: changes.unit_price,
    quantity: changes.quantity,
    item_note: changes.item_note  // ADD THIS (may be undefined if not changed, backend ignores)
})
```

**Step 5: Save overall pricing order notes**

The modal already has `#soNotes` textarea (line ~662). In the save flow (after all detail saves), add a call to the new `update_notes` endpoint:

```javascript
// After detail saves (after line ~1531):
const notesValue = document.getElementById('soNotes')?.value?.trim() || '';
const notesResponse = await fetch(`/pricing_order/${state.pricingOrderId}/update_notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ notes: notesValue })
});
```

**Step 6: Load existing notes when modal opens**

Find where pricing order data is loaded into the modal (look for where `soNotes` is populated). If not already set, add:

```javascript
document.getElementById('soNotes').value = po.notes || '';
```

Also ensure the API that returns pricing order data includes `notes` and each detail's `item_note`.

**Step 7: Commit**

```bash
git add app/templates/components/tw_pricing_order_modal.html
git commit -m "feat(notes): add item_note and overall notes UI to pricing order modal"
```

---

## Task 9: Ensure pricing order API returns item_note and notes

**Files:**
- Modify: `app/routes/pricing_order_routes.py` — wherever pricing order detail data is serialized to JSON

**Step 1: Find pricing detail serialization**

Search for where `pricing_details` are returned as JSON (the load endpoint used by the modal):

```bash
grep -n "pricing_details\|item_note\|to_dict" app/routes/pricing_order_routes.py | head -30
```

**Step 2: Add `item_note` and `notes` to responses**

In the serialization for pricing order details, add:

```python
'item_note': detail.item_note or '',
```

For the main pricing order object, add:

```python
'notes': pricing_order.notes or '',
```

**Step 3: Commit**

```bash
git add app/routes/pricing_order_routes.py
git commit -m "feat(notes): include item_note and notes in pricing order API responses"
```

---

## Testing Checklist

After all tasks:

1. **Quotation overall notes**: Open a quotation → Edit → type in Notes field → Save → reopen → notes should persist
2. **Quotation item notes**: Edit → click chevron below a product name → type note → Save → reopen → note sub-row appears expanded with content
3. **Pricing order creation**: Create pricing order from a quotation that has item notes → pricing order details should have same notes
4. **Pricing order overall notes**: Edit pricing order → type in soNotes → Save → reopen → notes should persist
5. **Pricing order item notes**: Edit → expand note row → type → Save → reopen → note appears expanded
6. **No notes**: Items without notes show no chevron and no extra row height in view mode
