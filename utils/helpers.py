# ==================================================
# 工具函数模块
# 功能：提供通用的辅助函数，避免代码重复
# ==================================================

import hashlib
from datetime import datetime
from typing import Any, Dict, List

# ==============================
# 🔐 密码处理
# ==============================

def hash_password(password: str) -> str:
    """
    对密码进行 SHA256 哈希加密
    
    参数:
        password: 明文密码
    
    返回:
        加密后的密码字符串
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    参数:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的加密密码
    
    返回:
        True 如果密码匹配，否则 False
    """
    return hash_password(plain_password) == hashed_password

# ==============================
# ⏰ 时间处理
# ==============================

def get_current_time_str() -> str:
    """获取当前时间的字符串格式 (YYYY-MM-DD HH:MM:SS)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_datetime(dt: datetime) -> str:
    """格式化 datetime 对象为易读字符串"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ==============================
# 📦 数据处理
# ==============================

def make_json_serializable(obj: Any) -> Any:
    """
    将对象转换为 JSON 可序列化的格式
    处理 datetime、Decimal 等特殊类型
    
    参数:
        obj: 需要转换的对象
    
    返回:
        转换后的对象
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    # 如果有 Decimal 类型，取消下面注释
    # from decimal import Decimal
    # if isinstance(obj, Decimal):
    #     return float(obj)
    return obj

def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """安全地从字典中获取值，避免 KeyError"""
    return data.get(key, default)