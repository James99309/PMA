# 系统定时任务配置指南

本文档介绍如何配置系统的定时任务，确保客户活跃度状态等功能的自动更新。

## 客户活跃度更新任务

### 功能介绍

客户活跃度更新任务会自动检查所有客户的活跃情况，并根据以下条件更新状态：

- 当客户连续1天没有数据更新时，包括客户数据更新、客户跟进记录创建、跟进记录回复、关联项目的创建或更新、项目跟进记录等，则将客户状态从"活跃"修改为"非活跃"。
- 反之，当满足任一活跃条件时，将客户状态从"非活跃"修改为"活跃"。

### 配置定时任务

#### Linux/macOS (使用crontab)

1. 打开终端，编辑crontab配置：

```bash
crontab -e
```

2. 添加以下内容，设置每天凌晨2点运行：

```
# 每天凌晨2点运行客户活跃度更新
0 2 * * * cd /path/to/your/PMA && source venv/bin/activate && python scripts/update_customer_activity.py --days=1 >> logs/cron_activity.log 2>&1
```

3. 保存并退出编辑器。

#### Windows (使用任务计划程序)

1. 打开任务计划程序（按Win+R，输入`taskschd.msc`）。
2. 点击"创建基本任务"。
3. 输入名称（如"PMA客户活跃度更新"）和描述。
4. 选择"每天"，并设置开始时间为凌晨2:00。
5. 选择"启动程序"。
6. 浏览并选择以下命令：
   - 程序/脚本：`C:\path\to\your\PMA\venv\Scripts\python.exe`
   - 添加参数：`scripts/update_customer_activity.py --days=1`
   - 起始于：`C:\path\to\your\PMA`

7. 完成任务创建。

### 手动运行

您随时可以手动运行此脚本来更新客户活跃度：

```bash
cd /path/to/your/PMA
source venv/bin/activate  # Linux/macOS
# Windows: venv\Scripts\activate

python scripts/update_customer_activity.py --days=1
```

### 参数说明

`update_customer_activity.py` 脚本支持以下参数：

- `--days=N`：设置不活跃判断阈值（几天没有活动），默认为1天
- `--company-id=ID`：仅检查指定ID的客户，不指定则检查所有客户

## 其他定时任务

您可以按照类似的方式配置其他定时任务，例如：

1. 数据备份
2. 系统日志清理
3. 项目状态更新
4. 报表生成

## 定时任务排错

如果定时任务无法正常运行，请检查：

1. 路径是否正确
2. 权限是否足够
3. Python虚拟环境是否配置正确
4. 日志文件是否有错误提示

查看日志：

```bash
tail -n 100 logs/customer_activity.log
```

## 注意事项

- 定时任务应避免与系统高峰期重叠
- 确保系统磁盘空间足够，特别是日志目录
- 定期检查日志文件大小，避免磁盘占满 