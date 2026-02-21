# ==================================================#
# 管理员中心
# 功能：区分超级管理员（轩璃）和普通管理员的管理界面
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
    st.subheader("➕ 添加新管理员")
    
    with st.form("add_admin_form"):
        username = st.text_input("输入要提升为管理员的用户名")
        submit = st.form_submit_button("授予管理员权限")
        
        if submit and username:
            supabase = get_supabase_client()
            # 查找用户
            user_res = supabase.table("users").select("id").eq("username", username).execute()
            if not user_res.data:
                st.error("❌ 用户不存在")
            else:
                user_id = user_res.data[0]["id"]
                # 检查是否已经是管理员
                check = supabase.table("admins").select("id").eq("user_id", user_id).execute()
                if check.data:
                    st.warning("⚠️ 该用户已是管理员")
                else:
                    # 添加为普通管理员
                    supabase.table("admins").insert({
                        "user_id": user_id,
                        "role": "normal",
                        "created_by": st.session_state.user.id
                    }).execute()
                    st.success(f"✅ 已授予 {username} 管理员权限！")

    st.markdown("---")
    st.subheader("👥 所有管理员列表")
    _display_all_admins()

def _show_normal_admin_panel():
    """普通管理员面板（示例：只能查用户）"""
    st.subheader("🔍 查询用户信息")
    username = st.text_input("输入用户名")
    if username:
        supabase = get_supabase_client()
        user_data = supabase.table("users").select("*").eq("username", username).execute().data
        if user_data:
            user = user_data[0]
            st.json({
                "道号": user["username"],
                "灵石": user["spirit_stones"],
                "境界": f"{user['realm']} {user['stage']}层",
                "是否管理员": "是" if _is_admin(user["id"]) else "否"
            })
        else:
            st.error("用户不存在")

def _is_admin(user_id: str) -> bool:
    """辅助函数：判断是否为管理员"""
    supabase = get_supabase_client()
    res = supabase.table("admins").select("id").eq("user_id", user_id).execute()
    return len(res.data) > 0

def _display_all_admins():
    """显示所有管理员（不含轩璃）"""
    supabase = get_supabase_client()
    admins = supabase.table("admins").select("user_id, created_at").execute().data
    if not admins:
        st.info("暂无普通管理员")
        return
    
    for admin in admins:
        user = supabase.table("users").select("username").eq("id", admin["user_id"]).execute().data[0]
        st.write(f"- {user['username']} （添加于 {admin['created_at'][:10]}）")