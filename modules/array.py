# ==================================================
# 阵法堂模块
# 功能：查看阵法、激活阵法、效果管理
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.database import get_user_sect
from core.errors import safe_page_load
from datetime import datetime, timedelta

def show_array_page():
    """
    显示阵法堂页面
    包含阵法列表和激活功能
    """
    if not FEATURES.get("array", True):
        st.warning("阵法堂暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 阵法堂", layout="wide")
    st.title("🌀 阵法堂")
    
    if st.button("⬅️ 返回主城", key="array_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("阵法堂"):
        _render_array_content()

def _render_array_content():
    """渲染阵法堂内容（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取所有阵法
    arrays = supabase.table("arrays").select("*").execute()
    arrays_data = arrays.data if arrays else []
    
    if not arrays_data:
        st.info("暂无可用阵法")
        return
    
    # 检查当前激活的阵法
    progress = supabase.table("user_progress")\
        .select("active_array_id, array_expire_time")\
        .eq("user_id", user_id)\
        .execute()
    
    active_array = None
    if progress.data:
        active = progress.data[0]
        expire_time = active.get("array_expire_time")
        if expire_time:
            expire_dt = datetime.fromisoformat(expire_time.replace("Z", "+00:00"))
            if datetime.now(expire_dt.tzinfo) < expire_dt:
                active_array = active
    
    st.subheader("🔮 可用阵法")
    
    for arr in arrays_data:
        _render_array_item(arr, user_id, active_array)

def _render_array_item(arr, user_id: int, active_array):
    """渲染单个阵法卡片（内部函数）"""
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"✨ {arr['name']}")
            st.write(f"**效果**: {arr.get('effect_type', '未知')} +{arr.get('effect_value', 0)}")
            st.write(f"**持续时间**: {arr.get('duration_minutes', 0)} 分钟")
            st.write(f"**消耗灵石**: {arr.get('spirit_stone_cost', 0):,}")
            st.caption(arr.get('description', ''))
        
        with col2:
            # 检查是否已激活
            is_active = active_array and active_array.get("active_array_id") == arr["id"]
            
            if is_active:
                st.success("✅ 已激活")
            else:
                if st.button("🔮 激活阵法", key=f"activate_array_{arr['id']}"):
                    _handle_activate_array(arr)

def _handle_activate_array(arr):
    """处理激活阵法逻辑（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 检查灵石
    cost = arr.get("spirit_stone_cost", 0)
    if st.session_state.user.spirit_stones < cost:
        st.toast(f"❌ 灵石不足，需要 {cost:,}", icon="❌")
        return
    
    # 扣除灵石
    supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": cost}).execute()
    
    # 计算过期时间
    duration = arr.get("duration_minutes", 0)
    expire_time = datetime.now() + timedelta(minutes=duration)
    
    # 更新用户进度
    supabase.table("user_progress").upsert({
        "user_id": user_id,
        "active_array_id": arr["id"],
        "array_expire_time": expire_time.isoformat()
    }).execute()
    
    st.toast(f"✅ 阵法「{arr['name']}」已激活，持续 {duration} 分钟！", icon="✅")
    st.rerun()