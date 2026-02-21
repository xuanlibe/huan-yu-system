# modules/sidebar.py
"""侧边栏模块：提供统一的全局导航（所有页面自动显示）"""

import streamlit as st

def render_sidebar():
    """渲染应用侧边栏（全局生效）"""
    with st.sidebar:
        # ========== 顶部：用户信息 & 快捷返回 ==========
        if 'user' in st.session_state and st.session_state.user:
            user = st.session_state.user
            st.title(f"⚔️ {user.username}")
            st.caption(f"{user.realm} {user.stage}层")
            st.write(f"💎 灵石：{user.spirit_stones:,}")
            st.divider()
            
            # 管理员专属快捷入口
            if user.is_admin:
                if st.button("🛡️ 管理中心", use_container_width=True, key="nav_admin"):
                    st.session_state.page = 'admin_center'
                    st.rerun()
                if st.button("📦 物品管理", use_container_width=True, key="nav_item_mgr"):
                    st.session_state.page = 'item_manager'
                    st.rerun()
                st.divider()
        else:
            st.title("⚔️ 寰宇修仙系统")
            st.divider()

        # ========== 核心导航 ==========
        st.subheader("🗺️ 地图导航")
        
        # 固定「返回主城」在最顶部
        if st.button("🏠 返回主城", use_container_width=True, key="nav_main_top"):
            st.session_state.page = 'main'
            st.rerun()

        # 其他功能页面
        pages = [
            ("🏪 藏宝阁", "shop"),
            ("🎒 背包", "backpack"),
            ("🏯 宗门", "sect"),
            ("🧪 炼丹", "alchemy"),
            ("🔨 锻造", "forge"),
            ("🌀 阵法", "array"),
            ("🏰 秘境", "dungeon"),
        ]
        for label, page_key in pages:
            if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.page = page_key
                st.rerun()
        
        # 藏宝阁子菜单（关键新增！）
        if st.session_state.get('page') == 'shop':
            st.markdown("### 🛒 操作")
            if st.button("📤 上架商品", use_container_width=True, key="nav_list_item"):
                st.session_state.page = 'list_item'
                st.rerun()
            if st.button("🏪 我的摊位", use_container_width=True, key="nav_my_listings"):
                st.session_state.page = 'my_listings'
                st.rerun()
            st.divider()

        # ========== 底部：账户操作 ==========
        if 'user' in st.session_state and st.session_state.user:
            if st.button("🚪 退出登录", use_container_width=True, type="primary"):
                st.session_state.clear()
                st.session_state.page = 'login'
                st.rerun()
        else:
            if st.button("🔑 登录 / 注册", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()