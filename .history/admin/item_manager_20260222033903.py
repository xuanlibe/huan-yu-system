# ==================================================#
# 物品定义管理器（编辑 effect 字段）
# 所有管理员可修改物品描述（effect）
# 新增：区分系统商品与玩家商品，强化权限提示
# ==================================================#

import streamlit as st
from core.config import get_supabase_client

def show_item_manager():
    user = st.session_state.user
    if not user.is_admin:
        st.error("❌ 无权访问")
        st.stop()

    st.title("📦 物品定义管理")
    st.caption("修改 'effect' 字段即修改藏宝阁商品描述")

    supabase = get_supabase_client()

    # 获取所有物品（保持原逻辑）
    items = supabase.table("items").select("*").order("name").execute().data
    if not items:
        st.info("暂无物品")
        return

    # === 新增：搜索功能（不影响原有逻辑）===
    search_query = st.text_input("🔍 搜索物品名称", key="item_search")
    if search_query:
        filtered_items = [
            item for item in items 
            if search_query.lower() in item["name"].lower()
        ]
    else:
        filtered_items = items
    # ======================================

    for item in filtered_items:
        with st.container(border=True):
            edit_key = f"edit_{item['id']}"
            
            # === 新增：商品类型标识（仅显示，不影响编辑）===
            is_system = item.get("is_system", False)
            owner_id = item.get("owner_id")
            if is_system:
                type_tag = "🔖 系统商品"
            elif owner_id:
                type_tag = "👤 玩家商品"
            else:
                type_tag = "❓ 未知类型"
            # ==========================================

            if st.session_state.get(edit_key, False):
                # 编辑模式（完全保留原逻辑）
                with st.form(f"form_{item['id']}"):
                    st.text_input("名称", value=item["name"], disabled=True)
                    st.caption(type_tag)  # 显示类型
                    new_effect = st.text_area("描述 (effect)", value=item.get("effect", ""))
                    col1, col2 = st.columns(2)
                    with col1:
                        save = st.form_submit_button("💾 保存")
                    with col2:
                        cancel = st.form_submit_button("❌ 取消")
                    if save:
                        supabase.table("items").update({
                            "effect": new_effect
                        }).eq("id", item["id"]).execute()
                        st.success("✅ 已更新")
                        st.session_state[edit_key] = False
                        st.rerun()
                    elif cancel:
                        st.session_state[edit_key] = False
                        st.rerun()
            else:
                # 查看模式（新增类型标识）
                st.markdown(f"### {item['name']}")
                st.write(item.get("effect", "无描述"))
                st.caption(f"{type_tag} | 分类: {item.get('category', 'N/A')} | 稀有度: {item.get('rarity', 'N/A')}")
                
                # === 新增：权限提示（仅当是系统商品时）===
                if is_system:
                    st.warning("⚠️ 此为系统商品，修改将影响所有玩家可见描述")
                # ======================================
                
                if st.button("✏️ 编辑描述", key=f"btn_{item['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()