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

/* 行程卡片樣式 */
.timeline-item {
    background: linear-gradient(145deg, #232a3d, #1a2035);
    border: 1px solid #2d3748;
    border-left: 4px solid #4299e1;
    padding: 18px;
    margin-bottom: 12px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* 支出卡片樣式 */
.expense-card {
    background: #1a2035;
    border: 1px solid #2d3748;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 10px;
    transition: transform 0.2s;
}

/* 底部導覽列 (手機版) */
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
                        st.markdown(f"<div style='background-color:rgba(255,0,0,0.1); color:#ff6b6b; padding:15px; border-radius:10px; border:1px solid #ff6b6b; margin-bottom:10px; font-weight:700;'>❌ 註冊失敗：{msg}</div>", unsafe_allow_html=True)
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
            c_name = st.text_input("旅程名稱", placeholder="例如：我的日本行")
            c_secret = st.text_input("旅程暗號", placeholder="自訂一個暗號分享給朋友...")
            c_privacy = st.radio("隱私設定", ["🌐 公開 (可搜尋)", "🔒 私人"], horizontal=True)
            c_pwd = st.text_input("存取密碼 (選填)", type="password")
            cc1, cc2 = st.columns(2)
            if cc1.form_submit_button("確定建立", use_container_width=True):
                success, msg = dm.create_trip(st.session_state.user, c_secret, c_name, "公開" in c_privacy, c_pwd if c_pwd else None)
                if success: st.session_state.dash_mode = "list"; st.rerun()
                else: st.error(msg)
            if cc2.form_submit_button("取消", use_container_width=True):
                st.session_state.dash_mode = "list"; st.rerun()
    
    elif mode == "join":
        with st.form("join_form"):
            st.markdown("### 👥 加入旅程")
            j_secret = st.text_input("輸入朋友給你的暗號")
            if st.form_submit_button("🔍 搜尋旅程", use_container_width=True):
                info = dm.get_trip_info(j_secret)
                if info: st.session_state.pending_join = j_secret
                else: st.error("找不到此旅程")
        if "pending_join" in st.session_state:
            s = st.session_state.pending_join
            info = dm.get_trip_info(s)
            st.info(f"📍 找到旅程：**{info['trip_name']}** (由 {info['owner_username']} {info['owner_id']} 建立)")
            with st.form("join_confirm"):
                j_pwd = st.text_input("請輸入密碼", type="password") if info['password'] else ""
                if st.form_submit_button("確認加入", use_container_width=True):
                    success, msg = dm.join_trip(st.session_state.user, s, j_pwd)
                    if success: del st.session_state.pending_join; st.session_state.dash_mode = "list"; st.rerun()
                    else: st.error(msg)
            if st.button("返回"): del st.session_state.pending_join; st.rerun()

    else:
        st.markdown("---")
        st.markdown("### 📂 我的旅程清單")
        my_t = user_info.get("my_trips", [])
        jo_t = user_info.get("joined_trips", [])
        trips = [(s, "👑 我建立的") for s in my_t] + [(s, "👥 我加入的") for s in jo_t]
        
        if not trips: st.info("目前無旅程，點擊上方按鈕建立一個吧！")
        for s, tag in trips:
            info = dm.get_trip_info(s)
            if info:
                with st.container(border=True):
                    c1, c2 = st.columns([8, 2])
                    with c1: st.markdown(f"**{info['trip_name']}**\n<small style='color:#64748b;'>{tag} · 暗號: {s}</small>", unsafe_allow_html=True)
                    with c2:
                        if st.button("進入 ➡️", key=f"go_{s}", use_container_width=True):
                            st.session_state.trip_code = s; st.rerun()

    st.markdown("---")
    with st.expander("👤 帳號設定"):
        new_p = st.text_input("修改個人登入密碼", type="password")
        if st.button("💾 確定修改密碼", use_container_width=True):
            if len(new_p) >= 4:
                success, msg = dm.update_user_password(st.session_state.user, new_p)
                if success: st.success(msg)
                else: st.error(msg)
            else: st.warning("密碼至少需 4 位")
    if st.button("🚪 登出帳號", use_container_width=True, type="secondary"):
        st.session_state.user = None; st.session_state.trip_code = None; st.rerun()
    st.stop()

# ─── 旅程內部層 ────────────────────────────────────────────────
trip_code = st.session_state.trip_code
data = dm.load_data(trip_code)
trip_meta = dm.get_trip_info(trip_code)

# 底部導覽
cols = st.columns(4)
for idx, (icon, label, key) in enumerate([("🏠","總覽","🏠 總覽看板"), ("📅","行程","📅 行程規劃"), ("💰","記帳","💰 記帳本"), ("⚙️","設定","⚙️ 旅程設定")]):
    if cols[idx].button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key; st.rerun()

page = st.session_state.get("page", "🏠 總覽看板")

# 頁面標題列
t1, t2 = st.columns([8, 2])
with t1:
    st.markdown(f"### {trip_meta['trip_name'] if trip_meta else data['trip_name']}")
    st.caption(f"🔑 暗號: {trip_code} | 👤 持有人: {trip_meta['owner_username'] if trip_meta else 'Unknown'}")
with t2:
    if st.button("🚪 退出", use_container_width=True): st.session_state.trip_code = None; st.rerun()
st.markdown("---")

if page == "🏠 總覽看板":
    budget = data["total_budget_twd"]
    spent = sum(e["amount_twd"] for e in data["expenses"])
    if budget == 0:
        st.warning("⚠️ **尚未設定旅程預算！**")
        with st.expander("🚀 點此快速設定"):
            new_b = st.number_input("設定總預算 (TWD)", min_value=0, step=1000)
            if st.button("儲存預算", use_container_width=True):
                data["total_budget_twd"] = new_b; dm.save_data(data, trip_code); st.rerun()
    else:
        spent_pct = min(spent / budget, 1.0)
        st.markdown(f"#### 💰 預算進度：{spent_pct*100:.1f}%")
        color = "#f6ad55" if spent_pct < 0.8 else "#f56565"
        st.markdown(f'<div style="background:#2d3748;height:24px;border-radius:12px;overflow:hidden;"><div style="background:{color};width:{spent_pct*100}%;height:100%;"></div></div>', unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between;color:#94a3b8;'><span>已花 NT${spent:,.0f}</span><span>預算 NT${budget:,.0f}</span></div>", unsafe_allow_html=True)
        with st.expander("🛠️ 快速調整預算"):
            adj_b = st.number_input("修改總額", value=float(budget), step=1000.0)
            if st.button("確定儲存"): data["total_budget_twd"] = adj_b; dm.save_data(data, trip_code); st.rerun()

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
            fig.update_layout(height=250, margin=dict(t=0,b=20,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else: st.caption("無資料")

    if data["itinerary"]:
        st.markdown("#### 📍 即將行程")
        for item in sorted(data["itinerary"], key=lambda x: x["date"]+x["time"])[:3]:
            st.markdown(f"""<div class='timeline-item'>
                <div style='color:#63b3ed; font-size:0.9rem; font-weight:700;'>📅 {item['date']} {item['time']}</div>
                <div style='font-size:1.1rem; font-weight:700; margin:4px 0;'>{item['activity']}</div>
                <div style='color:#94a3b8; font-size:0.85rem;'>📍 {item['location']}</div>
            </div>""", unsafe_allow_html=True)

elif page == "📅 行程規劃":
    with st.form("add_it", clear_on_submit=True):
        st.markdown("#### ➕ 新增行程")
        c1, c2 = st.columns(2)
        d = c1.date_input("日期", date.today())
        l = c1.text_input("地點", placeholder="例如：東京鐵塔")
        t = c2.time_input("時間", value=datetime.now().time())
        a = c2.text_input("活動", placeholder="要做什麼？")
        n = st.text_area("詳細備註 (選填)")
        if st.form_submit_button("📌 加入行程", use_container_width=True):
            if l and a: dm.add_itinerary_item(str(d), t.strftime("%H:%M"), l, a, n, trip_code); st.rerun()
            else: st.warning("請填寫地點與活動")
    
    st.markdown("---")
    it = data["itinerary"]
    for day in sorted(list(set(i["date"] for i in it))):
        st.markdown(f"#### 📅 {day}")
        for item in [i for i in it if i["date"] == day]:
            with st.container():
                st.markdown(f"""<div class='timeline-item'>
                    <div style='color:#63b3ed; font-weight:700;'>⏰ {item['time']}</div>
                    <div style='font-size:1.2rem; font-weight:700; margin:4px 0;'>{item['activity']}</div>
                    <div style='color:#94a3b8;'>📍 {item['location']}</div>
                    {f"<div style='color:#718096; font-size:0.85rem; margin-top:4px;'>📝 {item['notes']}</div>" if item.get('notes') else ""}
                </div>""", unsafe_allow_html=True)
                if st.button("🗑️ 刪除", key=f"del_{item['id']}", use_container_width=True):
                    dm.delete_itinerary_item(item['id'], trip_code); st.rerun()

elif page == "💰 記帳本":
    with st.form("add_exp", clear_on_submit=True):
        st.markdown("#### ➕ 新增支出")
        c1, c2 = st.columns(2)
        d = c1.date_input("日期", date.today())
        cat = c1.selectbox("分類", CATEGORIES)
        cur = c2.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"])
        amt = c2.number_input("金額", min_value=0.0, step=100.0)
        desc = st.text_input("說明", placeholder="買了什麼？")
        if st.form_submit_button("💰 記錄支出", use_container_width=True):
            if amt > 0: dm.add_expense(str(d), cat, desc, amt, cur, trip_code); st.rerun()
            else: st.warning("請輸入金額")
    
    st.markdown("---")
    for e in sorted(data["expenses"], key=lambda x: x["date"], reverse=True):
        with st.container():
            st.markdown(f"""<div class='expense-card'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='font-weight:700; font-size:1.1rem;'>{e['category']}</span>
                    <span style='color:#f6ad55; font-weight:800; font-size:1.2rem;'>NT${e['amount_twd']:,.0f}</span>
                </div>
                <div style='color:#e2e8f0; margin-top:4px;'>{e['description'] or '無說明'}</div>
                <div style='color:#94a3b8; font-size:0.85rem; margin-top:4px;'>📅 {e['date']} · {e['amount_original']:,.0f} {e['currency']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ 刪除", key=f"delexp_{e['id']}", use_container_width=True):
                dm.delete_expense(e['id'], trip_code); st.rerun()

elif page == "⚙️ 旅程設定":
    msg_area = st.empty() # 用來顯示訊息的唯一區域
    
    with st.form("set_meta"):
        st.markdown("#### ⚙️ 旅程基本設定")
        n = st.text_input("旅程名稱", data["trip_name"])
        b = st.number_input("總預算 (TWD)", value=float(data["total_budget_twd"]))
        st.markdown("#### 🔒 隱私與密碼")
        is_pub = st.checkbox("公開旅程 (可被搜尋)", value=trip_meta.get("is_public", True))
        pwd = st.text_input("存取密碼 (選填)", value=trip_meta.get("password", ""), type="password")
        if st.form_submit_button("💾 儲存修改"):
            data["trip_name"] = n; data["total_budget_twd"] = b; data["password"] = pwd if pwd else None
            dm.save_data(data, trip_code)
            m_db = dm._load_json(dm.TRIPS_META_FILE, {})
            if trip_code in m_db:
                m_db[trip_code].update({"trip_name": n, "is_public": is_pub, "password": pwd if pwd else None})
                dm._save_json(dm.TRIPS_META_FILE, m_db)
            st.success("✅ 設定已儲存！"); st.rerun()

    with st.form("set_rates"):
        st.markdown("#### 💱 匯率設定 (1 外幣 = 多少台幣)")
        r = data["exchange_rates"]
        c1, c2 = st.columns(2)
        j = c1.number_input("🇯🇵 JPY", value=float(r.get("JPY", 0.215)), format="%.4f", key="input_jpy")
        u = c1.number_input("🇺🇸 USD", value=float(r.get("USD", 32.0)), format="%.2f", key="input_usd")
        e = c2.number_input("🇪🇺 EUR", value=float(r.get("EUR", 35.0)), format="%.2f", key="input_eur")
        k = c2.number_input("🇰🇷 KRW", value=float(r.get("KRW", 0.024)), format="%.4f", key="input_krw")
        if st.form_submit_button("💾 儲存匯率", use_container_width=True):
            data["exchange_rates"] = {"JPY":j, "USD":u, "EUR":e, "KRW":k}
            dm.save_data(data, trip_code)
            st.success("✅ 匯率已手動儲存！")
            st.rerun()

    # 檢查是否有手動修改但未儲存
    has_unsaved = (j != r.get("JPY") or u != r.get("USD") or e != r.get("EUR") or k != r.get("KRW"))
    if has_unsaved:
        st.warning("⚠️ 偵測到手動輸入的匯率尚未儲存，若點擊下方按鈕將會覆蓋您的修改。")

    if st.button("🌐 更新網路即時匯率", use_container_width=True):
        try:
            resp = requests.get("https://api.exchangerate-api.com/v4/latest/TWD", timeout=10)
            if resp.status_code == 200:
                fx = resp.json().get("rates", {})
                new_rates = {}
                for cur in ["JPY","USD","EUR","KRW"]:
                    if cur in fx:
                        new_rates[cur] = round(1 / fx[cur], 4)
                
                data["exchange_rates"].update(new_rates)
                dm.save_data(data, trip_code)
                
                # 顯示成功訊息並立刻重新整理畫面，讓輸入框顯示最新數字
                msg_area.success("✅ 網路匯率已同步更新成功！")
                st.rerun()
            else:
                msg_area.error("❌ 伺服器回應異常，請稍後再試")
        except:
            msg_area.error("❌ 網路連線超時，請稍後再試")
