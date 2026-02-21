# 在个人信息下方添加
st.divider()
st.subheader("📖 我的功法")

# 从数据库获取用户已学习的功法
supabase = get_supabase_client()
user_arts = supabase.table("user_arts")\
    .select("*, items(name, description)")\
    .eq("user_id", st.session_state.user.id)\
    .execute()

if user_arts.data:
    for art in user_arts.data:
        with st.expander(art['items']['name']):
            st.write(art['items'].get('description', '（无）'))
else:
    st.info("你还没有学习任何功法")

# 预留自定义功法区域（暂不开放）
st.subheader("✨ 自定义功法（开发中）")
st.info("此功能将在后续版本开放")