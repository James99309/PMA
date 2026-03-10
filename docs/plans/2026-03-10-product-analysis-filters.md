# 产品分析明细数据筛选增强 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 增强植入产品分析的明细数据标签页，增加级联产品筛选、阶段筛选、负责人筛选、年份全选，以及订单量和关联客户列。

**Architecture:** 后端新增 1 个筛选选项 API + 增强现有 detail API（增加 stage/owner/subcategory/product_mn 参数，year=0 全量，批量查询订单量和关联客户）。前端用 Alpine.js 实现三级级联菜单组件 + 下拉筛选框。

**Tech Stack:** Flask/SQLAlchemy (backend), Alpine.js + Tailwind (frontend), PostgreSQL

---

## Task 1: 后端 — 筛选选项 API

**Files:**
- Modify: `app/views/product_analysis.py` — 新增 `/api/v2/filter_options` 端点

**Step 1: 添加筛选选项 API**

在 `product_analysis.py` 末尾（`api_v2_detail` 之后）添加新路由：

```python
@product_analysis.route('/api/v2/filter_options')
@login_required
@permission_required('quotation', 'view')
def api_v2_filter_options():
    """获取筛选选项数据（分类/子分类/产品型号级联 + 阶段 + 负责人）"""
    try:
        from app.models.product_code import ProductCategory, ProductSubcategory

        category_id = request.args.get('category_id', type=int)
        subcategory_id = request.args.get('subcategory_id', type=int)

        # 分类列表（始终返回）
        categories = ProductCategory.query.order_by(
            ProductCategory.display_order, ProductCategory.id
        ).all()
        cat_list = [{'id': c.id, 'name': c.name} for c in categories]

        # 子分类列表（当指定 category_id 时）
        sub_list = []
        if category_id:
            subs = ProductSubcategory.query.filter_by(
                category_id=category_id
            ).order_by(ProductSubcategory.display_order, ProductSubcategory.id).all()
            sub_list = [{'id': s.id, 'name': s.name} for s in subs]

        # 产品型号列表（当指定 subcategory_id 时）
        model_list = []
        if subcategory_id:
            products = Product.query.filter(
                Product.subcategory_id == subcategory_id,
                Product.is_deleted == False
            ).order_by(Product.product_name).all()
            model_list = [{'mn': p.product_mn, 'name': p.product_name, 'model': p.model}
                          for p in products if p.product_mn]

        # 阶段列表（静态）
        stages = [
            {'value': 'discover', 'label': '发现'},
            {'value': 'embed', 'label': '植入'},
            {'value': 'pre_tender', 'label': '预招标'},
            {'value': 'tendering', 'label': '招标中'},
            {'value': 'quoted', 'label': '已报价'},
            {'value': 'awarded', 'label': '中标'},
            {'value': 'signed', 'label': '签约'},
            {'value': 'lost', 'label': '丢失'},
            {'value': 'paused', 'label': '暂停'},
        ]

        # 负责人列表（从现有报价单数据中提取活跃用户）
        from app.services.product_attribution import get_analysis_view_scope
        scope = get_analysis_view_scope(current_user)
        q = _build_base_detail_query()
        q = _apply_scope_filter(q, scope)
        owner_ids = [r[0] for r in q.with_entities(
            func.distinct(Quotation.owner_id)
        ).all()]
        owners = User.query.filter(User.id.in_(owner_ids)).order_by(User.real_name).all() if owner_ids else []
        owner_list = [{'id': u.id, 'name': u.real_name or u.username} for u in owners]

        return jsonify({
            'success': True,
            'categories': cat_list,
            'subcategories': sub_list,
            'models': model_list,
            'stages': stages,
            'owners': owner_list
        })
    except Exception as e:
        logger.error(f"filter_options 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
```

**Step 2: Commit**

```
feat: add filter_options API for product analysis cascading filters
```

---

## Task 2: 后端 — 增强 detail API

**Files:**
- Modify: `app/views/product_analysis.py` — 修改 `api_v2_detail()` 函数

**需要改动的点：**

### 2a: year=0 表示全部年份

在 `api_v2_detail()` 中，将年份过滤改为条件过滤：

```python
year = int(request.args.get('year', datetime.now().year))
# ... existing code ...
# 替换固定年份过滤为条件过滤
if year > 0:
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)
    q = q.filter(QuotationDetail.created_at >= year_start, QuotationDetail.created_at < year_end)
```

### 2b: 新增筛选参数

添加 subcategory、stage、owner_id、product_mn 筛选：

```python
subcategory = request.args.get('subcategory_id', type=int)
stage = request.args.get('stage', '').strip()
owner_id = request.args.get('owner_id', type=int)
product_mn = request.args.get('product_mn', '').strip()

# subcategory 筛选 — 通过 Product 表关联
if subcategory:
    sub_models = db.session.query(Product.product_mn).filter(
        Product.subcategory_id == subcategory,
        Product.is_deleted == False
    ).distinct().subquery()
    q = q.filter(QuotationDetail.product_mn.in_(
        db.session.query(sub_models.c.product_mn)
    ))

# product_mn 精确匹配
if product_mn:
    q = q.filter(QuotationDetail.product_mn == product_mn)

# 阶段筛选
if stage:
    q = q.filter(Project.current_stage == stage)

# 负责人筛选
if owner_id:
    q = q.filter(Quotation.owner_id == owner_id)
```

### 2c: 批量查询订单量

在分页查询结果出来后，批量查 pricing_order_details：

```python
from app.models.pricing_order import PricingOrder, PricingOrderDetail

# 收集当页数据的 (project_id, product_mn) 对
project_ids = list({r.project_id for r in results})
product_mns = list({r.product_mn for r in results if r.product_mn})

# 一次性查询订单量：按 project_id + product_mn 聚合
order_qty_map = {}
if project_ids and product_mns:
    order_rows = db.session.query(
        PricingOrder.project_id,
        PricingOrderDetail.product_mn,
        func.sum(PricingOrderDetail.quantity).label('qty')
    ).join(
        PricingOrder, PricingOrderDetail.pricing_order_id == PricingOrder.id
    ).filter(
        PricingOrder.project_id.in_(project_ids),
        PricingOrderDetail.product_mn.in_(product_mns)
    ).group_by(
        PricingOrder.project_id, PricingOrderDetail.product_mn
    ).all()
    for row in order_rows:
        order_qty_map[(row.project_id, row.product_mn)] = int(row.qty or 0)
```

### 2d: 批量查询关联客户（分销商/代理商）

```python
from app.models.project_customer_association import ProjectCustomerAssociation
from app.models.customer import Company

# 一次性查询所有当页项目的分销商和代理商
customer_map = {}  # project_id -> 'distributor_name / dealer_name'
if project_ids:
    assoc_rows = db.session.query(
        ProjectCustomerAssociation.project_id,
        Company.company_name,
        Company.company_type
    ).join(
        Company, ProjectCustomerAssociation.company_id == Company.id
    ).filter(
        ProjectCustomerAssociation.project_id.in_(project_ids),
        Company.company_type.in_(['distributor', 'dealer']),
        Company.is_deleted == False
    ).all()

    # 按项目分组，先分销商后代理商
    from collections import defaultdict
    proj_customers = defaultdict(lambda: {'distributor': [], 'dealer': []})
    for row in assoc_rows:
        proj_customers[row.project_id][row.company_type].append(row.company_name)

    for pid, types in proj_customers.items():
        names = types['distributor'] + types['dealer']
        customer_map[pid] = ' / '.join(names)
```

### 2e: 在返回数据中添加新字段

```python
data.append({
    # ... 现有字段 ...
    'order_qty': order_qty_map.get((r.project_id, r.product_mn), 0),
    'customer': customer_map.get(r.project_id, ''),
})
```

### 2f: 同样修改 overview、distribution、ranking API 支持 year=0

在 `api_v2_overview()` 和其他 API 中，将年份过滤改为条件：

```python
year = int(request.args.get('year', datetime.now().year))
if year > 0:
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)
    q_year = q.filter(QuotationDetail.created_at >= year_start, QuotationDetail.created_at < year_end)
else:
    q_year = q  # 全部年份
```

**Step 2: Commit**

```
feat: enhance detail API with filters, order qty, customer, year=all
```

---

## Task 3: 前端 — 年份选择器加「全部」

**Files:**
- Modify: `app/templates/product_analysis/tw_analysis.html`

**Step 1: 在年份 select 中添加「全部」选项**

在 `<select id="yearSelect">` 中，在 `{% for y in range(...) %}` 之前加：

```html
<option value="0">{{ _('全部') }}</option>
```

**Step 2: 修改 changeYear() 和 fetchApi()**

`changeYear()` 已经用 `parseInt(y)` 所以 `0` 可以直接传。
`fetchApi()` 传 `year=0` 后端会跳过年份过滤。无需额外修改。

**Step 3: overview 显示调整**

当 year=0 时，「本月新增」卡片仍然显示当月数据（后端已处理），环比逻辑不变。

**Step 4: Commit**

```
feat: add "All" option to year selector in product analysis
```

---

## Task 4: 前端 — 级联产品筛选器组件

**Files:**
- Modify: `app/templates/product_analysis/tw_analysis.html` — 明细数据区域 + Alpine 状态

**Step 1: 添加 Alpine 筛选状态**

在 `productAnalysisDashboard()` 的 return 对象中添加：

```javascript
// 筛选相关状态
filterCategories: [],
filterSubcategories: [],
filterModels: [],
filterStages: [],
filterOwners: [],
// 当前选中
selectedCategoryId: 0,
selectedCategoryName: '',
selectedSubcategoryId: 0,
selectedSubcategoryName: '',
selectedProductMn: '',
selectedProductName: '',
selectedStage: '',
selectedOwnerId: 0,
// 级联菜单
cascadeOpen: false,
cascadeLevel: 1,  // 1=分类, 2=子分类, 3=型号
```

**Step 2: 添加级联菜单加载方法**

```javascript
async loadFilterOptions(categoryId, subcategoryId) {
    const params = new URLSearchParams();
    if (categoryId) params.set('category_id', categoryId);
    if (subcategoryId) params.set('subcategory_id', subcategoryId);
    const resp = await fetch('/product_analysis/api/v2/filter_options?' + params);
    const result = await resp.json();
    if (!result.success) return;
    this.filterCategories = result.categories || [];
    if (categoryId) this.filterSubcategories = result.subcategories || [];
    if (subcategoryId) this.filterModels = result.models || [];
    if (!this.filterStages.length) this.filterStages = result.stages || [];
    if (!this.filterOwners.length) this.filterOwners = result.owners || [];
},
```

**Step 3: 级联菜单 HTML**

在明细数据 tab 的筛选栏中，替换搜索框后加级联按钮：

```html
<!-- 产品级联筛选按钮 -->
<div class="relative" @click.outside="cascadeOpen = false">
    <button @click="cascadeOpen = !cascadeOpen; if(cascadeOpen && !filterCategories.length) loadFilterOptions()"
            class="h-10 px-3 rounded-lg border text-sm flex items-center gap-2"
            :class="selectedCategoryId ? 'border-primary bg-primary/5 text-primary' : 'border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300'">
        <span class="material-symbols-outlined text-base">inventory_2</span>
        <span x-text="selectedProductMn ? (selectedCategoryName+' / '+selectedSubcategoryName+' / '+selectedProductName) : selectedSubcategoryId ? (selectedCategoryName+' / '+selectedSubcategoryName) : selectedCategoryId ? selectedCategoryName : '选择产品'" class="max-w-[280px] truncate"></span>
        <svg x-show="selectedCategoryId" @click.stop="selectedCategoryId=0;selectedCategoryName='';selectedSubcategoryId=0;selectedSubcategoryName='';selectedProductMn='';selectedProductName='';cascadeOpen=false;loadDetail(1)" class="w-4 h-4 text-slate-400 hover:text-red-500 cursor-pointer"><use href="#icon-x"/></svg>
        <svg x-show="!selectedCategoryId" class="w-3 h-3"><use href="#icon-chevron"/></svg>
    </button>

    <!-- 级联菜单面板 -->
    <div x-show="cascadeOpen" x-transition
         class="absolute top-full left-0 mt-1 z-50 flex bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <!-- Level 1: 分类 -->
        <div class="w-40 max-h-80 overflow-y-auto border-r border-slate-200 dark:border-slate-700">
            <div @click="selectedCategoryId=0;selectedSubcategoryId=0;selectedProductMn='';cascadeOpen=false;loadDetail(1)"
                 class="px-3 py-2 text-sm cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500">全部产品</div>
            <template x-for="cat in filterCategories" :key="cat.id">
                <div @mouseenter="selectedCategoryId=cat.id;selectedCategoryName=cat.name;selectedSubcategoryId=0;selectedProductMn='';loadFilterOptions(cat.id)"
                     @click="selectedSubcategoryId=0;selectedProductMn='';cascadeOpen=false;loadDetail(1)"
                     class="px-3 py-2 text-sm cursor-pointer flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700"
                     :class="selectedCategoryId===cat.id ? 'bg-primary/5 text-primary' : ''">
                    <span x-text="cat.name"></span>
                    <svg class="w-3 h-3 text-slate-400"><use href="#icon-chevron-right"/></svg>
                </div>
            </template>
        </div>
        <!-- Level 2: 子分类 -->
        <div x-show="filterSubcategories.length" class="w-40 max-h-80 overflow-y-auto border-r border-slate-200 dark:border-slate-700">
            <template x-for="sub in filterSubcategories" :key="sub.id">
                <div @mouseenter="selectedSubcategoryId=sub.id;selectedSubcategoryName=sub.name;loadFilterOptions(selectedCategoryId, sub.id)"
                     @click="selectedProductMn='';cascadeOpen=false;loadDetail(1)"
                     class="px-3 py-2 text-sm cursor-pointer flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700"
                     :class="selectedSubcategoryId===sub.id ? 'bg-primary/5 text-primary' : ''">
                    <span x-text="sub.name"></span>
                    <svg class="w-3 h-3 text-slate-400"><use href="#icon-chevron-right"/></svg>
                </div>
            </template>
        </div>
        <!-- Level 3: 产品型号 -->
        <div x-show="filterModels.length" class="w-52 max-h-80 overflow-y-auto">
            <template x-for="m in filterModels" :key="m.mn">
                <div @click="selectedProductMn=m.mn;selectedProductName=m.name;cascadeOpen=false;loadDetail(1)"
                     class="px-3 py-2 text-sm cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700"
                     :class="selectedProductMn===m.mn ? 'bg-primary/5 text-primary font-medium' : ''">
                    <div x-text="m.name" class="truncate"></div>
                    <div x-text="m.model" class="text-xs text-slate-400 font-mono"></div>
                </div>
            </template>
        </div>
    </div>
</div>
```

**Step 4: 阶段和负责人下拉框 HTML**

```html
<!-- 阶段筛选 -->
<select x-model="selectedStage" @change="loadDetail(1)"
        class="h-10 pl-3 pr-8 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm">
    <option value="">全部阶段</option>
    <template x-for="s in filterStages" :key="s.value">
        <option :value="s.value" x-text="s.label"></option>
    </template>
</select>

<!-- 负责人筛选 -->
<select x-model="selectedOwnerId" @change="loadDetail(1)"
        class="h-10 pl-3 pr-8 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm">
    <option value="0">全部负责人</option>
    <template x-for="o in filterOwners" :key="o.id">
        <option :value="o.id" x-text="o.name"></option>
    </template>
</select>
```

**Step 5: Commit**

```
feat: add cascading product filter, stage & owner filters in detail tab
```

---

## Task 5: 前端 — 修改 loadDetail() 传递筛选参数

**Files:**
- Modify: `app/templates/product_analysis/tw_analysis.html` — `loadDetail()` 方法

**Step 1: 更新 loadDetail 传递新参数**

```javascript
async loadDetail(page) {
    if (page < 1) return;
    this.detailPage = page;
    try {
        const params = new URLSearchParams({
            year: this.selectedYear,
            page: page,
            per_page: this.detailPerPage
        });
        if (this.detailSearch) params.set('search', this.detailSearch);
        if (this.selectedCategoryId) params.set('category_id', this.selectedCategoryId);
        if (this.selectedSubcategoryId) params.set('subcategory_id', this.selectedSubcategoryId);
        if (this.selectedProductMn) params.set('product_mn', this.selectedProductMn);
        if (this.selectedStage) params.set('stage', this.selectedStage);
        if (this.selectedOwnerId) params.set('owner_id', this.selectedOwnerId);
        params.set('sort_by', this.detailSort);
        params.set('sort_dir', this.detailSortDir);
        const resp = await fetch('/product_analysis/api/v2/detail?' + params.toString());
        const result = await resp.json();
        if (result.success) {
            this.detailData = result.data;
            this.detailTotal = result.total;
            this.detailPages = result.pages;
        }
    } catch(e) { console.error(e); }
}
```

**Step 2: Commit**

```
feat: wire filter params to loadDetail API call
```

---

## Task 6: 前端 — 表格增加订单量和关联客户列

**Files:**
- Modify: `app/templates/product_analysis/tw_analysis.html` — 明细数据表格

**Step 1: 在 thead 中加列头**

在「数量」列后加「订单量」，在「项目」列后加「关联客户」：

```html
<!-- 数量列之后 -->
<th class="p-3 text-slate-500 font-medium text-right">{{ _('订单量') }}</th>
<!-- 项目列之后 -->
<th class="p-3 text-slate-500 font-medium">{{ _('关联客户') }}</th>
```

**Step 2: 在 tbody 中加数据列**

```html
<!-- 数量之后 -->
<td class="p-3 text-right" :class="row.order_qty > 0 ? 'text-green-600 font-medium' : 'text-slate-400'" x-text="row.order_qty || '-'"></td>
<!-- 项目之后 -->
<td class="p-3 text-xs text-slate-600 dark:text-slate-400 max-w-[150px] truncate" x-text="row.customer" :title="row.customer"></td>
```

**Step 3: colspan 更新**

空数据行的 colspan 从 8 改为 10。

**Step 4: Commit**

```
feat: add order_qty and customer columns to detail table
```

---

## Task 7: 后端 — detail API category_id 筛选支持

**Files:**
- Modify: `app/views/product_analysis.py` — `api_v2_detail()` 中的 category 筛选

**Step 1: 将现有 category name 筛选改为 category_id 筛选**

现有代码用 `category` (name字符串) 筛选，新增 `category_id` (整数) 支持：

```python
category_id = request.args.get('category_id', type=int)
# ...
if category_id:
    cat_models = db.session.query(Product.product_mn).filter(
        Product.category_id == category_id,
        Product.is_deleted == False
    ).distinct().subquery()
    q = q.filter(QuotationDetail.product_mn.in_(
        db.session.query(cat_models.c.product_mn)
    ))
elif category:
    # 保留原有 name 筛选兼容
    ...
```

**Step 2: Commit**

```
feat: support category_id filter in detail API
```

---

## Task 8: 前端 — 初始化时加载筛选选项

**Files:**
- Modify: `app/templates/product_analysis/tw_analysis.html` — `init()` 方法

**Step 1: 在 init 中预加载阶段和负责人**

```javascript
async init() {
    window.dashboard = this;
    this.selectedYear = parseInt(document.getElementById('yearSelect').value);
    // 预加载筛选选项（阶段、负责人、分类）
    this.loadFilterOptions();
    this.$watch('activeTab', (tab) => {
        if (tab === 'trend' && !this.trendData.length) this.loadTrend();
        if (tab === 'distribution' && !this.distribution.categories.length && !this.distribution.stages.length) this.loadDistribution();
        if (tab === 'ranking' && !this.ranking.length) this.loadRanking();
        if (tab === 'detail' && !this.detailData.length) this.loadDetail(1);
    });
    await this.loadOverview();
    await this.loadTrend();
},
```

**Step 2: Commit**

```
feat: preload filter options on dashboard init
```

---

## Task 9: 验证与测试

**Step 1: 本地启动验证**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 run.py
```

**Step 2: 功能验证清单**

- [ ] 年份选择「全部」→ 概览数据和明细数据显示全量
- [ ] 级联菜单：hover 分类 → 展开子分类 → 展开产品型号
- [ ] 选中分类 → 明细数据只显示该分类产品
- [ ] 选中子分类 → 明细数据只显示该子分类产品
- [ ] 选中产品型号 → 明细数据只显示该型号（精确匹配 product_mn）
- [ ] 阶段筛选 → 只显示对应阶段项目
- [ ] 负责人筛选 → 只显示对应负责人数据
- [ ] 组合筛选 → 多个筛选条件同时生效
- [ ] 订单量列 → 有订单的显示绿色数字，无订单的显示 `-`
- [ ] 关联客户列 → 显示 `分销商 / 代理商`，无则为空
- [ ] 搜索框 → 与筛选条件叠加生效
- [ ] 清除筛选 → 点击产品按钮上 ✕ 清除，下拉框选「全部」清除
- [ ] 翻页 → 筛选条件在翻页时保持

**Step 3: Commit all**

```
feat: product analysis detail filters - cascading product, stage, owner, order qty, customer
```
