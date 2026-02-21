# modules/shop/item_detail.py
import streamlit as st
from core.config import get_supabase_client

def show_item_detail(item_name):
    """显示物品详情"""
    st.title(f"📜 {item_name} 详情")
    
    # 从数据库获取物品信息
    supabase = get_supabase_client()
    item = supabase.table("items")\
        .select("*")\
        .eq("name", item_name)\
        .execute()
    
    if not item.data:
        st.error("物品不存在")
        return
    
    item_data = item.data[0]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("基本信息")
        st.write(f"**分类**: {item_data['category']}")
        st.write(f"**价格**: {item_data['price']:,} 灵石")
    
    with col2:
        st.subheader("详细介绍")
        desc = item_data.get('description') or "（无）"
        st.write(desc)
    
    # 返回按钮
    if st.button("⬅️ 返回商店"):
        st.session_state.page = 'shop'
        st.rerun()