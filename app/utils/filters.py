def project_type_style(project_type):
    """返回项目类型对应的样式类"""
    styles = {
        'sales_focus': 'bg-primary',
        '销售重点': 'bg-primary',
        'channel_follow': 'bg-info',
        '渠道跟进': 'bg-info',
        'normal': 'bg-secondary'
    }
    return styles.get(project_type, 'bg-secondary')

def project_stage_style(stage):
    """返回项目阶段对应的样式类"""
    styles = {
        '初步接触': 'bg-warning',
        '方案阶段': 'bg-info',
        '商务谈判': 'bg-primary',
        '签约完成': 'bg-success',
        '项目结束': 'bg-secondary'
    }
    return styles.get(stage, 'bg-secondary')

def format_date(date, format='%Y-%m-%d'):
    """格式化日期"""
    if not date:
        return '--'
    try:
        return date.strftime(format)
    except (AttributeError, ValueError):
        return '--'
        
def format_datetime(datetime, format='%Y-%m-%d %H:%M'):
    """格式化日期时间"""
    if not datetime:
        return '--'
    try:
        return datetime.strftime(format)
    except (AttributeError, ValueError):
        return '--'

def format_datetime_local(datetime, format='%Y-%m-%d %H:%M'):
    """格式化日期时间（使用本地时区）"""
    if not datetime:
        return '--'
    try:
        from datetime import timezone, timedelta
        import time
        
        # 获取本地时区偏移量
        local_offset = time.timezone if (time.daylight == 0) else time.altzone
        local_tz = timezone(timedelta(seconds=-local_offset))
        
        # 如果datetime是天真对象（没有时区信息），假设它是UTC
        if datetime.tzinfo is None:
            from datetime import timezone as tz
            datetime = datetime.replace(tzinfo=tz.utc)
        
        # 转换到本地时区
        local_datetime = datetime.astimezone(local_tz)
        return local_datetime.strftime(format)
    except (AttributeError, ValueError, ImportError):
        # 如果出错，回退到原始的格式化函数
        return format_datetime(datetime, format)

def format_currency(amount):
    """格式化货币"""
    if not amount:
        return '￥0.00'
    try:
        return '￥{:,.2f}'.format(float(amount))
    except (ValueError, TypeError):
        return '￥0.00' 