# modules/sidebar.py
"""
侧边栏模块
提供统一的导航侧边栏
"""

import streamlit as st

def render_sidebar():
    """渲染应用侧边栏"""
    with st.sidebar:
        st.title("⚔️ 寰宇修仙系统")
        st.divider()
        
        # 页面导航按钮
        pages = [
            ("🏠 主城", "main"),
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
        
        st.divider()
        
        # 返回登录页
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.clear()
            st.session_state.page = 'login'
            st.rerun()