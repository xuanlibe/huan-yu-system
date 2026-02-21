# ==================================================#
# 登录注册模块
# 功能：用户登录、注册、密码验证
# ==================================================#

import streamlit as st
from typing import Dict, Any, Optional
from core.config import get_supabase_client, MAIN_ADMIN_USERNAME, MAIN_ADMIN_PASSWORD
from utils.helpers import hash_password, verify_password

# ==============================#
# 👤 用户类定义
# ==============================#

class User:
    """ 用户数据类 封装用户的所有属性和基本信息 """
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
        """ 用户登录方法 """
        if not username or not password:
            return None

        # 🔒 特殊处理：轩璃管理员 → 使用固定 UUID
        if username == MAIN_ADMIN_USERNAME:
            if password == MAIN_ADMIN_PASSWORD:
                from datetime import datetime
                user_data = {
                    "id": "00000000-0000-0000-0000-000000000001",
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
                    "last_login": datetime.now().isoformat()
                }
                return cls(user_data)
            else:
                st.toast("❌ 主管理员密码错误", icon="🔒")
                return None

        # 普通用户登录流程
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("username", username).execute()
        users = response.data if response and hasattr(response, 'data') else []
        if not users:
            return None
        user_data = users[0]

        # 验证密码
        if not verify_password(password, user_data.get("password_hash", "")):
            return None

        # 检查是否被封禁
        if user_data.get("is_banned", False):
            st.toast("❌ 账号已被封禁", icon="🚫")
            return None

        # 🔍 检查是否为普通管理员
        user_id = user_data["id"]
        admin_check = supabase.table("admins").select("role").eq("user_id", user_id).execute()
        is_admin = len(admin_check.data) > 0
        is_super_admin = False

        # 更新权限字段
        user_data["is_admin"] = is_admin
        user_data["is_super_admin"] = is_super_admin

        # 更新最后登录时间
        from datetime import datetime
        supabase.table("users").update({"last_login": datetime.now().isoformat()}).eq("id", user_data["id"]).execute()
        return cls(user_data)

    @staticmethod
    def update_spirit_stones(user_id: str, amount: int):
        """更新用户灵石数量"""
        supabase = get_supabase_client()
        # supabase.rpc("add_spirit_stones", {"uid": user_id, "amount": amount}).execute()

# ==============================#
# 🖥️ 登录页面
# ==============================#

def show_login_page():
    """ 显示登录注册页面 """
    st.set_page_config(page_title="寰宇系统 - 登录", layout="centered")
    st.title("🌌 寰宇系统")
    st.markdown("欢迎来到修真世界！踏入仙途，成就大道。")

    tab1, tab2 = st.tabs(["🔑 登录", "会员注册"])

    # --- 登录标签页 ---
    with tab1:
        with st.form("login_form"):
            username = st.text_input("道号（用户名）", key="login_username")
            password = st.text_input("密令（密码）", type="password", key="login_password")
            submit = st.form_submit_button("登入修仙界", key="login_submit")

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

    # --- 注册标签页 ---
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("新道号（2-20字符）", key="reg_username")
            new_password = st.text_input("设置密令（至少6位）", type="password", key="reg_password")
            confirm_password = st.text_input("确认密令", type="password", key="reg_confirm")
            submit = st.form_submit_button("踏入仙途", key="reg_submit")

            if submit:
                if len(new_username) < 2 or len(new_username) > 20:
                    st.error("道号长度需在2-20字符之间")
                elif len(new_password) < 6:
                    st.error("密令至少6位")
                elif new_password != confirm_password:
                    st.error("两次输入的密令不一致")
                else:
                    _handle_registration(new_username, new_password)

def _handle_registration(username: str, password: str):
    """处理注册逻辑（内部函数）"""
    supabase = get_supabase_client()

    # 检查用户名是否已存在
    existing = supabase.table("users").select("id").eq("username", username).execute()
    if existing and existing.data:
        st.error("该道号已被占用")
        return

    # 创建新用户
    from datetime import datetime
    new_user_data = {
        "username": username,
        "password_hash": hash_password(password),
        "spirit_stones": 1000,
        "cultivation_level": 1,
        "realm": "练气",
        "stage": 1,
        "hp": 100,
        "mp": 50,
        "attack": 10,
        "defense": 5,
        "lifespan": 80,
        "last_login": datetime.now().isoformat()
    }

    result = supabase.table("users").insert(new_user_data).execute()
    if result and result.data:
        user = User(result.data[0])
        _ensure_user_cultivation_record(user.id)
        st.session_state.user = user
        st.session_state.page = 'main'
        st.success("注册成功！欢迎踏入修仙界！")
        st.rerun()
    else:
        st.error("注册失败，请稍后再试")

def _ensure_user_cultivation_record(user_id: str):
    """确保用户有修炼记录（内部函数）"""
    supabase = get_supabase_client()
    try:
        data = supabase.table("user_cultivation").select("*").eq("user_id", user_id).execute().data
        if not data:
            from datetime import datetime
            supabase.table("user_cultivation").insert({
                "user_id": user_id,
                "realm": "练气",
                "stage": 1,
                "exp": 0,
                "hp": 100,
                "mp": 50,
                "attack": 10,
                "defense": 5,
                "lifespan": 80,
                "updated_at": datetime.now().isoformat()
            }).execute()
    except Exception as e:
        st.toast(f"⚠️ 初始化修炼数据失败：{str(e)[:50]}", icon="⚠️")