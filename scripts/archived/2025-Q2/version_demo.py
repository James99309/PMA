#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import create_app
from app.models.version_management import VersionRecord, UpgradeLog, FeatureChange, SystemMetrics

def demonstrate_version_management():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("PMA系统版本管理功能工作原理演示")
        print("=" * 60)
        
        # 当前版本信息
        print("\\n1. 当前版本信息")
        print("-" * 30)
        current = VersionRecord.get_current_version()
        if current:
            print(f"版本号: {current.version_number}")
            print(f"版本名称: {current.version_name}")
            print(f"发布日期: {current.release_date}")
            print(f"运行环境: {current.environment}")
            print(f"描述: {current.description}")
            
            # 统计功能变更
            features = FeatureChange.query.filter_by(version_id=current.id, change_type='feature').count()
            fixes = FeatureChange.query.filter_by(version_id=current.id, change_type='fix').count()
            improvements = FeatureChange.query.filter_by(version_id=current.id, change_type='improvement').count()
            print(f"功能统计: 新功能{features}个, 修复{fixes}个, 改进{improvements}个")
        
        # 版本历史
        print("\\n2. 版本历史记录")
        print("-" * 30)
        versions = VersionRecord.query.order_by(VersionRecord.release_date.desc()).limit(5).all()
        for v in versions:
            status = "✅ 当前" if v.is_current else "📦 历史"
            print(f"{status} {v.version_number} - {v.version_name}")
        
        # 功能变更
        print("\\n3. 最近功能变更")
        print("-" * 30)
        changes = FeatureChange.query.order_by(FeatureChange.created_at.desc()).limit(8).all()
        type_icons = {'feature': '🆕', 'fix': '🔧', 'improvement': '⚡', 'security': '🔒'}
        for change in changes:
            icon = type_icons.get(change.change_type, '📝')
            print(f"{icon} [{change.change_type.upper()}] {change.title}")
            print(f"   模块: {change.module_name} | 优先级: {change.priority}")
        
        # 升级日志
        print("\\n4. 升级日志")
        print("-" * 30)
        upgrades = UpgradeLog.query.order_by(UpgradeLog.upgrade_date.desc()).limit(3).all()
        for upgrade in upgrades:
            status_icon = "✅" if upgrade.status == "success" else "❌" if upgrade.status == "failed" else "🔄"
            print(f"{status_icon} {upgrade.from_version} → {upgrade.to_version}")
            duration = f"{upgrade.duration_seconds}秒" if upgrade.duration_seconds else "未记录"
            print(f"   操作员: {upgrade.operator_name} | 耗时: {duration}")
        
        # 系统指标
        print("\\n5. 系统性能指标")
        print("-" * 30)
        if current:
            metrics = SystemMetrics.query.filter_by(version_id=current.id).order_by(SystemMetrics.recorded_at.desc()).first()
            if metrics:
                print(f"响应时间: {metrics.avg_response_time}ms")
                print(f"内存使用: {metrics.memory_usage}%")
                print(f"CPU使用: {metrics.cpu_usage}%")
                print(f"错误率: {metrics.error_rate}%")
                print(f"活跃用户: {metrics.active_users}人")
            else:
                print("暂无性能指标数据")
        
        print("\\n6. 工作原理说明")
        print("-" * 30)
        print("📋 数据模型:")
        print("   • VersionRecord: 存储版本基本信息和统计")
        print("   • UpgradeLog: 记录每次升级的详细过程")
        print("   • FeatureChange: 跟踪功能变更和改进")
        print("   • SystemMetrics: 监控系统性能指标")
        print("\\n🔄 自动化流程:")
        print("   • 应用启动时自动检查版本一致性")
        print("   • 升级时自动记录变更日志和耗时")
        print("   • 定期收集系统性能指标")
        print("   • 提供REST API供前端调用")
        print("\\n👥 管理员功能:")
        print("   • 查看版本历史和当前状态")
        print("   • 创建新版本记录和功能变更")
        print("   • 监控系统升级状态和性能")
        print("   • 分析版本趋势和系统健康度")
        print("\\n🎯 主要用途:")
        print("   • 跟踪系统版本变化和功能演进")
        print("   • 记录升级过程，便于问题排查")
        print("   • 监控系统性能，及时发现问题")
        print("   • 为管理决策提供数据支持")

if __name__ == "__main__":
    demonstrate_version_management() 