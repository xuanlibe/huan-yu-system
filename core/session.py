# ==================================================
# 会话管理模块
# 功能：初始化和管理 Streamlit 的 session_state
# ==================================================

import streamlit as st
from .config import CURRENT_VERSION

def initialize_session_state():
    """
    初始化所有必要的 Session 状态变量
    在应用启动时调用一次，确保所有页面都能访问这些变量
    """
    # 定义默认值
    defaults = {
        'page': 'login',              # 当前页面
        'user': None,                 # 当前用户对象
        'system_version': CURRENT_VERSION,  # 系统版本
        'last_error': None,           # 最后错误信息
        'show_confirm_discard': None, # 背包丢弃确认状态
    }
    
    # 遍历并初始化不存在的变量
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # 版本更新检查：如果版本变化，清空状态并重启
    if st.session_state.system_version != CURRENT_VERSION:
        st.session_state.clear()
        st.session_state.system_version = CURRENT_VERSION
        st.rerun()

def clear_user_session():
    """清除用户相关状态（用于退出登录）"""
    keys_to_clear = ['user', 'page']
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None if key == 'user' else 'login'