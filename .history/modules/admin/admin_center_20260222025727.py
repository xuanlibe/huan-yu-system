# ==================================================#
# 管理员中心
# 功能：区分超级管理员（轩璃）和普通管理员的管理界面
# 更新：支持轩璃添加/移除管理员
# ==================================================#

import streamlit as st
from core.config import get_supabase_client

def show_admin_center():
    """显示管理员中心"""
    user = st.session_state.user
    
    # 安全检查：只有管理员能访问
    if not user.is_admin:
        st.error("❌ 无权访问管理员中心")
        st.stop()

    st.title("🛡️ 管理员中心")
    
    if user.is_super_admin:
        st.success("👑 欢迎回来，轩璃大人！您拥有最高权限。")
        _show_super_admin_panel()
    else:
        st.info("🛠️ 普通管理员面板（当前仅支持查看用户）")
        _show_normal_admin_panel()

def _show_super_admin_panel():
    """超级管理员专属面板"""
    supabase = get_supabase_client()
    
    # --- 添加管理员 ---
    st.subheader("➕ 添加新管理员")
    with st.form("add_admin_form"):
        username = st.text_input("输入要提升为管理员的用户名", key="add_admin_username")
        submit = st.form_submit_button("授予管理员权限")
        
        if submit and username.strip():
            # 查找用户
            user_res = supabase.table("users").select("id, username").eq("username", username.strip()).execute()
            if not user_res.data:
                st.error("❌ 用户不存在")
            else:
                target_user = user_res.data[0]
                user_id = target_user["id"]
                
                # 检查是否已经是管理员（包括轩璃自己）
                if user_id == "00000000-0000-0000-0000-000000000001":
                    st.warning("⚠️ 轩璃已是超级管理员，无需重复授权")
                else:
                    check = supabase.table("admins").select("id").eq("user_id", user_id).execute()
                    if check.data:
                        st.warning(f"⚠️ {target_user['username']} 已是管理员")
                    else:
                        # 添加为普通管理员
                        supabase.table("admins").insert({
                            "user_id": user_id,
                            "role": "normal",
                            "created_by": st.session_state.user.id
                        }).execute()
                        st.success(f"✅ 已授予 {target_user['username']} 管理员权限！")
                        st.rerun()  # 刷新列表

    st.markdown("---")
    
    # --- 管理员列表（含移除功能）---
    st.subheader("👥 所有普通管理员")
    _display_and_manage_admins(supabase)

def _show_normal_admin_panel():
    """普通管理员面板（示例：只能查用户）"""
    st.subheader("🔍 查询用户信息")
    username = st.text_input("输入用户名", key="query_user")
    if username.strip():
        supabase = get_supabase_client()
        user_data = supabase.table("users").select("*").eq("username", username.strip()).execute().data
        if user_data:
            user = user_data[0]
            is_admin = _is_admin(user["id"])
            st.json({
                "道号": user["username"],
                "灵石": user["spirit_stones"],
                "境界": f"{user['realm']} {user['stage']}层",
                "生命": user["hp"],
                "是否管理员": "是" if is_admin else "否"
            })
        else:
            st.error("❌ 用户不存在")

def _is_admin(user_id: str) -> bool:
    """辅助函数：判断是否为普通管理员"""
    supabase = get_supabase_client()
    res = supabase.table("admins").select("id").eq("user_id", user_id).execute()
    return len(res.data) > 0

def _display_and_manage_admins(supabase):
    """显示并管理所有普通管理员（仅轩璃可见操作）"""
    admins = supabase.table("admins").select("id, user_id, created_at").execute().data
    if not admins:
        st.info("暂无普通管理员")
        return
    
    user = st.session_state.user
    for admin in admins:
        # 获取用户名
        user_info = supabase.table("users").select("username").eq("id", admin["user_id"]).execute().data
        if not user_info:
            continue  # 用户可能已被删除
        username = user_info[0]["username"]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"👤 {username} （{admin['created_at'][:10]}）")
        with col2:
            # 只有轩璃能移除
            if user.is_super_admin:
                if st.button("🗑️ 移除", key=f"remove_{admin['id']}"):
                    supabase.table("admins").delete().eq("id", admin["id"]).execute()
                    st.success(f"已移除 {username} 的管理员权限")
                    st.rerun()