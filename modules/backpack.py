# ==================================================
# 背包模块
# 功能：查看物品、使用物品、丢弃物品
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.errors import safe_page_load
from utils.helpers import get_current_time_str

def show_backpack_page():
    """
    显示背包页面
    包含物品列表、使用、丢弃功能
    """
    if not FEATURES.get("backpack", True):
        st.warning("背包功能暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 背包", layout="wide")
    st.title("🎒 个人背包")
    
    if st.button("⬅️ 返回主城", key="backpack_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("背包"):
        _render_backpack_content()

def _render_backpack_content():
    """渲染背包内容（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取背包物品
    inventory = supabase.table("user_inventory")\
        .select("*, items(name, category, effect, price, usable, effect_type, effect_value)")\
        .eq("user_id", user_id)\
        .execute()
    
    inventory_data = inventory.data if inventory else []
    
    if not inventory_data:
        st.info("背包空空如也，快去藏宝阁逛逛吧！")
        return
    
    st.write(f"共 {len(inventory_data)} 种物品")
    
    # 显示每个物品
    for inv_item in inventory_data:
        _render_inventory_item(inv_item)

def _render_inventory_item(inv_item):
    """渲染单个物品卡片（内部函数）"""
    item_info = inv_item.get("items", {})
    item_name = item_info.get("name", "未知物品") if item_info else "未知物品"
    quantity = inv_item.get("quantity", 0)
    
    with st.expander(f"{item_name} x{quantity}"):
        st.write(f"**类别**: {item_info.get('category', '其他')}")
        st.write(f"**效果**: {item_info.get('effect', '无')}")
        st.write(f"**获得时间**: {inv_item.get('acquired_date', '未知')[:19].replace('T', ' ')}")
        
        # 可使用物品
        if item_info.get("usable", False):
            if st.button("✨ 使用", key=f"use_{inv_item['id']}"):
                _handle_use_item(inv_item, item_info)
        
        # 丢弃功能
        if st.button("🗑️ 丢弃", key=f"discard_{inv_item['id']}"):
            _handle_discard_item(inv_item['id'], item_name, inv_item['quantity'])

def _handle_use_item(inv_item, item_info):
    """处理物品使用（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    effect_type = item_info.get("effect_type", "")
    effect_value = item_info.get("effect_value", 0)
    
    if effect_type == "heal_hp":
        # 恢复生命值
        current_hp = st.session_state.user.hp
        new_hp = current_hp + effect_value
        supabase.table("user_cultivation").update({"hp": new_hp}).eq("user_id", user_id).execute()
        st.session_state.user.hp = new_hp
        
    elif effect_type == "add_exp":
        # 增加经验
        current_exp = supabase.rpc("get_user_exp", {"uid": user_id}).execute().data or 0
        new_exp = current_exp + effect_value
        supabase.table("user_cultivation").update({"exp": new_exp}).eq("user_id", user_id).execute()
    
    # 从背包移除
    supabase.table("user_inventory").delete().eq("id", inv_item["id"]).execute()
    
    st.toast(f"✅ 使用了 1 个{item_info['name']}！", icon="✅")
    st.rerun()

def _handle_discard_item(inv_id: int, item_name: str, quantity: int):
    """处理物品丢弃（内部函数）"""
    # 显示确认弹窗
    with st.popover(f"确认丢弃 {item_name}?"):
        st.write(f"确定要丢弃 **{item_name}** x{quantity} 吗？")
        st.warning("此操作不可恢复！")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认", key=f"confirm_discard_{inv_id}"):
                supabase = get_supabase_client()
                supabase.table("user_inventory").delete().eq("id", inv_id).execute()
                st.toast(f"🗑️ 已丢弃 {item_name}", icon="✅")
                st.rerun()
        with col2:
            if st.button("❌ 取消", key=f"cancel_discard_{inv_id}"):
                st.rerun()