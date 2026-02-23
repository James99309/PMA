from app.models.user import User
from app.models.project import Project
from app.models.customer import Company, Contact
from .quotation import Quotation
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField, ProductCodeFieldOption, ProductCode, ProductCodeFieldValue, SpecificationDictionary
from app.models.product_relation import ProductRelation
# DEPRECATED - 研发库模型，仅用于访问历史数据 (2025-12-26)
from app.models.dev_product import DevProduct, DevProductSpec
from app.models.gantt_models import DevProductMilestone, StageDependency, StageAttachment, StageReview
from app.models.spec_template import (
    TestMethodDictionary, TestConditionDictionary, SpecCategory, SpecDefinition,
    SpecTemplate, SpecTemplateItem, ProductConfiguration, ProductConfigValue, SpecAttachment
)
from app.models.dictionary import Dictionary
from app.models.approval import ApprovalProcessTemplate, ApprovalStep, ApprovalInstance, ApprovalRecord, ApprovalStatus, ApprovalAction, ApprovalExternalToken
from app.models.pricing_order import PricingOrder, PricingOrderDetail, SettlementOrderDetail, PricingOrderApprovalRecord
from app.models.performance import PerformanceTarget, PerformanceStatistics, FiveStarProjectBaseline
from app.models.performance_config import (
    RolePerformanceConfig, RolePerformanceItem, PerformanceMetricsDefinition,
    RolePerformanceTarget, UserPerformanceTarget, get_user_effective_target
)
from app.models.expense import Expense, Department
from app.models.expense_budget import ExpenseBudget
from app.models.project_customer_association import ProjectCustomerAssociation
from app.models.salary_config import (
    SalaryGradeConfig, SalaryGradeBandwidth, SalaryBaseParams, SalaryStepRules,
    SalaryFormulaConfig, SalesTeamConfig, EmployeeSalaryConfig,
    QuarterlyPerformanceData, SalaryCalculationResult
)
from app.models.permission_module import (
    PermissionModule, PermissionModuleFeature, RoleFeaturePermission
)
from app.models.ai_analysis_cache import AIAnalysisCache, UserDailyLoginRecord
from app.models.monthly_activity_snapshot import MonthlyActivitySnapshot
from app.models.worklog import WorkItem, WorkLog
from app.models.worklog_read import WorklogRead
from app.models.message import Message
from app.models.quotation_confirmation_task import QuotationConfirmationTask
from app.models.task import Task, TaskAttachment, TaskReply
from app.models.announcement import Announcement, AnnouncementRead, AnnouncementAttachment
# 订单模块
from app.models.product_test import ProductTest, ProductTestDetail, ProductTestSampling
from app.models.sales_order import SalesOrder, SalesOrderDetail
from app.models.shipment import Shipment, ShipmentDetail
from app.models.product_serial_number import ProductSerialNumber, SerialNumberHistory
# 会议录音纪要模块
from app.models.meeting import (
    MeetingRecording, MeetingTranscript, MeetingSpeaker,
    MeetingMinutes, MeetingActionItem
)
from app.models.user_points_ledger import UserPointsLedger
# 文件管理模块
from app.models.file_manager import FileLibrary, UserFolder, UserFileRef
# 知识库模块
from app.models.knowledge import KnowledgeTag, KnowledgeDocument, KnowledgeChunk
# 资源池访问请求
from app.models.access_request import AccessRequest
# 系统图模块
from app.models.system_diagram import SystemDiagram

__all__ = ['User', 'Project', 'Company', 'Contact', 'Quotation', 'Product', 'ProductSpec',
           'ProductCategory', 'ProductSubcategory', 'ProductCodeField',
           'ProductCodeFieldOption', 'ProductCode', 'ProductCodeFieldValue', 'SpecificationDictionary',
           'ProductRelation', 'DevProduct', 'DevProductSpec', 'DevProductMilestone', 'StageDependency',
           'StageAttachment', 'StageReview',
           'TestMethodDictionary', 'TestConditionDictionary', 'SpecCategory', 'SpecDefinition',
           'SpecTemplate', 'SpecTemplateItem', 'ProductConfiguration', 'ProductConfigValue', 'SpecAttachment',
           'Dictionary',
           'ApprovalProcessTemplate', 'ApprovalStep', 'ApprovalInstance', 'ApprovalRecord',
           'ApprovalStatus', 'ApprovalAction', 'ApprovalExternalToken', 'PricingOrder', 'PricingOrderDetail',
           'SettlementOrderDetail', 'PricingOrderApprovalRecord', 'PerformanceTarget',
           'PerformanceStatistics', 'FiveStarProjectBaseline',
           'RolePerformanceConfig', 'RolePerformanceItem', 'PerformanceMetricsDefinition',
           'RolePerformanceTarget', 'UserPerformanceTarget', 'get_user_effective_target',
           'Expense', 'Department',
           'ExpenseBudget', 'ProjectCustomerAssociation',
           'SalaryGradeConfig', 'SalaryGradeBandwidth', 'SalaryBaseParams', 'SalaryStepRules',
           'SalaryFormulaConfig', 'SalesTeamConfig', 'EmployeeSalaryConfig',
           'QuarterlyPerformanceData', 'SalaryCalculationResult',
           'PermissionModule', 'PermissionModuleFeature', 'RoleFeaturePermission',
           'AIAnalysisCache', 'UserDailyLoginRecord',
           'MonthlyActivitySnapshot',
           'WorkItem', 'WorkLog', 'WorklogRead', 'Message',
           'Announcement', 'AnnouncementRead', 'AnnouncementAttachment',
           'ProductTest', 'ProductTestDetail', 'ProductTestSampling',
           'SalesOrder', 'SalesOrderDetail',
           'Shipment', 'ShipmentDetail', 'ProductSerialNumber', 'SerialNumberHistory',
           'MeetingRecording', 'MeetingTranscript', 'MeetingSpeaker',
           'MeetingMinutes', 'MeetingActionItem',
           'QuotationConfirmationTask',
           'Task', 'TaskAttachment', 'TaskReply',
           'UserPointsLedger',
           'FileLibrary', 'UserFolder', 'UserFileRef',
           'KnowledgeTag', 'KnowledgeDocument', 'KnowledgeChunk',
           'AccessRequest',
           'SystemDiagram']