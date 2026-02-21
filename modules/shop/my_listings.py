# modules/shop/my_listings.py
import streamlit as st
from core.config import get_supabase_client

def show_my_listings_page():
    st.set_page_config(page_title="寰宇系统 - 我的摊位", layout="wide")
    from modules.sidebar import render_sidebar
    render_sidebar()
    
    st.title("🏪 我的摊位")
    
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("请先登录")
        st.stop()
        
    user = st.session_state.user
    supabase = get_supabase_client()
    
    # 返回按钮
    if st.button("⬅️ 返回藏宝阁"):
        st.session_state.page = 'shop'
        st.rerun()
    
    # 获取用户上架的商品
    listings = supabase.table("shop_listings") \
        .select("*, items(uuid_id, name, category, effect)") \
        .eq("seller_id", user.id) \
        .eq("is_active", True) \
        .execute().data
        
    if not listings:
        st.info("📭 你还没有上架任何商品")
        return
        
    st.subheader(f"📦 共 {len(listings)} 件商品正在出售")
    
    for listing in listings:
        item = listing["items"]
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{item['name']}** ×{listing['quantity']} | 💰{listing['price']} 灵石")
            if item.get("effect"):
                st.caption(f"效果: {item['effect']}")
                
        with col2:
            st.write(f"品类: {item['category']}")
            
        with col3:
            # 下架按钮
            if st.button("🗑️ 下架", key=f"del_{listing['id']}"):
                try:
                    # 1. 删除商品 listing
                    supabase.table("shop_listings").delete().eq("id", listing["id"]).execute()
                    
                    # 2. 把物品退回到 user_inventory
                    # 检查背包是否已有该物品
                    inv = supabase.table("user_inventory") \
                        .select("*") \
                        .eq("user_id", user.id) \
                        .eq("item_uuid", item["uuid_id"]) \
                        .execute().data
                        
                    if inv:
                        # 已有 → 增加数量
                        current_qty = inv[0]["quantity"]
                        new_qty = current_qty + listing["quantity"]
                        supabase.table("user_inventory") \
                            .update({"quantity": new_qty}) \
                            .eq("id", inv[0]["id"]) \
                            .execute()
                    else:
                        # 没有 → 新增记录
                        supabase.table("user_inventory").insert({
                            "user_id": user.id,
                            "item_uuid": item["uuid_id"],
                            "quantity": listing["quantity"]
                        }).execute()
                    
                    st.success(f"✅ {item['name']} 已下架并退回背包！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 下架失败: {str(e)}")
        
        st.divider()