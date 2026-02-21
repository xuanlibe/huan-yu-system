# 在个人信息下方添加功法模块
st.divider()
st.subheader("📖 我的功法")

# 从数据库获取用户已学习的功法（示例，实际需要 user_arts 表）
supabase = get_supabase_client()
# 这里先显示所有系统功法作为示例
user_arts = supabase.table("items")\
    .select('"name", "effect"')\
    .eq('"is_system"', True)\
    .eq('"category"', '黄阶功法')\
    .execute()

if user_arts.data:
    for art in user_arts.data:
        with st.expander(art['name']):
            description = art.get('effect') or "（无）"
            st.write(description)
else:
    st.info("你还没有学习任何功法")

# 预留自定义功法区域（暂不开放）
st.subheader("✨ 自定义功法（开发中）")
st.info("此功能将在后续版本开放")