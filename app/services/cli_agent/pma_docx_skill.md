# PMA Word 文档生成 Skill v2.0

## 概述

生成 Word 文档时，必须使用 python-docx 编写完整可执行的 Python 代码。
所有样式参数均从实际 PMA 文档提取，**不得修改**。

### 数据库类型决定语言和公司名

| 数据库 | 公司名 | 语言 | 页码格式 |
|--------|--------|------|----------|
| SP8D   | 和源通信（上海）股份有限公司 | 中文 | 第 X 页 / 共 Y 页 |
| OVS    | Evertac Solutions | 英文 | Page X of Y |

调用时必须传入 `db_type="SP8D"` 或 `db_type="OVS"`。

---

## 完整可复用代码库

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

# ════════════════════════════════════════════════════════
# 1. 文档初始化
# ════════════════════════════════════════════════════════

def init_doc(db_type="SP8D"):
    """创建文档并设置默认字体、页面、样式"""
    doc = Document()

    # 默认字体（解决 MS Mincho 问题）
    styles_el = doc.styles.element
    docDefaults = styles_el.find(qn('w:docDefaults'))
    rPrDefault = docDefaults.find(qn('w:rPrDefault'))
    rPr = rPrDefault.find(qn('w:rPr'))
    if rPr is None: rPr = OxmlElement('w:rPr'); rPrDefault.append(rPr)
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None: rFonts = OxmlElement('w:rFonts'); rPr.insert(0, rFonts)
    for k,v in [('w:ascii','Arial'),('w:eastAsia','Microsoft YaHei'),('w:hAnsi','Arial'),('w:cs','Arial')]:
        rFonts.set(qn(k), v)

    # Heading 1：9pt，#1F4E79，不加粗，底边框
    # Heading 2：8pt，#2E75B6，不加粗
    for lvl, color, before, after in [('Heading 1','1F4E79','320','160'), ('Heading 2','2E75B6','240','120')]:
        h = doc.styles[lvl]
        rPr = h.element.find(qn('w:rPr'))
        if rPr is None: rPr = OxmlElement('w:rPr'); h.element.append(rPr)
        for tag in ['w:rFonts','w:b','w:color','w:sz','w:szCs']:
            for old in rPr.findall(qn(tag)): rPr.remove(old)
        rf = OxmlElement('w:rFonts')
        for k,v in [('w:ascii','Microsoft YaHei'),('w:eastAsia','Microsoft YaHei'),
                    ('w:hAnsi','Microsoft YaHei'),('w:cs','Microsoft YaHei')]:
            rf.set(qn(k), v)
        rPr.insert(0, rf)
        c = OxmlElement('w:color'); c.set(qn('w:val'), color); rPr.append(c)
        pPr = h.element.find(qn('w:pPr'))
        if pPr is None: pPr = OxmlElement('w:pPr'); h.element.insert(0, pPr)
        for old in pPr.findall(qn('w:spacing')): pPr.remove(old)
        sp = OxmlElement('w:spacing'); sp.set(qn('w:before'),before); sp.set(qn('w:after'),after)
        pPr.append(sp)

    # 页面：A4，四边 2cm
    sec = doc.sections[0]
    sec.page_width = Cm(21); sec.page_height = Cm(29.7)
    sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Cm(2.0)

    # 页眉页脚
    _add_header_footer(doc, db_type)

    return doc


# ════════════════════════════════════════════════════════
# 2. 颜色 & 字体常量
# ════════════════════════════════════════════════════════

COLOR = {
    'primary':     '1F4E79',   # 深蓝，表头背景
    'secondary':   '2E75B6',   # 中蓝，次级表头
    'h1':          '1F4E79',   # Heading 1 颜色
    'h2':          '2E75B6',   # Heading 2 颜色
    'border':      'DDDDDD',   # 表格边框（灰）
    'separator':   '1F4E79',   # 段落分隔线
    'meta':        '888888',   # 元信息灰
    'dim':         '555555',   # 次要文字
    'dim_light':   'AAAAAA',   # 页脚/版本号
    'red':         'C00000',   # 负面/未达标
    'green':       '1E7B1E',   # 正面/达标
    'row_alt':     'F2F2F2',   # 表格奇数行
    'row_sum':     'EBF3FB',   # 汇总行浅蓝
    'score_bad':   'FFF0F0',   # 评分背景红
    'score_good':  'F0FFF0',   # 评分背景绿
    'score_na':    'F5F5F5',   # 评分背景灰
    'cell_bad':    'FFDAD6',   # 单元格红
    'cell_good':   'E2EFDA',   # 单元格绿
    'cell_warn':   'FFF2CC',   # 单元格黄
}


# ════════════════════════════════════════════════════════
# 3. Run 字体工具
# ════════════════════════════════════════════════════════

def _set_run_font(run, ascii_f, east_f=None, sz=None, bold=False, color=None):
    """精确设置 run 的四属性字体，避免 MS Mincho 污染"""
    rPr = run._r.get_or_add_rPr()
    for old in rPr.findall(qn('w:rFonts')): rPr.remove(old)
    rf = OxmlElement('w:rFonts')
    rf.set(qn('w:ascii'), ascii_f); rf.set(qn('w:hAnsi'), ascii_f); rf.set(qn('w:cs'), ascii_f)
    if east_f: rf.set(qn('w:eastAsia'), east_f)
    if east_f and east_f != ascii_f: rf.set(qn('w:hint'), 'eastAsia')
    rPr.insert(0, rf)
    if sz:
        for old in rPr.findall(qn('w:sz')): rPr.remove(old)
        for old in rPr.findall(qn('w:szCs')): rPr.remove(old)
        s = OxmlElement('w:sz'); s.set(qn('w:val'), str(sz)); rPr.append(s)
        sc = OxmlElement('w:szCs'); sc.set(qn('w:val'), str(sz)); rPr.append(sc)
    for old in rPr.findall(qn('w:b')): rPr.remove(old)
    if bold: rPr.append(OxmlElement('w:b'))
    if color:
        for old in rPr.findall(qn('w:color')): rPr.remove(old)
        c = OxmlElement('w:color'); c.set(qn('w:val'), color); rPr.append(c)

def add_mixed(para, text, sz=11, color=None, bold=False):
    """中英文混排：中文 Microsoft YaHei，英文/数字 Calibri"""
    for seg in re.split(r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u2014\u2013]+)', text):
        if not seg: continue
        has_cn = any('\u4e00' <= c <= '\u9fff' for c in seg)
        run = para.add_run(seg)
        if has_cn: _set_run_font(run, 'Microsoft YaHei', 'Microsoft YaHei', sz, bold, color)
        else:       _set_run_font(run, 'Calibri', 'Arial', sz, bold, color)


# ════════════════════════════════════════════════════════
# 4. 段落工具
# ════════════════════════════════════════════════════════

def add_h1(doc, text):
    """一级标题：9pt，#1F4E79，不加粗，底边框蓝线"""
    para = doc.add_heading(level=1); para.clear()
    add_mixed(para, text, sz=18)
    pPr = para._p.get_or_add_pPr()
    for old in pPr.findall(qn('w:pBdr')): pPr.remove(old)
    pBdr = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'),'single'); bot.set(qn('w:sz'),'8')
    bot.set(qn('w:space'),'1'); bot.set(qn('w:color'), COLOR['separator'])
    pBdr.append(bot); pPr.append(pBdr)

def add_h2(doc, text):
    """二级标题：8pt，#2E75B6，不加粗"""
    para = doc.add_heading(level=2); para.clear()
    add_mixed(para, text, sz=16)

def add_body(doc, text, color=None):
    """正文段落：5.5pt，中英混排"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    add_mixed(para, text, sz=11, color=color)
    return para

def add_score(doc, text, sentiment='bad'):
    """
    评分段落：左边彩条 + 底色
    sentiment: 'bad'(红) | 'good'(绿) | 'neutral'(灰)
    """
    cfg = {
        'bad':     (COLOR['red'],   COLOR['score_bad']),
        'good':    (COLOR['green'], COLOR['score_good']),
        'neutral': ('888888',       COLOR['score_na']),
    }
    bc, fill = cfg[sentiment]
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr'); left = OxmlElement('w:left')
    left.set(qn('w:val'),'single'); left.set(qn('w:sz'),'16')
    left.set(qn('w:space'),'4'); left.set(qn('w:color'), bc)
    pBdr.append(left); pPr.append(pBdr)
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'), fill); pPr.append(shd)
    ind = OxmlElement('w:ind'); ind.set(qn('w:left'),'120'); pPr.append(ind)
    add_mixed(para, text, sz=11, color=bc)
    return para

def add_separator(doc):
    """页头下方的空白分隔横线"""
    sep = doc.add_paragraph()
    sep.paragraph_format.space_before = Pt(3)
    sep.paragraph_format.space_after = Pt(20)
    pPr = sep._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'),'single'); bot.set(qn('w:sz'),'8')
    bot.set(qn('w:space'),'1'); bot.set(qn('w:color'), COLOR['separator'])
    pBdr.append(bot); pPr.append(pBdr)


# ════════════════════════════════════════════════════════
# 5. 表格工具
# ════════════════════════════════════════════════════════

def _set_cell_bg(cell, hex_color):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:shd')): tcPr.remove(old)
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear')
    shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'), hex_color); tcPr.append(shd)

def _set_cell_borders(cell, color='DDDDDD'):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:tcBorders')): tcPr.remove(old)
    tcB = OxmlElement('w:tcBorders')
    for side in ['top','left','bottom','right']:
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'4')
        el.set(qn('w:space'),'0'); el.set(qn('w:color'), color)
        tcB.append(el)
    tcPr.append(tcB)

def _set_cell_padding(cell, top=100, bottom=100, left=120, right=120):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:tcMar')): tcPr.remove(old)
    tcMar = OxmlElement('w:tcMar')
    for side, val in [('top',top),('bottom',bottom),('left',left),('right',right)]:
        el = OxmlElement(f'w:{side}'); el.set(qn('w:w'),str(val)); el.set(qn('w:type'),'dxa')
        tcMar.append(el)
    tcPr.append(tcMar)

def _apply_cell(doc, cell, bg, is_label=False):
    _set_cell_bg(cell, bg)
    _set_cell_borders(cell, COLOR['border'])
    _set_cell_padding(cell)
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:vAlign')): tcPr.remove(old)
    va = OxmlElement('w:vAlign'); va.set(qn('w:val'),'center'); tcPr.append(va)
    for para in cell.paragraphs:
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_label else WD_ALIGN_PARAGRAPH.LEFT
        for run in para.runs:
            has_cn = any('\u4e00' <= c <= '\u9fff' for c in run.text)
            ea = 'Microsoft YaHei' if has_cn else 'Arial'
            asc = 'Microsoft YaHei' if has_cn else 'Calibri'
            _set_run_font(run, asc, ea, 11, bold=is_label, color='FFFFFF' if is_label else None)

def _set_table_full_width(table, widths_cm):
    """表格撑满页面（9638 dxa = 17cm）并设置列宽"""
    tbl = table._tbl; tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None: tblPr = OxmlElement('w:tblPr'); tbl.insert(0, tblPr)
    for old in tblPr.findall(qn('w:tblW')): tblPr.remove(old)
    tblW = OxmlElement('w:tblW'); tblW.set(qn('w:w'),'9638'); tblW.set(qn('w:type'),'dxa')
    tblPr.append(tblW)
    tblGrid = tbl.find(qn('w:tblGrid'))
    if tblGrid is None: tblGrid = OxmlElement('w:tblGrid'); tbl.insert(1, tblGrid)
    for gc in tblGrid.findall(qn('w:gridCol')): tblGrid.remove(gc)
    for w in widths_cm:
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), str(int(w*567))); tblGrid.append(gc)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                tc = cell._tc; tcPr = tc.get_or_add_tcPr()
                for old in tcPr.findall(qn('w:tcW')): tcPr.remove(old)
                tcW = OxmlElement('w:tcW')
                tcW.set(qn('w:w'), str(int(widths_cm[i]*567))); tcW.set(qn('w:type'),'dxa')
                tcPr.append(tcW)

def fill_table(table, data):
    """填充表格数据"""
    for r, row_data in enumerate(data):
        for c, val in enumerate(row_data):
            if r < len(table.rows) and c < len(table.columns):
                table.rows[r].cells[c].text = val

def style_info_table(doc, table, widths_cm):
    """
    基本信息表格：标签|值|标签|值 列对模式
    偶数列(0,2,4)=深蓝标题居中白字，奇数列(1,3,5)=白色内容左对齐
    """
    table.style = doc.styles['Normal Table']
    _set_table_full_width(table, widths_cm)
    for row in table.rows:
        for c_i, cell in enumerate(row.cells):
            is_label = (c_i % 2 == 0)
            _apply_cell(doc, cell, COLOR['primary'] if is_label else 'FFFFFF', is_label)

def style_data_table(doc, table, widths_cm):
    """
    数据表格：首行深蓝白字，内容行奇灰偶白
    """
    table.style = doc.styles['Normal Table']
    _set_table_full_width(table, widths_cm)
    for r_i, row in enumerate(table.rows):
        for cell in row.cells:
            if r_i == 0: _apply_cell(doc, cell, COLOR['primary'], True)
            else:
                bg = COLOR['row_alt'] if (r_i-1)%2==0 else 'FFFFFF'
                _apply_cell(doc, cell, bg, False)

def set_cell_color(cell, color_key):
    """单独设置某个单元格颜色，用于状态标记"""
    _set_cell_bg(cell, COLOR[color_key])
    _set_cell_borders(cell, COLOR['border'])


# ════════════════════════════════════════════════════════
# 6. 页眉页脚
# ════════════════════════════════════════════════════════

def _add_field(para, field_name):
    for el in [
        ('w:fldChar', {'w:fldCharType': 'begin'}),
        ('w:instrText', None, f' {field_name} '),
        ('w:fldChar', {'w:fldCharType': 'end'}),
    ]:
        run = OxmlElement('w:r')
        node = OxmlElement(el[0])
        if el[1]:
            for k,v in el[1].items(): node.set(qn(k),v)
        if len(el) > 2: node.text = el[2]
        run.append(node); para._p.append(run)

def _add_header_footer(doc, db_type="SP8D"):
    is_cn = (db_type == "SP8D")
    company = '和源通信（上海）股份有限公司' if is_cn else 'Evertac Solutions'
    section = doc.sections[0]
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)

    # 页眉
    hp = section.header.paragraphs[0]
    hp.clear(); hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hp.paragraph_format.space_before = Pt(0); hp.paragraph_format.space_after = Pt(2)
    run = hp.add_run(company)
    if is_cn: _set_run_font(run,'Microsoft YaHei','Microsoft YaHei',16,color='888888')
    else:      _set_run_font(run,'Calibri','Arial',16,color='888888')
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'),'single'); bot.set(qn('w:sz'),'6')
    bot.set(qn('w:space'),'1'); bot.set(qn('w:color'), COLOR['border'])
    pBdr.append(bot); pPr.append(pBdr)

    # 页脚
    fp = section.footer.paragraphs[0]
    fp.clear(); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(2); fp.paragraph_format.space_after = Pt(0)
    pPr2 = fp._p.get_or_add_pPr()
    pBdr2 = OxmlElement('w:pBdr'); top = OxmlElement('w:top')
    top.set(qn('w:val'),'single'); top.set(qn('w:sz'),'6')
    top.set(qn('w:space'),'1'); top.set(qn('w:color'), COLOR['border'])
    pBdr2.append(top); pPr2.append(pBdr2)
    if is_cn:
        r=fp.add_run('第 '); _set_run_font(r,'Microsoft YaHei','Microsoft YaHei',16,color='AAAAAA')
        _add_field(fp,'PAGE')
        r=fp.add_run(' 页 / 共 '); _set_run_font(r,'Microsoft YaHei','Microsoft YaHei',16,color='AAAAAA')
        _add_field(fp,'NUMPAGES')
        r=fp.add_run(' 页'); _set_run_font(r,'Microsoft YaHei','Microsoft YaHei',16,color='AAAAAA')
    else:
        r=fp.add_run('Page '); _set_run_font(r,'Calibri','Arial',16,color='AAAAAA')
        _add_field(fp,'PAGE')
        r=fp.add_run(' of '); _set_run_font(r,'Calibri','Arial',16,color='AAAAAA')
        _add_field(fp,'NUMPAGES')


# ════════════════════════════════════════════════════════
# 7. 文档头部块
# ════════════════════════════════════════════════════════

def add_doc_header(doc, company_tag, person_name, role, period, date, db_type="SP8D"):
    """
    文档顶部标题块（居中）
    company_tag: 如 'EVERTAC 市场部'
    person_name: 如 '骆永融'
    role:        如 '市场执行统筹'
    period:      如 '2026年Q1'
    date:        如 '2026年4月7日'
    """
    # 公司标签
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24); p.paragraph_format.space_after = Pt(5)
    for seg in re.split(r'([\u4e00-\u9fff]+)', company_tag):
        if not seg: continue
        r = p.add_run(seg)
        has_cn = any('\u4e00'<=c<='\u9fff' for c in seg)
        if has_cn: _set_run_font(r,'Microsoft YaHei','Microsoft YaHei',15,color=COLOR['meta'])
        else:       _set_run_font(r,'Calibri','Arial',15,color=COLOR['meta'])

    # 主标题：姓名 + 报告类型
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0); p2.paragraph_format.space_after = Pt(4)
    add_mixed(p2, f'{person_name} · {period}绩效评估报告', sz=22, color=COLOR['h1'])

    # 副标题：岗位 | 评估期间 | 编制日期
    p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_before = Pt(0); p3.paragraph_format.space_after = Pt(3)
    add_mixed(p3, f'{role} | 评估期间：{period} | 编制日期：{date}', sz=11, color=COLOR['meta'])

    # 分隔线
    add_separator(doc)


# ════════════════════════════════════════════════════════
# 8. 使用示例
# ════════════════════════════════════════════════════════

# SP8D 中文版
# doc = init_doc(db_type="SP8D")
# add_doc_header(doc, 'EVERTAC 市场部', '骆永融', '市场执行统筹', '2026年Q1', '2026年4月7日', db_type="SP8D")
# add_h1(doc, '一、基本信息')
# t = doc.add_table(rows=2, cols=4)
# fill_table(t, [['岗位','市场执行统筹','部门','市场部'], ['汇报对象','总经理','评估期间','2026年Q1']])
# style_info_table(doc, t, [3.57, 3.57, 3.57, 3.57])
# add_h1(doc, '二、KPI评估')
# add_h2(doc, '2.1 渠道活动（权重25%）')
# add_body(doc, 'Q1目标：3场')
# add_score(doc, '评分：1分（严重不达标）— 零落地。', sentiment='bad')
# doc.save('output_SP8D.docx')

# OVS 英文版
# doc = init_doc(db_type="OVS")
# ... 同上，db_type="OVS"
# doc.save('output_OVS.docx')
```

---

## PMA 系统集成说明

### API 调用方式

PMA 智能终端调用 Claude API 时，将以上代码库作为 system prompt 的一部分传入：

```python
system_prompt = f"""
你是 PMA 文档生成助手。
当前数据库类型：{db_type}  # 从 PMA 系统上下文注入

生成 Word 文档时，必须使用以下代码库（已内置所有样式函数），
直接调用函数生成文档，不要重新定义样式。

{open('pma_docx_skill.md').read()}

输出：完整可执行的 Python 代码，无需解释。
文件保存路径作为变量传入，不硬编码。
"""
```

### Claude API 输出 → PMA 执行流程

```
1. PMA 获取用户请求（生成报告/文档）
2. 注入 skill + db_type → 调用 Claude API
3. Claude 返回完整 python-docx 代码
4. PMA 后端在临时目录执行代码
5. 生成 .docx 文件返回给用户下载
```

### db_type 判断逻辑

```python
# PMA 后端
db_type = "SP8D" if current_database == "sp8d_db" else "OVS"
```
