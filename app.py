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
    "交通": "#63b3ed",
    "食物": "#f6ad55",
    "住宿": "#48bb78",
    "購物": "#ed64a1",
    "門票": "#9f7aea",
    "其他": "#a0aec0"
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

[data-testid="stVerticalBlock"] > div:has(div.stForm) {
    background: #1a2035;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #2d3748;
}

[data-testid="stFormSubmitButtonInstructions"] {
    display: none !important;
}

/* 底部導覽列 (手機版專屬) */
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

.timeline-item {
    background: #1e2538;
    border-left: 4px solid #4299e1;
    padding: 12px 16px;
    margin-bottom: 10px;
    border-radius: 0 8px 8px 0;
}

@media (max-width: 767px) {
    .stApp { padding-bottom: 80px; }
    section[data-testid="stSidebar"] { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── Session State 初始化 ─────────────────────────────────────
if "user" not in st.session_state: st.session_state.user = None
if "trip_code" not in st.session_state: st.session_state.trip_code = None
if "auth_page" not in st.session_state: st.session_state.auth_page = "login"
if "edit_item_id" not in st.session_state: st.session_state.edit_item_id = None
if "expense_from_item" not in st.session_state: st.session_state.expense_from_item = None
if "edit_expense_id" not in st.session_state: st.session_state.edit_expense_id = None

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
                else:
                    st.error(msg)
        if st.button("還沒有帳號？點此註冊", use_container_width=True):
            st.session_state.auth_page = "register"; st.rerun()
    else:
        with st.form("register_form"):
            st.markdown("### 📝 註冊新帳號")
            u = st.text_input("使用者名稱")
            p = st.text_input("密碼", type="password")
            if st.form_submit_button("完成註冊", use_container_width=True):
                if len(u) < 2 or len(p) < 4: st.warning("請填寫正確資訊")
                else:
                    success, msg = dm.register_user(u, p)
                    if success:
                        st.success(f"註冊成功！你的專屬序號是：{msg}")
                        st.session_state.auth_page = "login"
                    else: st.error(msg)
        if st.button("返回登入", use_container_width=True):
            st.session_state.auth_page = "login"; st.rerun()
    st.stop()

# ─── 儀表板層 ──────────────────────────────────────────────────
users_db = dm._load_json(dm.USERS_FILE, {})
user_info = users_db.get(st.session_state.user)

if st.session_state.trip_code is None:
    st.markdown(f"## 你好，{st.session_state.user} 👋")
    st.markdown(f"<p style='color:#63b3ed; font-weight:700;'>旅伴序號：{user_info['user_id']}</p>", unsafe_allow_html=True)

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
            c_name = st.text_input("旅程名稱", placeholder="例如：我的日本行")
            c_secret = st.text_input("旅程暗號 (分享用)", placeholder="請輸入暗號...")
            c_privacy = st.radio("隱私設定", ["🌐 公開 (可被搜尋)", "🔒 私人"], horizontal=True)
            c_pwd = st.text_input("存取密碼 (選填)", type="password")
            if st.form_submit_button("確定建立", use_container_width=True):
                success, msg = dm.create_trip(st.session_state.user, c_secret, c_name, "公開" in c_privacy, c_pwd if c_pwd else None)
                if success:
                    st.session_state.dash_mode = "list"; st.rerun()
                else: st.error(msg)
            if st.form_submit_button("取消", use_container_width=True):
                st.session_state.dash_mode = "list"; st.rerun()
    
    elif mode == "join":
        with st.form("join_form"):
            st.markdown("### 👥 加入旅程")
            j_secret = st.text_input("請輸入暗號")
            if st.form_submit_button("搜尋", use_container_width=True):
                info = dm.get_trip_info(j_secret)
                if info: st.session_state.pending_join = j_secret
                else: st.error("找不到此旅程")
        
        if "pending_join" in st.session_state:
            s = st.session_state.pending_join
            info = dm.get_trip_info(s)
            st.info(f"📍 找到旅程：**{info['trip_name']}** (由 {info['owner_username']} 建立)")
            with st.form("join_confirm"):
                j_pwd = st.text_input("密碼", type="password") if info['password'] else ""
                if st.form_submit_button("確認加入", use_container_width=True):
                    success, msg = dm.join_trip(st.session_state.user, s, j_pwd)
                    if success:
                        del st.session_state.pending_join; st.session_state.dash_mode = "list"; st.rerun()
                    else: st.error(msg)
            if st.button("返回"): del st.session_state.pending_join; st.rerun()
    
    else:
        st.markdown("---")
        st.markdown("### 📂 我的旅程清單")
        trips = [(s, "👑") for s in user_info.get("my_trips", [])] + [(s, "👥") for s in user_info.get("joined_trips", [])]
        if not trips: st.info("目前無旅程")
        for s, tag in trips:
            info = dm.get_trip_info(s)
            if info:
                with st.container(border=True):
                    c1, c2 = st.columns([8, 2])
                    with c1: st.markdown(f"**{tag} {info['trip_name']}**\n<small style='color:#64748b;'>暗號: {s}</small>", unsafe_allow_html=True)
                    with c2:
                        if st.button("進入 ➡️", key=f"go_{s}", use_container_width=True):
                            st.session_state.trip_code = s; st.rerun()

    if st.button("🚪 登出帳號", use_container_width=True):
        st.session_state.user = None; st.rerun()
    st.stop()

# ─── 旅程內部層 ────────────────────────────────────────────────
trip_code = st.session_state.trip_code
data = dm.load_data(trip_code)
trip_info = dm.get_trip_info(trip_code)

# 導覽列
cols = st.columns(4)
nav_keys = ["🏠 總覽看板", "📅 行程規劃", "💰 記帳本", "⚙️ 旅程設定"]
for i, (icon, label, key) in enumerate(NAV_ITEMS := [("🏠","總覽","🏠 總覽看板"),("📅","行程","📅 行程規劃"),("💰","記帳","💰 記帳本"),("⚙️","設定","⚙️ 旅程設定")]):
    if cols[i].button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key; st.rerun()

page = st.session_state.get("page", "🏠 總覽看板")

# 頂部標題
t1, t2 = st.columns([8, 2])
with t1: st.markdown(f"### {trip_info['trip_name']}"); st.caption(f"🔑 {trip_code} | 👤 {trip_info['owner_username']}")
with t2:
    if st.button("🚪 退出", use_container_width=True): st.session_state.trip_code = None; st.rerun()
st.markdown("---")

# 頁面邏輯
if page == "🏠 總覽看板":
    # ── 預算管理區 ──
    budget = data["total_budget_twd"]
    spent = sum(e["amount_twd"] for e in data["expenses"])
    
    if budget == 0:
        st.warning("⚠️ **你尚未設定旅程預算！**")
        with st.expander("🚀 點此立即快速設定預算"):
            new_b = st.number_input("預計旅費 (台幣 TWD)", min_value=0, step=1000, value=0)
            if st.button("儲存預算", use_container_width=True):
                data["total_budget_twd"] = new_b
                dm.save_data(data, trip_code)
                st.rerun()
    else:
        spent_pct = min(spent / budget, 1.0)
        st.markdown(f"#### 💰 預算進度：{spent_pct*100:.1f}%")
        color = "#f6ad55" if spent_pct < 0.8 else "#f56565"
        st.markdown(f'<div style="background:#2d3748;height:24px;border-radius:10px;overflow:hidden;"><div style="background:{color};width:{spent_pct*100}%;height:100%;"></div></div>', unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between;color:#94a3b8;'><span>已花 NT${spent:,.0f}</span><span>預算 NT${budget:,.0f}</span></div>", unsafe_allow_html=True)
        
        # 快速調整預算
        with st.expander("🛠️ 快速調整預算"):
            adj_b = st.number_input("修改預算總額", value=float(budget), step=1000.0)
            if st.button("儲存修改", use_container_width=True):
                data["total_budget_twd"] = adj_b
                dm.save_data(data, trip_code); st.rerun()

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📊 分類統計")
        by_cat = dm.get_expenses_by_category(data)
        if by_cat:
            fig = go.Figure(go.Pie(labels=list(by_cat.keys()), values=list(by_cat.values()), hole=.5))
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else: st.caption("無資料")
    with c2:
        st.markdown("#### 📈 每日消費")
        by_date = dm.get_expenses_by_date(data)
        if by_date:
            fig = px.bar(x=list(by_date.keys()), y=list(by_date.values()))
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else: st.caption("無資料")

    if data["itinerary"]:
        st.markdown("#### 📍 即將行程")
        for item in sorted(data["itinerary"], key=lambda x: x["date"]+x["time"])[:3]:
            st.markdown(f"<div class='timeline-item'><b>{item['time']}</b> {item['activity']} @{item['location']}</div>", unsafe_allow_html=True)

elif page == "📅 行程規劃":
    with st.form("add_it"):
        st.markdown("#### ➕ 新增行程")
        c1, c2 = st.columns(2)
        d = c1.date_input("日期", date.today())
        l = c1.text_input("地點")
        t = c2.time_input("時間", datetime.now().time())
        a = c2.text_input("活動")
        n = st.text_area("備註")
        if st.form_submit_button("加入行程", use_container_width=True):
            dm.add_itinerary_item(str(d), t.strftime("%H:%M"), l, a, n, trip_code); st.rerun()
    
    st.markdown("---")
    it = data["itinerary"]
    for day in sorted(list(set(i["date"] for i in it))):
        st.markdown(f"**📅 {day}**")
        for item in [i for i in it if i["date"] == day]:
            with st.container(border=True):
                st.markdown(f"**{item['time']} {item['activity']}** (@{item['location']})")
                if st.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    dm.delete_itinerary_item(item['id'], trip_code); st.rerun()

elif page == "💰 記帳本":
    with st.form("add_exp"):
        st.markdown("#### ➕ 新增支出")
        c1, c2 = st.columns(2)
        d = c1.date_input("日期", date.today())
        cat = c1.selectbox("分類", CATEGORIES)
        cur = c2.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"])
        amt = c2.number_input("金額", min_value=0.0)
        desc = st.text_input("說明")
        if st.form_submit_button("記錄支出", use_container_width=True):
            dm.add_expense(str(d), cat, desc, amt, cur, trip_code); st.rerun()
    
    st.markdown("---")
    for e in sorted(data["expenses"], key=lambda x: x["date"], reverse=True):
        with st.container(border=True):
            st.markdown(f"**{e['category']}** {e['description']}")
            st.caption(f"{e['date']} · {e['amount_original']} {e['currency']}")
            st.markdown(f"<span style='color:#f6ad55; font-weight:700;'>NT${e['amount_twd']:,.0f}</span>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"delexp_{e['id']}"):
                dm.delete_expense(e['id'], trip_code); st.rerun()

elif page == "⚙️ 旅程設定":
    with st.form("set"):
        st.markdown("#### ⚙️ 設定")
        n = st.text_input("名稱", data["trip_name"])
        b = st.number_input("預算", value=float(data["total_budget_twd"]))
        if st.form_submit_button("儲存"):
            dm.update_settings(n, b, data["exchange_rates"], trip_code); st.rerun()
    
    if st.button("🌐 更新即時匯率", use_container_width=True):
        resp = requests.get("https://open.er-api.com/v6/latest/TWD").json()
        fx = resp.get("rates", {})
        r = data["exchange_rates"]
        for c in ["JPY","USD","EUR","KRW"]:
            if c in fx: r[c] = round(1/fx[c], 5)
        dm.save_data(data, trip_code); st.success("匯率已更新！")
