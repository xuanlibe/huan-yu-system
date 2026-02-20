# ==================================================
# 寰宇系统 - 修仙模拟器 (v2.1 炼丹炼器增强版)
# 作者: 轩璃
# 功能: 登录 + 藏宝阁 + 背包 + 宗门 + 炼丹 + 炼器 + 阵法 + 秘境 + 管理员
# 数据库: Supabase (全云端)
# UI: Streamlit 纯文字 + 卡片式布局
# 软件名称: 寰宇系统（严格统一）
# ==================================================

import streamlit as st
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from supabase import create_client, Client
import time
import hashlib

# ==============================
# 🔑 Supabase 配置
# ==============================
# ⚠️ 本地测试时请创建 .streamlit/secrets.toml
if "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
else:
    # 占位符（实际部署时通过 secrets.toml 或环境变量注入）
    SUPABASE_URL = "https://your-supabase-url.supabase.co"
    SUPABASE_ANON_KEY = "your-supabase-anon-key-here"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception as e:
    st.error(f"❌ Supabase 初始化失败: {str(e)}")
    st.stop()

# ==============================
# 🛡️ 系统常量
# ==============================
MAIN_ADMIN_USERNAME = "轩璃"
MAIN_ADMIN_PASSWORD = "20050506"
CURRENT_VERSION = "2.1.0"

FEATURES = {
    "login": True,
    "shop": True,
    "backpack": True,
    "sect": True,
    "alchemy": True,
    "forge": True,
    "array": True,
    "dungeon": True,
    "admin": True,
}

SECT_CATEGORIES = ["天罚监司", "冥界", "人", "妖", "魔", "散修"]

# 炼丹材料价格（来自 炼丹材料.pdf）
ALCHEMY_MATERIAL_PRICES = {
    "聚气草": 250,
    "凝元石": 250,
    "筑基木": 350,
    "建魂花": 350,
    "金液草": 550,
    "凝丹果": 650,
    "育婴藤": 800,
    "温神叶": 1200,
    "化神花": 1500,
    "聚念石": 1000,
    "炼虚草": 35000,
    "凝空晶": 15000,
    "合体木": 35000,
    "融天芝": 20000,
    "大乘花": 50000,
    "聚元玉": 50000,
    "渡劫草": 200000,  # 2灵晶 = 20万灵石
    "护命果": 300000,  # 3灵晶
    "真仙灵草": 400000,
    "凝气石": 600000,
    "玄仙花": 1500000,
    "凝道晶": 1500000,
    "金仙叶": 2500000,
    "九转灵果": 2500000,
    "太乙灵根": 5000000,
    "混元石": 5000000,
    "大罗仙草": 10000000,  # 1仙晶 = 1000万灵石
    "造化玉": 15000000,
    "圣道花": 20000000,
    "育道石": 30000000,
    "准圣草": 25000000,
    "破界晶": 75000000,
    "寰宇灵花": 75000000,
    "造化叶": 50000000,
    "鸿蒙灵液": 75000000,
    "启元花": 75000000,
    # 修为丹药材料
    "血灵草": 250,
    "培元果": 250,
    "清心莲": 400,
    "化气藤": 400,
    "固基木": 650,
    "培元芝": 650,
    "九转灵砂": 1000,
    "金纹花": 1000,
    "化婴草": 1000,
    "融魂花": 1500,
    "凝神叶": 30000,
    "固魄石": 20000,
    "虚空草": 35000,
    "炼元晶": 20000,
    "混天石": 50000,
    "合道藤": 50000,
    "圣元花": 200000,
    "灵寒玉": 300000,
    "天地芝": 500000,
    "护道石": 500000,
    "太乙灵液": 1000000,
    "真仙根": 1000000,
    "九转仙芝": 2000000,
    "玄仙晶": 2000000,
    "金仙液": 2500000,
    "镇道玉": 2500000,
    "太乙雷草": 5000000,
    "破妄花": 5000000,
    "大罗灵花": 10000000,
    "镇世铁": 15000000,
    "圣道果": 25000000,
    "衍化玉": 25000000,
    "准圣芝": 50000000,
    "明道晶": 50000000,
    "寰宇花": 75000000,
    "镇世叶": 75000000,
    "鸿蒙灵液": 125000000,
    "衍道花": 125000000,
}

# 炼器材料攻击加成（来自 炼器材料.pdf）
FORGE_MATERIAL_BONUS = {
    # 黄阶
    "御灵铁": 0.1,
    "引灵玉": 0.1,
    "剑心髓": 0.4,
    "二级妖兽牙": 0.1,
    "二级妖兽骨": 0.3,
    # 玄阶
    "玄铁": 0.3,
    "精钢": 0.2,
    "灵木": 0.2,
    "三品妖猴牙": 0.2,
    "三品玉蟾甲": 0.3,
    "五行玉": 0.2,
    "金雷竹": 0.1,
    # 地阶
    "千年温玉": 1.0,
    "玄海冰魄": 0.5,
    "高级妖兽内丹": 0.5,
    "高级妖兽精血": 0.5,
    # 天阶
    "天外陨铁": 1.0,
    "深海寒玉": 0.5,
    "火焰晶金": 0.5,
    "混元母金": 0.5,
    # 神阶
    "女娲石": 1.0,
    "鸿蒙紫气": 1.0,
    "混沌奇石": 0.5,
    "神兽躯体": 0.5,
    # 仙阶
    "仙金": 1.0,
    "仙晶": 1.0,
    "仙木": 0.5,
    "法则神链": 0.5,
    "天道符文": 0.5,
    # 帝阶
    "宇宙晶核": 2.0,
    "世界之树树枝": 2.0,
    "古老强者精血": 0.5,
    "古老强者神魂碎片": 0.5,
}

def load_features_from_db():
    try:
        data = supabase.table("system_config").select("*").execute().data
        if data:
            config = data[0]
            for key in FEATURES:
                if key in config and isinstance(config[key], bool):
                    FEATURES[key] = config[key]
    except Exception as e:
        print(f"加载功能配置失败: {e}")

load_features_from_db()

# ==============================
# 🔐 工具函数
# ==============================

def make_json_serializable(obj):
    """将常见非 JSON 类型转为可序列化格式"""
    from datetime import datetime, date, time
    from uuid import UUID
    from decimal import Decimal
    
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    return obj

def safe_db_operation(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        # 如果结果包含 data 属性，进行 JSON 兼容处理
        if hasattr(result, 'data') and result.data is not None:
            result.data = make_json_serializable(result.data)
        return result
    except Exception as e:
        error_msg = str(e)
        if "JWT expired" in error_msg:
            st.session_state.clear()
            st.rerun()
        elif "row-level security policy" in error_msg:
            st.toast("❌ 权限不足，请重新登录", icon="🔒")
            st.session_state.clear()
            st.rerun()
        elif "JSON could not be generated" in error_msg or "not JSON serializable" in error_msg:
            st.toast("❌ 数据格式错误，请检查数据库字段类型", icon="💥")
            return None
        else:
            st.toast(f"❌ 系统错误: {error_msg[:100]}", icon="💥")
            return None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def get_current_time_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_user_cultivation_record(user_id: str):
    try:
        data = supabase.table("user_cultivation").select("*").eq("user_id", user_id).execute().data
        if not data:
            supabase.table("user_cultivation").insert({
                "user_id": user_id,
                "realm": "练气",
                "stage": 1,
                "exp": 0,
                "hp": 100,
                "mp": 50,
                "attack": 10,
                "defense": 5,
                "lifespan": 80
            }).execute()
    except Exception as e:
        st.toast(f"⚠️ 初始化修炼数据失败: {str(e)[:50]}", icon="⚠️")

# ==============================
# 👤 用户类
# ==============================
class User:
    def __init__(self, user_data: Dict[str, Any]):
        self.id = user_data.get("id")
        self.username = user_data.get("username", "")
        self.spirit_stones = user_data.get("spirit_stones", 0)
        self.is_admin = user_data.get("is_admin", False)
        self.is_super_admin = user_data.get("is_super_admin", False)
        self.cultivation_level = user_data.get("cultivation_level", 1)
        self.realm = user_data.get("realm", "练气")
        self.stage = user_data.get("stage", 1)
        self.hp = user_data.get("hp", 100)
        self.mp = user_data.get("mp", 50)
        self.attack = user_data.get("attack", 10)
        self.defense = user_data.get("defense", 5)
        self.lifespan = user_data.get("lifespan", 80)

    @classmethod
    def login(cls, username: str, password: str) -> Optional["User"]:
        if not username or not password:
            return None
        # 🔒 强化：轩璃必须使用硬编码密码，无视数据库
        if username == MAIN_ADMIN_USERNAME:
            if password == MAIN_ADMIN_PASSWORD:
                # 模拟一个超级用户对象（不依赖数据库）
                user_data = {
                    "id": "xuanli_main_admin",
                    "username": "轩璃",
                    "spirit_stones": 999999999,
                    "is_admin": True,
                    "is_super_admin": True,
                    "cultivation_level": 999,
                    "realm": "鸿蒙",
                    "stage": 9,
                    "hp": 110000000000,
                    "mp": 10000000000,
                    "attack": 500000000,
                    "defense": 500000000,
                    "lifespan": 100000000000,
                    "last_login": get_current_time_str()
                }
                return cls(user_data)
            else:
                st.toast("❌ 主管理员密码错误", icon="🔒")
                return None
        # 其他用户的正常流程
        response = supabase.table("users").select("*").eq("username", username).execute()
        users = response.data if response and hasattr(response, 'data') else []
        
        if not users:
            return None
        user_data = users[0]
        if not verify_password(password, user_data.get("password_hash", "")):
            return None
        if user_data.get("is_banned", False):
            st.toast("❌ 账号已被封禁", icon="🚫")
            return None
        supabase.table("users").update({"last_login": get_current_time_str()}).eq("id", user_data["id"]).execute()
        return cls(user_data)

    @staticmethod
    def update_spirit_stones(user_id: str, amount: int):
        """更新用户灵石（正数增加，负数减少）"""
        safe_db_operation(
            supabase.rpc, "add_spirit_stones", {"uid": user_id, "amount": amount}
        )

# ==============================
# 🏪 藏宝阁
# ==============================
class TreasurePavilion:
    @staticmethod
    def get_all_items() -> List[Dict[str, Any]]:
        items = safe_db_operation(
            supabase.table("items").select("*").execute
        )
        return items.data if items else []

    @staticmethod
    def buy_item(user_id: str, item_id: int, quantity: int = 1) -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "购买数量必须大于0"
        
        items = safe_db_operation(
            supabase.table("items").select("*").eq("id", item_id).execute
        )
        if not items or not items.data:
            return False, "商品不存在"
        item = items.data[0]
        total_price = item["price"] * quantity
        
        if item.get("stock", 999999) < quantity:
            return False, f"库存不足，当前仅剩 {item.get('stock', 0)} 件"
        
        users = safe_db_operation(
            supabase.table("users").select("spirit_stones").eq("id", user_id).execute
        )
        if not users or not users.data:
            return False, "用户不存在"
        current_stones = users.data[0]["spirit_stones"]
        
        if current_stones < total_price:
            return False, f"灵石不足！需要 {total_price}，当前拥有 {current_stones}"
        
        success = safe_db_operation(
            supabase.rpc, "deduct_spirit_stones", {"uid": user_id, "amount": total_price}
        )
        if not success or not success.data:
            return False, "扣除灵石失败"
        
        inventory = safe_db_operation(
            supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute
        )
        if inventory and inventory.data:
            current_qty = inventory.data[0]["quantity"]
            safe_db_operation(
                supabase.table("user_inventory").update({"quantity": current_qty + quantity}).eq("id", inventory.data[0]["id"]).execute
            )
        else:
            safe_db_operation(
                supabase.table("user_inventory").insert({
                    "user_id": user_id,
                    "item_id": item_id,
                    "quantity": quantity
                }).execute
            )
        
        if "stock" in item and item["stock"] < 999999:
            safe_db_operation(
                supabase.table("items").update({"stock": item["stock"] - quantity}).eq("id", item_id).execute
            )
        
        return True, f"✅ 成功购买 {item['name']} x{quantity}！"

# ==============================
# 🎒 背包
# ==============================
class Backpack:
    @staticmethod
    def get_user_inventory(user_id: str) -> List[Dict[str, Any]]:
        inventory = safe_db_operation(
            supabase.table("user_inventory")
            .select("*, items(name, category, effect, price, usable, effect_type, effect_value)")
            .eq("user_id", user_id)
            .execute
        )
        return inventory.data if inventory else []

    @staticmethod
    def use_item(user_id: str, inventory_id: str, item_data: Dict[str, Any]) -> Tuple[bool, str]:
        if not item_data.get("usable", False):
            return False, "该物品不可使用"
        
        effect_type = item_data.get("effect_type", "")
        effect_value = item_data.get("effect_value", 0)
        
        if effect_type == "heal_hp":
            current_hp = safe_db_operation(
                supabase.rpc, "get_user_hp", {"uid": user_id}
            )
            new_hp = (current_hp.data if current_hp else 100) + effect_value
            safe_db_operation(
                supabase.table("user_cultivation").update({"hp": new_hp}).eq("user_id", user_id).execute
            )
            safe_db_operation(
                supabase.table("user_inventory").delete().eq("id", inventory_id).execute
            )
            return True, f"使用 {item_data['name']}，恢复 {effect_value} 点生命！"
        
        elif effect_type == "add_exp":
            current_exp = safe_db_operation(
                supabase.rpc, "get_user_exp", {"uid": user_id}
            )
            new_exp = (current_exp.data if current_exp else 0) + effect_value
            safe_db_operation(
                supabase.table("user_cultivation").update({"exp": new_exp}).eq("user_id", user_id).execute
            )
            safe_db_operation(
                supabase.table("user_inventory").delete().eq("id", inventory_id).execute
            )
            return True, f"使用 {item_data['name']}，获得 {effect_value} 点经验！"
        
        else:
            return False, "未知物品效果"

# ==============================
# 🏯 宗门系统
# ==============================
class SectSystem:
    @staticmethod
    def get_all_sects() -> List[Dict[str, Any]]:
        sects = safe_db_operation(
            supabase.table("sects").select("*").order("category").execute
        )
        return sects.data if sects else []

    @staticmethod
    def get_user_sect(user_id: str) -> Optional[Dict[str, Any]]:
        members = safe_db_operation(
            supabase.table("sect_members").select("sect_id").eq("user_id", user_id).execute
        )
        if not members or not members.data:
            return None
        sect_id = members.data[0]["sect_id"]
        sect = safe_db_operation(
            supabase.table("sects").select("*").eq("id", sect_id).execute
        )
        return sect.data[0] if sect and sect.data else None

    @staticmethod
    def create_sect(user_id: str, sect_name: str, description: str, category: str) -> Tuple[bool, str]:
        if category != "散修":
            return False, "只有散修可创建新宗门"
        if len(sect_name) < 2 or len(sect_name) > 20:
            return False, "宗门名称需2-20字符"
        
        existing = safe_db_operation(
            supabase.table("sects").select("id").eq("sect_name", sect_name).execute
        )
        if existing and existing.data:
            return False, "宗门名称已存在"
        
        cost = 100000
        users = safe_db_operation(
            supabase.table("users").select("spirit_stones").eq("id", user_id).execute
        )
        if not users or not users.data or users.data[0]["spirit_stones"] < cost:
            return False, f"创建宗门需 {cost:,} 灵石"
        
        success = safe_db_operation(
            supabase.rpc, "deduct_spirit_stones", {"uid": user_id, "amount": cost}
        )
        if not success or not success.data:
            return False, "扣除灵石失败"
        
        new_sect = {
            "sect_name": sect_name,
            "description": description,
            "category": category,
            "founder_id": user_id,
            "leader_id": user_id,
            "member_count": 1,
            "max_members": 50,
            "is_open_join": False,
            "spirit_stones": 0
        }
        result = safe_db_operation(
            supabase.table("sects").insert(new_sect).execute
        )
        if not result or not result.data:
            return False, "创建宗门失败"
        
        safe_db_operation(
            supabase.table("sect_members").insert({
                "sect_id": result.data[0]["id"],
                "user_id": user_id,
                "role": "leader"
            }).execute
        )
        return True, f"✅ 宗门「{sect_name}」创建成功！"

    @staticmethod
    def join_sect(user_id: str, sect_id: str) -> Tuple[bool, str]:
        sect = safe_db_operation(
            supabase.table("sects").select("*").eq("id", sect_id).execute
        )
        if not sect or not sect.data:
            return False, "宗门不存在"
        sect_data = sect.data[0]
        
        if sect_data["member_count"] >= sect_data["max_members"]:
            return False, "宗门人数已达上限"
        
        current_sect = SectSystem.get_user_sect(user_id)
        if current_sect:
            return False, f"你已是「{current_sect['sect_name']}」成员"
        
        if sect_data["is_open_join"]:
            safe_db_operation(
                supabase.table("sect_members").insert({
                    "sect_id": sect_id,
                    "user_id": user_id,
                    "role": "member"
                }).execute
            )
            safe_db_operation(
                supabase.table("sects").update({
                    "member_count": sect_data["member_count"] + 1
                }).eq("id", sect_id).execute
            )
            return True, f"✅ 已加入「{sect_data['sect_name']}」！"
        else:
            existing_app = safe_db_operation(
                supabase.table("sect_applications").select("id").eq("sect_id", sect_id).eq("user_id", user_id).execute
            )
            if existing_app and existing_app.data:
                return False, "你已提交过申请，请等待审核"
            
            safe_db_operation(
                supabase.table("sect_applications").insert({
                    "sect_id": sect_id,
                    "user_id": user_id
                }).execute
            )
            return True, f"✅ 申请已提交，请等待「{sect_data['sect_name']}」宗主审核！"

# ==============================
# 🧪 炼丹房（增强版）
# ==============================
class AlchemySystem:
    @staticmethod
    def get_recipes() -> List[Dict[str, Any]]:
        """从数据库获取配方，并补充品级信息"""
        recipes = safe_db_operation(
            supabase.table("alchemy_recipes")
            .select("*, result_item:items(name), material_1:items!material_1_id(name), material_2:items!material_2_id(name)")
            .execute
        )
        if not recipes or not recipes.data:
            return []
        
        # 补充丹药品级（根据丹药设定.pdf）
        enhanced_recipes = []
        for recipe in recipes.data:
            name = recipe["name"]
            grade = "未知"
            
            # 突破丹药品级
            if "聚气凝元丹" in name:
                grade = "黄阶下品"
            elif "筑基建魂丹" in name:
                grade = "黄阶中品"
            elif "金液凝丹丸" in name:
                grade = "黄阶上品"
            elif "育婴温神丹" in name:
                grade = "玄阶下品"
            elif "化神聚念丹" in name:
                grade = "玄阶中品"
            elif "炼虚凝空丹" in name:
                grade = "玄阶上品"
            elif "合体融天丹" in name:
                grade = "地阶下品"
            elif "大乘聚元丹" in name:
                grade = "地阶中品"
            elif "渡劫护命丹" in name:
                grade = "地阶上品"
            elif "真仙凝气丹" in name:
                grade = "天阶下品"
            elif "玄仙凝道丹" in name:
                grade = "天阶中品"
            elif "金仙九转丹" in name:
                grade = "天阶上品"
            elif "太乙混元丹" in name:
                grade = "神阶下品"
            elif "大罗造化丹" in name:
                grade = "神阶中品"
            elif "圣人育道丹" in name:
                grade = "神阶上品"
            elif "准圣破界丹" in name:
                grade = "帝阶"
            elif "寰宇造化丹" in name:
                grade = "仙阶"
            elif "鸿蒙启元丹" in name:
                grade = "道阶"
            # 修为丹药品级
            elif "活血培元丸" in name:
                grade = "黄阶下品"
            elif "清心化气丹" in name:
                grade = "黄阶中品"
            elif "固基培元丹" in name:
                grade = "黄阶上品"
            elif "九转金丹" in name:
                grade = "玄阶下品"
            elif "化婴融魂丹" in name:
                grade = "玄阶中品"
            elif "凝神固魄丹" in name:
                grade = "玄阶上品"
            elif "虚空炼元丹" in name:
                grade = "地阶下品"
            elif "混元合道丹" in name:
                grade = "地阶中品"
            elif "圣元造化丹" in name:
                grade = "地阶上品"
            elif "天地护道丹" in name:
                grade = "天阶下品"
            elif "太乙真仙丹" in name:
                grade = "天阶中品"
            elif "九转玄仙丹" in name:
                grade = "天阶上品"
            elif "金仙镇道丹" in name:
                grade = "神阶下品"
            elif "太乙破妄丹" in name:
                grade = "神阶中品"
            elif "大罗镇世丹" in name:
                grade = "神阶上品"
            elif "圣人衍化丹" in name:
                grade = "神阶极品"
            elif "准圣明道丹" in name:
                grade = "仙阶"
            elif "寰宇镇世丹" in name:
                grade = "帝阶"
            elif "鸿蒙衍道丹" in name:
                grade = "道阶"
            
            recipe["grade"] = grade
            enhanced_recipes.append(recipe)
        
        return enhanced_recipes

    @staticmethod
    def craft(user_id: str, recipe_id: int) -> Tuple[bool, str]:
        recipes = safe_db_operation(
            supabase.table("alchemy_recipes").select("*").eq("id", recipe_id).execute
        )
        if not recipes or not recipes.data:
            return False, "配方不存在"
        recipe = recipes.data[0]
        
        # 检查材料
        inv = AlchemySystem.get_user_inventory_dict(user_id)
        mat1_id, mat1_qty = recipe["material_1_id"], recipe["material_1_qty"]
        mat2_id, mat2_qty = recipe["material_2_id"], recipe["material_2_qty"]
        
        if inv.get(mat1_id, 0) < mat1_qty:
            return False, f"缺少材料：{recipe['material_1']['name']} x{mat1_qty}"
        if mat2_id and inv.get(mat2_id, 0) < mat2_qty:
            return False, f"缺少材料：{recipe['material_2']['name']} x{mat2_qty}"
        
        # 扣除灵石
        cost = recipe["spirit_stone_cost"]
        users = safe_db_operation(
            supabase.table("users").select("spirit_stones").eq("id", user_id).execute
        )
        if not users or users.data[0]["spirit_stones"] < cost:
            return False, f"灵石不足，需要 {cost}"
        
        safe_db_operation(
            supabase.rpc, "deduct_spirit_stones", {"uid": user_id, "amount": cost}
        )
        
        # 扣除材料
        AlchemySystem._remove_item(user_id, mat1_id, mat1_qty)
        if mat2_id:
            AlchemySystem._remove_item(user_id, mat2_id, mat2_qty)
        
        # 产出结果（简化：100%成功）
        result_id = recipe["result_item_id"]
        AlchemySystem._add_item(user_id, result_id, 1)
        return True, f"✅ 炼制成功！获得 {recipe['result_item']['name']} x1"

    @staticmethod
    def get_user_inventory_dict(user_id: str) -> Dict[int, int]:
        inv = safe_db_operation(
            supabase.table("user_inventory").select("item_id, quantity").eq("user_id", user_id).execute
        )
        return {item["item_id"]: item["quantity"] for item in (inv.data if inv else [])}

    @staticmethod
    def _remove_item(user_id: str, item_id: int, qty: int):
        inv = safe_db_operation(
            supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute
        )
        if inv and inv.data:
            current = inv.data[0]
            new_qty = current["quantity"] - qty
            if new_qty <= 0:
                safe_db_operation(
                    supabase.table("user_inventory").delete().eq("id", current["id"]).execute
                )
            else:
                safe_db_operation(
                    supabase.table("user_inventory").update({"quantity": new_qty}).eq("id", current["id"]).execute
                )

    @staticmethod
    def _add_item(user_id: str, item_id: int, qty: int):
        inv = safe_db_operation(
            supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute
        )
        if inv and inv.data:
            current = inv.data[0]
            safe_db_operation(
                supabase.table("user_inventory").update({"quantity": current["quantity"] + qty}).eq("id", current["id"]).execute
            )
        else:
            safe_db_operation(
                supabase.table("user_inventory").insert({
                    "user_id": user_id,
                    "item_id": item_id,
                    "quantity": qty
                }).execute
            )

# ==============================
# 🔨 炼器坊（增强版）
# ==============================
class ForgeSystem:
    @staticmethod
    def get_blueprints() -> List[Dict[str, Any]]:
        """从数据库获取图纸，并补充材料加成"""
        blueprints = safe_db_operation(
            supabase.table("forge_blueprints")
            .select("*, result_item:items(name), material_1:items!material_1_id(name), material_2:items!material_2_id(name)")
            .execute
        )
        if not blueprints or not blueprints.data:
            return []
        
        # 补充材料攻击加成
        enhanced_blueprints = []
        for bp in blueprints.data:
            # 计算总攻击加成
            total_bonus = 0
            if bp["material_1"]["name"] in FORGE_MATERIAL_BONUS:
                total_bonus += FORGE_MATERIAL_BONUS[bp["material_1"]["name"]]
            if bp.get("material_2") and bp["material_2"]["name"] in FORGE_MATERIAL_BONUS:
                total_bonus += FORGE_MATERIAL_BONUS[bp["material_2"]["name"]]
            
            bp["attack_bonus"] = round(total_bonus, 1)
            enhanced_blueprints.append(bp)
        
        return enhanced_blueprints

    @staticmethod
    def craft(user_id: str, blueprint_id: int) -> Tuple[bool, str]:
        blueprints = safe_db_operation(
            supabase.table("forge_blueprints").select("*").eq("id", blueprint_id).execute
        )
        if not blueprints or not blueprints.data:
            return False, "图纸不存在"
        bp = blueprints.data[0]
        
        inv = ForgeSystem.get_user_inventory_dict(user_id)
        mat1_id, mat1_qty = bp["material_1_id"], bp["material_1_qty"]
        mat2_id, mat2_qty = bp["material_2_id"], bp["material_2_qty"]
        
        if inv.get(mat1_id, 0) < mat1_qty:
            return False, f"缺少材料：{bp['material_1']['name']} x{mat1_qty}"
        if mat2_id and inv.get(mat2_id, 0) < mat2_qty:
            return False, f"缺少材料：{bp['material_2']['name']} x{mat2_qty}"
        
        cost = bp["spirit_stone_cost"]
        users = safe_db_operation(
            supabase.table("users").select("spirit_stones").eq("id", user_id).execute
        )
        if not users or users.data[0]["spirit_stones"] < cost:
            return False, f"灵石不足，需要 {cost}"
        
        safe_db_operation(
            supabase.rpc, "deduct_spirit_stones", {"uid": user_id, "amount": cost}
        )
        
        # 扣除材料
        ForgeSystem._remove_item(user_id, mat1_id, mat1_qty)
        if mat2_id:
            ForgeSystem._remove_item(user_id, mat2_id, mat2_qty)
        
        # 产出结果（简化：100%成功）
        result_id = bp["result_item_id"]
        ForgeSystem._add_item(user_id, result_id, 1)
        return True, f"✅ 打造成功！获得 {bp['result_item']['name']} x1"

    @staticmethod
    def get_user_inventory_dict(user_id: str) -> Dict[int, int]:
        inv = safe_db_operation(
            supabase.table("user_inventory").select("item_id, quantity").eq("user_id", user_id).execute
        )
        return {item["item_id"]: item["quantity"] for item in (inv.data if inv else [])}

    @staticmethod
    def _remove_item(user_id: str, item_id: int, qty: int):
        inv = safe_db_operation(
            supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute
        )
        if inv and inv.data:
            current = inv.data[0]
            new_qty = current["quantity"] - qty
            if new_qty <= 0:
                safe_db_operation(
                    supabase.table("user_inventory").delete().eq("id", current["id"]).execute
                )
            else:
                safe_db_operation(
                    supabase.table("user_inventory").update({"quantity": new_qty}).eq("id", current["id"]).execute
                )

    @staticmethod
    def _add_item(user_id: str, item_id: int, qty: int):
        inv = safe_db_operation(
            supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute
        )
        if inv and inv.data:
            current = inv.data[0]
            safe_db_operation(
                supabase.table("user_inventory").update({"quantity": current["quantity"] + qty}).eq("id", current["id"]).execute
            )
        else:
            safe_db_operation(
                supabase.table("user_inventory").insert({
                    "user_id": user_id,
                    "item_id": item_id,
                    "quantity": qty
                }).execute
            )

# ==============================
# 🌀 阵法堂
# ==============================
class ArraySystem:
    @staticmethod
    def get_arrays() -> List[Dict[str, Any]]:
        arrays = safe_db_operation(
            supabase.table("arrays").select("*").execute
        )
        return arrays.data if arrays else []

    @staticmethod
    def activate(user_id: str, array_id: int) -> Tuple[bool, str]:
        arrays = safe_db_operation(
            supabase.table("arrays").select("*").eq("id", array_id).execute
        )
        if not arrays or not arrays.data:
            return False, "阵法不存在"
        arr = arrays.data[0]
        
        cost = arr["spirit_stone_cost"]
        users = safe_db_operation(
            supabase.table("users").select("spirit_stones").eq("id", user_id).execute
        )
        if not users or users.data[0]["spirit_stones"] < cost:
            return False, f"灵石不足，需要 {cost}"
        
        safe_db_operation(
            supabase.rpc, "deduct_spirit_stones", {"uid": user_id, "amount": cost}
        )
        
        expire_time = datetime.now() + timedelta(minutes=arr["duration_minutes"])
        safe_db_operation(
            supabase.table("user_progress").upsert({
                "user_id": user_id,
                "active_array_id": array_id,
                "array_expire_time": expire_time.isoformat()
            }).execute
        )
        
        return True, f"✅ 阵法「{arr['name']}」已激活，持续 {arr['duration_minutes']} 分钟！"

# ==============================
# 🕳️ 秘境副本
# ==============================
class DungeonSystem:
    @staticmethod
    def get_dungeons() -> List[Dict[str, Any]]:
        dungeons = safe_db_operation(
            supabase.table("dungeons").select("*, reward_item:items(name)").execute
        )
        return dungeons.data if dungeons else []

    @staticmethod
    def enter(user_id: str, dungeon_id: int) -> Tuple[bool, str]:
        dungeons = safe_db_operation(
            supabase.table("dungeons").select("*").eq("id", dungeon_id).execute
        )
        if not dungeons or not dungeons.data:
            return False, "秘境不存在"
        dungeon = dungeons.data[0]
        
        # 检查冷却
        progress = safe_db_operation(
            supabase.table("user_progress").select("last_dungeon_time").eq("user_id", user_id).execute
        )
        if progress and progress.data:
            last_time = progress.data[0]["last_dungeon_time"]
            if last_time:
                last = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                cooldown = timedelta(hours=dungeon["cooldown_hours"])
                if datetime.now() < last + cooldown:
                    wait = (last + cooldown - datetime.now()).total_seconds() / 3600
                    return False, f"秘境冷却中，还需 {wait:.1f} 小时"
        
        # 检查等级
        users = safe_db_operation(
            supabase.table("users").select("cultivation_level").eq("id", user_id).execute
        )
        if not users or users.data[0]["cultivation_level"] < dungeon["required_level"]:
            return False, f"需要 {dungeon['required_level']} 级才能进入"
        
        # 通关奖励
        spirit_reward = dungeon["reward_spirit_stones"]
        item_reward_id = dungeon["reward_item_id"]
        item_reward_qty = dungeon["reward_item_qty"]
        
        # 发放奖励
        safe_db_operation(
            supabase.rpc, "add_spirit_stones", {"uid": user_id, "amount": spirit_reward}
        )
        if item_reward_id:
            Backpack._add_item(user_id, item_reward_id, item_reward_qty)
        
        # 更新冷却
        safe_db_operation(
            supabase.table("user_progress").upsert({
                "user_id": user_id,
                "last_dungeon_time": get_current_time_str()
            }).execute
        )
        
        msg = f"✅ 通关「{dungeon['name']}」！获得 {spirit_reward:,} 灵石"
        if item_reward_id:
            msg += f" 和 {dungeon['reward_item']['name']} x{item_reward_qty}"
        return True, msg

# ==============================
# 🖥️ 页面路由与UI
# ==============================
def show_login_page():
    st.set_page_config(page_title="寰宇系统 - 登录", layout="centered")
    st.title("🌌 寰宇系统")
    st.markdown("欢迎来到修真世界！踏入仙途，成就大道。")
    
    tab1, tab2 = st.tabs(["🔑 登录", "會員註冊"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("道号（用户名）")
            password = st.text_input("密令（密码）", type="password")
            submit = st.form_submit_button("登入修仙界")
            
            if submit:
                if not username or not password:
                    st.error("请输入用户名和密码")
                else:
                    user = User.login(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = 'main'
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("新道号（2-20字符）")
            new_password = st.text_input("设置密令（至少6位）", type="password")
            confirm_password = st.text_input("确认密令", type="password")
            submit = st.form_submit_button("踏入仙途")
            
            if submit:
                if len(new_username) < 2 or len(new_username) > 20:
                    st.error("道号长度需在2-20字符之间")
                elif len(new_password) < 6:
                    st.error("密令至少6位")
                elif new_password != confirm_password:
                    st.error("两次输入的密令不一致")
                else:
                    existing = safe_db_operation(
                        supabase.table("users").select("id").eq("username", new_username).execute
                    )
                    if existing and existing.data:
                        st.error("该道号已被占用")
                    else:
                        new_user_data = {
                            "username": new_username,
                            "password_hash": hash_password(new_password),
                            "spirit_stones": 1000,
                            "cultivation_level": 1,
                            "realm": "练气",
                            "stage": 1,
                            "hp": 100,
                            "mp": 50,
                            "attack": 10,
                            "defense": 5,
                            "lifespan": 80,
                            "last_login": get_current_time_str()
                        }
                        result = safe_db_operation(
                            supabase.table("users").insert(new_user_data).execute
                        )
                        if result and result.data:
                            user = User(result.data[0])
                            ensure_user_cultivation_record(user.id)
                            st.session_state.user = user
                            st.session_state.page = 'main'
                            st.success("注册成功！欢迎踏入修仙界！")
                            st.rerun()
                        else:
                            st.error("注册失败，请稍后再试")

def show_main_page():
    st.set_page_config(page_title="寰宇系统 - 主城", layout="wide")
    
    with st.sidebar:
        st.title(f"👤 {st.session_state.user.username}")
        user = st.session_state.user
        st.write(f"境界: {user.realm} {user.stage}层")
        st.write(f"灵石: {user.spirit_stones:,} 💎")
        st.write(f"生命: {user.hp} ❤️")
        st.write(f"攻击: {user.attack} ⚔️")
        st.write(f"防御: {user.defense} 🛡️")
        
        current_sect = SectSystem.get_user_sect(user.id)
        if current_sect:
            st.write(f"宗门: {current_sect['sect_name']}")
        else:
            st.write("宗门: 散修")
        
        st.markdown("---")
        st.subheader("🧭 导航")
        
        # 构建导航菜单（只添加选项）
        nav_options = ["🏠 主城", "🏪 藏宝阁", "🎒 背包"]
        if FEATURES["sect"]:
            nav_options.append("🏯 宗门")
        if FEATURES["alchemy"]:
            nav_options.append("🧪 炼丹房")
        if FEATURES["forge"]:
            nav_options.append("🔨 炼器坊")
        if FEATURES["array"]:
            nav_options.append("🌀 阵法堂")
        if FEATURES["dungeon"]:
            nav_options.append("🕳️ 秘境")
        
        # 管理员和主管理员入口（独立于功能开关）
        if user.is_admin:
            nav_options.append("🛠️ 管理中心")
        if user.username == "轩璃":
            nav_options.append("👑 轩璃专属")
        
        # 显示导航选择器
        selected_nav = st.radio("选择功能", nav_options)
        
        if st.button("🚪 退出登录"):
            st.session_state.clear()
            st.rerun()

    # ========== 页面跳转逻辑（与菜单构建完全分离）==========
    if selected_nav == "🏠 主城":
        st.title("🌌 寰宇主城")
        st.markdown("""
        欢迎来到寰宇主城！这里是修真世界的中心。
        修行之路，始于足下。祝你早日证道成圣！
        """)
        
        cols = st.columns(2)
        buttons = [
            ("🏪 藏宝阁", "shop"),
            ("🏯 宗门", "sect"),
            ("🧪 炼丹房", "alchemy"),
            ("🔨 炼器坊", "forge"),
            ("🌀 阵法堂", "array"),
            ("🕳️ 秘境", "dungeon")
        ]
        for i, (label, page) in enumerate(buttons):
            with cols[i % 2]:
                if st.button(label):
                    st.session_state.page = page
                    st.rerun()
    
    elif selected_nav == "🏪 藏宝阁":
        st.session_state.page = 'shop'
        st.rerun()
    elif selected_nav == "🎒 背包":
        st.session_state.page = 'backpack'
        st.rerun()
    elif selected_nav == "🏯 宗门":
        st.session_state.page = 'sect'
        st.rerun()
    elif selected_nav == "🧪 炼丹房":
        st.session_state.page = 'alchemy'
        st.rerun()
    elif selected_nav == "🔨 炼器坊":
        st.session_state.page = 'forge'
        st.rerun()
    elif selected_nav == "🌀 阵法堂":
        st.session_state.page = 'array'
        st.rerun()
    elif selected_nav == "🕳️ 秘境":
        st.session_state.page = 'dungeon'
        st.rerun()
    elif selected_nav == "🛠️ 管理中心":
        st.session_state.page = 'admin'
        st.rerun()
    elif selected_nav == "👑 轩璃专属":
        st.session_state.page = 'xuanli_admin'
        st.rerun()

def show_shop_page():
    if not FEATURES["shop"]:
        st.warning("藏宝阁暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 藏宝阁", layout="wide")
    st.title("🏪 藏宝阁 · 丹药材料商店")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    items = TreasurePavilion.get_all_items()
    if not items:
        st.info("藏宝阁暂无商品上架")
        return
    
    categories = {}
    for item in items:
        cat = item.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    for category, cat_items in categories.items():
        st.subheader(f"📦 {category}")
        for item in cat_items:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{item['name']}**")
                    st.caption(item.get("effect", ""))
                    st.write(f"💰 价格: {item['price']:,} 灵石")
                    if "stock" in item and item["stock"] < 999999:
                        st.write(f"📦 库存: {item['stock']}")
                with col2:
                    qty = st.number_input("数量", min_value=1, max_value=999, value=1, key=f"qty_{item['id']}")
                with col3:
                    if st.button("🛒 购买", key=f"buy_{item['id']}"):
                        success, msg = TreasurePavilion.buy_item(st.session_state.user.id, item["id"], qty)
                        if success:
                            users = safe_db_operation(
                                supabase.table("users").select("*").eq("id", st.session_state.user.id).execute
                            )
                            if users and users.data:
                                st.session_state.user = User(users.data[0])
                            st.toast(msg, icon="✅")
                            st.rerun()
                        else:
                            st.toast(msg, icon="❌")

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Item:
    """物品类"""
    id: str
    name: str
    category: str
    effect: str
    usable: bool = False
    rarity: str = "普通"
    description: str = ""

@dataclass
class InventoryItem:
    """库存物品类"""
    item_id: str
    quantity: int
    acquired_date: str
    user_id: str

class BackpackManager:
    """背包管理器 - 每个用户独立背包"""
    
    def __init__(self):
        # 初始化背包数据存储
        if 'backpack_data' not in st.session_state:
            st.session_state.backpack_data = {}
    
    def get_user_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户背包物品列表"""
        if user_id not in st.session_state.backpack_data:
            st.session_state.backpack_data[user_id] = []
        return st.session_state.backpack_data[user_id]
    
    def add_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """添加物品到用户背包"""
        if user_id not in st.session_state.backpack_data:
            st.session_state.backpack_data[user_id] = []
        
        # 查找是否已有该物品
        for inv_item in st.session_state.backpack_data[user_id]:
            if inv_item['item_id'] == item_id:
                inv_item['quantity'] += quantity
                return True
        
        # 如果没有该物品则新增
        new_inv_item = {
            'item_id': item_id,
            'quantity': quantity,
            'acquired_date': datetime.now().isoformat(),
            'user_id': user_id
        }
        st.session_state.backpack_data[user_id].append(new_inv_item)
        return True
    
    def remove_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """从用户背包移除物品"""
        if user_id not in st.session_state.backpack_data:
            return False
            
        for i, inv_item in enumerate(st.session_state.backpack_data[user_id]):
            if inv_item['item_id'] == item_id:
                if inv_item['quantity'] >= quantity:
                    inv_item['quantity'] -= quantity
                    if inv_item['quantity'] <= 0:
                        # 数量为0时完全移除物品
                        st.session_state.backpack_data[user_id].pop(i)
                    return True
                else:
                    # 数量不足
                    return False
        return False  # 物品不存在
    
    def use_item(self, user_id: str, item_id: str, item_details: Dict[str, Any]) -> tuple[bool, str]:
        """使用物品"""
        if user_id not in st.session_state.backpack_data:
            return False, "背包为空"
        
        # 检查物品是否存在及数量
        item_found = False
        for inv_item in st.session_state.backpack_data[user_id]:
            if inv_item['item_id'] == item_id:
                if inv_item['quantity'] <= 0:
                    return False, "物品数量不足"
                item_found = True
                break
        
        if not item_found:
            return False, "物品不存在"
        
        # 执行使用操作
        result = self.remove_item(user_id, item_id, 1)
        if result:
            # 这里可以根据物品类型执行不同效果
            effect_msg = f"成功使用了1个{item_details.get('name', '物品')}！"
            if item_details.get('effect'):
                effect_msg += f"\n效果: {item_details.get('effect')}"
            return True, effect_msg
        else:
            return False, "使用失败"

    def get_item_quantity(self, user_id: str, item_id: str) -> int:
        """获取用户特定物品的数量"""
        if user_id not in st.session_state.backpack_data:
            return 0
        
        for inv_item in st.session_state.backpack_data[user_id]:
            if inv_item['item_id'] == item_id:
                return inv_item['quantity']
        return 0

    def has_item(self, user_id: str, item_id: str, required_quantity: int = 1) -> bool:
        """检查用户是否有足够数量的指定物品"""
        current_quantity = self.get_item_quantity(user_id, item_id)
        return current_quantity >= required_quantity

# 实例化背包管理器
Backpack = BackpackManager()

# 物品数据库示例
ITEM_DATABASE = {
    "health_potion": Item(
        id="health_potion",
        name="生命药水",
        category="消耗品",
        effect="恢复100点生命值",
        usable=True,
        rarity="普通",
        description="一瓶蓝色的药水，能快速恢复生命力"
    ),
    "mana_potion": Item(
        id="mana_potion",
        name="法力药水",
        category="消耗品",
        effect="恢复50点法力值",
        usable=True,
        rarity="普通",
        description="一瓶紫色的药水，能快速恢复法力"
    ),
    "exp_scroll": Item(
        id="exp_scroll",
        name="经验卷轴",
        category="道具",
        effect="获得100点经验值",
        usable=True,
        rarity="稀有",
        description="古老的卷轴，蕴含着神秘的经验之力"
    ),
    "gold_coin": Item(
        id="gold_coin",
        name="金币",
        category="货币",
        effect="通用货币",
        usable=False,
        rarity="普通",
        description="游戏中的通用货币"
    )
}

def show_backpack_page():
    if not st.session_state.get('features', {}).get("backpack", True):  # 默认开启背包功能
        st.warning("背包功能暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 背包", layout="wide")
    st.title("🎒 个人背包")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    # 获取当前用户ID
    user_id = st.session_state.get('user', {}).get('id', 'default_user')
    
    # 获取用户背包
    inventory = Backpack.get_user_inventory(user_id)
    
    if not inventory:
        st.info("背包空空如也，快去藏宝阁逛逛吧！")
        # 提供一些测试按钮来添加物品
        st.subheader("测试功能 - 添加物品")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("添加生命药水"):
                Backpack.add_item(user_id, "health_potion", 3)
                st.rerun()
        
        with col2:
            if st.button("添加法力药水"):
                Backpack.add_item(user_id, "mana_potion", 2)
                st.rerun()
        
        with col3:
            if st.button("添加金币"):
                Backpack.add_item(user_id, "gold_coin", 50)
                st.rerun()
        
        return
    
    st.write(f"共 {len(inventory)} 种物品")
    
    # 显示背包内容
    for inv_item in inventory:
        # 获取物品详情
        item = ITEM_DATABASE.get(inv_item['item_id'], 
                                Item(id=inv_item['item_id'], name='未知物品', category='其他', effect='无'))
        
        with st.expander(f"{item.name} x{inv_item['quantity']} ({item.rarity})"):
            st.write(f"**类别**: {item.category}")
            st.write(f"**效果**: {item.effect}")
            st.write(f"**描述**: {item.description}")
            st.write(f"**获得时间**: {inv_item['acquired_date'][:19].replace('T', ' ')}")
            
            if item.usable:
                if st.button("✨ 使用", key=f"use_{inv_item['item_id']}"):
                    success, msg = Backpack.use_item(
                        user_id, 
                        inv_item["item_id"], 
                        item.__dict__
                    )
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()  # 重新加载页面以更新背包状态
                    else:
                        st.toast(msg, icon="❌")
            
            # 提供丢弃功能
            if st.button("🗑️ 丢弃", key=f"discard_{inv_item['item_id']}"):
                # 弹出确认对话框
                if 'show_confirm_discard' not in st.session_state:
                    st.session_state.show_confirm_discard = None
                
                st.session_state.show_confirm_discard = inv_item['item_id']
                
                # 显示确认弹窗
                with st.popover("确认丢弃?"):
                    st.write(f"确定要丢弃 {item.name} 吗?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("确认", key=f"confirm_discard_{inv_item['item_id']}"):
                            # 丢弃全部该物品
                            Backpack.remove_item(user_id, inv_item['item_id'], inv_item['quantity'])
                            st.session_state.show_confirm_discard = None
                            st.rerun()
                    with col2:
                        if st.button("取消", key=f"cancel_discard_{inv_item['item_id']}"):
                            st.session_state.show_confirm_discard = None
                            st.rerun()

# 模拟用户对象用于测试
class MockUser:
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name

# 测试函数
def test_backpack_system():
    """测试背包系统功能"""
    st.header("背包系统测试")
    
    # 初始化用户
    if 'test_user' not in st.session_state:
        st.session_state.test_user = MockUser('test_user_001', '测试用户')
        st.session_state.user = st.session_state.test_user
    
    # 显示当前背包状态
    st.subheader(f"用户 {st.session_state.user.name} 的背包")
    inventory = Backpack.get_user_inventory(st.session_state.user.id)
    for item in inventory:
        item_detail = ITEM_DATABASE.get(item['item_id'])
        if item_detail:
            st.write(f"- {item_detail.name}: {item['quantity']} 个")
    
    # 测试操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("添加生命药水"):
            Backpack.add_item(st.session_state.user.id, "health_potion", 5)
            st.success("已添加5瓶生命药水")
    
    with col2:
        if st.button("使用生命药水"):
            item_detail = ITEM_DATABASE.get("health_potion")
            success, msg = Backpack.use_item(
                st.session_state.user.id, 
                "health_potion", 
                item_detail.__dict__ if item_detail else {}
            )
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    with col3:
        if st.button("查看背包数据"):
            st.json(st.session_state.backpack_data)

def show_sect_page():
    if not FEATURES["sect"]:
        st.warning("宗门系统暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 宗门", layout="wide")
    st.title("🏯 宗门系统")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    user = st.session_state.user
    current_sect = SectSystem.get_user_sect(user.id)
    
    # ========== 无宗门状态：浏览/创建 ==========
    if not current_sect:
        st.info("你目前是散修，可选择加入现有宗门或创建自己的宗门。")
        all_sects = SectSystem.get_all_sects()
        if not all_sects:
            st.info("暂无宗门")
        else:
            for category in SECT_CATEGORIES:
                sects_in_cat = [s for s in all_sects if s["category"] == category]
                if sects_in_cat:
                    st.subheader(f"🔹 {category}")
                    for sect in sects_in_cat:
                        with st.container(border=True):
                            st.markdown(f"**{sect['sect_name']}**")
                            st.caption(sect["description"])
                            st.write(f"成员: {sect['member_count']} / {sect['max_members']}")
                            if st.button(f"➕ 申请加入「{sect['sect_name']}」", key=f"join_{sect['id']}"):
                                success, msg = SectSystem.join_sect(user.id, sect["id"])
                                if success:
                                    st.toast(msg, icon="✅")
                                    st.rerun()
                                else:
                                    st.toast(msg, icon="❌")
        
        st.markdown("---")
        st.subheader("🆕 创建宗门（仅散修）")
        with st.form("create_sect_form"):
            new_sect_name = st.text_input("宗门名称", max_chars=20)
            new_sect_desc = st.text_area("宗门描述", max_chars=200)
            new_category = st.selectbox("宗门类型", SECT_CATEGORIES)
            submitted = st.form_submit_button("创建宗门（消耗 100,000 灵石）")
            if submitted:
                if user.spirit_stones < 100000:
                    st.error("❌ 灵石不足！创建宗门需 100,000 灵石")
                elif not new_sect_name.strip():
                    st.error("❌ 宗门名称不能为空")
                else:
                    success, msg = SectSystem.create_sect(user.id, new_sect_name, new_sect_desc, new_category)
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.toast(msg, icon="❌")
        return

    # ========== 已有宗门：进入宗门内部 ==========
    # 顶部信息栏
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(f"🏛️ {current_sect['sect_name']}")
    with col2:
        st.write(f"**类型**: {current_sect['category']}")
    with col3:
        st.write(f"**资金**: {current_sect['spirit_stones']:,} 💎")

    # 宗门功能导航
    sect_tabs = ["📜 宗门概况", "👥 成员列表", "🌀 护山大阵", "🏪 宗门商店", "📋 宗门事务"]
    selected_tab = st.tabs(sect_tabs)

    # ========== TAB 1: 宗门概况 ==========
    with selected_tab[0]:
        st.write(f"**宗门宣言**: {current_sect.get('description', '无')}")
        st.write(f"**规模**: {current_sect['member_count']} / {current_sect['max_members']} 人")
        join_mode = "自由加入" if current_sect["is_open_join"] else "需审核"
        st.write(f"**加入方式**: {join_mode}")
        
        # 宗主管理
        is_leader = (current_sect["leader_id"] == user.id) or user.is_super_admin
        if is_leader:
            st.markdown("---")
            st.subheader("👑 宗主管理")
            with st.expander("⚙️ 修改宗门设置"):
                with st.form("update_sect_form"):
                    desc = st.text_area("宗门宣言", value=current_sect["description"], max_chars=200)
                    join_mode_sel = st.selectbox("加入方式", ["自由加入", "需审核"], 
                                                index=0 if current_sect["is_open_join"] else 1)
                    submit_update = st.form_submit_button("保存")
                    if submit_update:
                        update_data = {
                            "description": desc,
                            "is_open_join": (join_mode_sel == "自由加入")
                        }
                        safe_db_operation(
                            supabase.table("sects").update(update_data).eq("id", current_sect["id"]).execute
                        )
                        st.toast("✅ 宗门信息已更新", icon="💾")
                        st.rerun()

    # ========== TAB 2: 成员列表 ==========
    with selected_tab[1]:
        st.subheader("👥 宗门成员")
        try:
            members = supabase.table("users") \
                .select("id,username,realm,stage,spirit_stones") \
                .in_("id", current_sect.get("member_ids", [])) \
                .execute().data or []
        except:
            members = []
        
        for member in members:
            with st.container(border=True):
                role = "👑 宗主" if member["id"] == current_sect["leader_id"] else "弟子"
                st.markdown(f"**{member['username']}** ({role})")
                st.write(f"境界: {member['realm']} {member['stage']}层")
                if is_leader and member["id"] != user.id:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("踢出宗门", key=f"kick_{member['id']}"):
                            # TODO: 实现踢人逻辑（需更新 sect.member_ids）
                            st.toast("⚠️ 踢人功能待开发", icon="🛠️")
                    with col2:
                        if member["id"] == current_sect["leader_id"]:
                            if st.button("禅让宗主", key=f"transfer_{member['id']}"):
                                st.toast("⚠️ 禅让功能待开发", icon="🛠️")

    # ========== TAB 3: 护山大阵 ==========
    with selected_tab[2]:
        st.subheader("🌀 护山大阵")
        st.info("护山大阵可提升宗门防御、聚灵效率，需消耗宗门资金激活")
        
        # 模拟大阵数据（实际可存入数据库）
        arrays = [
            {"name": "九宫八卦阵", "level": 1, "effect": "防御+10%", "cost": 50000},
            {"name": "周天星斗大阵", "level": 3, "effect": "聚灵+20%", "cost": 200000},
            {"name": "诛仙剑阵", "level": 5, "effect": "攻击+30%", "cost": 500000}
        ]
        
        for arr in arrays:
            with st.expander(f"{arr['name']}（{arr['effect']}）"):
                st.write(f"**等级要求**: {arr['level']}阶宗门")
                st.write(f"**激活费用**: {arr['cost']:,} 灵石")
                if st.button(f"激活「{arr['name']}」", key=f"activate_{arr['name']}"):
                    if current_sect["spirit_stones"] >= arr["cost"]:
                        # 扣款（模拟）
                        new_funds = current_sect["spirit_stones"] - arr["cost"]
                        supabase.table("sects").update({"spirit_stones": new_funds}).eq("id", current_sect["id"]).execute()
                        st.toast(f"✅ 「{arr['name']}」已激活！", icon="✨")
                        st.rerun()
                    else:
                        st.error("❌ 宗门资金不足")

    # ========== TAB 4: 宗门商店 ==========
    with selected_tab[3]:
        st.subheader("🏪 宗门商店（仅本宗弟子可见）")
        sect_items = [
            {"name": "筑基丹", "price": 5000, "desc": "提升筑基成功率"},
            {"name": "玄铁剑", "price": 20000, "desc": "攻击+100"},
            {"name": "聚灵符", "price": 10000, "desc": "修炼速度+10%"},
        ]
        for item in sect_items:
            with st.container(border=True):
                st.markdown(f"**{item['name']}** - {item['price']:,} 💎")
                st.caption(item["desc"])
                if st.button(f"购买", key=f"buy_{item['name']}"):
                    if user.spirit_stones >= item["price"]:
                        # 扣用户灵石 + 加物品到背包（简化）
                        User.update_spirit_stones(user.id, -item["price"])
                        st.toast(f"✅ 购买 {item['name']} 成功！", icon="🛒")
                        st.rerun()
                    else:
                        st.error("❌ 灵石不足")

    # ========== TAB 5: 宗门事务 ==========
    with selected_tab[4]:
        st.subheader("📋 宗门公告")
        st.info("【宗主公告】近期将开启秘境试炼，请各位弟子做好准备！")
        
        st.markdown("---")
        st.subheader("💰 资金流水（最近5条）")
        # 模拟流水（实际应从 transaction_log 表读取）
        logs = [
            {"type": "收入", "amount": 5000, "desc": "弟子贡献", "time": "2026-02-20"},
            {"type": "支出", "amount": 10000, "desc": "购买材料", "time": "2026-02-19"},
        ]
        for log in logs:
            color = "green" if log["type"] == "收入" else "red"
            st.markdown(f"<span style='color:{color}'>● {log['time']} {log['desc']} {log['amount']:,} 💎</span>", unsafe_allow_html=True)

    # ========== 底部：退出宗门 ==========
    st.markdown("---")
    if st.button("🚪 退出宗门"):
        st.warning("退出宗门将失去所有宗门权益，确认？")
        if st.button("✅ 确认退出"):
            # TODO: 实现退出逻辑
            st.toast("⚠️ 退出功能待开发", icon="🛠️")

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import random

@dataclass
class Item:
    """物品类"""
    id: str
    name: str
    category: str
    effect: str
    usable: bool = False
    rarity: str = "普通"
    description: str = ""
    attack_bonus: int = 0  # 武器类物品的攻击加成

@dataclass
class Recipe:
    """炼丹配方"""
    id: str
    name: str
    grade: str
    result_item: Item
    material_1: Item
    material_1_qty: int
    material_2: Optional[Item] = None
    material_2_qty: int = 0
    spirit_stone_cost: int = 0
    success_rate: float = 1.0  # 成功率

@dataclass
class Blueprint:
    """炼器图纸"""
    id: str
    name: str
    result_item: Item
    material_1: Item
    material_1_qty: int
    material_2: Optional[Item] = None
    material_2_qty: int = 0
    spirit_stone_cost: int = 0
    success_rate: float = 0.8  # 成功率
    attack_bonus: int = 0

class BackpackManager:
    """背包管理器 - 每个用户独立背包"""
    
    def __init__(self):
        # 初始化背包数据存储
        if 'backpack_data' not in st.session_state:
            st.session_state.backpack_data = {}
    
    def get_user_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户背包物品列表"""
        if user_id not in st.session_state.backpack_data:
            st.session_state.backpack_data[user_id] = []
        return st.session_state.backpack_data[user_id]
    
    def add_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """添加物品到用户背包"""
        if user_id not in st.session_state.backpack_data:
            st.session_state.backpack_data[user_id] = []
        
        # 查找是否已有该物品
        for inv_item in st.session_state.backpack_data[user_id]:
            if inv_item['item_id'] == item_id:
                inv_item['quantity'] += quantity
                return True
        
        # 如果没有该物品则新增
        new_inv_item = {
            'item_id': item_id,
            'quantity': quantity,
            'acquired_date': datetime.now().isoformat(),
            'user_id': user_id
        }
        st.session_state.backpack_data[user_id].append(new_inv_item)
        return True
    
    def remove_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """从用户背包移除物品"""
        if user_id not in st.session_state.backpack_data:
            return False
            
        for i, inv_item in enumerate(st.session_state.backpack_data[user_id]):
            if inv_item['item_id'] == item_id:
                if inv_item['quantity'] >= quantity:
                    inv_item['quantity'] -= quantity
                    if inv_item['quantity'] <= 0:
                        # 数量为0时完全移除物品
                        st.session_state.backpack_data[user_id].pop(i)
                    return True
                else:
                    # 数量不足
                    return False
        return False  # 物品不存在
    
    def get_item_quantity(self, user_id: str, item_id: str) -> int:
        """获取用户特定物品的数量"""
        if user_id not in st.session_state.backpack_data:
            return 0
        
        for inv_item in st.session_state.backpack_data[user_id]:
            if inv_item['item_id'] == item_id:
                return inv_item['quantity']
        return 0

    def has_items(self, user_id: str, required_items: Dict[str, int]) -> bool:
        """检查用户是否有足够的材料"""
        for item_id, required_qty in required_items.items():
            if self.get_item_quantity(user_id, item_id) < required_qty:
                return False
        return True

    def consume_items(self, user_id: str, required_items: Dict[str, int]) -> bool:
        """消耗材料"""
        for item_id, qty in required_items.items():
            if not self.remove_item(user_id, item_id, qty):
                return False
        return True

# 全局背包管理器实例
Backpack = BackpackManager()

class AlchemySystem:
    """炼丹系统"""
    
    @staticmethod
    def get_recipes() -> List[Recipe]:
        """获取所有炼丹配方"""
        # 示例配方数据
        recipes = [
            Recipe(
                id="health_elixir",
                name="回血丹",
                grade="初级",
                result_item=Item(
                    id="health_elixir_item",
                    name="回血丹",
                    category="丹药",
                    effect="恢复200点生命值",
                    usable=True,
                    rarity="普通",
                    description="基础疗伤丹药，可快速恢复生命"
                ),
                material_1=Item(id="herb_a", name="草药A", category="材料", effect="", usable=False),
                material_1_qty=3,
                material_2=Item(id="water_b", name="灵泉水", category="材料", effect="", usable=False),
                material_2_qty=1,
                spirit_stone_cost=100,
                success_rate=0.9
            ),
            Recipe(
                id="mana_elixir",
                name="回蓝丹",
                grade="初级",
                result_item=Item(
                    id="mana_elixir_item",
                    name="回蓝丹",
                    category="丹药",
                    effect="恢复150点法力值",
                    usable=True,
                    rarity="普通",
                    description="基础回魔丹药，可快速恢复法力"
                ),
                material_1=Item(id="herb_b", name="草药B", category="材料", effect="", usable=False),
                material_1_qty=3,
                material_2=Item(id="crystal_c", name="月光石", category="材料", effect="", usable=False),
                material_2_qty=1,
                spirit_stone_cost=120,
                success_rate=0.85
            )
        ]
        return recipes
    
    @staticmethod
    def craft(user_id: str, recipe_id: str) -> Tuple[bool, str]:
        """炼制丹药"""
        recipes = AlchemySystem.get_recipes()
        recipe = next((r for r in recipes if r.id == recipe_id), None)
        
        if not recipe:
            return False, "配方不存在"
        
        # 检查用户是否有足够的材料和灵石
        required_items = {
            recipe.material_1.id: recipe.material_1_qty
        }
        if recipe.material_2:
            required_items[recipe.material_2.id] = recipe.material_2_qty
        
        if not Backpack.has_items(user_id, required_items):
            return False, "材料不足"
        
        # 检查灵石余额（这里简化为假设用户有足够的灵石）
        # 实际应用中需要检查用户的灵石余额
        
        # 消耗材料
        if not Backpack.consume_items(user_id, required_items):
            return False, "消耗材料失败"
        
        # 检查成功率
        success = random.random() <= recipe.success_rate
        
        if success:
            # 添加产物到背包
            Backpack.add_item(user_id, recipe.result_item.id, 1)
            return True, f"炼制成功！获得了1个{recipe.result_item.name}"
        else:
            return False, f"炼制失败！{recipe.name}炼制失败了"

class ForgeSystem:
    """炼器系统"""
    
    @staticmethod
    def get_blueprints() -> List[Blueprint]:
        """获取所有炼器图纸"""
        blueprints = [
            Blueprint(
                id="iron_sword",
                name="铁剑",
                result_item=Item(
                    id="iron_sword_item",
                    name="铁剑",
                    category="武器",
                    effect="基础近战武器",
                    usable=False,
                    rarity="普通",
                    description="一把普通的铁剑",
                    attack_bonus=10
                ),
                material_1=Item(id="iron_ore", name="铁矿石", category="材料", effect="", usable=False),
                material_1_qty=5,
                material_2=Item(id="coal", name="煤炭", category="材料", effect="", usable=False),
                material_2_qty=2,
                spirit_stone_cost=200,
                success_rate=0.75,
                attack_bonus=10
            ),
            Blueprint(
                id="wooden_shield",
                name="木盾",
                result_item=Item(
                    id="wooden_shield_item",
                    name="木盾",
                    category="防具",
                    effect="提升防御力",
                    usable=False,
                    rarity="普通",
                    description="一面坚固的木制盾牌",
                    attack_bonus=0  # 防具不增加攻击
                ),
                material_1=Item(id="hardwood", name="硬木", category="材料", effect="", usable=False),
                material_1_qty=4,
                material_2=Item(id="leather", name="皮革", category="材料", effect="", usable=False),
                material_2_qty=1,
                spirit_stone_cost=150,
                success_rate=0.8,
                attack_bonus=0
            )
        ]
        return blueprints
    
    @staticmethod
    def craft(user_id: str, blueprint_id: str) -> Tuple[bool, str]:
        """打造装备"""
        blueprints = ForgeSystem.get_blueprints()
        blueprint = next((bp for bp in blueprints if bp.id == blueprint_id), None)
        
        if not blueprint:
            return False, "图纸不存在"
        
        # 检查用户是否有足够的材料和灵石
        required_items = {
            blueprint.material_1.id: blueprint.material_1_qty
        }
        if blueprint.material_2:
            required_items[blueprint.material_2.id] = blueprint.material_2_qty
        
        if not Backpack.has_items(user_id, required_items):
            return False, "材料不足"
        
        # 消耗材料
        if not Backpack.consume_items(user_id, required_items):
            return False, "消耗材料失败"
        
        # 检查成功率
        success = random.random() <= blueprint.success_rate
        
        if success:
            # 添加产物到背包
            Backpack.add_item(user_id, blueprint.result_item.id, 1)
            return True, f"打造成功！获得了1件{blueprint.result_item.name}"
        else:
            return False, f"打造失败！{blueprint.name}打造失败了"

def show_alchemy_page():
    if not st.session_state.get('features', {}).get("alchemy", True):  # 默认开启炼丹功能
        st.warning("炼丹房暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 炼丹房", layout="wide")
    st.title("🧪 炼丹房")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    recipes = AlchemySystem.get_recipes()
    if not recipes:
        st.info("暂无炼丹配方")
        return
    
    user_id = st.session_state.get('user', {}).get('id', 'default_user')
    
    for recipe in recipes:
        with st.container(border=True):
            # 显示丹药品级
            grade_badge = f" :gray[{recipe.grade}]"
            st.subheader(recipe["name"] + grade_badge)
            
            # 检查材料是否充足
            required_items = {
                recipe.material_1.id: recipe.material_1_qty
            }
            if recipe.material_2:
                required_items[recipe.material_2.id] = recipe.material_2_qty
            
            materials_sufficient = Backpack.has_items(user_id, required_items)
            
            st.write(f"**:green[产出]: {recipe.result_item.name} x1**")
            
            # 显示材料需求
            st.write("**材料需求:**")
            material1_qty = Backpack.get_item_quantity(user_id, recipe.material_1.id)
            material1_status = "✅" if material1_qty >= recipe.material_1_qty else "❌"
            st.write(f"  {material1_status} {recipe.material_1.name} x{recipe.material_1_qty} (拥有: {material1_qty})")
            
            if recipe.material_2:
                material2_qty = Backpack.get_item_quantity(user_id, recipe.material_2.id)
                material2_status = "✅" if material2_qty >= recipe.material_2_qty else "❌"
                st.write(f"  {material2_status} {recipe.material_2.name} x{recipe.material_2_qty} (拥有: {material2_qty})")
            
            st.write(f"**:purple[消耗]: {recipe.spirit_stone_cost:,} 灵石**")
            st.write(f"**:orange[成功率]: {int(recipe.success_rate * 100)}%**")
            
            # 根据材料是否充足启用按钮
            btn_disabled = not materials_sufficient
            btn_label = "🔥 开始炼制" if materials_sufficient else "❌ 材料不足"
            
            if st.button(btn_label, key=f"craft_alchemy_{recipe.id}", disabled=btn_disabled):
                success, msg = AlchemySystem.craft(user_id, recipe.id)
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_forge_page():
    if not st.session_state.get('features', {}).get("forge", True):  # 默认开启炼器功能
        st.warning("炼器坊暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 炼器坊", layout="wide")
    st.title("🔨 炼器坊")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    blueprints = ForgeSystem.get_blueprints()
    if not blueprints:
        st.info("暂无炼器图纸")
        return
    
    user_id = st.session_state.get('user', {}).get('id', 'default_user')
    
    for bp in blueprints:
        with st.container(border=True):
            st.subheader(bp.name)
            
            # 显示攻击加成
            if bp.attack_bonus > 0:
                st.write(f"**:blue[攻击加成: +{bp.attack_bonus} ⚔️]**")
            elif hasattr(bp.result_item, 'attack_bonus') and bp.result_item.attack_bonus > 0:
                st.write(f"**:blue[攻击加成: +{bp.result_item.attack_bonus} ⚔️]**")
            
            # 检查材料是否充足
            required_items = {
                bp.material_1.id: bp.material_1_qty
            }
            if bp.material_2:
                required_items[bp.material_2.id] = bp.material_2_qty
            
            materials_sufficient = Backpack.has_items(user_id, required_items)
            
            st.write(f"**:green[产出]: {bp.result_item.name} x1**")
            
            # 显示材料需求
            st.write("**材料需求:**")
            material1_qty = Backpack.get_item_quantity(user_id, bp.material_1.id)
            material1_status = "✅" if material1_qty >= bp.material_1_qty else "❌"
            st.write(f"  {material1_status} {bp.material_1.name} x{bp.material_1_qty} (拥有: {material1_qty})")
            
            if bp.material_2:
                material2_qty = Backpack.get_item_quantity(user_id, bp.material_2.id)
                material2_status = "✅" if material2_qty >= bp.material_2_qty else "❌"
                st.write(f"  {material2_status} {bp.material_2.name} x{bp.material_2_qty} (拥有: {material2_qty})")
            
            st.write(f"**:purple[消耗]: {bp.spirit_stone_cost:,} 灵石**")
            st.write(f"**:orange[成功率]: {int(bp.success_rate * 100)}%**")
            
            # 根据材料是否充足启用按钮
            btn_disabled = not materials_sufficient
            btn_label = "⚒️ 开始打造" if materials_sufficient else "❌ 材料不足"
            
            if st.button(btn_label, key=f"craft_forge_{bp.id}", disabled=btn_disabled):
                success, msg = ForgeSystem.craft(user_id, bp.id)
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_array_page():
    if not FEATURES["array"]:
        st.warning("阵法堂暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 阵法堂", layout="wide")
    st.title("🌀 阵法堂")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    arrays = ArraySystem.get_arrays()
    if not arrays:
        st.info("暂无可用阵法")
        return
    
    for arr in arrays:
        with st.container(border=True):
            st.subheader(arr["name"])
            st.write(arr["description"])
            st.write(f"效果: {arr['effect_type']} +{arr['effect_value']}")
            st.write(f"持续: {arr['duration_minutes']} 分钟")
            st.write(f"消耗: {arr['spirit_stone_cost']:,} 灵石")
            if st.button("🔮 激活阵法", key=f"activate_array_{arr['id']}"):
                success, msg = ArraySystem.activate(st.session_state.user.id, arr["id"])
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_dungeon_page():
    if not FEATURES["dungeon"]:
        st.warning("秘境暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 秘境", layout="wide")
    st.title("🕳️ 秘境挑战")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    dungeons = DungeonSystem.get_dungeons()
    if not dungeons:
        st.info("暂无秘境开放")
        return
    
    for dungeon in dungeons:
        with st.container(border=True):
            st.subheader(dungeon["name"])
            st.write(dungeon["description"])
            st.write(f"要求等级: {dungeon['required_level']}")
            st.write(f"冷却时间: {dungeon['cooldown_hours']} 小时")
            st.write(f"奖励: {dungeon['reward_spirit_stones']:,} 灵石")
            if dungeon.get("reward_item"):
                st.write(f"        {dungeon['reward_item']['name']} x{dungeon['reward_item_qty']}")
            if st.button("⚔️ 进入秘境", key=f"enter_dungeon_{dungeon['id']}"):
                success, msg = DungeonSystem.enter(st.session_state.user.id, dungeon["id"])
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_xuanli_admin_page():
    """轩璃专属超级管理界面"""
    if st.session_state.user.username != "轩璃":
        st.error("权限不足")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return

    st.set_page_config(page_title="寰宇系统 - 轩璃专属", layout="wide")
    st.title("👑 轩璃专属管理台")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["👥 用户管理", "💎 灵石发放", "📜 系统日志"])

    with tab1:
        st.subheader("所有用户")
        try:
            # 使用 Service Role Key 绕过 RLS（需配置环境变量）
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if service_role_key:
                admin_client = create_client(SUPABASE_URL, service_role_key)
                users = admin_client.table("users").select("*").execute().data
            else:
                # 降级：只显示当前用户（安全起见）
                users = [st.session_state.user.__dict__]
                st.warning("未配置 SERVICE_ROLE_KEY，仅显示当前用户")
            
            for u in users:
                with st.expander(f"{u['username']} (ID: {u['id']})"):
                    st.write(f"灵石: {u.get('spirit_stones', 0):,}")
                    st.write(f"境界: {u.get('realm', '未知')} {u.get('stage', '')}层")
                    is_banned = u.get("is_banned", False)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("封禁" if not is_banned else "解封", key=f"ban_{u['id']}"):
                            action = "is_banned" if not is_banned else "is_banned"
                            value = not is_banned
                            supabase.table("users").update({action: value}).eq("id", u["id"]).execute()
                            st.toast(f"✅ 已{'封禁' if value else '解封'} {u['username']}", icon="🛡️")
                            st.rerun()
                    with col2:
                        if st.button("删除", key=f"del_{u['id']}"):
                            supabase.table("users").delete().eq("id", u["id"]).execute()
                            st.toast(f"🗑️ 已删除 {u['username']}", icon="🔥")
                            st.rerun()
        except Exception as e:
            st.error(f"加载用户失败: {str(e)[:100]}")

    with tab2:
        st.subheader("批量发放灵石")
        all_users = supabase.table("users").select("id,username").execute().data
        usernames = [u["username"] for u in all_users]
        selected = st.multiselect("选择用户", usernames)
        amount = st.number_input("灵石数量", min_value=1, value=1000)
        if st.button("发放"):
            for u in all_users:
                if u["username"] in selected:
                    supabase.rpc("add_spirit_stones", {"uid": u["id"], "amount": amount}).execute()
            st.success(f"✅ 已向 {len(selected)} 人发放 {amount:,} 灵石")

    with tab3:
        st.subheader("最近操作日志（模拟）")
        st.info("日志功能待开发，当前仅显示时间")
        st.write(f"当前时间: {get_current_time_str()}")

# ==============================
# 🚀 主程序
# ==============================

import streamlit as st

CURRENT_VERSION = "1.0.0"  # 设置你的当前版本号

def show_login_page():
    st.title("登录页面")
    st.write("请登录...")
    # 添加实际的登录表单
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        # 登录逻辑
        st.session_state.user = username
        st.session_state.page = 'main'
        st.rerun()

def main_page():
    st.title("主页面")
    st.write("主页面内容")
    if st.button("登出"):
        st.session_state.user = None
        st.session_state.page = 'login'
        st.rerun()

def initialize_session_state():
    """初始化session state"""
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # 版本控制
    if 'system_version' not in st.session_state:
        st.session_state.system_version = CURRENT_VERSION
    if st.session_state.system_version != CURRENT_VERSION:
        st.session_state.clear()
        st.rerun()

def main():
    # 初始化 session state
    initialize_session_state()
    
    # 页面路由逻辑 - 只调用一次
    if st.session_state.page in ['login', 'main']:
        if st.session_state.page == 'login':
            show_login_page()
        elif st.session_state.page == 'main':
            main_page()
    else:
        st.session_state.page = 'login'
        show_login_page()

# 启动应用
main()
# 页面映射表
page_map = {
    'login': show_login_page,
    'main': show_main_page,
    'shop': show_shop_page,
    'backpack': show_backpack_page,
    'sect': show_sect_page,
    'alchemy': show_alchemy_page,
    'forge': show_forge_page,
    'array': show_array_page,
    'dungeon': show_dungeon_page,
    'xuanli_admin': show_xuanli_admin_page,
}

# ==============================
# ▶️ 应用入口
# ==============================

if __name__ == "__main__":
    main()