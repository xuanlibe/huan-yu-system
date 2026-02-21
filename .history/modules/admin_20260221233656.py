# ==================================================
# 管理员后台模块
# 功能：用户管理、灵石发放、系统配置
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client, MAIN_ADMIN_USERNAME
from core.database import get_user_sect
from core.errors import safe_page_load
from utils.helpers import hash_password

def show_xuanli_admin_page():
    """
    显示轩璃专属超级管理界面
    只有用户名=轩璃的用户可以访问
    """
    # 权限检查
    if st.session_state.user.username != MAIN_ADMIN_USERNAME:
        st.error("❌ 权限不足！此页面仅限轩璃访问")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 轩璃专属", layout="wide")
    st.title("👑 轩璃专属管理台")
    
    if st.button("⬅️ 返回主城", key="admin_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("管理后台"):
        _render_admin_content()

def _render_admin_content():
    """渲染管理后台内容（内部函数）"""
    tabs = st.tabs(["👥 用户管理", "💎 灵石发放", "⚙️ 系统配置", "📜 操作日志"])
    
    with tabs[0]:
        _render_user_management()
    
    with tabs[1]:
        _render_spirit_stones_grant()
    
    with tabs[2]:
        _render_system_config()
    
    with tabs[3]:
        _render_operation_log()

def _render_user_management():
    """渲染用户管理标签页（内部函数）"""
    st.subheader("👥 所有用户列表")
    
    supabase = get_supabase_client()
    
    try:
        # 获取所有用户
        users = supabase.table("users").select("*").execute()
        users_data = users.data if users else []
        
        if not users_data:
            st.info("暂无用户数据")
            return
        
        st.write(f"共 {len(users_data)} 名用户")
        
        # 显示用户列表
        for user in users_data:
            with st.expander(f"👤 {user['username']} (ID: {user['id'][:8]}...)"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**灵石**: {user.get('spirit_stones', 0):,}")
                    st.write(f"**境界**: {user.get('realm', '未知')} {user.get('stage', 0)}层")
                
                with col2:
                    st.write(f"**管理员**: {'是' if user.get('is_admin', False) else '否'}")
                    st.write(f"**封禁**: {'是' if user.get('is_banned', False) else '否'}")
                
                with col3:
                    # 封禁/解封按钮
                    is_banned = user.get("is_banned", False)
                    btn_label = "🔓 解封" if is_banned else "🔒 封禁"
                    if st.button(btn_label, key=f"ban_user_{user['id']}"):
                        supabase.table("users").update({"is_banned": not is_banned}).eq("id", user["id"]).execute()
                        st.toast(f"✅ 已{'解封' if is_banned else '封禁'} {user['username']}", icon="✅")
                        st.rerun()
                    
                    # 删除按钮
                    if st.button("🗑️ 删除", key=f"del_user_{user['id']}"):
                        if user['username'] != MAIN_ADMIN_USERNAME:
                            supabase.table("users").delete().eq("id", user["id"]).execute()
                            st.toast(f"🗑️ 已删除 {user['username']}", icon="✅")
                            st.rerun()
                        else:
                            st.error("❌ 不能删除主管理员账号！")
    
    except Exception as e:
        st.error(f"加载用户失败：{str(e)[:200]}")

def _render_spirit_stones_grant():
    """渲染灵石发放标签页（内部函数）"""
    st.subheader("💎 批量发放灵石")
    
    supabase = get_supabase_client()
    
    # 获取所有用户
    users = supabase.table("users").select("id, username").execute()
    users_data = users.data if users else []
    
    if not users_data:
        st.info("暂无用户")
        return
    
    usernames = [u["username"] for u in users_data]
    
    col1, col2 = st.columns(2)
    with col1:
        selected = st.multiselect("选择用户", usernames, default=usernames)
    with col2:
        amount = st.number_input("灵石数量", min_value=1, value=1000, step=100)
    
    if st.button("🎁 发放灵石"):
        if not selected:
            st.warning("请至少选择一名用户")
        else:
            count = 0
            for u in users_data:
                if u["username"] in selected:
                    supabase.rpc("add_spirit_stones", {"uid": u["id"], "amount": amount}).execute()
                    count += 1
            
            st.success(f"✅ 已向 {count} 名用户发放 {amount:,} 灵石")

def _render_system_config():
    """渲染系统配置标签页（内部函数）"""
    st.subheader("⚙️ 系统功能开关")
    
    supabase = get_supabase_client()
    
    # 获取当前配置
    config = supabase.table("system_config").select("*").execute()
    config_data = config.data[0] if config.data else {}
    
    # 功能开关
    features = {
        "shop": "🏪 藏宝阁",
        "backpack": "🎒 背包",
        "sect": "🏯 宗门",
        "alchemy": "🧪 炼丹房",
        "forge": "🔨 炼器坊",
        "array": "🌀 阵法堂",
        "dungeon": "🕳️ 秘境",
        "admin": "🛠️ 管理后台"
    }
    
    with st.form("system_config_form"):
        updated_config = {}
        for key, label in features.items():
            current_value = config_data.get(key, True)
            updated_config[key] = st.checkbox(label, value=current_value)
        
        submitted = st.form_submit_button("💾 保存配置")
        
        if submitted:
            supabase.table("system_config").update(updated_config).eq("id", config_data.get("id", 1)).execute()
            st.success("✅ 配置已保存")

def _render_operation_log():
    """渲染操作日志标签页（内部函数）"""
    st.subheader("📜 最近操作日志")
    
    # 显示 session 中记录的最后错误
    if st.session_state.get("last_error"):
        error = st.session_state.last_error
        with st.expander(f"❌ {error.get('page', '未知')} - {error.get('time', '未知')}"):
            st.code(error.get('error', '无详情'))
    else:
        st.info("暂无错误记录")
    
    st.markdown("---")
    st.info("💡 完整日志功能待开发，当前仅显示最近错误")