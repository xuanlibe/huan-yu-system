# ==================================================
# 秘境模块
# 功能：查看秘境、挑战秘境、奖励发放
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.database import get_user_sect
from core.errors import safe_page_load
from datetime import datetime, timedelta

def show_dungeon_page():
    """
    显示秘境页面
    包含秘境列表和挑战功能
    """
    if not FEATURES.get("dungeon", True):
        st.warning("秘境暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 秘境", layout="wide")
    st.title("🕳️ 秘境挑战")
    
    if st.button("⬅️ 返回主城", key="dungeon_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("秘境"):
        _render_dungeon_content()

def _render_dungeon_content():
    """渲染秘境内容（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取所有秘境
    dungeons = supabase.table("dungeons").select("""
        *,
        reward_item:items!reward_item_id(name)
    """).execute()
    
    dungeons_data = dungeons.data if dungeons else []
    
    if not dungeons_data:
        st.info("暂无秘境开放")
        return
    
    # 获取用户挑战记录
    progress = supabase.table("user_progress")\
        .select("last_dungeon_time")\
        .eq("user_id", user_id)\
        .execute()
    
    last_time = None
    if progress.data:
        last_time = progress.data[0].get("last_dungeon_time")
    
    st.subheader("⚔️ 可挑战秘境")
    
    for dungeon in dungeons_data:
        _render_dungeon_item(dungeon, user_id, last_time)

def _render_dungeon_item(dungeon, user_id: int, last_time):
    """渲染单个秘境卡片（内部函数）"""
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"🗡️ {dungeon['name']}")
            st.write(f"**要求等级**: {dungeon.get('required_level', 1)}")
            st.write(f"**冷却时间**: {dungeon.get('cooldown_hours', 24)} 小时")
            st.write(f"**灵石奖励**: {dungeon.get('reward_spirit_stones', 0):,}")
            
            reward_item = dungeon.get("reward_item", {})
            if reward_item:
                st.write(f"**物品奖励**: {reward_item.get('name', '未知')} x{dungeon.get('reward_item_qty', 0)}")
            
            st.caption(dungeon.get('description', ''))
        
        with col2:
            # 检查冷却
            can_enter = True
            wait_hours = 0
            
            if last_time:
                last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                cooldown = timedelta(hours=dungeon.get("cooldown_hours", 24))
                if datetime.now(last_dt.tzinfo) < last_dt + cooldown:
                    can_enter = False
                    wait_hours = (last_dt + cooldown - datetime.now(last_dt.tzinfo)).total_seconds() / 3600
            
            # 检查等级
            user_level = st.session_state.user.cultivation_level
            if user_level < dungeon.get("required_level", 1):
                can_enter = False
            
            if can_enter:
                if st.button("⚔️ 进入秘境", key=f"enter_dungeon_{dungeon['id']}"):
                    _handle_enter_dungeon(dungeon)
            else:
                if wait_hours > 0:
                    st.warning(f"⏳ 冷却中 ({wait_hours:.1f}小时)")
                else:
                    st.warning(f"⚠️ 等级不足 (需要 {dungeon.get('required_level', 1)})")

def _handle_enter_dungeon(dungeon):
    """处理进入秘境逻辑（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 发放奖励
    spirit_reward = dungeon.get("reward_spirit_stones", 0)
    supabase.rpc("add_spirit_stones", {"uid": user_id, "amount": spirit_reward}).execute()
    
    # 发放物品奖励
    item_id = dungeon.get("reward_item_id")
    item_qty = dungeon.get("reward_item_qty", 0)
    if item_id and item_qty > 0:
        _add_item(user_id, item_id, item_qty)
    
    # 更新挑战时间
    supabase.table("user_progress").upsert({
        "user_id": user_id,
        "last_dungeon_time": datetime.now().isoformat()
    }).execute()
    
    # 显示奖励
    msg = f"✅ 通关「{dungeon['name']}」！获得 {spirit_reward:,} 灵石"
    reward_item = dungeon.get("reward_item", {})
    if reward_item:
        msg += f" 和 {reward_item.get('name', '物品')} x{dungeon.get('reward_item_qty', 0)}"
    
    st.toast(msg, icon="✅")
    st.rerun()

def _add_item(user_id: int, item_id: int, qty: int):
    """添加物品到背包（内部函数）"""
    supabase = get_supabase_client()
    inv = supabase.table("user_inventory")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("item_id", item_id)\
        .execute()
    
    if inv.data:
        current_qty = inv.data[0]["quantity"]
        supabase.table("user_inventory").update({"quantity": current_qty + qty}).eq("id", inv.data[0]["id"]).execute()
    else:
        supabase.table("user_inventory").insert({
            "user_id": user_id,
            "item_id": item_id,
            "quantity": qty
        }).execute()