# ==================================================
# 寰宇系统 - 修仙模拟器 (v2.0 最终完整版)
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
if "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
else:
    SUPABASE_URL = "https://rwfveqinwgwwdfkfsrna.supabase.co"  # ← 缩进 4 空格
    SUPABASE_ANON_KEY = "sb_publishable_A0FQbhUOT2HqR6Li1MNtSA_nf5jpfHD"

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
CURRENT_VERSION = "2.0.0"

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

OFFICIAL_SECTS = {
    "天罚监司": ["天罚监司"],
    "冥界": ["冥界"],
    "人": ["逍遥剑宗", "白玉京"],
    "妖": ["神机阁", "云月阁"],
    "魔": ["无极魔宗", "玄煞魔门"],
    "散修": []
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

def safe_db_operation(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = str(e)
        if "JWT expired" in error_msg:
            st.session_state.clear()
            st.rerun()
        elif "row-level security policy" in error_msg:
            st.toast("❌ 权限不足，请重新登录", icon="🔒")
            st.session_state.clear()
            st.rerun()
        else:
            st.toast(f"❌ 系统错误: {error_msg[:100]}", icon="💥")
        return None

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
        
        if username == MAIN_ADMIN_USERNAME and password == MAIN_ADMIN_PASSWORD:
            existing = supabase.table("users").select("*").eq("username", username).execute().data
            if existing:
                user_data = existing[0]
                supabase.table("users").update({"last_login": get_current_time_str()}).eq("id", user_data["id"]).execute()
                return cls(user_data)
            else:
                new_user = {
                    "username": username,
                    "password_hash": hash_password(password),
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
                result = supabase.table("users").insert(new_user).execute()
                if result.data:
                    user_data = result.data[0]
                    ensure_user_cultivation_record(user_data["id"])
                    return cls(user_data)
                else:
                    return None
        
        users = supabase.table("users").select("*").eq("username", username).execute().data
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
# 🧪 炼丹房
# ==============================

class AlchemySystem:
    @staticmethod
    def get_recipes() -> List[Dict[str, Any]]:
        recipes = safe_db_operation(
            supabase.table("alchemy_recipes")
            .select("*, result_item:items(name), material_1:items!material_1_id(name), material_2:items!material_2_id(name)")
            .execute
        )
        return recipes.data if recipes else []
    
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
# 🔨 炼器坊
# ==============================

class ForgeSystem:
    @staticmethod
    def get_blueprints() -> List[Dict[str, Any]]:
        blueprints = safe_db_operation(
            supabase.table("forge_blueprints")
            .select("*, result_item:items(name), material_1:items!material_1_id(name), material_2:items!material_2_id(name)")
            .execute
        )
        return blueprints.data if blueprints else []
    
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
        
        ForgeSystem._remove_item(user_id, mat1_id, mat1_qty)
        if mat2_id:
            ForgeSystem._remove_item(user_id, mat2_id, mat2_qty)
        
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
        if user.is_admin:
            nav_options.append("🛠️ 管理中心")
        
        selected_nav = st.radio("选择功能", nav_options)
        
        if st.button("🚪 退出登录"):
            st.session_state.clear()
            st.rerun()
    
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

def show_backpack_page():
    if not FEATURES["backpack"]:
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
    
    inventory = Backpack.get_user_inventory(st.session_state.user.id)
    if not inventory:
        st.info("背包空空如也，快去藏宝阁逛逛吧！")
        return
    
    st.write(f"共 {len(inventory)} 种物品")
    for inv_item in inventory:
        item = inv_item.get("items", {})
        with st.expander(f"{item.get('name', '未知')} x{inv_item['quantity']}"):
            st.write(f"类别: {item.get('category', '其他')}")
            st.write(f"效果: {item.get('effect', '无')}")
            if item.get("usable", False):
                if st.button("✨ 使用", key=f"use_{inv_item['id']}"):
                    success, msg = Backpack.use_item(
                        st.session_state.user.id, 
                        inv_item["id"], 
                        item
                    )
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.toast(msg, icon="❌")

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
    
    if current_sect:
        st.subheader(f"🏛️ {current_sect['sect_name']}")
        st.write(f"**分类**: {current_sect['category']}")
        st.write(f"**描述**: {current_sect['description']}")
        st.write(f"**成员**: {current_sect['member_count']} / {current_sect['max_members']}")
        st.write(f"**宗门资金**: {current_sect['spirit_stones']:,} 灵石")
        st.write(f"**加入方式**: {'自由加入' if current_sect['is_open_join'] else '需审核'}")
        
        if current_sect["leader_id"] == user.id or user.is_super_admin:
            st.markdown("---")
            st.subheader("👑 宗主管理")
            with st.expander("⚙️ 设置加入方式"):
                new_join_mode = st.selectbox("加入方式", ["自由加入", "需审核"], 
                                            index=0 if current_sect["is_open_join"] else 1)
                if st.button("保存设置"):
                    safe_db_operation(
                        supabase.table("sects").update({
                            "is_open_join": (new_join_mode == "自由加入")
                        }).eq("id", current_sect["id"]).execute
                    )
                    st.toast("✅ 设置已保存", icon="💾")
                    st.rerun()
        
        if st.button("🚪 退出宗门"):
            st.warning("退出宗门功能开发中...")
    
    else:
        st.info("你目前是散修，可选择加入现有宗门或创建自己的宗门。")
        all_sects = SectSystem.get_all_sects()
        if not all_sects:
            st.info("暂无宗门")
            return
        
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
            new_sect_name = st.text_input("宗门名称")
            new_sect_desc = st.text_area("宗门描述", max_chars=200)
            submitted = st.form_submit_button("创建宗门（消耗 100,000 灵石）")
            if submitted:
                success, msg = SectSystem.create_sect(user.id, new_sect_name, new_sect_desc, "散修")
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_alchemy_page():
    if not FEATURES["alchemy"]:
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
    
    for recipe in recipes:
        with st.container(border=True):
            st.subheader(recipe["name"])
            st.write(f"产出: {recipe['result_item']['name']} x1")
            st.write(f"材料: {recipe['material_1']['name']} x{recipe['material_1_qty']}")
            if recipe.get("material_2") and recipe["material_2_qty"] > 0:
                st.write(f"      {recipe['material_2']['name']} x{recipe['material_2_qty']}")
            st.write(f"消耗: {recipe['spirit_stone_cost']:,} 灵石")
            if st.button("🔥 开始炼制", key=f"craft_alchemy_{recipe['id']}"):
                success, msg = AlchemySystem.craft(st.session_state.user.id, recipe["id"])
                if success:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.toast(msg, icon="❌")

def show_forge_page():
    if not FEATURES["forge"]:
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
    
    for bp in blueprints:
        with st.container(border=True):
            st.subheader(bp["name"])
            st.write(f"产出: {bp['result_item']['name']} x1")
            st.write(f"材料: {bp['material_1']['name']} x{bp['material_1_qty']}")
            if bp.get("material_2") and bp["material_2_qty"] > 0:
                st.write(f"      {bp['material_2']['name']} x{bp['material_2_qty']}")
            st.write(f"消耗: {bp['spirit_stone_cost']:,} 灵石")
            if st.button("⚒️ 开始打造", key=f"craft_forge_{bp['id']}"):
                success, msg = ForgeSystem.craft(st.session_state.user.id, bp["id"])
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

def show_admin_page():
    if not st.session_state.user.is_super_admin:
        st.error("权限不足")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 管理中心", layout="wide")
    st.title("🛠️ 管理中心（轩璃专属）")
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()
    
    st.success("👑 欢迎回来，轩璃大人！")
    
    tab1, tab2 = st.tabs(["⚙️ 系统设置", "🏯 宗门管理"])
    
    with tab1:
        st.subheader("功能开关")
        new_features = {}
        for key, enabled in FEATURES.items():
            new_features[key] = st.checkbox(key, value=enabled)
        if st.button("保存功能设置"):
            config_data = {"id": "global", **new_features}
            safe_db_operation(
                supabase.table("system_config").upsert(config_data).execute
            )
            st.toast("✅ 功能设置已保存", icon="💾")
    
    with tab2:
        st.subheader("官方宗门配置")
        for category, sects in OFFICIAL_SECTS.items():
            st.write(f"**{category}**: {', '.join(sects) if sects else '无'}")

# ==============================
# 🚀 主程序
# ==============================

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'system_version' not in st.session_state:
        st.session_state.system_version = CURRENT_VERSION
    
    if st.session_state.system_version != CURRENT_VERSION:
        st.session_state.clear()
        st.rerun()
    
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
        'admin': show_admin_page
    }
    
    if st.session_state.page in page_map:
        page_map[st.session_state.page]()
    else:
        st.session_state.page = 'login'
        st.rerun()

if __name__ == "__main__":
    main()