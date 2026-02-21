# modules/shop/list_item.py
"""玩家上架商品页面 - 支持管理员上架任意商品"""

import streamlit as st
from core.config import get_supabase_client

def show_list_item_page():
    st.set_page_config(page_title="寰宇系统 - 上架商品", layout="wide")
    from modules.sidebar import render_sidebar
    render_sidebar()
    
    st.title("📤 上架商品")
    
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("请先登录")
        st.stop()
    
    user = st.session_state.user
    supabase = get_supabase_client()
    
    if st.button("⬅️ 返回藏宝阁"):
        st.session_state.page = 'shop'
        st.rerun()
    
    # === 管理员：可上架任意系统商品 ===
    if user.is_admin:
        st.info("🛠️ 管理员模式：可上架任意系统商品")
        system_items = supabase.table("items")\
            .select('"uuid_id", "name", "category", "effect", "price"')\
            .eq('"is_system"', True)\
            .execute().data
        
        if not system_items:
            st.warning("暂无系统商品可上架")
            return
        
        item_options = {f"{item['name']} ({item['category']})": item for item in system_items}
        selected_name = st.selectbox("选择系统商品", list(item_options.keys()))
        selected_item = item_options[selected_name]
        
        price = st.number_input("售价（灵石）", min_value=1, value=selected_item['price'])
        quantity = st.number_input("上架数量", min_value=1, value=1)
        
        if st.button("✅ 确认上架"):
            try:
                supabase.table("shop_listings").insert({
                    "item_uuid": selected_item["uuid_id"],
                    "seller_id": user.id,
                    "price": price,
                    "quantity": quantity,
                    "is_active": True
                }).execute()
                st.success("✅ 商品已上架！")
                st.session_state.page = 'shop'
                st.rerun()
            except Exception as e:
                st.error(f"❌ 上架失败: {str(e)}")
    
    # === 普通玩家：只能上架背包物品 ===
    else:
        inventory = supabase.table("user_inventory")\
            .select("*, items(uuid_id, name, category, effect)")\
            .eq("user_id", user.id)\
            .execute().data
        
        if not inventory:
            st.info("🎒 背包为空，无法上架")
            return
        
        valid_inventory = [inv for inv in inventory if inv['quantity'] > 0]
        if not valid_inventory:
            st.info("🎒 背包中没有可用物品")
            return
        
        item_options = {
            f"{inv['items']['name']} (x{inv['quantity']})": inv['id']
            for inv in valid_inventory
        }
        
        selected_name = st.selectbox("选择要上架的物品", list(item_options.keys()))
        inv_id = item_options[selected_name]
        
        selected_inv = next(inv for inv in valid_inventory if inv['id'] == inv_id)
        max_qty = selected_inv['quantity']
        item_uuid = selected_inv['items']['uuid_id']
        
        price = st.number_input("售价（灵石）", min_value=1, value=100)
        quantity = st.number_input("上架数量", min_value=1, max_value=max_qty)
        
        if 'listing_in_progress' not in st.session_state:
            st.session_state.listing_in_progress = False
        
        if st.button("✅ 确认上架", disabled=st.session_state.listing_in_progress):
            if st.session_state.listing_in_progress:
                return
            
            st.session_state.listing_in_progress = True
            try:
                supabase.table("shop_listings").insert({
                    "item_uuid": item_uuid,
                    "seller_id": user.id,
                    "price": price,
                    "quantity": quantity,
                    "is_active": True
                }).execute()
                
                new_quantity = max_qty - quantity
                if new_quantity == 0:
                    supabase.table("user_inventory").delete().eq("id", inv_id).execute()
                else:
                    supabase.table("user_inventory").update({
                        "quantity": new_quantity
                    }).eq("id", inv_id).execute()
                
                st.success("✅ 商品已上架！")
                st.session_state.page = 'shop'
                st.rerun()
            
            except Exception as e:
                st.error(f"❌ 上架失败: {str(e)}")
            finally:
                st.session_state.listing_in_progress = False