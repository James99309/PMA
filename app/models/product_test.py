# -*- coding: utf-8 -*-
"""
产品测试模型
管理工厂测试和FAT测试记录
"""
from app import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ProductTest(db.Model):
    """产品测试记录表 - 工厂测试/FAT测试"""
    __tablename__ = 'product_tests'

    id = Column(Integer, primary_key=True)

    # ========== 关联信息 ==========
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    approval_step_id = Column(Integer, ForeignKey('approval_steps.id'), nullable=True)  # 关联审批步骤

    # ========== 测试分类 ==========
    test_category = Column(String(20), nullable=False)  # factory: 工厂测试, verification: FAT验证测试
    test_type = Column(String(20), nullable=True)  # site_fat: 现场FAT, incoming: 到货测试

    # ========== 测试模式 ==========
    test_mode = Column(String(20), default='full')  # full: 全部测试, sampling: 采样测试
    total_quantity = Column(Integer, default=0)  # 总数量
    sample_quantity = Column(Integer, nullable=True)  # 采样数量（仅采样模式）

    # ========== 测试状态 ==========
    status = Column(String(20), default='pending')
    # pending: 待测试
    # in_progress: 测试中
    # completed: 已完成
    # passed: 全部通过
    # failed: 存在失败

    # ========== 测试结果 ==========
    passed_count = Column(Integer, default=0)  # 通过数量
    failed_count = Column(Integer, default=0)  # 失败数量

    # ========== 测试信息 ==========
    test_date = Column(DateTime, nullable=True)  # 测试日期
    tester_name = Column(String(100), nullable=True)  # 测试人员姓名
    tester_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 测试人员ID（如内部人员）
    signature_url = Column(String(500), nullable=True)  # 测试人员签名图片

    # ========== 元数据 ==========
    notes = Column(Text, nullable=True)  # 备注
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime, nullable=True)  # 提交时间

    # 关系
    purchase_order = relationship('PurchaseOrder', backref='tests')
    tester_user = relationship('User', foreign_keys=[tester_user_id], backref='conducted_tests')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_tests')

    def __repr__(self):
        return f'<ProductTest {self.test_category}:{self.status}>'

    @property
    def status_label(self):
        """状态标签"""
        labels = {
            'pending': '待测试',
            'in_progress': '测试中',
            'completed': '已完成',
            'passed': '全部通过',
            'failed': '存在失败'
        }
        return labels.get(self.status, self.status)

    @property
    def test_category_label(self):
        """测试类别标签"""
        labels = {
            'factory': '工厂测试',
            'verification': 'FAT验证测试'
        }
        return labels.get(self.test_category, self.test_category)

    @property
    def test_type_label(self):
        """测试类型标签"""
        labels = {
            'site_fat': '现场FAT',
            'incoming': '到货测试'
        }
        return labels.get(self.test_type, self.test_type)

    @property
    def test_mode_label(self):
        """测试模式标签"""
        labels = {
            'full': '全部测试',
            'sampling': '采样测试'
        }
        return labels.get(self.test_mode, self.test_mode)

    @property
    def progress_percentage(self):
        """测试进度百分比"""
        total = self.sample_quantity if self.test_mode == 'sampling' else self.total_quantity
        if not total:
            return 0
        completed = self.passed_count + self.failed_count
        return int((completed / total) * 100)

    def update_result_counts(self):
        """从详细记录更新通过/失败计数"""
        self.passed_count = sum(1 for d in self.details if d.result == 'passed')
        self.failed_count = sum(1 for d in self.details if d.result == 'failed')

        # 更新状态
        total = self.sample_quantity if self.test_mode == 'sampling' else self.total_quantity
        completed = self.passed_count + self.failed_count

        if completed == 0:
            self.status = 'pending'
        elif completed < total:
            self.status = 'in_progress'
        else:
            # 全部完成
            if self.failed_count == 0:
                self.status = 'passed'
            else:
                self.status = 'failed'


class ProductTestDetail(db.Model):
    """产品测试明细表 - 单个序列号的测试结果"""
    __tablename__ = 'product_test_details'

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('product_tests.id'), nullable=False)
    serial_number_id = Column(Integer, ForeignKey('product_serial_numbers.id'), nullable=False)

    # ========== 测试顺序（采样时的抽取顺序）==========
    sequence = Column(Integer, default=0)  # 测试顺序号

    # ========== 测试结果 ==========
    result = Column(String(20), nullable=True)  # passed: 通过, failed: 失败, null: 待测
    report_file_url = Column(String(500), nullable=True)  # 测试报告文件URL
    report_file_name = Column(String(200), nullable=True)  # 原始文件名

    # ========== 测试详情 ==========
    tested_at = Column(DateTime, nullable=True)  # 测试时间
    notes = Column(Text, nullable=True)  # 备注/问题描述

    # 关系
    test = relationship('ProductTest', backref='details')
    serial_number = relationship('ProductSerialNumber')

    def __repr__(self):
        return f'<ProductTestDetail SN:{self.serial_number_id} Result:{self.result}>'

    @property
    def result_label(self):
        """结果标签"""
        labels = {
            'passed': '通过',
            'failed': '不通过',
            None: '待测试'
        }
        return labels.get(self.result, self.result)

    @property
    def status_icon(self):
        """状态图标"""
        icons = {
            'passed': '✅',
            'failed': '❌',
            None: '⏳'
        }
        return icons.get(self.result, '⏳')


class ProductTestSampling(db.Model):
    """采样测试记录表 - 记录采样抽取信息"""
    __tablename__ = 'product_test_samplings'

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('product_tests.id'), nullable=False)

    # ========== 采样信息 ==========
    total_population = Column(Integer, nullable=False)  # 总体数量
    sample_size = Column(Integer, nullable=False)  # 样本数量
    random_seed = Column(String(100), nullable=True)  # 随机种子（用于可追溯）

    # ========== 采样时间和操作人 ==========
    sampled_at = Column(DateTime, default=func.now())
    sampled_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # 关系
    test = relationship('ProductTest', backref='sampling_record', uselist=False)
    sampled_by = relationship('User', backref='test_samplings')

    def __repr__(self):
        return f'<ProductTestSampling {self.sample_size}/{self.total_population}>'
