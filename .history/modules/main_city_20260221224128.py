# ==================================================
# 主城模块
# 功能：显示主城界面和导航菜单
# ==================================================

import streamlit as st
from core.config import FEATURES, SECT_CATEGORIES
from core.config import get_supabase_client
from modules.sect import get_user_sect  # 需要从 sect.py 导入

def show_main_page():
    """
    显示主城主界面
    包含侧边栏用户信息和导航菜单
    """
    st.set_page_config(page_title="寰宇系统 - 主城", layout="wide")
    
    # 检查用户是否登录
    if 'user' not in st.session_state or st.session_state.user is None:
        st.session_state.page = 'login'
        st.rerun()
    
    user = st.session_state.user
    
    # ==============================
    # 侧边栏：用户信息和导航
    # ==============================
    with st.sidebar:
        st.title(f"👤 {user.username}")
        st.write(f"境界：{user.realm} {user.stage}层")
        st.write(f"灵石：{user.spirit_stones:,} 💎")
        st.write(f"生命：{user.hp} ❤️")
        st.write(f"攻击：{user.attack} ⚔️")
        st.write(f"防御：{user.defense} 🛡️")
        
        # 显示宗门信息
        current_sect = get_user_sect(user.id)
        if current_sect:
            st.write(f"宗门：{current_sect['sect_name']}")
        else:
            st.write("宗门：散修")
        
        st.markdown("---")
        st.subheader("🧭 导航")
        
        # 构建导航菜单
        nav_options = ["🏠 主城", "🏪 藏宝阁", "🎒 背包"]
        if FEATURES["sect"]:
            nav_options.append("🏯 宗门")
        if FEATURES["alchemy"]:
            nav_options.append("🧪 炼丹房")
        if FEATURES["forge"]:
            nav_options.append("🔨 炼器坊")
        if FEATURES["array"]:
            nav_options.append("🌀 阵法堂")
        if FEATURES["dungeon"]:
            nav_options.append("🕳️ 秘境")
        
        # 管理员入口
        if user.is_admin:
            nav_options.append("🛠️ 管理中心")
        if user.username == "轩璃":
            nav_options.append("👑 轩璃专属")
        
        # 导航选择器
        selected_nav = st.radio("选择功能", nav_options, key="main_nav_radio")
        
        if st.button("🚪 退出登录", key="logout_btn"):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # ==============================
    # 主内容区：根据选择显示不同页面
    # ==============================
    _handle_navigation(selected_nav)

def _handle_navigation(selected_nav: str):
    """处理导航选择（内部函数）"""
    if selected_nav == "🏠 主城":
        _render_main_city_content()
    elif selected_nav == "🏪 藏宝阁":
        st.session_state.page = 'shop'
        st.rerun()
    elif selected_nav == "🎒 背包":
        st.session_state.page = 'backpack'
        st.rerun()
    elif selected_nav == "🏯 宗门":
        st.session_state.page = 'sect'
        st.rerun()
    elif selected_nav == "🧪 炼丹房":
        st.session_state.page = 'alchemy'
        st.rerun()
    elif selected_nav == "🔨 炼器坊":
        st.session_state.page = 'forge'
        st.rerun()
    elif selected_nav == "🌀 阵法堂":
        st.session_state.page = 'array'
        st.rerun()
    elif selected_nav == "🕳️ 秘境":
        st.session_state.page = 'dungeon'
        st.rerun()
    elif selected_nav == "🛠️ 管理中心":
        st.session_state.page = 'admin'
        st.rerun()
    elif selected_nav == "👑 轩璃专属":
        st.session_state.page = 'xuanli_admin'
        st.rerun()

def _render_main_city_content():
    """渲染主城内容（内部函数）"""
    st.title("🌌 寰宇主城")
    st.markdown("""
    欢迎来到寰宇主城！这里是修真世界的中心。
    修行之路，始于足下。祝你早日证道成圣！
    """)
    
    # 功能快捷按钮
    cols = st.columns(2)
    buttons = [
        ("🏪 藏宝阁", "shop"),
        ("🏯 宗门", "sect"),
        ("🧪 炼丹房", "alchemy"),
        ("🔨 炼器坊", "forge"),
        ("🌀 阵法堂", "array"),
        ("🕳️ 秘境", "dungeon")
    ]
    
    for i, (label, page) in enumerate(buttons):
        with cols[i % 2]:
            if st.button(label, key=f"main_btn_{page}"):
                st.session_state.page = page
                st.rerun()