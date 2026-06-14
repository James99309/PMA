# -*- coding: utf-8 -*-
"""质量得分(植入品质)批量计算 helper。

单据得分 = 该报价单里出现过的「推荐产品」(citation_coefficient>0)系数之和
(去重不看数量),与报价单详情「质量得分」、绩效「植入品质」同一口径。
列表页用批量函数避免 N+1;0 分不返回(调用方据此不显示徽章)。
"""
from sqlalchemy import text, bindparam


def quotation_quality_scores(quotation_ids):
    """返回 {quotation_id: score>0}(去重推荐系数和)。0 分不收录。"""
    ids = [i for i in (quotation_ids or []) if i]
    if not ids:
        return {}
    from app import db
    sql = text(
        "SELECT q.id, COALESCE(SUM(p.citation_coefficient), 0) AS s "
        "FROM quotations q "
        "JOIN (SELECT DISTINCT quotation_id, product_mn FROM quotation_details) dp "
        "     ON dp.quotation_id = q.id "
        "JOIN products p ON p.product_mn = dp.product_mn AND p.citation_coefficient > 0 "
        "WHERE q.id IN :ids "
        "GROUP BY q.id"
    ).bindparams(bindparam('ids', expanding=True))
    rows = db.session.execute(sql, {'ids': ids}).fetchall()
    return {r[0]: round(float(r[1]), 1) for r in rows if r[1] and float(r[1]) > 0}


def project_quality_scores(project_ids):
    """返回 {project_id: 最高单据得分>0}(项目下多张报价单取最高)。0 分不收录。"""
    ids = [i for i in (project_ids or []) if i]
    if not ids:
        return {}
    from app import db
    sql = text(
        "SELECT qs.project_id, MAX(qs.s) AS s FROM ("
        "  SELECT q.id, q.project_id, COALESCE(SUM(p.citation_coefficient), 0) AS s "
        "  FROM quotations q "
        "  JOIN (SELECT DISTINCT quotation_id, product_mn FROM quotation_details) dp "
        "       ON dp.quotation_id = q.id "
        "  JOIN products p ON p.product_mn = dp.product_mn AND p.citation_coefficient > 0 "
        "  WHERE q.project_id IN :ids "
        "  GROUP BY q.id, q.project_id"
        ") qs GROUP BY qs.project_id"
    ).bindparams(bindparam('ids', expanding=True))
    rows = db.session.execute(sql, {'ids': ids}).fetchall()
    return {r[0]: round(float(r[1]), 1) for r in rows if r[1] and float(r[1]) > 0}
