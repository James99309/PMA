#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA 页面截图工具
用于自动登录并截取指定页面，生成教程截图
支持数据脱敏（马赛克/模糊/替换）保护隐私
"""
import os
import sys
import asyncio
import re
from datetime import datetime
from typing import Optional, List, Dict
from PIL import Image, ImageFilter, ImageDraw

# 路径修正
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

from playwright.async_api import async_playwright, Page, Browser

class DataMasker:
    """数据脱敏处理器"""

    # 虚假数据用于替换真实信息
    FAKE_NAMES = ["张三", "李四", "王五", "赵六", "陈七", "周八", "吴九", "郑十"]
    FAKE_COMPANIES = ["示例科技有限公司", "测试贸易公司", "演示电子有限公司", "样本机械制造厂"]
    FAKE_PHONES = ["138****1234", "139****5678", "136****9012", "137****3456"]
    FAKE_EMAILS = ["demo@example.com", "test@sample.com", "user@demo.cn"]

    @staticmethod
    def blur_region(image_path: str, regions: List[Dict], blur_radius: int = 15) -> str:
        """
        对图片的指定区域进行高斯模糊

        Args:
            image_path: 图片路径
            regions: 需要模糊的区域列表 [{'x': 100, 'y': 200, 'width': 300, 'height': 50}, ...]
            blur_radius: 模糊半径

        Returns:
            处理后的图片路径
        """
        img = Image.open(image_path)

        for region in regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']

            # 裁剪区域
            box = (x, y, x + w, y + h)
            region_img = img.crop(box)

            # 应用高斯模糊
            blurred = region_img.filter(ImageFilter.GaussianBlur(blur_radius))

            # 粘贴回原图
            img.paste(blurred, box)

        # 保存
        img.save(image_path)
        return image_path

    @staticmethod
    def mosaic_region(image_path: str, regions: List[Dict], block_size: int = 10) -> str:
        """
        对图片的指定区域进行马赛克处理

        Args:
            image_path: 图片路径
            regions: 需要马赛克的区域列表
            block_size: 马赛克块大小

        Returns:
            处理后的图片路径
        """
        img = Image.open(image_path)

        for region in regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']

            # 裁剪区域
            box = (x, y, x + w, y + h)
            region_img = img.crop(box)

            # 缩小再放大实现马赛克效果
            small = region_img.resize(
                (max(1, w // block_size), max(1, h // block_size)),
                Image.Resampling.BILINEAR
            )
            mosaic = small.resize((w, h), Image.Resampling.NEAREST)

            # 粘贴回原图
            img.paste(mosaic, box)

        img.save(image_path)
        return image_path

    @staticmethod
    def redact_region(image_path: str, regions: List[Dict], color: str = "#000000") -> str:
        """
        对图片的指定区域进行涂黑/遮盖

        Args:
            image_path: 图片路径
            regions: 需要遮盖的区域列表
            color: 遮盖颜色

        Returns:
            处理后的图片路径
        """
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        for region in regions:
            x, y = region['x'], region['y']
            w, h = region['width'], region['height']
            draw.rectangle([x, y, x + w, y + h], fill=color)

        img.save(image_path)
        return image_path

    @staticmethod
    def get_replace_script() -> str:
        """
        获取页面数据替换的 JavaScript 脚本
        用于在截图前替换页面中的敏感信息
        """
        return r"""
        (function() {
            // 虚假数据
            const fakeCompanies = ["示例科技有限公司", "测试贸易公司", "演示电子有限公司", "样本机械制造厂", "示范工业集团", "创新软件公司", "未来科技集团", "智慧数据公司"];
            const fakeNames = ["张三", "李四", "王五", "赵六", "陈七", "周八", "吴九", "郑十"];
            const fakePhones = ["138****1234", "139****5678", "136****9012", "137****3456"];
            const fakeEmails = ["demo@example.com", "test@sample.com", "user@demo.cn"];
            const fakeAddresses = ["北京市朝阳区示例路100号", "上海市浦东新区测试大道200号", "广州市天河区演示街300号"];
            const fakeProjects = ["示例项目A", "测试项目B", "演示项目C", "样本项目D", "创新项目E"];
            const fakeExpenseDesc = ["差旅费报销", "办公用品采购", "客户招待费", "交通费报销", "通讯费报销"];

            let companyIndex = 0, nameIndex = 0, phoneIndex = 0, emailIndex = 0, addressIndex = 0, projectIndex = 0, expenseIndex = 0;

            // 手机号正则
            const phoneRegex = /1[3-9]\d{9}/g;
            // 邮箱正则
            const emailRegex = /[\w.-]+@[\w.-]+\.\w+/g;

            // ==================== Tailwind 表格数据替换 ====================

            // 获取表头索引
            function getColumnIndex(headerText) {
                const headers = document.querySelectorAll('table thead th');
                for (let i = 0; i < headers.length; i++) {
                    const text = headers[i].textContent.trim().toLowerCase();
                    if (headerText.some(h => text.includes(h))) {
                        return i;
                    }
                }
                return -1;
            }

            // 根据表头替换对应列的数据
            function replaceColumnByHeader() {
                const clientColIndex = getColumnIndex(['客户', 'client', '公司', 'company']);
                const contactColIndex = getColumnIndex(['联系人', 'contact', '对接人']);
                const projectColIndex = getColumnIndex(['项目', 'project', '关联项目', 'related project']);

                document.querySelectorAll('table tbody tr').forEach((row, rowIndex) => {
                    const cells = row.querySelectorAll('td');

                    // 替换客户/公司列
                    if (clientColIndex >= 0 && cells[clientColIndex]) {
                        const cell = cells[clientColIndex];
                        const textEl = cell.querySelector('a, span, p') || cell;
                        if (textEl.textContent.trim() && textEl.textContent.trim() !== '-') {
                            textEl.textContent = fakeCompanies[rowIndex % fakeCompanies.length];
                        }
                    }

                    // 替换联系人列
                    if (contactColIndex >= 0 && cells[contactColIndex]) {
                        const cell = cells[contactColIndex];
                        const textEl = cell.querySelector('a, span, p') || cell;
                        if (textEl.textContent.trim() && textEl.textContent.trim() !== '-') {
                            textEl.textContent = fakeNames[rowIndex % fakeNames.length];
                        }
                    }

                    // 替换关联项目列
                    if (projectColIndex >= 0 && cells[projectColIndex]) {
                        const cell = cells[projectColIndex];
                        const textEl = cell.querySelector('a, span, p') || cell;
                        if (textEl.textContent.trim() && textEl.textContent.trim() !== '-') {
                            textEl.textContent = fakeProjects[rowIndex % fakeProjects.length];
                        }
                    }
                });
            }

            // 执行表头匹配替换
            replaceColumnByHeader();

            // 1. 替换表格中第二列的链接（通常是名称列：公司名、项目名等）
            document.querySelectorAll('table tbody tr').forEach((row, rowIndex) => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    // 第二列通常是名称（公司名/项目名）
                    const nameCell = cells[1];
                    const link = nameCell.querySelector('a');
                    if (link) {
                        const href = link.getAttribute('href') || '';
                        if (href.includes('/customer/') || href.includes('/company/')) {
                            link.textContent = fakeCompanies[rowIndex % fakeCompanies.length];
                            link.setAttribute('title', fakeCompanies[rowIndex % fakeCompanies.length]);
                        } else if (href.includes('/project/')) {
                            link.textContent = fakeProjects[rowIndex % fakeProjects.length];
                            link.setAttribute('title', fakeProjects[rowIndex % fakeProjects.length]);
                        } else if (href.includes('/expense/')) {
                            // 报销单号不需要脱敏
                        } else if (href.includes('/quotation/')) {
                            link.textContent = fakeCompanies[rowIndex % fakeCompanies.length];
                        }
                    }
                }
            });

            // 2. 替换表格中的 blue 链接（主链接，通常是名称）
            document.querySelectorAll('td a.text-blue-600, td a.text-blue-400').forEach((link, i) => {
                const href = link.getAttribute('href') || '';
                if (href.includes('/customer/') || href.includes('/company/')) {
                    link.textContent = fakeCompanies[i % fakeCompanies.length];
                    link.setAttribute('title', fakeCompanies[i % fakeCompanies.length]);
                } else if (href.includes('/project/')) {
                    link.textContent = fakeProjects[i % fakeProjects.length];
                    link.setAttribute('title', fakeProjects[i % fakeProjects.length]);
                }
            });

            // 3. 替换详情页中的数据
            function replaceDetailPageData() {
                // 查找 dt/dd 结构
                document.querySelectorAll('dl').forEach(dl => {
                    const dts = dl.querySelectorAll('dt');
                    const dds = dl.querySelectorAll('dd');

                    dts.forEach((dt, i) => {
                        const label = dt.textContent.trim().toLowerCase();
                        const dd = dds[i];
                        if (!dd) return;

                        if (label.includes('公司') || label.includes('客户') || label.includes('company') || label.includes('customer')) {
                            dd.textContent = fakeCompanies[companyIndex++ % fakeCompanies.length];
                        } else if (label.includes('联系人') || label.includes('姓名') || label.includes('contact') || label.includes('name')) {
                            dd.textContent = fakeNames[nameIndex++ % fakeNames.length];
                        } else if (label.includes('电话') || label.includes('手机') || label.includes('phone') || label.includes('mobile')) {
                            dd.textContent = fakePhones[phoneIndex++ % fakePhones.length];
                        } else if (label.includes('邮箱') || label.includes('email')) {
                            dd.textContent = fakeEmails[emailIndex++ % fakeEmails.length];
                        } else if (label.includes('地址') || label.includes('address')) {
                            dd.textContent = fakeAddresses[addressIndex++ % fakeAddresses.length];
                        }
                    });
                });

                // Tailwind 卡片式详情
                document.querySelectorAll('[class*="grid"] > div').forEach(item => {
                    const label = item.querySelector('span, label, p.text-gray, p.text-slate');
                    const value = item.querySelector('p:not(.text-gray):not(.text-slate), span.font-medium, div.font-medium');

                    if (!label || !value) return;
                    const labelText = label.textContent.trim().toLowerCase();

                    if (labelText.includes('公司') || labelText.includes('客户')) {
                        value.textContent = fakeCompanies[companyIndex++ % fakeCompanies.length];
                    } else if (labelText.includes('联系人') || labelText.includes('姓名')) {
                        value.textContent = fakeNames[nameIndex++ % fakeNames.length];
                    } else if (labelText.includes('电话') || labelText.includes('手机')) {
                        value.textContent = fakePhones[phoneIndex++ % fakePhones.length];
                    } else if (labelText.includes('邮箱')) {
                        value.textContent = fakeEmails[emailIndex++ % fakeEmails.length];
                    }
                });
            }

            // 4. 全局文本替换（手机号、邮箱）
            function walkTextNodes(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    let text = node.textContent;
                    let changed = false;

                    // 替换手机号
                    if (phoneRegex.test(text)) {
                        text = text.replace(phoneRegex, () => {
                            return fakePhones[phoneIndex++ % fakePhones.length];
                        });
                        changed = true;
                    }

                    // 替换邮箱
                    if (emailRegex.test(text)) {
                        text = text.replace(emailRegex, () => {
                            return fakeEmails[emailIndex++ % fakeEmails.length];
                        });
                        changed = true;
                    }

                    if (changed) {
                        node.textContent = text;
                    }
                } else if (node.nodeType === Node.ELEMENT_NODE &&
                           !['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(node.tagName)) {
                    for (let child of node.childNodes) {
                        walkTextNodes(child);
                    }
                }
            }

            // 执行替换
            replaceDetailPageData();
            walkTextNodes(document.body);

            console.log('数据脱敏完成');
        })();
        """


class ScreenshotTool:
    """页面截图工具"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:5000",
        username: str = "",
        password: str = "",
        output_dir: str = "docs/screenshots",
        headless: bool = False,  # 默认显示浏览器，方便调试
        language: str = "zh",  # zh 或 en
        mask_data: bool = True  # 是否脱敏数据
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.output_dir = os.path.join(PROJECT_ROOT, output_dir)
        self.headless = headless
        self.language = language
        self.mask_data = mask_data
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.masker = DataMasker()

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    async def start(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--window-size=1920,1080']
        )
        self.page = await self.browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN' if self.language == 'zh' else 'en-US'
        )
        print(f"浏览器已启动 (headless={self.headless})")

    async def login(self) -> bool:
        """登录系统"""
        if not self.username or not self.password:
            print("警告: 未提供登录凭据，跳过登录")
            return False

        try:
            # 访问登录页面
            login_url = f"{self.base_url}/auth/login"
            await self.page.goto(login_url, wait_until='networkidle')
            print(f"访问登录页面: {login_url}")

            # 填写登录表单
            await self.page.fill('input[name="username"], input[name="email"], #username, #email', self.username)
            await self.page.fill('input[name="password"], #password', self.password)

            # 点击登录按钮
            await self.page.click('button[type="submit"], input[type="submit"], .btn-primary:has-text("登录"), .btn-primary:has-text("Login")')

            # 等待页面跳转
            await self.page.wait_for_load_state('networkidle')

            # 检查是否登录成功（不在登录页面）
            if '/auth/login' not in self.page.url:
                print(f"登录成功! 当前页面: {self.page.url}")

                # 切换语言
                await self.switch_language()

                return True
            else:
                print("登录失败，请检查用户名和密码")
                return False

        except Exception as e:
            print(f"登录过程出错: {e}")
            return False

    async def switch_language(self):
        """切换界面语言"""
        try:
            target_lang = 'zh' if self.language == 'zh' else 'en'

            # 通过 POST 请求切换语言
            switch_script = f"""
            (async () => {{
                const response = await fetch('/language/switch', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ language: '{target_lang}' }})
                }});
                return await response.json();
            }})()
            """

            result = await self.page.evaluate(switch_script)
            print(f"已切换语言到: {'中文' if target_lang == 'zh' else 'English'}")

            # 刷新页面使语言生效
            await self.page.reload(wait_until='networkidle')
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"切换语言时出错: {e}")

    async def screenshot(
        self,
        path: str,
        filename: str,
        wait_for: Optional[str] = None,
        wait_time: int = 1000,
        full_page: bool = False,
        clip: Optional[Dict] = None,
        actions: Optional[List[Dict]] = None,
        mask_data: Optional[bool] = None,
        blur_regions: Optional[List[Dict]] = None,
        mosaic_regions: Optional[List[Dict]] = None
    ) -> str:
        """
        截取页面截图

        Args:
            path: 页面路径，如 '/customer/tw-list'
            filename: 保存的文件名（不含扩展名）
            wait_for: 等待某个选择器出现
            wait_time: 额外等待时间（毫秒）
            full_page: 是否截取整个页面
            clip: 截取区域 {'x': 0, 'y': 0, 'width': 800, 'height': 600}
            actions: 截图前执行的操作列表
                     [{'type': 'click', 'selector': '.btn'},
                      {'type': 'fill', 'selector': 'input', 'value': 'text'},
                      {'type': 'hover', 'selector': '.menu'}]
            mask_data: 是否脱敏数据（覆盖全局设置）
            blur_regions: 需要高斯模糊的区域列表
            mosaic_regions: 需要马赛克的区域列表

        Returns:
            截图文件的完整路径
        """
        # 添加语言参数
        lang_param = f"lang={self.language}"
        if '?' in path:
            url = f"{self.base_url}{path}&{lang_param}"
        else:
            url = f"{self.base_url}{path}?{lang_param}"

        await self.page.goto(url, wait_until='networkidle')
        print(f"访问页面: {url}")

        # 等待特定元素
        if wait_for:
            await self.page.wait_for_selector(wait_for, timeout=10000)

        # 执行操作
        if actions:
            for action in actions:
                action_type = action.get('type')
                selector = action.get('selector')

                if action_type == 'click':
                    await self.page.click(selector)
                elif action_type == 'fill':
                    await self.page.fill(selector, action.get('value', ''))
                elif action_type == 'hover':
                    await self.page.hover(selector)
                elif action_type == 'wait':
                    await asyncio.sleep(action.get('time', 1000) / 1000)
                elif action_type == 'select':
                    await self.page.select_option(selector, action.get('value'))

                # 每个操作后等待一下
                await asyncio.sleep(0.3)

        # 数据脱敏：执行 JavaScript 替换页面中的敏感数据
        should_mask = mask_data if mask_data is not None else self.mask_data
        if should_mask:
            await self.page.evaluate(DataMasker.get_replace_script())
            print("已执行页面数据脱敏")
            await asyncio.sleep(0.5)  # 等待替换生效

        # 额外等待
        if wait_time > 0:
            await asyncio.sleep(wait_time / 1000)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d')
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.png")

        # 截图参数
        screenshot_args = {
            'path': filepath,
            'full_page': full_page
        }
        if clip:
            screenshot_args['clip'] = clip

        # 执行截图
        await self.page.screenshot(**screenshot_args)
        print(f"截图已保存: {filepath}")

        # 后处理：对指定区域进行模糊或马赛克
        if blur_regions:
            DataMasker.blur_region(filepath, blur_regions)
            print(f"已对 {len(blur_regions)} 个区域进行高斯模糊")

        if mosaic_regions:
            DataMasker.mosaic_region(filepath, mosaic_regions)
            print(f"已对 {len(mosaic_regions)} 个区域进行马赛克处理")

        return filepath

    async def screenshot_element(
        self,
        path: str,
        selector: str,
        filename: str,
        wait_time: int = 1000
    ) -> str:
        """截取页面中的特定元素"""
        url = f"{self.base_url}{path}"
        await self.page.goto(url, wait_until='networkidle')

        # 等待元素
        element = await self.page.wait_for_selector(selector, timeout=10000)

        if wait_time > 0:
            await asyncio.sleep(wait_time / 1000)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d')
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.png")

        # 截取元素
        await element.screenshot(path=filepath)
        print(f"元素截图已保存: {filepath}")

        return filepath

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("浏览器已关闭")


async def demo():
    """演示用法"""
    # 配置
    tool = ScreenshotTool(
        base_url="http://127.0.0.1:5000",  # 本地应用
        username="your_username",           # 替换为实际用户名
        password="your_password",           # 替换为实际密码
        output_dir="docs/screenshots",
        headless=False,                     # 显示浏览器窗口
        language="zh",
        mask_data=True                      # 启用数据脱敏
    )

    try:
        # 启动浏览器
        await tool.start()

        # 登录
        logged_in = await tool.login()
        if not logged_in:
            print("登录失败，退出")
            return

        # 截取客户列表页面（自动脱敏）
        await tool.screenshot(
            path='/customer/tw-list',
            filename='customer_list',
            wait_time=2000
        )

        # 截取项目列表页面
        await tool.screenshot(
            path='/project/tw-list',
            filename='project_list',
            wait_time=2000
        )

        # 截取报销单列表
        await tool.screenshot(
            path='/expense/tw-list',
            filename='expense_list',
            wait_time=2000
        )

        # 如果需要对特定区域进行额外的马赛克处理
        # await tool.screenshot(
        #     path='/customer/tw-view/1',
        #     filename='customer_detail',
        #     wait_time=2000,
        #     mosaic_regions=[
        #         {'x': 200, 'y': 300, 'width': 400, 'height': 30},  # 手机号区域
        #         {'x': 200, 'y': 350, 'width': 400, 'height': 30},  # 地址区域
        #     ]
        # )

        print("\n所有截图完成!")
        print(f"截图保存目录: {tool.output_dir}")
        print("\n脱敏处理说明:")
        print("  - 公司名称 → 示例科技有限公司、测试贸易公司等")
        print("  - 联系人   → 张三、李四、王五等")
        print("  - 手机号   → 138****1234 格式")
        print("  - 邮箱     → demo@example.com 格式")
        print("  - 地址     → 示例地址")

    finally:
        await tool.close()


if __name__ == '__main__':
    # 运行演示
    asyncio.run(demo())
