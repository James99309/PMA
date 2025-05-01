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

def format_currency(amount):
    """格式化货币"""
    if not amount:
        return '￥0.00'
    try:
        return '￥{:,.2f}'.format(float(amount))
    except (ValueError, TypeError):
        return '￥0.00' 