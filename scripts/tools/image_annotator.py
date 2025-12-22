#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片标注工具
在截图上绘制红框、箭头、数字标注、文字说明
"""
import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional


class ImageAnnotator:
    """图片标注器"""

    def __init__(self, image_path: str):
        """
        初始化标注器

        Args:
            image_path: 原始图片路径
        """
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.draw = ImageDraw.Draw(self.image)

        # 尝试加载中文字体
        self.font_large = self._load_font(24)
        self.font_medium = self._load_font(18)
        self.font_small = self._load_font(14)

        # 颜色定义
        self.RED = (255, 0, 0)
        self.BLUE = (0, 100, 255)
        self.GREEN = (0, 180, 0)
        self.ORANGE = (255, 140, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)

    def _load_font(self, size: int):
        """加载字体"""
        # macOS 中文字体路径
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue

        # 回退到默认字体
        return ImageFont.load_default()

    def draw_rect(
        self,
        x: int, y: int,
        width: int, height: int,
        color: Tuple[int, int, int] = None,
        line_width: int = 3,
        label: str = None,
        label_position: str = 'top'  # top, bottom, left, right
    ):
        """
        绘制矩形框

        Args:
            x, y: 左上角坐标
            width, height: 宽高
            color: 颜色，默认红色
            line_width: 线宽
            label: 标签文字
            label_position: 标签位置
        """
        if color is None:
            color = self.RED

        # 绘制矩形
        self.draw.rectangle(
            [x, y, x + width, y + height],
            outline=color,
            width=line_width
        )

        # 绘制标签
        if label:
            # 计算标签位置
            bbox = self.draw.textbbox((0, 0), label, font=self.font_small)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            padding = 4
            if label_position == 'top':
                label_x = x
                label_y = y - text_height - padding * 2 - 2
            elif label_position == 'bottom':
                label_x = x
                label_y = y + height + 2
            elif label_position == 'left':
                label_x = x - text_width - padding * 2 - 2
                label_y = y
            else:  # right
                label_x = x + width + 2
                label_y = y

            # 绘制标签背景
            self.draw.rectangle(
                [label_x, label_y, label_x + text_width + padding * 2, label_y + text_height + padding * 2],
                fill=color
            )

            # 绘制标签文字
            self.draw.text(
                (label_x + padding, label_y + padding),
                label,
                fill=self.WHITE,
                font=self.font_small
            )

        return self

    def draw_circle(
        self,
        x: int, y: int,
        radius: int = 20,
        color: Tuple[int, int, int] = None,
        line_width: int = 3,
        number: int = None
    ):
        """
        绘制圆圈（用于标注步骤编号）

        Args:
            x, y: 圆心坐标
            radius: 半径
            color: 颜色
            line_width: 线宽
            number: 圆内数字
        """
        if color is None:
            color = self.RED

        # 绘制圆形
        self.draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            outline=color,
            fill=color,
            width=line_width
        )

        # 绘制数字
        if number is not None:
            text = str(number)
            bbox = self.draw.textbbox((0, 0), text, font=self.font_medium)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            self.draw.text(
                (x - text_width // 2, y - text_height // 2 - 2),
                text,
                fill=self.WHITE,
                font=self.font_medium
            )

        return self

    def draw_arrow(
        self,
        start_x: int, start_y: int,
        end_x: int, end_y: int,
        color: Tuple[int, int, int] = None,
        line_width: int = 3,
        arrow_size: int = 15
    ):
        """
        绘制箭头

        Args:
            start_x, start_y: 起点坐标
            end_x, end_y: 终点坐标（箭头指向）
            color: 颜色
            line_width: 线宽
            arrow_size: 箭头大小
        """
        import math

        if color is None:
            color = self.RED

        # 绘制线段
        self.draw.line(
            [(start_x, start_y), (end_x, end_y)],
            fill=color,
            width=line_width
        )

        # 计算箭头角度
        angle = math.atan2(end_y - start_y, end_x - start_x)

        # 绘制箭头
        arrow_angle = math.pi / 6  # 30度
        x1 = end_x - arrow_size * math.cos(angle - arrow_angle)
        y1 = end_y - arrow_size * math.sin(angle - arrow_angle)
        x2 = end_x - arrow_size * math.cos(angle + arrow_angle)
        y2 = end_y - arrow_size * math.sin(angle + arrow_angle)

        self.draw.polygon(
            [(end_x, end_y), (x1, y1), (x2, y2)],
            fill=color
        )

        return self

    def draw_text(
        self,
        x: int, y: int,
        text: str,
        color: Tuple[int, int, int] = None,
        font_size: str = 'medium',  # small, medium, large
        background: bool = True
    ):
        """
        绘制文字标注

        Args:
            x, y: 位置
            text: 文字内容
            color: 颜色
            font_size: 字体大小
            background: 是否绘制背景
        """
        if color is None:
            color = self.RED

        font = {
            'small': self.font_small,
            'medium': self.font_medium,
            'large': self.font_large
        }.get(font_size, self.font_medium)

        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 4

        if background:
            # 绘制背景
            self.draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=color
            )
            text_color = self.WHITE
        else:
            text_color = color

        self.draw.text((x, y), text, fill=text_color, font=font)

        return self

    def draw_highlight(
        self,
        x: int, y: int,
        width: int, height: int,
        color: Tuple[int, int, int] = None,
        alpha: int = 80
    ):
        """
        绘制半透明高亮区域

        Args:
            x, y: 左上角坐标
            width, height: 宽高
            color: 颜色
            alpha: 透明度 (0-255)
        """
        if color is None:
            color = (255, 255, 0)  # 黄色高亮

        # 创建半透明层
        overlay = Image.new('RGBA', self.image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [x, y, x + width, y + height],
            fill=(*color, alpha)
        )

        # 合并图层
        if self.image.mode != 'RGBA':
            self.image = self.image.convert('RGBA')

        self.image = Image.alpha_composite(self.image, overlay)
        self.draw = ImageDraw.Draw(self.image)

        return self

    def draw_step_marker(
        self,
        x: int, y: int,
        step_number: int,
        description: str = None,
        color: Tuple[int, int, int] = None
    ):
        """
        绘制步骤标记（圆圈+数字+可选描述）

        Args:
            x, y: 位置
            step_number: 步骤编号
            description: 步骤描述
            color: 颜色
        """
        if color is None:
            color = self.RED

        # 绘制圆圈和数字
        self.draw_circle(x, y, radius=18, color=color, number=step_number)

        # 绘制描述文字
        if description:
            self.draw_text(x + 25, y - 10, description, color=color, font_size='small')

        return self

    def save(self, output_path: str = None):
        """
        保存标注后的图片

        Args:
            output_path: 输出路径，默认覆盖原文件
        """
        if output_path is None:
            output_path = self.image_path

        # 确保转换为 RGB 模式（用于 PNG/JPG）
        if self.image.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', self.image.size, (255, 255, 255))
            background.paste(self.image, mask=self.image.split()[-1])
            background.save(output_path)
        else:
            self.image.save(output_path)

        return output_path


def annotate_dashboard(image_path: str, output_path: str):
    """标注仪表台截图"""
    annotator = ImageAnnotator(image_path)

    # 标注左侧导航栏
    annotator.draw_rect(0, 60, 180, 700, label='导航菜单', label_position='right')

    # 标注顶部搜索栏
    annotator.draw_rect(570, 8, 320, 40, label='全局搜索', label_position='bottom')

    # 标注语言切换
    annotator.draw_rect(1300, 8, 100, 40, label='语言切换', label_position='bottom')

    # 标注统计卡片区域
    annotator.draw_rect(220, 120, 1200, 100, label='数据统计', label_position='bottom')

    annotator.save(output_path)
    return output_path


def annotate_customer_list(image_path: str, output_path: str):
    """标注客户列表截图"""
    annotator = ImageAnnotator(image_path)

    # 步骤标记
    annotator.draw_step_marker(1380, 88, 1, '添加客户')
    annotator.draw_step_marker(350, 278, 2, '筛选条件')
    annotator.draw_step_marker(400, 440, 3, '点击查看详情')

    # 标注区域
    annotator.draw_rect(230, 245, 1190, 60, color=annotator.BLUE, label='筛选区域')
    annotator.draw_rect(230, 320, 1190, 480, color=annotator.GREEN, label='数据列表')

    annotator.save(output_path)
    return output_path


# 示例用法
if __name__ == '__main__':
    # 测试标注功能
    test_image = '/Users/nijie/Documents/PMA/docs/screenshots/tutorial/dashboard_20251221.png'
    if os.path.exists(test_image):
        output = test_image.replace('.png', '_annotated.png')
        annotate_dashboard(test_image, output)
        print(f"标注完成: {output}")
