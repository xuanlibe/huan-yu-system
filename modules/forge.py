# ==================================================
# 炼器坊模块
# 功能：查看图纸、打造装备、材料管理
# ==================================================

import streamlit as st
from core.config import FEATURES, get_supabase_client
from core.database import get_user_sect
from core.errors import safe_page_load
import random

def show_forge_page():
    """
    显示炼器坊页面
    包含图纸列表和打造功能
    """
    if not FEATURES.get("forge", True):
        st.warning("炼器坊暂未开放")
        if st.button("返回主城"):
            st.session_state.page = 'main'
            st.rerun()
        return
    
    st.set_page_config(page_title="寰宇系统 - 炼器坊", layout="wide")
    st.title("🔨 炼器坊")
    
    if st.button("⬅️ 返回主城", key="forge_back_btn"):
        st.session_state.page = 'main'
        st.rerun()
    
    with safe_page_load("炼器坊"):
        _render_forge_content()

def _render_forge_content():
    """渲染炼器坊内容（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 获取所有图纸
    blueprints = supabase.table("forge_blueprints").select("""
        *,
        result_item:items!result_item_id(name, category, effect, attack_bonus),
        material_1:items!material_1_id(name, category),
        material_2:items!material_2_id(name, category)
    """).execute()
    
    blueprints_data = blueprints.data if blueprints else []
    
    if not blueprints_data:
        st.info("暂无炼器图纸")
        return
    
    # 按品级分组显示
    st.subheader("📐 图纸列表")
    
    for bp in blueprints_data:
        _render_forge_blueprint(bp, user_id)

def _render_forge_blueprint(bp, user_id: int):
    """渲染单个图纸卡片（内部函数）"""
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"⚔️ {bp['name']}")
            
            # 显示产物
            result_item = bp.get("result_item", {})
            st.write(f"**产出**: {result_item.get('name', '未知')} x{bp.get('result_qty', 1)}")
            
            # 显示攻击加成
            attack_bonus = result_item.get("attack_bonus", 0)
            if attack_bonus > 0:
                st.write(f"**攻击加成**: +{attack_bonus} ⚔️")
            
            # 显示材料需求
            st.write("**材料需求:**")
            mat1 = bp.get("material_1", {})
            mat1_qty = bp.get("material_1_qty", 0)
            st.write(f"  • {mat1.get('name', '未知')} x{mat1_qty}")
            
            mat2 = bp.get("material_2", {})
            if mat2:
                mat2_qty = bp.get("material_2_qty", 0)
                st.write(f"  • {mat2.get('name', '未知')} x{mat2_qty}")
            
            st.write(f"**消耗灵石**: {bp.get('spirit_stone_cost', 0):,}")
            st.write(f"**成功率**: {int(bp.get('success_rate', 0.8) * 100)}%")
        
        with col2:
            # 检查材料是否足够
            has_materials = _check_forge_materials(user_id, bp)
            
            btn_label = "⚒️ 开始打造" if has_materials else "❌ 材料不足"
            btn_disabled = not has_materials
            
            if st.button(btn_label, key=f"forge_craft_{bp['id']}", disabled=btn_disabled):
                _handle_craft_forge(bp)

def _check_forge_materials(user_id: int, bp) -> bool:
    """检查用户是否有足够材料（内部函数）"""
    supabase = get_supabase_client()
    
    # 获取用户背包
    inventory = supabase.table("user_inventory")\
        .select("item_id, quantity")\
        .eq("user_id", user_id)\
        .execute()
    
    inv_dict = {item["item_id"]: item["quantity"] for item in (inventory.data or [])}
    
    # 检查材料 1
    mat1_id = bp.get("material_1_id")
    mat1_qty = bp.get("material_1_qty", 0)
    if inv_dict.get(mat1_id, 0) < mat1_qty:
        return False
    
    # 检查材料 2
    mat2_id = bp.get("material_2_id")
    mat2_qty = bp.get("material_2_qty", 0)
    if mat2_id and inv_dict.get(mat2_id, 0) < mat2_qty:
        return False
    
    # 检查灵石
    user = st.session_state.user
    if user.spirit_stones < bp.get("spirit_stone_cost", 0):
        return False
    
    return True

def _handle_craft_forge(bp):
    """处理打造逻辑（内部函数）"""
    supabase = get_supabase_client()
    user_id = st.session_state.user.id
    
    # 扣除材料
    mat1_id = bp.get("material_1_id")
    mat1_qty = bp.get("material_1_qty", 0)
    _remove_item(user_id, mat1_id, mat1_qty)
    
    mat2_id = bp.get("material_2_id")
    mat2_qty = bp.get("material_2_qty", 0)
    if mat2_id:
        _remove_item(user_id, mat2_id, mat2_qty)
    
    # 扣除灵石
    cost = bp.get("spirit_stone_cost", 0)
    supabase.rpc("deduct_spirit_stones", {"uid": user_id, "amount": cost}).execute()
    
    # 判定成功率
    success_rate = bp.get("success_rate", 0.8)
    success = random.random() <= success_rate
    
    if success:
        # 添加产物
        result_id = bp.get("result_item_id")
        result_qty = bp.get("result_qty", 1)
        _add_item(user_id, result_id, result_qty)
        
        result_item = bp.get("result_item", {})
        st.toast(f"✅ 打造成功！获得 {result_item.get('name', '装备')} x{result_qty}", icon="✅")
    else:
        st.toast(f"❌ 打造失败！材料已消耗", icon="❌")
    
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