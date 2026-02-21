# ==================================================
# 寰宇系统 - 主入口文件
# 作者：轩璃
# 说明：这是应用的唯一入口，负责初始化和路由分发
# ==================================================

import streamlit as st

# ==============================
# 导入核心模块
# ==============================
from core.session import initialize_session_state
from core.config import FEATURES

# ==============================
# 导入所有页面模块
# ==============================
from modules.login import show_login_page
from modules.main_city import show_main_page
from modules.shop import show_shop_page
from modules.backpack import show_backpack_page
from modules.sect import show_sect_page
from modules.alchemy import show_alchemy_page
from modules.forge import show_forge_page
from modules.array import show_array_page
from modules.dungeon import show_dungeon_page
from modules.admin import show_xuanli_admin_page

# ==============================
# 页面路由映射表
# ==============================
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
    'xuanli_admin': show_xuanli_admin_page,
}

def main():
    """
    主函数
    1. 初始化会话状态
    2. 根据当前页面路由到对应模块
    """
    # 初始化 Session State
    initialize_session_state()
    
    # 获取当前页面
    current_page = st.session_state.get('page', 'login')
    
    # 路由分发
    if current_page in PAGE_MAP:
        PAGE_MAP[current_page]()
    else:
        # 未知页面，重定向到登录页
        st.session_state.page = 'login'
        show_login_page()

# ==============================
# 应用入口
# ==============================
if __name__ == "__main__":
    st.set_page_config(page_title="寰宇系统", layout="wide")
    main()