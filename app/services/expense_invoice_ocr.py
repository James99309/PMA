# -*- coding: utf-8 -*-
"""报销发票 OCR — Claude Vision 提取增值税发票/收据/外币票据字段

通用引擎在 claude_vision_ocr.extract_with_schema, 本模块只负责发票专属的
schema/prompt(含 9 货币 + 报销科目枚举).
"""
from app.services.claude_vision_ocr import extract_with_schema
from app.models.expense import EXPENSE_CATEGORIES


_CATEGORY_KEYS = ', '.join(c[0] for c in EXPENSE_CATEGORIES)
_CATEGORY_HINTS = '; '.join(f'{c[0]}={c[1]}' for c in EXPENSE_CATEGORIES)


_INVOICE_PROMPT = f"""You are an expense invoice / receipt OCR engine.
Extract fields from the given invoice or receipt image (中国增值税发票, 通用收据,
酒店账单, 出租车票, 加油票, 外币 receipt 等都要支持) and return ONLY a JSON object.
Do NOT include explanation, markdown, or code fences. Output raw JSON only.

Schema:
{{
  "seller": string|null,         // 开票方/商户名 (公司全名)
  "invoice_no": string|null,     // 发票号码 / 收据编号 (数字串, 去空格连字符)
  "date": string|null,           // 发生/开票日期, 格式 YYYY-MM-DD; 模糊则推断当天
  "currency": string|null,       // ISO code: CNY, USD, HKD, TWD, SGD, MYR, IDR, THB, VND
  "invoice_amount": number|null, // 价税合计/总金额, 小数, 不带货币符号
  "tax_amount": number|null,     // 税额, 没有则 null
  "category": string|null,       // 报销科目 enum key, 必须从下列里选: {_CATEGORY_KEYS}
                                  //   含义: {_CATEGORY_HINTS}
                                  //   找不到合理映射就给 "other"
  "description": string|null,    // 一行简短描述, 例: "上海至北京 高铁" / "国贸停车 2 小时"
  "confidence": {{                // 每字段 0.0-1.0 置信度 (category 通常较低)
    "seller": number,
    "invoice_no": number,
    "date": number,
    "currency": number,
    "invoice_amount": number,
    "tax_amount": number,
    "category": number,
    "description": number
  }}
}}

Rules:
- 字段缺失或不清晰 → null 且 confidence=0.
- 中国增值税发票头尾的"价税合计 (大写)"行,金额取小写阿拉伯数字行.
- 没明确写货币的中国发票 → currency="CNY".
- 美元 $ → "USD"; 港币 HK$ → "HKD"; 新币 S$ → "SGD"; 马币 RM → "MYR"; 泰铢 ฿ → "THB"; 印尼盾 Rp → "IDR"; 越南盾 ₫ → "VND"; 新台币 NT$ → "TWD".
- category 推断示例: "中石化加油" → fuel; "停车场" → parking; "高铁/机票/酒店" → travel_accommodation; "市内出租/网约车" → local_transport; "餐厅/快餐" → meals; "招待/宴请/茶歇" → entertainment; "办公耗材/打印" → office_supplies; "话费/流量" → communication.
- description 简洁,15 字内; 突出"做了什么"而不是"商家叫什么".
- Confidence: 清晰印刷 0.95+; 略模糊 0.7-0.9; 推断 / 手写 < 0.7.
- category 是软推荐, 用户可改; 不确定就给较低 confidence (≤0.7) 让 UI 飘黄."""


# 区域语言指令: SG(en) 时强制 description 直接出英文(中文票也翻),
# seller 保留票面原文(专有名词)。CN(zh) 不追加, 维持原行为。
_LANG_DIRECTIVE = {
    'en': (
        "\n\nLANGUAGE: Output the \"description\" field in natural English. "
        "If the receipt/invoice is written in Chinese or any other language, "
        "translate the description into English. Keep \"seller\" exactly as "
        "printed on the receipt (do NOT translate the merchant name). "
        "All other fields follow the schema as specified."
    ),
}


def extract_invoice(image_blob: bytes, lang: str = 'zh') -> dict:
    """从发票/收据图字节流提取字段。

    Args:
        image_blob: 发票/收据图字节流
        lang: 区域系统语言 'zh'|'en'。'en' 时 description 直接出英文
              (确认页一开始就是英文, 无需事后翻译); seller 仍保票面原文。

    Returns:
        成功 → {'success': True, 'data': {seller, invoice_no, date, currency,
                invoice_amount, tax_amount, category, description, confidence}}
        失败 → {'success': False, 'message': '...'}
    """
    prompt = _INVOICE_PROMPT + _LANG_DIRECTIVE.get(lang, '')
    return extract_with_schema(
        image_blob,
        prompt,
        user_text='请提取这张发票/收据的字段, 仅返回 JSON.',
    )
