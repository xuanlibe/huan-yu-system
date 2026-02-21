# ==================================================
# 藏宝阁模块
# 功能：商品浏览、购买、库存管理
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.errors import safe_page_load
from modules.login import User

def show_shop_page():
    """
    显示藏宝阁页面
    包含商品分类展示和购买功能
    """
    if not FEATURES.get("shop", True):
        st.warning("藏宝阁暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 藏宝阁", layout="wide")
    st.title("🏪 藏宝阁 · 丹药材料商店")
    
    if st.button("⬅️ 返回主城", key="shop_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("藏宝阁"):
        _render_shop_content()

def _render_shop_content():
    """渲染藏宝阁内容（内部函数）"""
    supabase = get_supabase_client()
    
    # 获取所有商品
    items = supabase.table("items").select("*").execute()
    items_data = items.data if items else []
    
    if not items_data:
        st.info("藏宝阁暂无商品上架")
        return
    
    # 按类别分组
    categories = {}
    for item in items_data:
        cat = item.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # 显示每个类别的商品
    for category, cat_items in categories.items():
        st.subheader(f"📦 {category}")
        for item in cat_items:
            _render_shop_item(item)

def _render_shop_item(item):
    """渲染单个商品卡片（内部函数）"""
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{item['name']}**")
            st.caption(item.get("effect", ""))
            st.write(f"💰 价格：{item['price']:,} 灵石")
            if "stock" in item and item["stock"] < 999999:
                st.write(f"📦 库存：{item['stock']}")
        
        with col2:
            qty = st.number_input(
                "数量", 
                min_value=1, 
                max_value=999, 
                value=1, 
                key=f"shop_qty_{item['id']}"
            )
        
        with col3:
            if st.button("🛒 购买", key=f"shop_buy_{item['id']}"):
                _handle_purchase(item['id'], qty)

def _handle_purchase(item_id: int, quantity: int):
    """处理购买逻辑（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取商品信息
    items = supabase.table("items").select("*").eq("id", item_id).execute()
    if not items.data:
        st.toast("❌ 商品不存在", icon="❌")
        return
    
    item = items.data[0]
    total_price = item["price"] * quantity
    
    # 检查库存
    if item.get("stock", 999999) < quantity:
        st.toast(f"❌ 库存不足，当前仅剩 {item.get('stock', 0)} 件", icon="❌")
        return
    
    # 检查用户灵石
    users = supabase.table("users").select("spirit_stones").eq("id", user_id).execute()
    if not users.data or users.data[0]["spirit_stones"] < total_price:
        st.toast(f"❌ 灵石不足！需要 {total_price}，当前拥有 {users.data[0]['spirit_stones'] if users.data else 0}", icon="❌")
        return
    
    # 扣除灵石
    supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": total_price}).execute()
    
    # 添加到背包
    inventory = supabase.table("user_inventory").select("*").eq("user_id", user_id).eq("item_id", item_id).execute()
    if inventory.data:
        current_qty = inventory.data[0]["quantity"]
        supabase.table("user_inventory").update({"quantity": current_qty + quantity}).eq("id", inventory.data[0]["id"]).execute()
    else:
        supabase.table("user_inventory").insert({
            "user_id": user_id,
            "item_id": item_id,
            "quantity": quantity
        }).execute()
    
    # 更新库存
    if "stock" in item and item["stock"] < 999999:
        supabase.table("items").update({"stock": item["stock"] - quantity}).eq("id", item_id).execute()
    
    # 更新用户状态
    users = supabase.table("users").select("*").eq("id", user_id).execute()
    if users.data:
        st.session_state.user = User(users.data[0])
    
    st.toast(f"✅ 成功购买 {item['name']} x{quantity}！", icon="✅")
    st.rerun()