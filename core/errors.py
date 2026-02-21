# ==================================================
# 错误处理模块
# 功能：提供安全的页面加载上下文，隔离错误
# ==================================================

import streamlit as st
from contextlib import contextmanager
from datetime import datetime

@contextmanager
def safe_page_load(page_name: str):
    """
    安全加载页面的上下文管理器
    
    用法:
        with safe_page_load("背包"):
            # 这里的代码出错不会影响其他页面
            show_backpack_content()
    
    参数:
        page_name: 页面名称，用于错误提示
    """
    try:
        yield  # 执行被包裹的代码
    except Exception as e:
        # 显示友好的错误信息
        st.error(f"⚠️ **{page_name}** 模块发生错误")
        st.code(str(e)[:500])  # 显示部分错误详情
        st.info("💡 其他功能仍可正常使用，请尝试刷新或联系管理员")
        
        # 记录错误到 session
        st.session_state.last_error = {
            'page': page_name,
            'error': str(e),
            'time': datetime.now().isoformat()
        }
        
        # 提供返回按钮
        if st.button("🏠 返回主城"):
            st.session_state.page = 'main'
            st.rerun()

def log_error(message: str, error: Exception):
    """记录错误日志（可扩展为写入文件或数据库）"""
    print(f"[ERROR] {message}: {str(error)}")