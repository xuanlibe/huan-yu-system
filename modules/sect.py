# ==================================================
# 宗门模块
# 功能：创建宗门、加入宗门、宗门管理
# ==================================================

import streamlit as st
from core.config import FEATURES, SECT_CATEGORIES, get_supabase_client
from core.database import get_user_sect  # ✅ 从核心数据库模块导入
from core.errors import safe_page_load

def show_sect_page():
    """
    显示宗门页面
    包含宗门浏览、创建、管理功能
    """
    if not FEATURES.get("sect", True):
        st.warning("宗门系统暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 宗门", layout="wide")
    st.title("🏯 宗门系统")
    
    if st.button("⬅️ 返回主城", key="sect_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("宗门"):
        _render_sect_content()

def _render_sect_content():
    """渲染宗门内容（内部函数）"""
    supabase = get_supabase_client()
    user = st.session_state.user
    current_sect = get_user_sect(user.id)
    
    # 无宗门状态
    if not current_sect:
        _render_no_sect_view()
    else:
        _render_sect_detail_view(current_sect)

def _render_no_sect_view():
    """渲染无宗门视图（内部函数）"""
    st.info("你目前是散修，可选择加入现有宗门或创建自己的宗门。")
    
    supabase = get_supabase_client()
    all_sects = supabase.table("sects").select("*").order("category").execute().data or []
    
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
                        st.write(f"成员：{sect['member_count']} / {sect['max_members']}")
                        
                        if st.button(f"➕ 申请加入「{sect['sect_name']}」", key=f"join_{sect['id']}"):
                            _handle_join_sect(sect["id"], sect["sect_name"])
    
    # 创建宗门
    st.markdown("---")
    st.subheader("🆕 创建宗门（仅散修）")
    with st.form("create_sect_form"):
        new_sect_name = st.text_input("宗门名称", max_chars=20, key="new_sect_name")
        new_sect_desc = st.text_area("宗门描述", max_chars=200, key="new_sect_desc")
        new_category = st.selectbox("宗门类型", SECT_CATEGORIES, key="new_sect_cat")
        submitted = st.form_submit_button("创建宗门（消耗 100,000 灵石）", key="create_sect_submit")
        
        if submitted:
            _handle_create_sect(new_sect_name, new_sect_desc, new_category)

def _handle_join_sect(sect_id: str, sect_name: str):
    """处理加入宗门（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 检查是否已有宗门
    current = get_user_sect(user_id)
    if current:
        st.toast(f"❌ 你已是「{current['sect_name']}」成员", icon="❌")
        return
    
    # 加入逻辑
    supabase.table("sect_members").insert({
        "sect_id": sect_id,
        "user_id": user_id,
        "role": "member"
    }).execute()
    
    st.toast(f"✅ 已加入「{sect_name}」！", icon="✅")
    st.rerun()

def _handle_create_sect(name: str, desc: str, category: str):
    """处理创建宗门（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    if st.session_state.user.spirit_stones < 100000:
        st.error("❌ 灵石不足！创建宗门需 100,000 灵石")
        return
    
    if not name.strip():
        st.error("❌ 宗门名称不能为空")
        return
    
    # 扣除灵石
    supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": 100000}).execute()
    
    # 创建宗门
    result = supabase.table("sects").insert({
        "sect_name": name,
        "description": desc,
        "category": category,
        "founder_id": user_id,
        "leader_id": user_id,
        "member_count": 1,
        "max_members": 50,
        "is_open_join": False,
        "spirit_stones": 0
    }).execute()
    
    if result.data:
        # 添加宗主到成员表
        supabase.table("sect_members").insert({
            "sect_id": result.data[0]["id"],
            "user_id": user_id,
            "role": "leader"
        }).execute()
        
        st.toast(f"✅ 宗门「{name}」创建成功！", icon="✅")
        st.rerun()
    else:
        st.error("❌ 创建失败")

def _render_sect_detail_view(current_sect):
    """渲染宗门详情视图（内部函数）"""
    user = st.session_state.user
    
    # 顶部信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(f"🏛️ {current_sect['sect_name']}")
    with col2:
        st.write(f"**类型**: {current_sect['category']}")
    with col3:
        st.write(f"**资金**: {current_sect['spirit_stones']:,} 💎")
    
    # 宗门功能标签页
    tabs = st.tabs(["📜 宗门概况", "👥 成员列表", "🏪 宗门商店"])
    
    with tabs[0]:
        st.write(f"**宗门宣言**: {current_sect.get('description', '无')}")
        st.write(f"**规模**: {current_sect['member_count']} / {current_sect['max_members']} 人")
        
        # 宗主管理
        if current_sect["leader_id"] == user.id or user.is_super_admin:
            st.markdown("---")
            st.subheader("👑 宗主管理")
            if st.button("🚪 退出宗门"):
                _handle_leave_sect()
    
    with tabs[1]:
        st.subheader("👥 宗门成员")
        st.info("成员列表功能待完善")
    
    with tabs[2]:
        st.subheader("🏪 宗门商店")
        st.info("宗门商店功能待完善")

def _handle_leave_sect():
    """处理退出宗门（内部函数）"""
    st.warning("退出宗门将失去所有宗门权益，确认？")
    if st.button("✅ 确认退出"):
        supabase = get_supabase_client()
        user_id = st.session_state.user.id
        supabase.table("sect_members").delete().eq("user_id", user_id).execute()
        st.toast("✅ 已退出宗门", icon="✅")
        st.rerun()