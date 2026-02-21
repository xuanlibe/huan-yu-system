# modules/shop/list_item.py
import streamlit as st
from core.config import get_supabase_client

def show_list_item_page():
    st.title("📤 上架商品")
    user = st.session_state.user
    
    supabase = get_supabase_client()
    # 获取玩家背包中的物品
    inventory = supabase.table("user_inventory")\
        .select("*, items(uuid_id, name, category, effect)")\
        .eq("user_id", user.id)\
        .execute().data

    if not inventory:
        st.info("🎒 背包为空，无法上架")
        return

    item_options = {
        f"{inv['items']['name']} (x{inv['quantity']})": inv['items']['uuid_id']
        for inv in inventory if inv['quantity'] > 0
    }

    selected_name = st.selectbox("选择要上架的物品", list(item_options.keys()))
    item_uuid = item_options[selected_name]

    price = st.number_input("售价（灵石）", min_value=1, value=100)
    quantity = st.number_input("上架数量", min_value=1, 
                              max_value=next(inv['quantity'] for inv in inventory 
                                           if inv['items']['uuid_id'] == item_uuid))

    if st.button("✅ 确认上架"):
        # 创建上架记录
        supabase.table("shop_listings").insert({
            "item_uuid": item_uuid,
            "seller_id": user.id,
            "price": price,
            "quantity": quantity,
            "is_active": True
        }).execute()
        st.success("✅ 商品已上架！")
        st.session_state.page = 'shop'
        st.rerun()