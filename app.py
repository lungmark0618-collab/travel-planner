import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import sys
import os
import requests
import importlib
import uuid

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

# ─── 常數設定 ──────────────────────────────────────────────────
CATEGORIES = ["食物", "交通", "住宿", "購物", "門票", "其他"]
CATEGORY_COLORS = {
    "交通": "#63b3ed", "食物": "#f6ad55", "住宿": "#48bb78", 
    "購物": "#ed64a1", "門票": "#9f7aea", "其他": "#a0aec0"
}

# ─── CSS 樣式 ──────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #0e1117;
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
}

/* 卡片式表單 */
[data-testid="stVerticalBlock"] > div:has(div.stForm) {
    background: #1a2035;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #2d3748;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

[data-testid="stFormSubmitButtonInstructions"] { display: none !important; }

.timeline-item {
    background: linear-gradient(145deg, #232a3d, #1a2035);
    border: 1px solid #2d3748;
    border-left: 4px solid #4299e1;
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 12px;
}

.expense-card {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
}

.mobile-nav {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: #1a2035; display: flex; justify-content: space-around;
    padding: 12px 0; border-top: 1px solid #2d3748; z-index: 1000;
}

@media (max-width: 767px) {
    .stApp { padding-bottom: 90px; }
    section[data-testid="stSidebar"] { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── Session State 初始化 ─────────────────────────────────────
if "user" not in st.session_state: st.session_state.user = None
if "trip_code" not in st.session_state: st.session_state.trip_code = None
if "auth_page" not in st.session_state: st.session_state.auth_page = "login"

# ─── 帳號層：登入/註冊 ───────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("<div style='text-align:center; padding: 40px 0;'><h1 style='font-size:3rem; margin:0;'>✈️ 旅伴助手</h1><p style='color:#94a3b8;'>你的專屬旅遊管家</p></div>", unsafe_allow_html=True)
    
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
                else: st.error(f"❌ {msg}")
        if st.button("還沒有帳號？點此註冊", use_container_width=True):
            st.session_state.auth_page = "register"; st.rerun()
    else:
        with st.form("register_form"):
            st.markdown("### 📝 註冊新帳號")
            u = st.text_input("使用者名稱")
            st.markdown("<p style='color:#f6e05e; font-size:0.8rem; margin-top:-15px;'>⚠️ 提醒：使用者名稱設定後即無法修改，且不可與他人重複。</p>", unsafe_allow_html=True)
            p = st.text_input("密碼", type="password")
            if st.form_submit_button("確認完成註冊", use_container_width=True):
                if len(u) < 2 or len(p) < 4: st.warning("請填寫正確資訊")
                else:
                    success, msg = dm.register_user(u, p)
                    if success:
                        st.success(f"✅ 註冊成功！你的專屬序號是：{msg}")
                        st.session_state.auth_page = "login"
                    else:
                        # 這是重點：用強烈的紅字顯示重複錯誤
                        st.markdown(f"<div style='background-color:#fed7d7; color:#c53030; padding:10px; border-radius:5px; border:1px solid #fc8181; margin-bottom:10px; font-weight:700;'>❌ 註冊失敗：{msg}</div>", unsafe_allow_html=True)
        if st.button("返回登入", use_container_width=True):
            st.session_state.auth_page = "login"; st.rerun()
    st.stop()

# ─── 儀表板層 ──────────────────────────────────────────────────
users_db = dm._load_json(dm.USERS_FILE, {})
user_info = users_db.get(st.session_state.user)

if st.session_state.trip_code is None:
    st.markdown(f"<h1 style='margin-bottom:0;'>你好，{st.session_state.user} 👋</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#63b3ed; font-weight:700; font-size:1.2rem;'>旅伴序號：{user_info['user_id']}</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 建立新旅程", use_container_width=True, type="primary"):
            st.session_state.dash_mode = "create"; st.rerun()
    with col2:
        if st.button("👥 加入現有旅程", use_container_width=True):
            st.session_state.dash_mode = "join"; st.rerun()

    mode = st.session_state.get("dash_mode", "list")
    
    if mode == "create":
        with st.form("create_trip_form"):
            st.markdown("### 🌟 建立全新旅程")
            c_name = st.text_input("旅程名稱")
            c_secret = st.text_input("旅程暗號")
            c_privacy = st.radio("隱私設定", ["🌐 公開", "🔒 私人"], horizontal=True)
            c_pwd = st.text_input("存取密碼 (選填)", type="password")
            if st.form_submit_button("確定建立", use_container_width=True):
                success, msg = dm.create_trip(st.session_state.user, c_secret, c_name, "公開" in c_privacy, c_pwd if c_pwd else None)
                if success: st.session_state.dash_mode = "list"; st.rerun()
                else: st.error(msg)
            if st.form_submit_button("取消", use_container_width=True):
                st.session_state.dash_mode = "list"; st.rerun()
    
    elif mode == "join":
        with st.form("join_form"):
            st.markdown("### 👥 加入旅程")
            j_secret = st.text_input("輸入暗號")
            if st.form_submit_button("搜尋", use_container_width=True):
                info = dm.get_trip_info(j_secret)
                if info: st.session_state.pending_join = j_secret
                else: st.error("找不到此旅程")
        if "pending_join" in st.session_state:
            s = st.session_state.pending_join
            info = dm.get_trip_info(s)
            st.info(f"📍 找到：{info['trip_name']} (由 {info['owner_username']} 建立)")
            with st.form("join_confirm"):
                j_pwd = st.text_input("密碼", type="password") if info['password'] else ""
                if st.form_submit_button("確認加入", use_container_width=True):
                    success, msg = dm.join_trip(st.session_state.user, s, j_pwd)
                    if success: del st.session_state.pending_join; st.session_state.dash_mode = "list"; st.rerun()
                    else: st.error(msg)

    else:
        st.markdown("---")
        st.markdown("### 📂 我的旅程清單")
        trips = [(s, "👑") for s in user_info.get("my_trips", [])] + [(s, "👥") for s in user_info.get("joined_trips", [])]
        for s, tag in trips:
            info = dm.get_trip_info(s)
            if info:
                with st.container(border=True):
                    c1, c2 = st.columns([8, 2])
                    with c1: st.markdown(f"**{tag} {info['trip_name']}**\n<small>{s}</small>", unsafe_allow_html=True)
                    with c2:
                        if st.button("進入 ➡️", key=f"go_{s}", use_container_width=True):
                            st.session_state.trip_code = s; st.rerun()

    st.markdown("---")
    with st.expander("👤 帳號設定"):
        new_p = st.text_input("修改登入密碼", type="password")
        if st.button("💾 確定修改密碼", use_container_width=True):
            if len(new_p) >= 4:
                success, msg = dm.update_user_password(st.session_state.user, new_p)
                if success: st.success(msg)
                else: st.error(msg)
    if st.button("🚪 登出帳號", use_container_width=True, type="secondary"):
        st.session_state.user = None; st.rerun()
    st.stop()

# ─── 旅程內部層 ────────────────────────────────────────────────
trip_code = st.session_state.trip_code
data = dm.load_data(trip_code)
trip_meta = dm.get_trip_info(trip_code)

cols = st.columns(4)
for idx, (icon, label, key) in enumerate([("🏠","總覽","🏠 總覽看板"), ("📅","行程","📅 行程規劃"), ("💰","記帳","💰 記帳本"), ("⚙️","設定","⚙️ 旅程設定")]):
    if cols[idx].button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key; st.rerun()

page = st.session_state.get("page", "🏠 總覽看板")
st.markdown(f"### {trip_meta['trip_name'] if trip_meta else data['trip_name']} | 🔑 {trip_code}")
st.markdown("---")

if page == "🏠 總覽看板":
    budget = data["total_budget_twd"]
    spent = sum(e["amount_twd"] for e in data["expenses"])
    if budget == 0:
        st.warning("⚠️ 尚未設定預算！")
        with st.expander("🚀 快速設定"):
            new_b = st.number_input("預算", min_value=0)
            if st.button("儲存"): data["total_budget_twd"] = new_b; dm.save_data(data, trip_code); st.rerun()
    else:
        spent_pct = min(spent / budget, 1.0)
        color = "#f6ad55" if spent_pct < 0.8 else "#f56565"
        st.markdown(f'<div style="background:#2d3748;height:24px;border-radius:10px;"><div style="background:{color};width:{spent_pct*100}%;height:100%;"></div></div>', unsafe_allow_html=True)
        st.markdown(f"已花 NT${spent:,.0f} / 預算 NT${budget:,.0f}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        by_cat = dm.get_expenses_by_category(data)
        if by_cat:
            fig = go.Figure(go.Pie(labels=list(by_cat.keys()), values=list(by_cat.values()), hole=.5))
            fig.update_layout(height=200, margin=dict(t=0,b=0,l=0,r=0), showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        by_date = dm.get_expenses_by_date(data)
        if by_date:
            fig = px.bar(x=list(by_date.keys()), y=list(by_date.values()))
            fig.update_layout(height=200, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

elif page == "📅 行程規劃":
    with st.form("add_it"):
        d = st.date_input("日期")
        l = st.text_input("地點")
        a = st.text_input("活動")
        if st.form_submit_button("📌 加入", use_container_width=True):
            dm.add_itinerary_item(str(d), "12:00", l, a, "", trip_code); st.rerun()
    for item in data["itinerary"]:
        with st.container():
            st.markdown(f"<div class='timeline-item'><b>{item['date']}</b> {item['activity']} @{item['location']}</div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{item['id']}"): dm.delete_itinerary_item(item['id'], trip_code); st.rerun()

elif page == "💰 記帳本":
    with st.form("add_exp"):
        cat = st.selectbox("分類", CATEGORIES)
        cur = st.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"])
        amt = st.number_input("金額")
        if st.form_submit_button("💰 記錄", use_container_width=True):
            dm.add_expense(str(date.today()), cat, "", amt, cur, trip_code); st.rerun()
    for e in data["expenses"]:
        with st.container():
            st.markdown(f"<div class='expense-card'><b>{e['category']}</b> NT${e['amount_twd']:,.0f}</div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delexp_{e['id']}"): dm.delete_expense(e['id'], trip_code); st.rerun()

elif page == "⚙️ 旅程設定":
    # 這裡是最重要的修正點：使用 Placeholder
    msg_area = st.empty()
    
    with st.form("set_meta"):
        st.markdown("#### ⚙️ 基本設定")
        n = st.text_input("名稱", data["trip_name"])
        b = st.number_input("預算", value=float(data["total_budget_twd"]))
        if st.form_submit_button("💾 儲存"):
            data["trip_name"] = n; data["total_budget_twd"] = b
            dm.save_data(data, trip_code); st.rerun()

    # 匯率按鈕單獨放在外面
    if st.button("🌐 從網路更新即時匯率", use_container_width=True):
        try:
            resp = requests.get("https://open.er-api.com/v6/latest/TWD", timeout=5)
            if resp.status_code == 200:
                fx = resp.json().get("rates", {})
                r = data["exchange_rates"]
                for cur in ["JPY","USD","EUR","KRW"]:
                    if cur in fx: r[cur] = round(1/fx[cur], 5)
                dm.save_data(data, trip_code)
                msg_area.success("✅ 已取得最新市場匯率！")
            else:
                msg_area.error("❌ 匯率伺服器異常")
        except:
            msg_area.error("❌ 無法連線至伺服器")

    if st.button("🚪 退出此旅程", use_container_width=True, type="secondary"):
        st.session_state.trip_code = None; st.rerun()
