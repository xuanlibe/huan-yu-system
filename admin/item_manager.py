# ==================================================#
# 物品定义管理器（编辑 effect 字段）
# 所有管理员可修改物品描述（effect）
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

    # 获取所有物品
    items = supabase.table("items").select("*").order("name").execute().data

    if not items:
        st.info("暂无物品")
        return

    for item in items:
        with st.container(border=True):
            edit_key = f"edit_{item['id']}"
            
            if st.session_state.get(edit_key, False):
                # 编辑模式
                with st.form(f"form_{item['id']}"):
                    st.text_input("名称", value=item["name"], disabled=True)
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
                # 查看模式
                st.markdown(f"### {item['name']}")
                st.write(item.get("effect", "无描述"))
                st.caption(f"分类: {item.get('category', 'N/A')} | 稀有度: {item.get('rarity', 'N/A')}")
                
                if st.button("✏️ 编辑描述", key=f"btn_{item['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()