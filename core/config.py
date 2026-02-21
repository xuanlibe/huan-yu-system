# ==================================================
# 核心配置模块
# 功能：管理全局常量、Supabase 连接、功能开关
# ==================================================

import streamlit as st
from supabase import create_client, Client

# ==============================
# 🛡️ 系统常量
# ==============================
MAIN_ADMIN_USERNAME = "轩璃"
MAIN_ADMIN_PASSWORD = "20050506"
CURRENT_VERSION = "2.1.0"

# 功能开关控制（可以在这里快速关闭某个功能）
FEATURES = {
    "login": True,
    "shop": True,
    "backpack": True,
    "sect": True,
    "alchemy": True,
    "forge": True,
    "array": True,
    "dungeon": True,
    "admin": True,
}

# 宗门分类
SECT_CATEGORIES = ["天罚监司", "冥界", "人", "妖", "魔", "散修"]

# ==============================
# 🔑 数据库连接管理
# ==============================

def get_supabase_client() -> Client:
    """
    获取 Supabase 客户端（单例模式）
    避免重复创建连接，提高性能
    """
    if 'supabase_client' not in st.session_state:
        # 从 secrets.toml 读取配置，如果没有则使用占位符
        url = st.secrets.get("SUPABASE_URL", "https://your-supabase-url.supabase.co")
        key = st.secrets.get("SUPABASE_ANON_KEY", "your-supabase-anon-key-here")
        
        try:
            st.session_state.supabase_client = create_client(url, key)
        except Exception as e:
            st.error(f"❌ 数据库连接失败：{str(e)}")
            st.stop()
    
    return st.session_state.supabase_client

# ==============================
# 💰 游戏数据常量
# ==============================

# 炼丹材料价格表（来自你的 PDF 文档）
ALCHEMY_MATERIAL_PRICES = {
    "聚气草": 250, "凝元石": 250, "筑基木": 350, "建魂花": 350,
    "金液草": 550, "凝丹果": 650, "育婴藤": 800, "温神叶": 1200,
    # ... (把你原来的所有材料价格都复制到这里)
    "鸿蒙灵液": 125000000,
}

# 炼器材料攻击加成表
FORGE_MATERIAL_BONUS = {
    "御灵铁": 0.1, "引灵玉": 0.1, "剑心髓": 0.4,
    # ... (把你原来的所有材料加成复制到这里)
    "古老强者神魂碎片": 0.5,
}