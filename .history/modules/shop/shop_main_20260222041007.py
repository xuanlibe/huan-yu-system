# modules/shop/shop_main.py
import streamlit as st
from core.config import get_supabase_client
from modules.sidebar import render_sidebar

def show_shop_page():
    st.set_page_config(page_title="寰宇系统 - 藏宝阁", layout="wide")
    render_sidebar()
    
    # 处理详情页
    if 'viewing_item_uuid' in st.session_state:
        from modules.shop.item_detail import show_item_detail
        show_item_detail(st.session_state.viewing_item_uuid)
        return

    st.title("🏪 藏宝阁")
    
    # === 权限优化：管理员和玩家都能上架 ===
    user = st.session_state.user if 'user' in st.session_state else None
    if user:
        if st.button("📤 我要上架商品", type="primary"):
            st.session_state.page = 'list_item'
            st.rerun()
    # ===================================
    
    if st.button("⬅️ 返回主城"):
        st.session_state.page = 'main'
        st.rerun()

    supabase = get_supabase_client()

    # === 获取所有活跃商品（系统 + 玩家）===
    listings = []
    
    # 1. 系统商品（is_system=true）
    system_items = supabase.table("items")\
        .select('"uuid_id", "name", "category", "effect", "price", "stock"')\
        .eq('"is_system"', True)\
        .execute().data
    
    for item in system_items:
        listings.append({
            "type": "system",
            "item_uuid": item["uuid_id"],
            "name": item["name"],
            "category": item["category"],
            "effect": item["effect"],
            "price": item["price"],
            "quantity": item["stock"],
            "is_active": True,
            "seller_id": None
        })
    
    # 2. 玩家上架商品
    player_listings = supabase.table("shop_listings")\
        .select("*, items(uuid_id, name, category, effect)")\
        .eq("is_active", True)\
        .execute().data
    
    for listing in player_listings:
        item = listing["items"]
        listings.append({
            "type": "player",
            "listing_id": listing["id"],
            "item_uuid": item["uuid_id"],
            "name": item["name"],
            "category": item["category"],
            "effect": item["effect"],
            "price": listing["price"],
            "quantity": listing["quantity"],
            "is_active": True,
            "seller_id": listing["seller_id"]
        })

    # 按分类分组
    categories = {}
    for listing in listings:
        cat = listing["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(listing)

    for category, items_list in categories.items():
        st.subheader(f"📦 {category}")
        for item in items_list:
            _render_listing(item, user)

def _render_listing(listing, user):
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        if st.button(f"**{listing['name']}**", key=f"detail_{listing['item_uuid']}_{listing.get('listing_id', 'sys')}"):
            st.session_state.viewing_item_uuid = listing['item_uuid']
            st.rerun()
        st.caption(listing['effect'])

    with col2:
        st.write(f"💰 {listing['price']:,} 灵石")
        qty_text = "不限量" if listing['quantity'] == -1 else f"{listing['quantity']}个"
        st.write(f"📦 {qty_text}")

        # 购买按钮（仅活跃商品）
        if listing['is_active']:
            qty = st.number_input("数量", min_value=1, max_value=999, value=1,
                                key=f"qty_{listing.get('listing_id', listing['item_uuid'])}")
            if st.button("🛒 购买", key=f"buy_{listing.get('listing_id', listing['item_uuid'])}"):
                _handle_purchase(listing, qty)

    with col3:
        # === 管理员：可编辑 + 可下架所有商品 ===
        if user and user.is_admin:
            # 编辑按钮（唯一 key）
            if listing['type'] == 'system':
                edit_key = f"edit_desc_sys_{listing['item_uuid']}"
            else:
                edit_key = f"edit_desc_player_{listing['listing_id']}"
            
            if st.button("✏️ 编辑", key=edit_key):
                st.session_state.editing_item_uuid = listing['item_uuid']
                st.session_state.page = 'item_manager'
                st.rerun()
            
            # 下架按钮（管理员可下架所有）
            if listing['type'] == 'player':  # 系统商品不能下架
                if st.button("🔽 强制下架", key=f"admin_unlist_{listing['listing_id']}"):
                    _toggle_listing_status(listing['listing_id'], False, is_admin=True)
        
        # === 普通玩家：只能管理自己的上架 ===
        elif user and listing['type'] == 'player' and str(listing['seller_id']) == str(user.id):
            if st.button("🔽 下架", key=f"unlist_{listing['listing_id']}"):
                _toggle_listing_status(listing['listing_id'], False, is_admin=False)

def _handle_purchase(listing, quantity):
    st.warning("购买功能暂未实现")

def _toggle_listing_status(listing_id, is_active, is_admin=False):
    supabase = get_supabase_client()
    user = st.session_state.user
    
    if not is_active:  # 下架时处理物品返还
        listing = supabase.table("shop_listings")\
            .select("*").eq("id", listing_id).execute().data[0]
        
        # 只有非管理员下架才返还物品（管理员下架视为没收）
        if not is_admin:
            item_uuid = listing["item_uuid"]
            quantity = listing["quantity"]
            
            existing = supabase.table("user_inventory")\
                .select("*").eq("user_id", user.id).eq("item_uuid", item_uuid)\
                .execute().data
            
            if existing:
                current_qty = existing[0]["quantity"]
                supabase.table("user_inventory").update({
                    "quantity": current_qty + quantity
                }).eq("id", existing[0]["id"]).execute()
            else:
                supabase.table("user_inventory").insert({
                    "user_id": user.id,
                    "item_uuid": item_uuid,
                    "quantity": quantity
                }).execute()
    
    # 更新上架状态
    supabase.table("shop_listings").update({"is_active": is_active}).eq("id", listing_id).execute()
    action = "强制下架" if is_admin else "下架"
    st.success(f"✅ {action}成功！")
    st.rerun()