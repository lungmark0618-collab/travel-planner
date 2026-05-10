import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import sys
import os
import requests
import importlib

# 確保載入最新的 data_manager
sys.path.insert(0, os.path.dirname(__file__))
import data_manager as dm
importlib.reload(dm)

# ─── 頁面設定 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="✈️ 旅伴助手",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── CSS 樣式 ──────────────────────────────────────────────────
st.markdown("""
<style>
/* 隱藏預設元件 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 全域背景與字體 */
.stApp {
    background-color: #0e1117;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 卡片與容器 */
[data-testid="stVerticalBlock"] > div:has(div.stForm) {
    background: #1a2035;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #2d3748;
}

/* 隱藏表單提示 */
[data-testid="stFormSubmitButtonInstructions"] {
    display: none !important;
}

/* 自訂標題 */
.main-header {
    text-align: center;
    padding: 30px 0;
}
.main-header h1 {
    font-size: 2.5rem;
    background: linear-gradient(135deg, #63b3ed 0%, #4299e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
}

/* 儀表板卡片 */
.trip-card {
    background: linear-gradient(145deg, #1e2538, #1a2035);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: transform 0.2s;
}
.trip-card:hover {
    transform: translateY(-2px);
    border-color: #4299e1;
}

/* 底部導覽 (手機版) */
.mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #1a2035;
    display: flex;
    justify-content: space-around;
    padding: 10px 0;
    border-top: 1px solid #2d3748;
    z-index: 1000;
}

@media (max-width: 767px) {
    .stApp { padding-bottom: 70px; }
    section[data-testid="stSidebar"] { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── 初始化 Session State ──────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "trip_code" not in st.session_state:
    st.session_state.trip_code = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

# ─── 帳號層：登入/註冊 ───────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("<div class='main-header'><h1>✈️ 旅伴助手</h1><p style='color:#94a3b8;'>專屬你的私人旅遊規劃管家</p></div>", unsafe_allow_html=True)
    
    if st.session_state.auth_page == "login":
        with st.form("login_form"):
            st.markdown("### 🔑 登入帳號")
            u = st.text_input("使用者名稱")
            p = st.text_input("密碼", type="password")
            if st.form_submit_button("登入", use_container_width=True):
                user_data, msg = dm.login_user(u, p)
                if user_data:
                    st.session_state.user = u
                    st.rerun()
                else:
                    st.error(msg)
        if st.button("還沒有帳號？點此註冊", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()
            
    else:
        with st.form("register_form"):
            st.markdown("### 📝 註冊新帳號")
            u = st.text_input("使用者名稱 (建議用英文/數字)")
            p = st.text_input("密碼", type="password")
            if st.form_submit_button("完成註冊", use_container_width=True):
                if len(u) < 2 or len(p) < 4:
                    st.warning("名稱至少2字，密碼至少4字")
                else:
                    success, msg = dm.register_user(u, p)
                    if success:
                        st.success(f"註冊成功！你的專屬序號是：{msg}")
                        st.session_state.auth_page = "login"
                        # 不自動 rerun 讓使用者看清楚序號
                    else:
                        st.error(msg)
        if st.button("已有帳號？返回登入", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()
    st.stop()

# ─── 儀表板層：選擇/建立旅程 ──────────────────────────────────────
# 取得目前使用者完整資訊
user_info, _ = dm.login_user(st.session_state.user, "") # 這裡 login_user 僅內部調用不重驗密碼
# (注意：正式開發應優化資料取得，此處簡單示範)
# 修正：直接讀取 JSON
users_db = dm._load_json(dm.USERS_FILE, {})
user_info = users_db.get(st.session_state.user)

if st.session_state.trip_code is None:
    st.markdown(f"""
    <div style='padding:20px 0;'>
        <h2 style='margin-bottom:0;'>你好，{st.session_state.user} 👋</h2>
        <p style='color:#63b3ed; font-weight:700;'>旅伴序號：{user_info['user_id']}</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🆕 建立新旅程", use_container_width=True, type="primary"):
            st.session_state.dash_mode = "create"
            st.rerun()
    with col_r:
        if st.button("👥 加入現有旅程", use_container_width=True):
            st.session_state.dash_mode = "join"
            st.rerun()

    # 處理建立/加入模式
    mode = st.session_state.get("dash_mode", "list")
    
    if mode == "create":
        with st.form("create_trip_form"):
            st.markdown("### 🌟 建立全新旅程")
            c_name = st.text_input("旅程名稱", placeholder="例如：2024 東京賞櫻趣")
            c_secret = st.text_input("旅程暗號 (分享給朋友用)", placeholder="例如：tokyo_sakura")
            c_privacy = st.radio("隱私設定", ["🌐 公開 (可搜尋並加入)", "🔒 私人 (只有我能看到)"], horizontal=True)
            c_pwd = st.text_input("存取密碼 (選填，公開模式建議設定)", type="password", help="別人加入時需輸入此密碼")
            
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.form_submit_button("💾 確定建立", use_container_width=True):
                    is_pub = "公開" in c_privacy
                    success, msg = dm.create_trip(st.session_state.user, c_secret, c_name, is_pub, c_pwd if c_pwd else None)
                    if success:
                        st.success(msg)
                        st.session_state.dash_mode = "list"
                        st.rerun()
                    else:
                        st.error(msg)
            with cc2:
                if st.form_submit_button("取消", use_container_width=True):
                    st.session_state.dash_mode = "list"
                    st.rerun()
    
    elif mode == "join":
        with st.form("join_trip_form"):
            st.markdown("### 👥 加入旅程")
            j_secret = st.text_input("請輸入朋友給你的「旅程暗號」")
            j_submit = st.form_submit_button("🔍 搜尋旅程", use_container_width=True)
            if j_submit:
                info = dm.get_trip_info(j_secret)
                if info:
                    st.session_state.pending_join = j_secret
                else:
                    st.error("找不到此旅程")
        
        if "pending_join" in st.session_state:
            s = st.session_state.pending_join
            info = dm.get_trip_info(s)
            st.info(f"📍 找到旅程：**{info['trip_name']}**")
            st.markdown(f"<p style='color:#94a3b8;'>由旅伴 **{info['owner_username']}** ({info['owner_id']}) 建立</p>", unsafe_allow_html=True)
            
            with st.form("join_confirm_form"):
                j_pwd = st.text_input("請輸入此旅程的存取密碼", type="password") if info['password'] else ""
                if st.form_submit_button("確認加入", use_container_width=True):
                    success, msg = dm.join_trip(st.session_state.user, s, j_pwd)
                    if success:
                        st.success(msg)
                        del st.session_state.pending_join
                        st.session_state.dash_mode = "list"
                        st.rerun()
                    else:
                        st.error(msg)
            if st.button("返回"):
                del st.session_state.pending_join
                st.rerun()
    
    else:
        # 顯示旅程清單
        st.markdown("---")
        st.markdown("### 📂 我的旅程清單")
        
        my_trips = user_info.get("my_trips", [])
        joined_trips = user_info.get("joined_trips", [])
        
        all_display = []
        for s in my_trips: all_display.append((s, "👑 我建立的"))
        for s in joined_trips: all_display.append((s, "👥 我加入的"))
        
        if not all_display:
            st.info("目前還沒有任何旅程，點擊上方按鈕建立一個吧！")
        else:
            for secret, tag in all_display:
                info = dm.get_trip_info(secret)
                if info:
                    with st.container(border=True):
                        c1, c2 = st.columns([8, 2])
                        with c1:
                            st.markdown(f"**{info['trip_name']}**")
                            st.caption(f"{tag} · 暗號: {secret}")
                        with c2:
                            if st.button("進入 ➡️", key=f"go_{secret}", use_container_width=True):
                                st.session_state.trip_code = secret
                                st.rerun()

    if st.button("🚪 登出帳號", use_container_width=True, type="secondary"):
        st.session_state.user = None
        st.session_state.trip_code = None
        st.rerun()
    st.stop()

# ─── 旅程內部層：4 個分頁功能 ──────────────────────────────────────
trip_code = st.session_state.trip_code
data = dm.load_data(trip_code)
trip_info = dm.get_trip_info(trip_code)

# 導覽項目
NAV_ITEMS = [
    ("🏠", "總覽", "🏠 總覽看板"),
    ("📅", "行程", "📅 行程規劃"),
    ("💰", "記帳", "💰 記帳本"),
    ("⚙️", "設定", "⚙️ 旅程設定")
]

# 手機版底部導覽
st.markdown('<div class="mobile-nav">', unsafe_allow_html=True)
cols = st.columns(len(NAV_ITEMS))
for idx, (icon, label, key) in enumerate(NAV_ITEMS):
    if cols[idx].button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

page = st.session_state.get("page", "🏠 總覽看板")

# 頁面標題列
t_col1, t_col2 = st.columns([8, 2])
with t_col1:
    st.markdown(f"### {trip_info['trip_name'] if trip_info else '我的旅程'}")
    st.caption(f"🔑 暗號: {trip_code} | 👤 持有人: {trip_info['owner_username'] if trip_info else 'Unknown'}")
with t_col2:
    if st.button("🚪 退出", use_container_width=True):
        st.session_state.trip_code = None
        st.rerun()

st.markdown("---")

# 這裡插入原本的四個頁面邏輯 (略，因為 app.py 太長，我會用 patch 的方式把原本的功能接回來)
# 為了讓程式能動，我先補上原本的 總覽 邏輯，其餘邏輯我會分次補齊

if page == "🏠 總覽看板":
    # ── 預算進度條 ──
    total_budget = data["total_budget_twd"]
    total_spent = sum(e["amount_twd"] for e in data["expenses"])
    remaining = total_budget - total_spent
    spent_pct = min(total_spent / total_budget, 1.0) if total_budget > 0 else 0

    st.markdown(f"#### 💰 預算執行率：{spent_pct*100:.1f}%")
    bar_color = "#f6ad55" if spent_pct < 0.8 else "#f56565"
    st.markdown(f'''
    <div style="background:#2d3748; border-radius:10px; height:24px; width:100%; overflow:hidden; margin-bottom:10px;">
        <div style="background:{bar_color}; width:{spent_pct*100}%; height:100%; transition: width 0.5s;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; color:#94a3b8; font-size:0.9rem;">
        <span>已花 NT${total_spent:,.0f}</span>
        <span>預算 NT${total_budget:,.0f}</span>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    
    # ── 圖表分析 ──
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("#### 📊 支出分類")
        by_cat = dm.get_expenses_by_category(data)
        if by_cat:
            CATEGORY_COLORS = {"交通": "#63b3ed", "食物": "#f6ad55", "住宿": "#48bb78", "購物": "#ed64a1", "門票": "#9f7aea", "其他": "#a0aec0"}
            cat_names = list(by_cat.keys())
            cat_vals  = list(by_cat.values())
            fig_pie = go.Figure(go.Pie(labels=cat_names, values=cat_vals, hole=0.5))
            fig_pie.update_layout(height=250, showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.caption("尚無資料")

    with col_chart2:
        st.markdown("#### 📅 每日趨勢")
        by_date = dm.get_expenses_by_date(data)
        if by_date:
            fig_bar = px.bar(x=list(by_date.keys()), y=list(by_date.values()))
            fig_bar.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.caption("尚無資料")

    # 最近行程
    if data["itinerary"]:
        st.markdown("#### 📍 即將到來的行程")
        for item in sorted(data["itinerary"], key=lambda x: x["date"]+x["time"])[:3]:
            st.info(f"{item['date']} {item['time']} - {item['activity']} (@{item['location']})")

elif page == "📅 行程規劃":
    st.info("行程規劃功能載入中...")
    # (此處應接續原本的行程規劃代碼)
elif page == "💰 記帳本":
    st.info("記帳本功能載入中...")
    # (此處應接續原本的記帳本代碼)
elif page == "⚙️ 旅程設定":
    st.info("旅程設定功能載入中...")
    # (此處應接續原本的設定代碼)
