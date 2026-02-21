# ==================================================#
# 寰宇系统 - 主入口文件
# 作者：轩璃
# 说明：这是应用的唯一入口，负责初始化和路由分发
# ==================================================#

import streamlit as st

# ==============================#
# 导入核心模块
# ==============================#
from core.session import initialize_session_state
from core.config import FEATURES

# ==============================#
# 导入所有页面模块
# ==============================#
from modules.login import show_login_page
from modules.main_city import show_main_page
from modules.backpack import show_backpack_page
from modules.sect import show_sect_page
from modules.alchemy import show_alchemy_page
from modules.forge import show_forge_page
from modules.array import show_array_page
from modules.dungeon import show_dungeon_page
# 注意：藏宝阁使用新版模块结构
from modules.shop.shop_main import show_shop_page  # ← 关键修改：指向 shop/shop_main.py

# === 新增：上架页面 ===
from modules.shop.list_item import show_list_item_page  # ← 新增这行！

# ==============================#
# 导入管理员模块（从 admin/ 目录）
# ==============================#
from admin.admin_center import show_admin_center  # ← 管理员中心
from admin.item_manager import show_item_manager  # ← 物品管理器

# ==============================#
# 页面路由映射表
# ==============================#
PAGE_MAP = {
    'login': show_login_page,
    'main': show_main_page,
    'shop': show_shop_page,
    'backpack': show_backpack_page,
    'sect': show_sect_page,
    'alchemy': show_alchemy_page,
    'forge': show_forge_page,
    'array': show_array_page,
    'dungeon': show_dungeon_page,
    'admin_center': show_admin_center,  # 管理员中心
    'item_manager': show_item_manager,  # 物品管理器
    'list_item': show_list_item_page,   # ← 新增这行！
}

def main():
    initialize_session_state()
    current_page = st.session_state.get('page', 'login')

    # 🔒 安全检查：仅检查存在的管理员页面
    if current_page in ['admin_center', 'item_manager']:
        if 'user' not in st.session_state or st.session_state.user is None:
            st.session_state.page = 'login'
            st.rerun()
        user = st.session_state.user
        if current_page == 'admin_center' and not user.is_admin:
            st.error("❌ 无权访问管理员中心")
            st.session_state.page = 'main'
            st.rerun()
        elif current_page == 'item_manager' and not user.is_admin:
            st.error("❌ 无权访问物品管理器")
            st.session_state.page = 'main'
            st.rerun()

    # 路由分发
    if current_page in PAGE_MAP:
        PAGE_MAP[current_page]()
    else:
        st.session_state.page = 'login'
        show_login_page()

# ==============================#
# 应用入口
# ==============================#
if __name__ == "__main__":
    st.set_page_config(page_title="寰宇系统", layout="wide")
    main()