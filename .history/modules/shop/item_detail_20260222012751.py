# modules/shop/item_detail.py
"""
物品详情页面模块
功能：显示单个物品的详细信息
"""

import streamlit as st
from core.config import get_supabase_client


def show_item_detail(item_uuid):
    """
    显示物品详情页面
    
    参数:
        item_uuid (str): 物品的 UUID 标识符
    """
    # 从数据库获取物品详细信息
    supabase = get_supabase_client()
    item = supabase.table("items")\
        .select('"name", "category", "effect", "price", "stock"')\
        .eq('"uuid_id"', item_uuid)\
        .execute()
    
    # 如果物品不存在，显示错误信息
    if not item.data:
        st.error("物品不存在")
        return
    
    # 获取物品数据
    item_data = item.data[0]
    
    # 显示页面标题
    st.title(f"📜 {item_data['name']} 详情")
    
    # 创建两列布局：左侧基本信息，右侧详细介绍
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("基本信息")
        st.write(f"**分类**: {item_data['category']}")
        # 价格显示（统一格式：XXX 灵石）
        st.write(f"**价格**: {item_data['price']:,} 灵石")
        
        # 库存显示处理
        if item_data['stock'] == -1:
            qty_text = "不限量"
        else:
            qty_text = f"{item_data['stock']}个"
        st.write(f"**库存**: {qty_text}")
    
    with col2:
        st.subheader("详细介绍")
        description = item_data.get('effect') or "（无）"
        st.write(description)
    
    # 返回商店按钮
    if st.button("⬅️ 返回商店"):
        # 清除会话状态中的详情页标识
        if 'viewing_item_uuid' in st.session_state:
            del st.session_state.viewing_item_uuid
        st.rerun()