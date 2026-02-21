# ==================================================#
# 管理员中心（增强版）
# 功能：
# - 轩璃：管理管理员 + 封禁任何人
# - 普通管理员：仅封禁普通用户（不能动管理员）
# ==================================================#

import streamlit as st
from core.config import get_supabase_client

def show_admin_center():
    """显示管理员中心"""
    user = st.session_state.user
    if not user.is_admin:
        st.error("❌ 无权访问管理员中心")
        st.stop()

    st.title("🛡️ 管理员中心")

    if user.is_super_admin:
        st.success("👑 欢迎回来，轩璃大人！您拥有最高权限。")
        _show_super_admin_panel()
    else:
        st.info("🛠️ 普通管理员面板")
        _show_normal_admin_panel()

def _show_super_admin_panel():
    """超级管理员面板：全能管理"""
    supabase = get_supabase_client()

    # --- 添加管理员 ---
    st.subheader("➕ 添加新管理员")
    with st.form("add_admin_form"):
        username = st.text_input("输入用户名", key="add_admin_user")
        submit = st.form_submit_button("授予管理员权限")
        if submit:
            if not username.strip():
                st.warning("⚠️ 用户名不能为空")
            else:
                _grant_admin(supabase, username.strip())

    st.markdown("---")

    # --- 管理员列表 ---
    st.subheader("👥 所有普通管理员")
    _manage_admins_list(supabase)

    st.markdown("---")

    # --- 封禁用户（全能）---
    st.subheader("🔒 封禁/解封用户（可操作任何人）")
    _ban_user_section(supabase, can_ban_admins=True)

    st.markdown("---")

    # --- 物品管理入口 ---
    st.subheader("📦 物品管理")
    if st.button("🔧 编辑物品描述", key="go_item_manager_super"):
        st.session_state.page = 'item_manager'
        st.rerun()

def _show_normal_admin_panel():
    """普通管理员面板：仅能封禁普通用户"""
    st.subheader("🔍 查询与封禁用户")
    _ban_user_section(get_supabase_client(), can_ban_admins=False)

    st.markdown("---")

    # --- 物品管理入口 ---
    st.subheader("📦 物品管理")
    if st.button("🔧 编辑物品描述", key="go_item_manager_normal"):
        st.session_state.page = 'item_manager'
        st.rerun()

def _ban_user_section(supabase, can_ban_admins: bool):
    """封禁用户功能区（复用组件）"""
    username = st.text_input("输入要操作的用户名", key="ban_username")
    if not username.strip():
        return

    # 查找用户
    user_res = supabase.table("users").select("*").eq("username", username.strip()).execute()
    if not user_res.data:
        st.error("❌ 用户不存在")
        return

    target = user_res.data[0]
    user_id = target["id"]

    # 轩璃的固定 ID（请确认是否匹配你的数据库）
    SUPER_ADMIN_ID = "00000000-0000-0000-0000-000000000001"

    # 权限限制
    if user_id == SUPER_ADMIN_ID:
        st.warning("⚠️ 轩璃不可被操作")
        return

    if user_id == st.session_state.user.id:
        st.warning("⚠️ 不能操作自己的账号")
        return

    # 检查目标是否为管理员
    is_target_admin = target.get("is_admin", False)

    if is_target_admin and not can_ban_admins:
        st.warning("⚠️ 你无权操作其他管理员")
        return

    # 显示用户信息
    st.write(f"**道号**：{target['username']}")
    st.write(f"**当前状态**：{'⛔ 已封禁' if target.get('is_banned') else '✅ 正常'}")
    st.write(f"**灵石**：{target['spirit_stones']:,}")
    st.write(f"**境界**：{target['realm']} {target['stage']}层")

    col1, col2 = st.columns(2)
    with col1:
        if not target.get("is_banned"):
            if st.button("🔒 封禁账号", key=f"ban_{user_id}"):
                supabase.table("users").update({"is_banned": True}).eq("id", user_id).execute()
                st.success(f"✅ 已封禁 {username}")
                st.rerun()
    with col2:
        if target.get("is_banned"):
            if st.button("🔓 解封账号", key=f"unban_{user_id}"):
                supabase.table("users").update({"is_banned": False}).eq("id", user_id).execute()
                st.success(f"✅ 已解封 {username}")
                st.rerun()

def _grant_admin(supabase, username: str):
    """安全授予管理员权限（直接更新 users 表）"""
    try:
        # 查找用户
        user_res = supabase.table("users").select("id, username, is_admin").eq("username", username).execute()
        if not user_res.data:
            st.error("❌ 用户不存在")
            return

        target_user = user_res.data[0]
        user_id = target_user["id"]

        # 轩璃 ID
        SUPER_ADMIN_ID = "00000000-0000-0000-0000-000000000001"
        if user_id == SUPER_ADMIN_ID:
            st.warning("⚠️ 轩璃已是超级管理员")
            return

        # 已是管理员？
        if target_user.get("is_admin", False):
            st.warning(f"⚠️ {target_user['username']} 已是管理员")
            return

        # 直接更新 is_admin 字段
        supabase.table("users").update({"is_admin": True}).eq("id", user_id).execute()
        st.success(f"✅ 已授予 {target_user['username']} 管理员权限！")
        st.rerun()

    except Exception as e:
        st.error(f"❌ 授予权限失败: {str(e)}")

def _manage_admins_list(supabase):
    """管理普通管理员列表（仅轩璃）"""
    try:
        # 获取所有 is_admin = true 的用户（排除轩璃）
        SUPER_ADMIN_ID = "00000000-0000-0000-0000-000000000001"
        admins = supabase.table("users")\
            .select("id, username, created_at")\
            .eq("is_admin", True)\
            .neq("id", SUPER_ADMIN_ID)\
            .execute().data

        if not admins:
            st.info("暂无普通管理员")
            return

        for admin in admins:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"👤 {admin['username']} （{admin['created_at'][:10]}）")
            with col2:
                if st.button("🗑️ 移除", key=f"remove_admin_{admin['id']}"):
                    # 移除管理员权限
                    supabase.table("users").update({"is_admin": False}).eq("id", admin["id"]).execute()
                    st.success(f"已移除 {admin['username']} 的管理员权限")
                    st.rerun()

    except Exception as e:
        st.error(f"❌ 加载管理员列表失败: {str(e)}")