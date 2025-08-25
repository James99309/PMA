def project_type_style(project_type):
    """返回项目类型对应的样式类"""
    styles = {
        'sales_focus': 'bg-primary',
        'sales_key': 'bg-primary',      # 向sales_focus统一
        'channel_follow': 'bg-info',
        'business_opportunity': 'bg-success',
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

def format_achievement_rate(achievement_rate, qualifying_rate=None):
    """
    格式化达成率，根据合格值设置颜色
    
    Args:
        achievement_rate: 达成率（百分比数值，如85.5）
        qualifying_rate: 合格值（百分比数值，如80）
    
    Returns:
        带HTML标签的达成率字符串
    """
    if achievement_rate is None:
        return "-"
    
    # 确保是数值类型
    try:
        rate = float(achievement_rate)
    except (ValueError, TypeError):
        return "-"
    
    # 格式化为整数百分比
    rate_str = f"{int(rate)}%"
    
    # 如果设置了合格值，根据达成率与合格值比较设置颜色
    if qualifying_rate is not None and qualifying_rate > 0:
        try:
            qualifying = float(qualifying_rate)
            if rate >= qualifying:
                return f'<span class="text-success">{rate_str}</span>'
            else:
                return f'<span class="text-danger">{rate_str}</span>'
        except (ValueError, TypeError):
            pass
    
    # 没有设置合格值或合格值无效，使用正常颜色
    return rate_str 