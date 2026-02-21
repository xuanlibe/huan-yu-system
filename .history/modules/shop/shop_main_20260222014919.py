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
    
    # 返回主城按钮
    if st.button("⬅️ 返回主城", key="shop_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
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
        item (dict): 商品数据字典
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
        
        # 购买按钮 - 使用实际购买逻辑
        qty = st.number_input(
            "数量", 
            min_value=1, 
            max_value=999, 
            value=1, 
            key=f"shop_qty_{item['uuid_id']}"
        )
        
        if st.button("🛒 购买", key=f"buy_{item['uuid_id']}"):
            _handle_purchase(item['uuid_id'], qty)


def _handle_purchase(item_uuid: str, quantity: int):
    """处理购买逻辑"""
    supabase = get_supabase_client()
    
    # 检查用户是否已登录
    if 'user' not in st.session_state or not st.session_state.user:
        st.toast("❌ 请先登录", icon="❌")
        return
    
    user_id = st.session_state.user.id
    
    # 获取商品信息
    item_response = supabase.table("items")\
        .select('"id", "name", "price", "stock"')\
        .eq('"uuid_id"', item_uuid)\
        .execute()
    
    if not item_response.data:
        st.toast("❌ 商品不存在", icon="❌")
        return
    
    item = item_response.data[0]
    total_price = item["price"] * quantity
    
    # 检查库存
    if item.get("stock", -1) != -1 and item["stock"] < quantity:
        st.toast(f"❌ 库存不足，当前仅剩 {item.get('stock', 0)} 件", icon="❌")
        return
    
    # 检查用户灵石
    user_response = supabase.table("users")\
        .select("spirit_stones")\
        .eq("id", user_id)\
        .execute()
    
    if not user_response.data:
        st.toast("❌ 用户信息错误", icon="❌")
        return
    
    current_stones = user_response.data[0]["spirit_stones"]
    if current_stones < total_price:
        st.toast(f"❌ 灵石不足！需要 {total_price:,} 灵石，当前拥有 {current_stones:,}", icon="❌")
        return
    
    try:
        # 扣除灵石
        supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": total_price}).execute()
        
        # 添加到背包
        inventory_response = supabase.table("user_inventory")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("item_id", item["id"])\
            .execute()
        
        if inventory_response.data:
            # 更新现有数量
            current_qty = inventory_response.data[0]["quantity"]
            supabase.table("user_inventory")\
                .update({"quantity": current_qty + quantity})\
                .eq("id", inventory_response.data[0]["id"])\
                .execute()
        else:
            # 新增物品到背包
            supabase.table("user_inventory")\
                .insert({
                    "user_id": user_id,
                    "item_id": item["id"],
                    "quantity": quantity
                }).execute()
        
        # 更新库存（如果有限制）
        if item.get("stock", -1) != -1:
            supabase.table("items")\
                .update({"stock": item["stock"] - quantity})\
                .eq("id", item["id"])\
                .execute()
        
        # 更新用户状态
        updated_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if updated_user.data:
            from modules.login import User
            st.session_state.user = User(updated_user.data[0])
        
        st.toast(f"✅ 成功购买 {item['name']} x{quantity}！", icon="✅")
        st.rerun()
        
    except Exception as e:
        st.toast(f"❌ 购买失败: {str(e)}", icon="❌")