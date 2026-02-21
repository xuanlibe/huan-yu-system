# modules/shop/list_item.py
"""玩家上架商品页面 - 完整版"""

import streamlit as st
from core.config import get_supabase_client

def show_list_item_page():
    # === 统一页面配置 ===
    st.set_page_config(page_title="寰宇系统 - 上架商品", layout="wide")
    
    # === 渲染全局侧边栏 ===
    from modules.sidebar import render_sidebar
    render_sidebar()
    
    st.title("📤 上架商品")
    
    # === 权限检查 ===
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("请先登录")
        st.stop()
    
    user = st.session_state.user
    supabase = get_supabase_client()
    
    # === 获取玩家背包中的物品（关联 items 表）===
    inventory = supabase.table("user_inventory")\
        .select("*, items(uuid_id, name, category, effect)")\
        .eq("user_id", user.id)\
        .execute().data
    
    if not inventory:
        st.info("🎒 背包为空，无法上架")
        return
    
    # 过滤数量 > 0 的物品
    valid_inventory = [inv for inv in inventory if inv['quantity'] > 0]
    if not valid_inventory:
        st.info("🎒 背包中没有可用物品")
        return
    
    # === 构建物品选项 ===
    item_options = {
        f"{inv['items']['name']} (x{inv['quantity']})": inv['id']  # 使用 inventory.id 作为 key
        for inv in valid_inventory
    }
    
    selected_name = st.selectbox("选择要上架的物品", list(item_options.keys()))
    inv_id = item_options[selected_name]
    
    # 获取选中物品的完整信息
    selected_inv = next(inv for inv in valid_inventory if inv['id'] == inv_id)
    max_qty = selected_inv['quantity']
    item_uuid = selected_inv['items']['uuid_id']
    
    # === 输入价格和数量 ===
    price = st.number_input("售价（灵石）", min_value=1, value=100)
    quantity = st.number_input("上架数量", min_value=1, max_value=max_qty)
    
    # === 防重复提交：使用 session_state 标记 ===
    if 'listing_in_progress' not in st.session_state:
        st.session_state.listing_in_progress = False
    
    if st.button("✅ 确认上架", disabled=st.session_state.listing_in_progress):
        if st.session_state.listing_in_progress:
            return  # 防止重复点击
        
        st.session_state.listing_in_progress = True
        try:
            # 1. 创建上架记录
            supabase.table("shop_listings").insert({
                "item_uuid": item_uuid,
                "seller_id": user.id,
                "price": price,
                "quantity": quantity,
                "is_active": True
            }).execute()
            
            # 2. 从背包扣除数量（关键修复！）
            new_quantity = max_qty - quantity
            if new_quantity == 0:
                # 删除背包记录
                supabase.table("user_inventory").delete().eq("id", inv_id).execute()
            else:
                # 更新数量
                supabase.table("user_inventory").update({
                    "quantity": new_quantity
                }).eq("id", inv_id).execute()
            
            st.success("✅ 商品已上架！")
            st.session_state.page = 'shop'
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ 上架失败: {str(e)}")
        finally:
            st.session_state.listing_in_progress = False  # 重置状态