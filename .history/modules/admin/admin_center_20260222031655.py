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
        if submit and username.strip():
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
    
    # 检查是否是管理员
    is_target_admin = _is_admin(user_id)
    is_target_super = (user_id == "00000000-0000-0000-0000-000000000001")
    
    # 权限限制
    if is_target_super:
        st.warning("⚠️ 轩璃不可被操作")
        return
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
    """授予管理员权限（内部函数）"""
    user_res = supabase.table("users").select("id, username").eq("username", username).execute()
    if not user_res.data:
        st.error("❌ 用户不存在")
        return
    
    target_user = user_res.data[0]
    user_id = target_user["id"]
    
    if user_id == "00000000-0000-0000-0000-000000000001":
        st.warning("⚠️ 轩璃已是超级管理员")
        return
    
    check = supabase.table("admins").select("id").eq("user_id", user_id).execute()
    if check.data:
        st.warning(f"⚠️ {target_user['username']} 已是管理员")
    else:
        supabase.table("admins").insert({
            "user_id": user_id,
            "role": "normal",
            "created_by": st.session_state.user.id
        }).execute()
        st.success(f"✅ 已授予 {target_user['username']} 管理员权限！")
        st.rerun()

def _manage_admins_list(supabase):
    """管理普通管理员列表（仅轩璃）"""
    admins = supabase.table("admins").select("id, user_id, created_at").execute().data
    if not admins:
        st.info("暂无普通管理员")
        return
    
    for admin in admins:
        user_info = supabase.table("users").select("username").eq("id", admin["user_id"]).execute().data
        if not user_info:
            continue
        username = user_info[0]["username"]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"👤 {username} （{admin['created_at'][:10]}）")
        with col2:
            if st.button("🗑️ 移除", key=f"remove_admin_{admin['id']}"):
                supabase.table("admins").delete().eq("id", admin["id"]).execute()
                st.success(f"已移除 {username} 的管理员权限")
                st.rerun()

def _is_admin(user_id: str) -> bool:
    """判断是否为普通管理员"""
    supabase = get_supabase_client()
    res = supabase.table("admins").select("id").eq("user_id", user_id).execute()
    return len(res.data) > 0