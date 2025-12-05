#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译审计和修复工具

功能：
1. 扫描代码中所有需要翻译的字符串
2. 与翻译文件(messages.po)比对
3. 识别：缺失翻译、无效翻译、空翻译、废弃翻译
4. 生成修复建议或自动修复

使用方法：
    python scripts/tools/translation_audit.py              # 仅检查
    python scripts/tools/translation_audit.py --fix        # 检查并修复
    python scripts/tools/translation_audit.py --clean      # 清理废弃条目
    python scripts/tools/translation_audit.py --full       # 完整修复（检查+修复+清理）

遵循 CLAUDE.md 中的脚本创建规范
"""

import os
import sys
import re
import argparse
from datetime import datetime
from collections import defaultdict

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)

# 配置
PO_FILE = os.path.join(PROJECT_ROOT, 'app/translations/en/LC_MESSAGES/messages.po')
SCAN_DIRS = [
    os.path.join(PROJECT_ROOT, 'app/templates'),
    os.path.join(PROJECT_ROOT, 'app/views'),
    os.path.join(PROJECT_ROOT, 'app/routes'),
    os.path.join(PROJECT_ROOT, 'app/models'),
]

# 常用翻译映射（用于自动生成翻译建议）
COMMON_TRANSLATIONS = {
    # ==================== 按钮/动作 ====================
    '保存': 'Save',
    '取消': 'Cancel',
    '删除': 'Delete',
    '编辑': 'Edit',
    '添加': 'Add',
    '返回': 'Back',
    '确认': 'Confirm',
    '提交': 'Submit',
    '搜索': 'Search',
    '重置': 'Reset',
    '上传': 'Upload',
    '下载': 'Download',
    '导出': 'Export',
    '导入': 'Import',
    '清除': 'Clear',
    '刷新': 'Refresh',
    '关闭': 'Close',
    '查看': 'View',
    '详情': 'Details',
    '更多': 'More',
    '新建': 'Create',
    '复制': 'Copy',
    '粘贴': 'Paste',
    '撤销': 'Undo',
    '恢复': 'Restore',
    '锁定': 'Lock',
    '解锁': 'Unlock',
    '启用': 'Enable',
    '禁用': 'Disable',
    '激活': 'Activate',
    '停用': 'Deactivate',
    '选择': 'Select',
    '应用': 'Apply',
    '预览': 'Preview',
    '打印': 'Print',
    '发送': 'Send',
    '接收': 'Receive',
    '同步': 'Sync',
    '备份': 'Backup',
    '还原': 'Restore',
    '清空': 'Clear All',
    '展开': 'Expand',
    '折叠': 'Collapse',
    '排序': 'Sort',
    '筛选': 'Filter',
    '合并': 'Merge',
    '拆分': 'Split',
    '移动': 'Move',
    '批量': 'Batch',
    '召回': 'Recall',
    '重新提交': 'Resubmit',

    # ==================== 状态 ====================
    '成功': 'Success',
    '失败': 'Failed',
    '错误': 'Error',
    '警告': 'Warning',
    '提示': 'Info',
    '加载中': 'Loading',
    '处理中': 'Processing',
    '已完成': 'Completed',
    '待处理': 'Pending',
    '已取消': 'Cancelled',
    '进行中': 'In Progress',
    '已暂停': 'Paused',
    '已过期': 'Expired',
    '已删除': 'Deleted',
    '已归档': 'Archived',
    '草稿': 'Draft',
    '待审批': 'Pending Approval',
    '已批准': 'Approved',
    '已拒绝': 'Rejected',
    '有效': 'Active',
    '无效': 'Inactive',
    '生产中': 'In Production',
    '已停产': 'Discontinued',
    '待上市': 'Upcoming',

    # ==================== 表单 ====================
    '必填': 'Required',
    '可选': 'Optional',
    '请选择': 'Please select',
    '请输入': 'Please enter',
    '无': 'None',
    '是': 'Yes',
    '否': 'No',
    '全部': 'All',
    '默认': 'Default',
    '自定义': 'Custom',
    '未设置': 'Not Set',
    '未知': 'Unknown',
    '暂无': 'None',
    '空': 'Empty',

    # ==================== 通用字段 ====================
    '操作': 'Actions',
    '状态': 'Status',
    '类型': 'Type',
    '名称': 'Name',
    '描述': 'Description',
    '备注': 'Remarks',
    '时间': 'Time',
    '日期': 'Date',
    '数量': 'Quantity',
    '金额': 'Amount',
    '价格': 'Price',
    '单位': 'Unit',
    '序号': 'No.',
    '编号': 'Number',
    '编码': 'Code',
    '标题': 'Title',
    '内容': 'Content',
    '来源': 'Source',
    '目标': 'Target',
    '原因': 'Reason',
    '结果': 'Result',
    '级别': 'Level',
    '优先级': 'Priority',
    '权限': 'Permission',
    '角色': 'Role',
    '用户': 'User',
    '账号': 'Account',
    '密码': 'Password',
    '邮箱': 'Email',
    '电话': 'Phone',
    '地址': 'Address',
    '国家': 'Country',
    '地区': 'Region',
    '城市': 'City',
    '位置': 'Position',
    '坐标': 'Coordinates',
    '范围': 'Range',
    '大小': 'Size',
    '宽度': 'Width',
    '高度': 'Height',
    '长度': 'Length',
    '重量': 'Weight',
    '颜色': 'Color',
    '版本': 'Version',
    '格式': 'Format',
    '模式': 'Mode',
    '方式': 'Method',
    '选项': 'Options',
    '参数': 'Parameters',
    '配置': 'Configuration',
    '设置': 'Settings',
    '属性': 'Properties',
    '特性': 'Features',
    '功能': 'Functions',
    '服务': 'Service',
    '接口': 'Interface',
    '协议': 'Protocol',
    '标签': 'Tag',
    '分类': 'Category',
    '子分类': 'Subcategory',
    '父级': 'Parent',
    '子级': 'Child',
    '关联': 'Related',
    '附件': 'Attachment',
    '评论': 'Comment',
    '回复': 'Reply',
    '消息': 'Message',
    '通知': 'Notification',
    '提醒': 'Reminder',
    '历史': 'History',
    '记录': 'Record',
    '日志': 'Log',
    '统计': 'Statistics',
    '报表': 'Report',
    '图表': 'Chart',
    '仪表盘': 'Dashboard',
    '概览': 'Overview',
    '摘要': 'Summary',
    '总计': 'Total',
    '合计': 'Subtotal',
    '平均': 'Average',
    '最大': 'Maximum',
    '最小': 'Minimum',
    '百分比': 'Percentage',
    '比例': 'Ratio',
    '增长': 'Growth',
    '下降': 'Decline',
    '变化': 'Change',
    '趋势': 'Trend',

    # ==================== 产品相关 ====================
    '产品': 'Product',
    '产品名称': 'Product Name',
    '产品类型': 'Product Type',
    '产品状态': 'Product Status',
    '产品分类': 'Product Category',
    '产品系列': 'Product Series',
    '产品MN': 'Product MN',
    '产品二维码': 'Product QR Code',
    '产品规格': 'Product Specifications',
    '产品详情': 'Product Details',
    '产品文档': 'Product Documents',
    '产品编码': 'Product Code',
    '产品库': 'Product Library',
    '产品列表': 'Product List',
    '产品信息': 'Product Information',
    '产品图片': 'Product Image',
    '市场价格': 'Market Price',
    '计量单位': 'Unit of Measurement',
    '品牌': 'Brand',
    '型号': 'Model',
    '规格': 'Specifications',
    '规格说明': 'Specifications',
    '规格MN': 'Spec MN',
    'MN编号': 'MN Number',
    'MN编码': 'MN Code',
    '配件': 'Accessory',
    '配件数量': 'Accessory Quantity',
    '必选配件': 'Required Accessory',
    '推荐配件': 'Recommended Accessory',
    '互斥组': 'Mutual Exclusion Group',
    '关联产品': 'Related Products',
    '关联产品配置': 'Related Product Configuration',

    # ==================== 图片/文件 ====================
    '上传图片': 'Upload Image',
    '上传PDF文档': 'Upload PDF',
    '上传PDF': 'Upload PDF',
    '上传文件': 'Upload File',
    '图片': 'Image',
    '文档': 'Document',
    '文件': 'File',
    'PDF': 'PDF',
    '图片上传': 'Image Upload',
    '文件上传': 'File Upload',
    '图片预览': 'Image Preview',
    '文件预览': 'File Preview',
    '文件大小': 'File Size',
    '文件类型': 'File Type',
    '文件名': 'File Name',
    '下载文件': 'Download File',

    # ==================== 确认对话框 ====================
    '确认删除': 'Confirm Delete',
    '确认锁定': 'Confirm Lock',
    '确认解锁': 'Confirm Unlock',
    '确认提交': 'Confirm Submit',
    '确认取消': 'Confirm Cancel',
    '确认保存': 'Confirm Save',
    '确定': 'OK',
    '确定要': 'Are you sure you want to',
    '此操作不可撤销': 'This action cannot be undone',
    '请谨慎操作': 'Please proceed with caution',

    # ==================== 时间相关 ====================
    '更新时间': 'Update Time',
    '创建时间': 'Created Time',
    '生成时间': 'Generated Time',
    '开始时间': 'Start Time',
    '结束时间': 'End Time',
    '到期时间': 'Expiry Time',
    '提交时间': 'Submit Time',
    '审批时间': 'Approval Time',
    '完成时间': 'Completion Time',
    '最后更新': 'Last Updated',
    '最后登录': 'Last Login',
    '今天': 'Today',
    '昨天': 'Yesterday',
    '明天': 'Tomorrow',
    '本周': 'This Week',
    '上周': 'Last Week',
    '本月': 'This Month',
    '上月': 'Last Month',
    '本年': 'This Year',
    '去年': 'Last Year',

    # ==================== 客户相关 ====================
    '客户': 'Customer',
    '客户名称': 'Customer Name',
    '客户类型': 'Customer Type',
    '客户状态': 'Customer Status',
    '客户信息': 'Customer Information',
    '客户列表': 'Customer List',
    '联系人': 'Contact',
    '联系方式': 'Contact Information',
    '公司': 'Company',
    '公司名称': 'Company Name',

    # ==================== 项目相关 ====================
    '项目': 'Project',
    '项目名称': 'Project Name',
    '项目状态': 'Project Status',
    '项目类型': 'Project Type',
    '项目信息': 'Project Information',
    '项目列表': 'Project List',
    '项目编号': 'Project Number',
    '项目经理': 'Project Manager',
    '负责人': 'Person in Charge',

    # ==================== 报价相关 ====================
    '报价': 'Quotation',
    '报价单': 'Quotation',
    '报价单号': 'Quotation Number',
    '报价金额': 'Quotation Amount',
    '报价日期': 'Quotation Date',
    '有效期': 'Validity Period',
    '折扣': 'Discount',
    '税率': 'Tax Rate',
    '税额': 'Tax Amount',
    '含税': 'Tax Inclusive',
    '不含税': 'Tax Exclusive',
    '总价': 'Total Price',
    '单价': 'Unit Price',
    '小计': 'Subtotal',
    '明细': 'Details',
    '产品明细': 'Product Details',

    # ==================== 订单相关 ====================
    '订单': 'Order',
    '订单号': 'Order Number',
    '订单状态': 'Order Status',
    '订单金额': 'Order Amount',
    '订单日期': 'Order Date',
    '发货': 'Shipment',
    '收货': 'Receipt',
    '物流': 'Logistics',
    '快递': 'Express',
    '运费': 'Shipping Fee',

    # ==================== 审批相关 ====================
    '审批': 'Approval',
    '审批流程': 'Approval Process',
    '审批状态': 'Approval Status',
    '审批人': 'Approver',
    '审批意见': 'Approval Comments',
    '审批通过': 'Approved',
    '审批拒绝': 'Rejected',
    '待审批': 'Pending Approval',
    '已审批': 'Approved',
    '驳回': 'Reject',
    '退回': 'Return',
    '撤回': 'Withdraw',

    # ==================== 报销相关 ====================
    '报销': 'Expense',
    '报销单': 'Expense Report',
    '报销金额': 'Expense Amount',
    '报销类型': 'Expense Type',
    '发票': 'Invoice',
    '发票号': 'Invoice Number',
    '发票金额': 'Invoice Amount',
    '费用': 'Cost',
    '费用类型': 'Cost Type',

    # ==================== 库存相关 ====================
    '库存': 'Inventory',
    '入库': 'Stock In',
    '出库': 'Stock Out',
    '库存数量': 'Stock Quantity',
    '可用库存': 'Available Stock',
    '安全库存': 'Safety Stock',
    '仓库': 'Warehouse',
    '货架': 'Shelf',
    '批次': 'Batch',
    '批号': 'Batch Number',

    # ==================== 系统相关 ====================
    '系统': 'System',
    '系统设置': 'System Settings',
    '系统管理': 'System Management',
    '管理员': 'Administrator',
    '超级管理员': 'Super Admin',
    '普通用户': 'Regular User',
    '登录': 'Login',
    '登出': 'Logout',
    '注册': 'Register',
    '忘记密码': 'Forgot Password',
    '修改密码': 'Change Password',
    '个人信息': 'Personal Information',
    '个人设置': 'Personal Settings',
    '帮助': 'Help',
    '关于': 'About',
    '版权': 'Copyright',
    '隐私': 'Privacy',
    '条款': 'Terms',

    # ==================== 错误提示 ====================
    '操作成功': 'Operation Successful',
    '操作失败': 'Operation Failed',
    '保存成功': 'Saved Successfully',
    '保存失败': 'Save Failed',
    '删除成功': 'Deleted Successfully',
    '删除失败': 'Delete Failed',
    '上传成功': 'Upload Successful',
    '上传失败': 'Upload Failed',
    '下载成功': 'Download Successful',
    '下载失败': 'Download Failed',
    '提交成功': 'Submitted Successfully',
    '提交失败': 'Submit Failed',
    '加载失败': 'Load Failed',
    '请求失败': 'Request Failed',
    '网络错误': 'Network Error',
    '服务器错误': 'Server Error',
    '参数错误': 'Parameter Error',
    '权限不足': 'Insufficient Permissions',
    '登录已过期': 'Session Expired',
    '请重新登录': 'Please log in again',
    '数据不存在': 'Data Not Found',
    '数据已存在': 'Data Already Exists',
    '格式错误': 'Format Error',
    '必填项不能为空': 'Required fields cannot be empty',
    '请稍后重试': 'Please try again later',

    # ==================== 分页 ====================
    '共': 'Total',
    '条': 'items',
    '页': 'pages',
    '第': 'Page',
    '上一页': 'Previous',
    '下一页': 'Next',
    '首页': 'First',
    '末页': 'Last',
    '跳转': 'Go to',
    '每页': 'Per page',
    '显示': 'Show',
    '条记录': 'records',

    # ==================== 其他 ====================
    '返回列表': 'Back to List',
    '返回首页': 'Back to Home',
    '暂无数据': 'No Data',
    '加载更多': 'Load More',
    '正在加载': 'Loading',
    '请稍候': 'Please wait',
    '点击': 'Click',
    '双击': 'Double click',
    '拖拽': 'Drag',
    '复制成功': 'Copied',
    '已复制': 'Copied',
    '或': 'or',
    '和': 'and',
    '的': 'of',
    '个': '',
    '条': 'items',
    '份': 'copies',
    '次': 'times',
    '年': 'year',
    '月': 'month',
    '日': 'day',
    '时': 'hour',
    '分': 'minute',
    '秒': 'second',
}


class TranslationAuditor:
    def __init__(self):
        self.code_strings = set()  # 代码中的翻译字符串
        self.po_entries = {}  # PO文件中的条目 {msgid: msgstr}
        self.po_obsolete = {}  # 废弃的条目
        self.po_file_lines = []  # PO文件原始行

        self.missing = []  # 缺失翻译（代码有，PO无）
        self.unused = []  # 无效翻译（PO有，代码无）
        self.empty = []  # 空翻译（PO有但msgstr为空）
        self.obsolete_in_use = []  # 废弃但仍在使用

    def scan_code(self):
        """扫描代码中所有需要翻译的字符串"""
        print("📂 扫描代码文件...")

        # 匹配 _('...') 和 _("...")
        pattern = re.compile(r"_\(['\"]([^'\"]+)['\"]\)")

        file_count = 0
        for scan_dir in SCAN_DIRS:
            if not os.path.exists(scan_dir):
                continue
            for root, dirs, files in os.walk(scan_dir):
                for filename in files:
                    if filename.endswith(('.html', '.py')):
                        filepath = os.path.join(root, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                matches = pattern.findall(content)
                                self.code_strings.update(matches)
                                file_count += 1
                        except Exception as e:
                            print(f"  ⚠️ 读取文件失败: {filepath}: {e}")

        print(f"  ✅ 扫描了 {file_count} 个文件")
        print(f"  ✅ 发现 {len(self.code_strings)} 个翻译字符串")

    def parse_po_file(self):
        """解析PO翻译文件"""
        print("\n📄 解析翻译文件...")

        if not os.path.exists(PO_FILE):
            print(f"  ❌ 翻译文件不存在: {PO_FILE}")
            return False

        with open(PO_FILE, 'r', encoding='utf-8') as f:
            self.po_file_lines = f.readlines()

        current_msgid = None
        current_msgstr = None
        is_obsolete = False

        i = 0
        while i < len(self.po_file_lines):
            line = self.po_file_lines[i].strip()

            # 检查废弃标记
            if line.startswith('#~ msgid "'):
                is_obsolete = True
                current_msgid = line[10:-1]  # 去掉 #~ msgid " 和 "
                i += 1
                # 读取 msgstr
                if i < len(self.po_file_lines):
                    next_line = self.po_file_lines[i].strip()
                    if next_line.startswith('#~ msgstr "'):
                        current_msgstr = next_line[11:-1]
                        if current_msgid:
                            self.po_obsolete[current_msgid] = current_msgstr
                is_obsolete = False
                current_msgid = None
                current_msgstr = None

            # 活跃条目
            elif line.startswith('msgid "') and not line.startswith('msgid ""'):
                current_msgid = line[7:-1]
                i += 1
                # 读取 msgstr
                if i < len(self.po_file_lines):
                    next_line = self.po_file_lines[i].strip()
                    if next_line.startswith('msgstr "'):
                        current_msgstr = next_line[8:-1]
                        if current_msgid:
                            self.po_entries[current_msgid] = current_msgstr
                current_msgid = None
                current_msgstr = None

            i += 1

        print(f"  ✅ 活跃条目: {len(self.po_entries)} 个")
        print(f"  ✅ 废弃条目: {len(self.po_obsolete)} 个")
        return True

    def analyze(self):
        """分析翻译状态"""
        print("\n🔍 分析翻译状态...")

        # 1. 缺失翻译（代码有，PO无）
        for s in self.code_strings:
            if s not in self.po_entries and s not in self.po_obsolete:
                self.missing.append(s)
            elif s in self.po_obsolete and s not in self.po_entries:
                self.obsolete_in_use.append(s)

        # 2. 无效翻译（PO有，代码无）
        for s in self.po_entries:
            if s not in self.code_strings:
                self.unused.append(s)

        # 3. 空翻译
        for msgid, msgstr in self.po_entries.items():
            if msgid in self.code_strings and not msgstr:
                self.empty.append(msgid)

        self.missing.sort()
        self.unused.sort()
        self.empty.sort()
        self.obsolete_in_use.sort()

    def report(self):
        """生成报告"""
        print("\n" + "=" * 60)
        print("📊 翻译审计报告")
        print("=" * 60)

        print(f"\n代码中翻译字符串: {len(self.code_strings)} 个")
        print(f"翻译文件活跃条目: {len(self.po_entries)} 个")
        print(f"翻译文件废弃条目: {len(self.po_obsolete)} 个")

        print(f"\n❌ 缺失翻译: {len(self.missing)} 个")
        print(f"⚠️ 无效翻译: {len(self.unused)} 个")
        print(f"🔸 空翻译: {len(self.empty)} 个")
        print(f"🔄 废弃但在用: {len(self.obsolete_in_use)} 个")

        # 详细列表
        if self.missing:
            print("\n--- 缺失翻译（需要添加）---")
            for s in self.missing[:30]:
                suggested = self.suggest_translation(s)
                print(f"  {s}")
                if suggested:
                    print(f"    → 建议: {suggested}")
            if len(self.missing) > 30:
                print(f"  ... 还有 {len(self.missing) - 30} 个")

        if self.empty:
            print("\n--- 空翻译（需要填写）---")
            for s in self.empty[:20]:
                suggested = self.suggest_translation(s)
                print(f"  {s}")
                if suggested:
                    print(f"    → 建议: {suggested}")
            if len(self.empty) > 20:
                print(f"  ... 还有 {len(self.empty) - 20} 个")

        if self.obsolete_in_use:
            print("\n--- 废弃但仍在使用（需要恢复）---")
            for s in self.obsolete_in_use[:20]:
                print(f"  {s}")
                print(f"    → 现有翻译: {self.po_obsolete.get(s, '无')}")
            if len(self.obsolete_in_use) > 20:
                print(f"  ... 还有 {len(self.obsolete_in_use) - 20} 个")

        if self.unused:
            print("\n--- 无效翻译（可以删除）---")
            for s in self.unused[:20]:
                print(f"  {s}")
            if len(self.unused) > 20:
                print(f"  ... 还有 {len(self.unused) - 20} 个")

        print("\n" + "=" * 60)

    def suggest_translation(self, chinese_text):
        """基于常用映射和规则生成翻译建议"""
        # 直接匹配
        if chinese_text in COMMON_TRANSLATIONS:
            return COMMON_TRANSLATIONS[chinese_text]

        # 尝试组合匹配
        result = chinese_text
        for cn, en in sorted(COMMON_TRANSLATIONS.items(), key=lambda x: -len(x[0])):
            if cn in result:
                result = result.replace(cn, en)

        # 如果有变化，返回结果
        if result != chinese_text and not any('\u4e00' <= c <= '\u9fff' for c in result):
            return result

        return None

    def fix_translations(self, dry_run=False):
        """修复翻译问题"""
        print("\n🔧 修复翻译问题...")

        if dry_run:
            print("  (试运行模式，不会实际修改文件)")

        additions = []

        # 1. 为缺失的翻译生成条目
        for msgid in self.missing:
            msgstr = self.suggest_translation(msgid) or ''
            additions.append((msgid, msgstr))

        # 2. 为空翻译填充建议
        updates = {}
        for msgid in self.empty:
            suggested = self.suggest_translation(msgid)
            if suggested:
                updates[msgid] = suggested

        # 3. 恢复废弃但在用的翻译
        restorations = []
        for msgid in self.obsolete_in_use:
            msgstr = self.po_obsolete.get(msgid, '')
            restorations.append((msgid, msgstr))

        print(f"\n  将添加 {len(additions)} 个新条目")
        print(f"  将更新 {len(updates)} 个空翻译")
        print(f"  将恢复 {len(restorations)} 个废弃条目")

        if dry_run:
            return

        # 实际修复
        self._apply_fixes(additions, updates, restorations)

    def _apply_fixes(self, additions, updates, restorations):
        """应用修复到PO文件"""
        with open(PO_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 处理废弃条目恢复
            if line.startswith('#~ msgid "'):
                msgid = line[10:-1]
                if msgid in [r[0] for r in restorations]:
                    # 跳过废弃的 msgid 和 msgstr 行
                    i += 1
                    if i < len(lines) and lines[i].startswith('#~ msgstr'):
                        i += 1
                    continue

            # 处理空翻译更新
            if line.startswith('msgid "') and not line.startswith('msgid ""'):
                msgid = line[7:-1]
                new_lines.append(line)
                i += 1
                if i < len(lines) and lines[i].startswith('msgstr "'):
                    if msgid in updates:
                        new_lines.append(f'msgstr "{updates[msgid]}"')
                    else:
                        new_lines.append(lines[i])
                    i += 1
                continue

            new_lines.append(line)
            i += 1

        # 添加新条目
        if additions or restorations:
            # 在文件末尾添加新条目
            new_lines.append('')
            new_lines.append(f'# ===== 自动添加 ({datetime.now().strftime("%Y-%m-%d %H:%M")}) =====')

            for msgid, msgstr in additions:
                new_lines.append('')
                new_lines.append(f'msgid "{msgid}"')
                new_lines.append(f'msgstr "{msgstr}"')

            for msgid, msgstr in restorations:
                new_lines.append('')
                new_lines.append(f'# 从废弃条目恢复')
                new_lines.append(f'msgid "{msgid}"')
                new_lines.append(f'msgstr "{msgstr}"')

        # 写入文件
        with open(PO_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print(f"\n  ✅ 已更新翻译文件: {PO_FILE}")

    def clean_obsolete(self, dry_run=False):
        """清理废弃条目"""
        print("\n🧹 清理废弃条目...")

        # 找出真正不再使用的废弃条目
        truly_obsolete = []
        for msgid in self.po_obsolete:
            if msgid not in self.code_strings:
                truly_obsolete.append(msgid)

        print(f"  废弃且不再使用: {len(truly_obsolete)} 个")
        print(f"  废弃但仍在使用: {len(self.obsolete_in_use)} 个（将保留）")

        if dry_run:
            print("  (试运行模式，不会实际修改文件)")
            return

        # 从文件中移除废弃条目
        with open(PO_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        i = 0
        removed = 0

        while i < len(lines):
            line = lines[i]

            # 检测废弃条目
            if line.startswith('#~ msgid "'):
                msgid = line[10:-1].strip('"')
                if msgid in truly_obsolete:
                    # 跳过这个废弃条目（msgid + msgstr）
                    i += 1
                    while i < len(lines) and lines[i].startswith('#~'):
                        i += 1
                    removed += 1
                    continue

            new_lines.append(line)
            i += 1

        # 写入文件
        with open(PO_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"  ✅ 已移除 {removed} 个废弃条目")

    def compile_translations(self):
        """编译翻译文件"""
        print("\n📦 编译翻译文件...")
        import subprocess
        result = subprocess.run(
            ['pybabel', 'compile', '-d', os.path.join(PROJECT_ROOT, 'app/translations')],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            print("  ✅ 编译成功")
        else:
            print(f"  ❌ 编译失败: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description='翻译审计和修复工具')
    parser.add_argument('--fix', action='store_true', help='修复缺失和空翻译')
    parser.add_argument('--clean', action='store_true', help='清理废弃条目')
    parser.add_argument('--full', action='store_true', help='完整修复（检查+修复+清理+编译）')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际修改文件')
    parser.add_argument('--compile', action='store_true', help='编译翻译文件')
    args = parser.parse_args()

    print("=" * 60)
    print("🌍 PMA 翻译审计工具")
    print("=" * 60)

    auditor = TranslationAuditor()

    # 扫描和分析
    auditor.scan_code()
    if not auditor.parse_po_file():
        return 1
    auditor.analyze()
    auditor.report()

    # 执行修复
    if args.full:
        auditor.fix_translations(dry_run=args.dry_run)
        auditor.clean_obsolete(dry_run=args.dry_run)
        if not args.dry_run:
            auditor.compile_translations()
    else:
        if args.fix:
            auditor.fix_translations(dry_run=args.dry_run)
        if args.clean:
            auditor.clean_obsolete(dry_run=args.dry_run)
        if args.compile and not args.dry_run:
            auditor.compile_translations()

    print("\n✅ 完成")
    return 0


if __name__ == '__main__':
    sys.exit(main())
