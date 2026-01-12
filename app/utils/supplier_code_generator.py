# -*- coding: utf-8 -*-
"""
供应商编码自动生成工具

编码规则：
- 3位大写字母
- 基于公司名称的拼音首字母（中文）或直接首字母（英文）
- 自动去重：如果已存在则末位递增

示例：
- 华为技术 → HWJ
- 如果HWJ已存在 → HWK
- Huawei → HUA
"""
import re

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False


def generate_supplier_code(company_name, existing_codes):
    """
    自动生成供应商编码

    Args:
        company_name: 公司名称
        existing_codes: 已存在的编码集合 (set)

    Returns:
        str: 3位大写字母编码
    """
    # 提取首字母
    base_code = _extract_initials(company_name)[:3].upper()

    # 补足3位
    while len(base_code) < 3:
        base_code += 'A'

    # 确保是有效的字母
    base_code = ''.join(c if c.isalpha() else 'A' for c in base_code)

    # 去重：如果存在则递增末位
    final_code = base_code
    while final_code in existing_codes:
        final_code = _increment_code(final_code)

    return final_code


def _extract_initials(name):
    """
    提取名称首字母（支持中英文）

    Args:
        name: 公司名称

    Returns:
        str: 首字母组合
    """
    if not name:
        return 'AAA'

    # 移除特殊字符，保留中文和字母
    clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '', name)

    initials = []
    for char in clean_name:
        if '\u4e00' <= char <= '\u9fff':
            # 中文字符：取拼音首字母
            if HAS_PYPINYIN:
                py = lazy_pinyin(char, style=Style.FIRST_LETTER)
                if py and py[0]:
                    initials.append(py[0].upper())
            else:
                # 没有pypinyin库，使用简单的hash方式生成字母
                initials.append(chr(65 + (ord(char) % 26)))
        elif char.isalpha():
            # 英文字母：直接取
            initials.append(char.upper())

        if len(initials) >= 3:
            break

    return ''.join(initials) if initials else 'AAA'


def _increment_code(code):
    """
    编码递增

    规则：HWA → HWB → ... → HWZ → HXA → ... → HZZ → IAA

    Args:
        code: 当前编码

    Returns:
        str: 递增后的编码
    """
    if len(code) != 3:
        return code

    code_list = list(code)

    # 从最后一位开始递增
    for i in range(2, -1, -1):
        if code_list[i] < 'Z':
            code_list[i] = chr(ord(code_list[i]) + 1)
            return ''.join(code_list)
        code_list[i] = 'A'

    # 全部进位回AAA（理论上不会到这里，因为有17576种组合）
    return ''.join(code_list)


def get_existing_supplier_codes():
    """
    获取所有已存在的供应商编码

    Returns:
        set: 已存在的编码集合
    """
    from app.models.customer import Company

    codes = Company.query.filter(
        Company.supplier_code.isnot(None),
        Company.supplier_code != ''
    ).with_entities(Company.supplier_code).all()

    return set(c.supplier_code for c in codes if c.supplier_code)
