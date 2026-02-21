# ==================================================
# 数据库辅助函数模块
# 功能：存放通用的数据库查询函数，避免模块间循环导入
# ==================================================

from .config import get_supabase_client

def get_user_sect(user_id: str):
    """
    获取用户当前所属宗门
    
    参数:
        user_id: 用户 ID
    
    返回:
        宗门信息字典，如果没有宗门则返回 None
    """
    supabase = get_supabase_client()
    members = supabase.table("sect_members").select("sect_id").eq("user_id", user_id).execute()
    
    if not members.data:
        return None
    
    sect_id = members.data[0]["sect_id"]
    sect = supabase.table("sects").select("*").eq("id", sect_id).execute()
    
    return sect.data[0] if sect.data else None

def get_user_inventory_count(user_id: str) -> int:
    """
    获取用户背包物品总数
    
    参数:
        user_id: 用户 ID
    
    返回:
        物品总数量
    """
    supabase = get_supabase_client()
    result = supabase.table("user_inventory").select("quantity").eq("user_id", user_id).execute()
    return sum(item.get("quantity", 0) for item in (result.data or []))

def get_user_cultivation(user_id: str):
    """
    获取用户修炼数据
    
    参数:
        user_id: 用户 ID
    
    返回:
        修炼数据字典，如果没有则返回 None
    """
    supabase = get_supabase_client()
    result = supabase.table("user_cultivation").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else None