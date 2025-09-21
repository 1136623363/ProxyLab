from datetime import datetime, timezone, timedelta
from typing import Optional

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time() -> datetime:
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

def utc_to_beijing(utc_dt: Optional[datetime]) -> Optional[datetime]:
    """将UTC时间转换为北京时间"""
    if utc_dt is None:
        return None
    
    # 如果已经是timezone-aware，直接转换
    if utc_dt.tzinfo is not None:
        return utc_dt.astimezone(BEIJING_TZ)
    
    # 如果是naive datetime，假设为UTC
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(BEIJING_TZ)

def beijing_to_utc(beijing_dt: Optional[datetime]) -> Optional[datetime]:
    """将北京时间转换为UTC时间"""
    if beijing_dt is None:
        return None
    
    # 如果已经是timezone-aware，直接转换
    if beijing_dt.tzinfo is not None:
        return beijing_dt.astimezone(timezone.utc)
    
    # 如果是naive datetime，假设为北京时间
    return beijing_dt.replace(tzinfo=BEIJING_TZ).astimezone(timezone.utc)

def format_beijing_time(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化北京时间为字符串"""
    if dt is None:
        return ""
    
    beijing_dt = utc_to_beijing(dt)
    return beijing_dt.strftime(format_str)
