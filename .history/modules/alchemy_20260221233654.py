# ==================================================
# 炼丹房模块
# 功能：查看配方、炼制丹药、材料管理
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.database import get_user_sect
from core.errors import safe_page_load

def show_alchemy_page():
    """
    显示炼丹房页面
    包含配方列表和炼制功能
    """
    if not FEATURES.get("alchemy", True):
        st.warning("炼丹房暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 炼丹房", layout="wide")
    st.title("🧪 炼丹房")
    
    if st.button("⬅️ 返回主城", key="alchemy_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("炼丹房"):
        _render_alchemy_content()

def _render_alchemy_content():
    """渲染炼丹房内容（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取所有配方
    recipes = supabase.table("alchemy_recipes").select("""
        *,
        result_item:items!result_item_id(name, category, effect),
        material_1:items!material_1_id(name, category),
        material_2:items!material_2_id(name, category)
    """).execute()
    
    recipes_data = recipes.data if recipes else []
    
    if not recipes_data:
        st.info("暂无炼丹配方")
        return
    
    # 按品级分组显示
    st.subheader("📜 丹方列表")
    
    for recipe in recipes_data:
        _render_alchemy_recipe(recipe, user_id)

def _render_alchemy_recipe(recipe, user_id: int):
    """渲染单个配方卡片（内部函数）"""
    supabase = get_supabase_client()
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"🔮 {recipe['name']}")
            st.write(f"**品级**: {recipe.get('grade', '未知')}")
            
            # 显示产物
            result_item = recipe.get("result_item", {})
            st.write(f"**产出**: {result_item.get('name', '未知')} x{recipe.get('result_qty', 1)}")
            
            # 显示材料需求
            st.write("**材料需求:**")
            mat1 = recipe.get("material_1", {})
            mat1_qty = recipe.get("material_1_qty", 0)
            st.write(f"  • {mat1.get('name', '未知')} x{mat1_qty}")
            
            mat2 = recipe.get("material_2", {})
            if mat2:
                mat2_qty = recipe.get("material_2_qty", 0)
                st.write(f"  • {mat2.get('name', '未知')} x{mat2_qty}")
            
            st.write(f"**消耗灵石**: {recipe.get('spirit_stone_cost', 0):,}")
            st.write(f"**成功率**: {int(recipe.get('success_rate', 1.0) * 100)}%")
        
        with col2:
            # 检查材料是否足够
            has_materials = _check_materials(user_id, recipe)
            
            btn_label = "🔥 开始炼制" if has_materials else "❌ 材料不足"
            btn_disabled = not has_materials
            
            if st.button(btn_label, key=f"alchemy_craft_{recipe['id']}", disabled=btn_disabled):
                _handle_craft_alchemy(recipe)

def _check_materials(user_id: int, recipe) -> bool:
    """检查用户是否有足够材料（内部函数）"""
    supabase = get_supabase_client()
    
    # 获取用户背包
    inventory = supabase.table("user_inventory")\
        .select("item_id, quantity")\
        .eq("user_id", user_id)\
        .execute()
    
    inv_dict = {item["item_id"]: item["quantity"] for item in (inventory.data or [])}
    
    # 检查材料 1
    mat1_id = recipe.get("material_1_id")
    mat1_qty = recipe.get("material_1_qty", 0)
    if inv_dict.get(mat1_id, 0) < mat1_qty:
        return False
    
    # 检查材料 2
    mat2_id = recipe.get("material_2_id")
    mat2_qty = recipe.get("material_2_qty", 0)
    if mat2_id and inv_dict.get(mat2_id, 0) < mat2_qty:
        return False
    
    # 检查灵石
    user = st.session_state.user
    if user.spirit_stones < recipe.get("spirit_stone_cost", 0):
        return False
    
    return True

def _handle_craft_alchemy(recipe):
    """处理炼制逻辑（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 扣除材料
    mat1_id = recipe.get("material_1_id")
    mat1_qty = recipe.get("material_1_qty", 0)
    _remove_item(user_id, mat1_id, mat1_qty)
    
    mat2_id = recipe.get("material_2_id")
    mat2_qty = recipe.get("material_2_qty", 0)
    if mat2_id:
        _remove_item(user_id, mat2_id, mat2_qty)
    
    # 扣除灵石
    cost = recipe.get("spirit_stone_cost", 0)
    supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": cost}).execute()
    
    # 判定成功率
    import random
    success_rate = recipe.get("success_rate", 1.0)
    success = random.random() <= success_rate
    
    if success:
        # 添加产物
        result_id = recipe.get("result_item_id")
        result_qty = recipe.get("result_qty", 1)
        _add_item(user_id, result_id, result_qty)
        
        result_item = recipe.get("result_item", {})
        st.toast(f"✅ 炼制成功！获得 {result_item.get('name', '丹药')} x{result_qty}", icon="✅")
    else:
        st.toast(f"❌ 炼制失败！材料已消耗", icon="❌")
    
    st.rerun()

def _remove_item(user_id: int, item_id: int, qty: int):
    """从背包移除物品（内部函数）"""
    supabase = get_supabase_client()
    inv = supabase.table("user_inventory")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("item_id", item_id)\
        .execute()
    
    if inv.data:
        current_qty = inv.data[0]["quantity"]
        new_qty = current_qty - qty
        if new_qty <= 0:
            supabase.table("user_inventory").delete().eq("id", inv.data[0]["id"]).execute()
        else:
            supabase.table("user_inventory").update({"quantity": new_qty}).eq("id", inv.data[0]["id"]).execute()

def _add_item(user_id: int, item_id: int, qty: int):
    """添加物品到背包（内部函数）"""
    supabase = get_supabase_client()
    inv = supabase.table("user_inventory")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("item_id", item_id)\
        .execute()
    
    if inv.data:
        current_qty = inv.data[0]["quantity"]
        supabase.table("user_inventory").update({"quantity": current_qty + qty}).eq("id", inv.data[0]["id"]).execute()
    else:
        supabase.table("user_inventory").insert({
            "user_id": user_id,
            "item_id": item_id,
            "quantity": qty
        }).execute()