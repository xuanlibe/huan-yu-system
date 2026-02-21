# modules/shop/shop_main.py
import streamlit as st
from core.config import get_supabase_client
from modules.sidebar import render_sidebar
from modules.shop.item_detail import show_item_detail

def show_shop_page():
    """新藏宝阁页面"""
    st.set_page_config(page_title="寰宇系统 - 藏宝阁", layout="wide")
    render_sidebar()
    
    # 检查是否查看物品详情
    if 'viewing_item' in st.session_state:
        show_item_detail(st.session_state.viewing_item)
        return
    
    st.title("🏪 藏宝阁")
    
    # 获取所有系统商品
    supabase = get_supabase_client()
    listings = supabase.table("shop_listings")\
        .select("*, items(name, category, price)")\
        .eq("seller_id", None)\
        .eq("is_active", True)\
        .execute()
    
    if not listings.data:
        st.info("藏宝阁暂无商品")
        return
    
    # 按分类分组
    categories = {}
    for listing in listings.data:
        cat = listing['items']['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(listing)
    
    # 显示商品
    for category, items in categories.items():
        st.subheader(f"📦 {category}")
        for item in items:
            _render_shop_item(item)

def _render_shop_item(listing):
    """渲染商店商品"""
    item = listing['items']
    qty_text = "不限量" if listing['quantity'] == -1 else f"{listing['quantity']}个"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # 点击商品名跳转详情
        if st.button(f"**{item['name']}**", key=f"item_{item['name']}"):
            st.session_state.viewing_item = item['name']
            st.rerun()
        st.caption(item.get('description', '（无）'))
    
    with col2:
        st.write(f"💰 {item['price']:,} ls")
        st.write(f"📦 {qty_text}")
        if st.button("🛒 购买", key=f"buy_{item['name']}"):
            st.toast(f"购买 {item['name']} 成功！", icon="🎉")