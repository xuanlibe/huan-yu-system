# modules/shop/shop_main.py
"""
藏宝阁主页面模块
功能：显示所有系统商品，支持按分类分组展示和物品详情跳转
"""

import streamlit as st
from core.config import get_supabase_client
from modules.sidebar import render_sidebar


def show_shop_page():
    """
    显示藏宝阁主页面
    
    功能流程：
    1. 设置页面配置和侧边栏
    2. 检查是否需要显示物品详情页
    3. 从数据库获取所有系统商品
    4. 按分类分组并渲染商品列表
    """
    # 设置页面标题和布局
    st.set_page_config(page_title="寰宇系统 - 藏宝阁", layout="wide")
    render_sidebar()
    
    # 检查是否需要显示物品详情页
    if 'viewing_item_uuid' in st.session_state:
        from modules.shop.item_detail import show_item_detail
        show_item_detail(st.session_state.viewing_item_uuid)
        return
    
    # 显示页面标题
    st.title("🏪 藏宝阁")
    
    # 从数据库获取所有系统商品
    supabase = get_supabase_client()
    items = supabase.table("items")\
        .select('"uuid_id", "name", "category", "effect", "price", "stock", "usable"')\
        .eq('"is_system"', True)\
        .execute()
    
    # 如果没有商品，显示提示信息
    if not items.data:
        st.info("藏宝阁暂无商品")
        return
    
    # 按分类分组商品
    categories = {}
    for item in items.data:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # 渲染每个分类的商品
    for category, items_list in categories.items():
        st.subheader(f"📦 {category}")
        for item in items_list:
            _render_shop_item(item)


def _render_shop_item(item):
    """
    渲染单个商品卡片
    
    参数:
        item (dict): 商品数据字典，包含 uuid_id, name, category, effect, price, stock 等字段
    """
    # 处理库存显示文本
    if item['stock'] == -1:
        qty_text = "不限量"
    else:
        qty_text = f"{item['stock']}个"
    
    # 创建两列布局：左侧商品信息，右侧操作按钮
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 商品名称按钮（点击跳转详情页）
        if st.button(f"**{item['name']}**", key=f"item_{item['uuid_id']}"):
            st.session_state.viewing_item_uuid = item['uuid_id']
            st.rerun()
        
        # 商品效果描述
        description = item.get('effect') or "（无）"
        st.caption(description)
    
    with col2:
        # 价格显示（统一格式：XXX 灵石）
        st.write(f"💰 {item['price']:,} 灵石")
        # 库存显示
        st.write(f"📦 {qty_text}")
        
        # 购买按钮
        if st.button("🛒 购买", key=f"buy_{item['uuid_id']}"):
            st.toast(f"购买 {item['name']} 成功！", icon="🎉")