#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA系统截图工具 v3
按模块截取所有TW风格页面、模态框、详情页
支持数据脱敏和演示数据填充
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())


class PMAScreenshotTool:
    """PMA系统截图工具"""

    def __init__(self, base_url: str = "http://localhost:5011"):
        self.base_url = base_url
        self.browser: Browser = None
        self.page: Page = None
        self.output_dir = None
        self.screenshot_count = 0

    async def init(self):
        """初始化浏览器"""
        today = datetime.now().strftime('%Y%m%d')
        self.output_dir = os.path.join(
            get_project_root(),
            'docs', 'screenshots', f'pma_screenshots_{today}'
        )
        os.makedirs(self.output_dir, exist_ok=True)

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page(viewport={'width': 1920, 'height': 1080})

        print(f"浏览器已启动")
        print(f"截图保存目录: {self.output_dir}")

    async def login(self, username: str = "admin", password: str = "1505562299AaBb"):
        """登录系统"""
        await self.page.goto(f"{self.base_url}/auth/login")
        await self.page.fill('input[name="username"]', username)
        await self.page.fill('input[name="password"]', password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        print("登录成功")

    async def screenshot(self, name: str, module: str = ""):
        """截图并保存"""
        await asyncio.sleep(0.5)

        if module:
            filename = f"{module}_{name}.png"
        else:
            filename = f"{name}.png"

        filepath = os.path.join(self.output_dir, filename)
        await self.page.screenshot(path=filepath, full_page=False)

        self.screenshot_count += 1
        print(f"  [{self.screenshot_count}] {filename}")
        return filepath

    async def goto(self, path: str):
        """访问页面"""
        url = f"{self.base_url}{path}"
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=15000)
        except:
            # 如果超时，尝试只等待DOM加载完成
            await self.page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(0.8)

    async def mask_sensitive_data(self):
        """数据脱敏 - 替换页面上的敏感信息为演示数据"""
        await self.page.evaluate('''() => {
            // 演示公司名称
            const demoCompanies = ['示例科技有限公司', '测试贸易公司', '演示电子有限公司', '样本机械制造厂', '示范工业集团'];
            // 演示项目名称
            const demoProjects = ['示例项目A', '测试项目B', '演示项目C', '样本项目D', '创新项目E'];
            // 演示人名
            const demoNames = ['张三', '李四', '王五', '赵六', '陈七', '周八', '吴九', '郑十'];

            // 替换表格中的公司名称链接
            document.querySelectorAll('a[href*="/customer/"], a[href*="/company/"]').forEach((el, idx) => {
                if (el.textContent && el.textContent.length > 2 && !el.textContent.includes('管理') && !el.textContent.includes('添加')) {
                    el.textContent = demoCompanies[idx % demoCompanies.length];
                }
            });

            // 替换项目名称链接
            document.querySelectorAll('a[href*="/project/"]').forEach((el, idx) => {
                if (el.textContent && el.textContent.length > 2 && !el.textContent.includes('管理') && !el.textContent.includes('创建')) {
                    el.textContent = demoProjects[idx % demoProjects.length];
                }
            });

            // 替换报销单编号
            document.querySelectorAll('a[href*="/expense/"]').forEach((el, idx) => {
                if (el.textContent && el.textContent.match(/^BX\\d+/)) {
                    el.textContent = 'BX202512' + String(idx + 1).padStart(4, '0');
                }
            });

            // 替换报价单编号
            document.querySelectorAll('a[href*="/quotation/"]').forEach((el, idx) => {
                if (el.textContent && el.textContent.match(/^QU\\d+/)) {
                    el.textContent = 'QU202512-' + String(idx + 1).padStart(3, '0');
                }
            });
        }''')

    async def fill_demo_form_data(self, form_type: str):
        """填充演示表单数据"""
        if form_type == 'customer':
            await self.page.fill('input[name="company_name"], #company_name', '演示科技有限公司')
        elif form_type == 'project':
            await self.page.fill('input[name="project_name"], #project_name', '演示项目-2025')
        elif form_type == 'contact':
            await self.page.fill('input[name="name"], #name', '张经理')
            try:
                await self.page.fill('input[name="position"], #position', '销售总监')
                await self.page.fill('input[name="phone"], #phone', '138****8888')
                await self.page.fill('input[name="email"], #email', 'demo@example.com')
            except:
                pass
        elif form_type == 'action':
            try:
                await self.page.fill('textarea[name="content"], #content, textarea', '与客户进行了电话沟通，讨论了合作方案')
            except:
                pass

    async def close_modal(self):
        """关闭模态框"""
        # 首先尝试按ESC键 (TW模态框通过ESC关闭)
        await self.page.keyboard.press('Escape')
        await asyncio.sleep(0.3)

        # 如果模态框仍然打开，点击关闭按钮
        modal = await self.page.query_selector('[role="dialog"]:not(.hidden)')
        if modal:
            close_selectors = [
                'button[onclick*="closeFormModal"]',
                'button[onclick*="close"]',
                '[data-action="close"]',
            ]

            for selector in close_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn and await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(0.3)
                        return True
                except:
                    continue

        return True

    async def wait_for_modal(self):
        """等待模态框出现"""
        await asyncio.sleep(0.5)  # 等待动画完成

        # 检查 TW form modal (role="dialog" + 没有hidden类)
        try:
            modal = await self.page.query_selector('[role="dialog"]:not(.hidden)')
            if modal and await modal.is_visible():
                return True
        except:
            pass

        # 检查 Alpine.js action modal - 精确ID匹配
        try:
            modal = await self.page.query_selector('#addActionModal')
            if modal and await modal.is_visible():
                return True
        except:
            pass

        # 检查 Alpine.js action modal (id包含ActionModal且可见) - 宽松匹配
        try:
            modal = await self.page.query_selector('[id*="ActionModal"]')
            if modal and await modal.is_visible():
                return True
        except:
            pass

        # 检查任何可见的固定层z-50模态框
        try:
            modals = await self.page.query_selector_all('.fixed.inset-0.z-50')
            for modal in modals:
                if await modal.is_visible():
                    return True
        except:
            pass

        return False

    # ==================== 仪表盘模块 ====================
    async def capture_dashboard(self):
        """截取仪表盘"""
        print("\n[仪表盘模块]")
        await self.goto("/?lang=zh")
        await self.mask_sensitive_data()
        await self.screenshot("dashboard_main", "01_dashboard")

    # ==================== 客户模块 ====================
    async def capture_customer_module(self):
        """截取客户模块 - TW风格"""
        print("\n[客户模块]")

        # 1. 客户列表页 (TW风格)
        await self.goto("/customer/?lang=zh")
        await self.mask_sensitive_data()
        await self.screenshot("list", "02_customer")

        # 2. 添加客户模态框
        add_btn = await self.page.query_selector('button[onclick*="openAddCustomerModal"]')
        if add_btn:
            await add_btn.click()
            if await self.wait_for_modal():
                await self.fill_demo_form_data('customer')
                await self.screenshot("add_modal", "02_customer")
                await self.close_modal()

        # 3. 获取客户ID用于后续截图
        await self.goto("/customer/?lang=zh")
        detail_link = await self.page.query_selector('a[href*="/customer/"][href*="/view"]')
        customer_id = None
        if detail_link:
            href = await detail_link.get_attribute('href')
            match = re.search(r'/customer/(\d+)/view', href)
            if match:
                customer_id = match.group(1)

        if customer_id:
            # 4. 客户详情页 (TW风格)
            await self.goto(f"/customer/{customer_id}/view?lang=zh")
            await self.mask_sensitive_data()
            await self.screenshot("detail", "02_customer")

            # 5. 编辑客户模态框 - 使用onclick选择器
            try:
                edit_btn = await self.page.query_selector('button[onclick*="openCustomerEditModal"]')
                if edit_btn and await edit_btn.is_visible():
                    await edit_btn.click()
                    if await self.wait_for_modal():
                        await self.screenshot("edit_modal", "02_customer")
                        await self.close_modal()
                else:
                    print("    未找到编辑客户按钮")
            except Exception as e:
                print(f"    编辑客户模态框截图失败: {e}")

            # 6. 添加行动记录模态框 - 使用onclick选择器
            try:
                await self.goto(f"/customer/{customer_id}/view?lang=zh")
                # 滚动到页面底部，因为行动记录区域在下方
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(0.5)

                action_btn = await self.page.query_selector('button[onclick*="openAddActionModal"]')
                if action_btn:
                    await action_btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    if await action_btn.is_visible():
                        await action_btn.click()
                        if await self.wait_for_modal():
                            await self.fill_demo_form_data('action')
                            await self.screenshot("add_action_modal", "02_customer")
                            await self.close_modal()
                else:
                    print("    未找到添加行动记录按钮")
            except Exception as e:
                print(f"    添加行动记录模态框截图失败: {e}")

            # 7. 查找联系人 - 使用正确的URL格式 /customer/contacts/{id}/view
            await self.goto(f"/customer/{customer_id}/view?lang=zh")
            contact_links = await self.page.query_selector_all('a[href*="/contacts/"][href*="/view"]')
            contact_id = None
            for link in contact_links:
                href = await link.get_attribute('href')
                if href and '/contacts/' in href and '/view' in href:
                    match = re.search(r'/contacts/(\d+)/view', href)
                    if match:
                        contact_id = match.group(1)
                        break

            # 8. 添加联系人模态框 - 使用正确的onclick
            try:
                add_contact_btn = await self.page.query_selector('button[onclick*="openAddContactModal"]')
                if add_contact_btn and await add_contact_btn.is_visible():
                    await add_contact_btn.click()
                    if await self.wait_for_modal():
                        await self.fill_demo_form_data('contact')
                        await self.screenshot("add_contact_modal", "02_customer")
                        await self.close_modal()
                else:
                    print("    未找到添加联系人按钮")
            except Exception as e:
                print(f"    添加联系人模态框截图失败: {e}")

            if contact_id:
                # 9. 联系人详情页 (TW风格) - 正确的URL: /customer/contacts/{id}/view
                try:
                    await self.goto(f"/customer/contacts/{contact_id}/view?lang=zh")
                    await self.mask_sensitive_data()
                    await self.screenshot("contact_detail", "02_customer")

                    # 10. 编辑联系人模态框 - 使用正确的onclick: openEditContactModal
                    edit_contact_btn = await self.page.query_selector('button[onclick*="openEditContactModal"]')
                    if edit_contact_btn and await edit_contact_btn.is_visible():
                        await edit_contact_btn.click()
                        if await self.wait_for_modal():
                            await self.screenshot("contact_edit_modal", "02_customer")
                            await self.close_modal()
                    else:
                        print("    未找到编辑联系人按钮")

                    # 11. 联系人行动记录模态框 - 使用正确的onclick: openAddActionModal
                    await self.goto(f"/customer/contacts/{contact_id}/view?lang=zh")
                    # 滚动到页面底部
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(0.5)

                    action_btn = await self.page.query_selector('button[onclick*="openAddActionModal"]')
                    if action_btn:
                        await action_btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        if await action_btn.is_visible():
                            await action_btn.click()
                            if await self.wait_for_modal():
                                await self.fill_demo_form_data('action')
                                await self.screenshot("contact_add_action_modal", "02_customer")
                                await self.close_modal()
                    else:
                        print("    未找到联系人添加行动记录按钮")
                except Exception as e:
                    print(f"    联系人截图失败: {e}")

    # ==================== 项目模块 ====================
    async def capture_project_module(self):
        """截取项目模块 - TW风格"""
        print("\n[项目模块]")

        # 1. 项目列表页 (TW风格)
        await self.goto("/project/?lang=zh")
        await self.mask_sensitive_data()
        await self.screenshot("list", "03_project")

        # 2. 创建项目模态框
        create_btn = await self.page.query_selector('button[onclick*="openProjectCreateModal"]')
        if create_btn:
            await create_btn.click()
            if await self.wait_for_modal():
                await self.fill_demo_form_data('project')
                await self.screenshot("create_modal", "03_project")
                await self.close_modal()

        # 3. 获取多个项目ID，找一个有编辑按钮的
        await self.goto("/project/?lang=zh")
        detail_links = await self.page.query_selector_all('a[href*="/project/view/"]')
        project_ids = []
        for link in detail_links[:5]:  # 最多尝试5个项目
            href = await link.get_attribute('href')
            match = re.search(r'/project/view/(\d+)', href)
            if match:
                project_ids.append(match.group(1))

        detail_captured = False
        edit_captured = False
        action_captured = False

        for project_id in project_ids:
            await self.goto(f"/project/view/{project_id}?tw=1&lang=zh")
            await self.mask_sensitive_data()

            # 4. 项目详情页 (TW风格) - 只截一次
            if not detail_captured:
                await self.screenshot("detail", "03_project")
                detail_captured = True

            # 5. 编辑项目模态框
            if not edit_captured:
                try:
                    edit_btn = await self.page.query_selector('button[onclick*="openProjectEditModal"]')
                    if edit_btn and await edit_btn.is_visible():
                        await edit_btn.click()
                        if await self.wait_for_modal():
                            await self.screenshot("edit_modal", "03_project")
                            await self.close_modal()
                            edit_captured = True
                except Exception as e:
                    print(f"    项目{project_id}编辑模态框失败: {e}")

            # 6. 添加行动记录模态框
            if not action_captured:
                try:
                    await self.goto(f"/project/view/{project_id}?tw=1&lang=zh")
                    await asyncio.sleep(1)  # 等待页面完全加载包括JS

                    action_btn = await self.page.query_selector('button[onclick*="openAddActionModal"]')
                    if action_btn:
                        await action_btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        if await action_btn.is_visible():
                            await action_btn.click()
                            await asyncio.sleep(0.5)
                            if await self.wait_for_modal():
                                await self.fill_demo_form_data('action')
                                await self.screenshot("add_action_modal", "03_project")
                                await self.close_modal()
                                action_captured = True
                except Exception as e:
                    print(f"    项目{project_id}行动记录模态框失败: {e}")

            # 如果都截完了就退出循环
            if edit_captured and action_captured:
                break

        if not edit_captured:
            print("    未找到可编辑的项目")
        if not action_captured:
            print("    未找到可添加行动记录的项目")

    # ==================== 报价单模块 ====================
    async def capture_quotation_module(self):
        """截取报价单模块 - TW风格，包含产品配置流程"""
        print("\n[报价单模块]")

        # 1. 报价单列表页 (TW风格)
        await self.goto("/quotation/quotations?lang=zh")
        await self.mask_sensitive_data()
        await self.screenshot("list", "04_quotation")

        # 2. 报价单创建模态框 - 点击列表页的"创建报价单"按钮
        try:
            # 找到并点击"创建报价单"按钮
            create_btn = await self.page.query_selector('button:has-text("创建报价单"), button:has-text("New Quotation"), button:has-text("新建报价单")')
            if create_btn and await create_btn.is_visible():
                await create_btn.click()
                await asyncio.sleep(1)  # 等待模态框加载

                # 等待模态框出现
                if await self.wait_for_modal():
                    await self.screenshot("create_modal", "04_quotation")
                    await self.close_modal()
                else:
                    print("    创建模态框未出现")
            else:
                print("    未找到创建报价单按钮")
        except Exception as e:
            print(f"    创建模态框截图失败: {e}")

        # 5. 获取有父子关系明细的报价单ID
        await self.goto("/quotation/quotations?lang=zh")
        detail_links = await self.page.query_selector_all('a[href*="/quotation/"][href*="/detail"]')
        quotation_id = None

        for link in detail_links[:5]:
            href = await link.get_attribute('href')
            match = re.search(r'/quotation/(\d+)/detail', href)
            if match:
                quotation_id = match.group(1)
                break

        if quotation_id:
            # 6. 报价单详情页 (TW风格) - 展示父子关系明细
            await self.goto(f"/quotation/{quotation_id}/detail?tw=1&lang=zh")
            await self.mask_sensitive_data()
            await asyncio.sleep(0.5)

            # 截取详情页
            await self.screenshot("detail", "04_quotation")

            # 滚动到产品明细区域
            await self.page.evaluate('window.scrollTo(0, 400)')
            await asyncio.sleep(0.3)
            await self.screenshot("detail_products", "04_quotation")

            # 7. 编辑页面 - TW版重定向到detail页面的edit模式
            await self.goto(f"/quotation/{quotation_id}/edit?lang=zh")
            await self.mask_sensitive_data()
            await asyncio.sleep(1)
            # 检查是否有编辑按钮或产品配置按钮
            await self.screenshot("edit_view", "04_quotation")

    # ==================== 报销单模块 ====================
    async def capture_expense_module(self):
        """截取报销单模块 - TW风格，使用模态框"""
        print("\n[报销单模块]")

        # 1. 报销单列表页 (TW风格)
        await self.goto("/expense/?lang=zh")
        await self.mask_sensitive_data()
        await self.screenshot("list", "05_expense")

        # 2. 新建报销单模态框 - 点击列表页的"新建报销单"按钮
        try:
            # 找到并点击"新建报销单"按钮
            add_btn = await self.page.query_selector('button:has-text("新建报销单"), button:has-text("New Expense")')
            if add_btn and await add_btn.is_visible():
                await add_btn.click()
                await asyncio.sleep(0.8)

                # 等待模态框出现
                if await self.wait_for_modal():
                    await self.screenshot("create_modal", "05_expense")
                    await self.close_modal()
                else:
                    print("    创建模态框未出现")
            else:
                print("    未找到新建报销单按钮")
        except Exception as e:
            print(f"    创建模态框截图失败: {e}")

        # 3. 获取报销单ID（找草稿状态的）
        await self.goto("/expense/?lang=zh")
        await asyncio.sleep(0.5)
        detail_links = await self.page.query_selector_all('a[href*="/expense/"][class*="text-blue"]')
        expense_id = None
        for link in detail_links:
            href = await link.get_attribute('href')
            if href:
                match = re.search(r'/expense/(\d+)$', href)
                if match:
                    expense_id = match.group(1)
                    break

        if expense_id:
            # 4. 报销单详情页 (TW风格)
            await self.goto(f"/expense/{expense_id}?lang=zh")
            await self.mask_sensitive_data()
            await asyncio.sleep(0.5)
            await self.screenshot("detail", "05_expense")

            # 5. 编辑模态框 - 点击详情页的"编辑"按钮
            try:
                edit_btn = await self.page.query_selector('button:has-text("编辑"), [onclick*="openEditExpenseModal"]')
                if edit_btn and await edit_btn.is_visible():
                    await edit_btn.click()
                    await asyncio.sleep(0.8)

                    if await self.wait_for_modal():
                        await self.screenshot("edit_modal", "05_expense")
                        await self.close_modal()
                    else:
                        print("    编辑模态框未出现")
                else:
                    print("    未找到编辑按钮（可能状态不允许编辑）")
            except Exception as e:
                print(f"    编辑模态框截图失败: {e}")

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("\n浏览器已关闭")

    async def run(self):
        """运行截图任务"""
        print("=" * 60)
        print("PMA系统截图工具 v3 - TW风格版")
        print("=" * 60)

        try:
            await self.init()
            await self.login()

            await self.capture_dashboard()
            await self.capture_customer_module()
            await self.capture_project_module()
            await self.capture_quotation_module()
            await self.capture_expense_module()

        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()

        print("\n" + "=" * 60)
        print(f"截图完成！共 {self.screenshot_count} 张")
        print(f"保存目录: {self.output_dir}")
        print("=" * 60)


async def main():
    tool = PMAScreenshotTool()
    await tool.run()


if __name__ == '__main__':
    asyncio.run(main())
