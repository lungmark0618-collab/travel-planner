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
    page_title="智慧旅遊小管家 | Smart Travel Buddy",
    layout="centered",
    initial_sidebar_state="collapsed"
)



# ─── 常數設定 ──────────────────────────────────────────────────
CATEGORIES = ["食物", "交通", "住宿", "購物", "門票", "其他"]
CATEGORY_COLORS = {
    "交通": "#5856D6", # 深靛藍
    "食物": "#FF7E5F", # 珊瑚橘
    "住宿": "#2ECC71", # 翡翠綠
    "購物": "#F093FB", # 玫瑰粉
    "門票": "#F6D365", # 琥珀黃
    "其他": "#BDC3C7"  # 銀灰色
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
}

@media (max-width: 767px) {
    .stApp { padding-bottom: 90px; }
}
</style>
""", unsafe_allow_html=True)

# ─── Session State 初始化 ─────────────────────────────────────
if "user" not in st.session_state: st.session_state.user = None
if "trip_code" not in st.session_state: st.session_state.trip_code = None
if "auth_page" not in st.session_state: st.session_state.auth_page = "login"
if "rate_ver" not in st.session_state: st.session_state.rate_ver = 0

# ─── 帳號層：登入/註冊 ───────────────────────────────────────────
if st.session_state.user is None:
    st.markdown("## 🌍 智慧旅遊小管家")
    st.markdown("<p style='color:#a0aec0;'>您的隨身小管家</p>", unsafe_allow_html=True)
    
    if st.session_state.auth_page == "login":
        # 讀取 URL 中記住的帳號
        saved_user = st.query_params.get("remember_user", "")
        with st.form("login_form"):
            st.markdown("### 🔑 登入帳號")
            u = st.text_input("使用者名稱", value=saved_user)
            p = st.text_input("密碼", type="password")
            remember = st.checkbox("記住我 (下次自動填寫帳號)", value=bool(saved_user))
            if st.form_submit_button("登入", use_container_width=True):
                user_data, msg = dm.login_user(u, p)
                if user_data:
                    st.session_state.user = u
                    if remember: st.query_params["remember_user"] = u
                    else: st.query_params.clear()
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
    if col1.button("🆕 建立新旅程", use_container_width=True, type="primary"):
        st.session_state.dash_mode = "create"; st.rerun()
    if col2.button("👥 加入現有旅程", use_container_width=True):
        st.error("⚠️ 功能維護中，暫不開放加入")

    mode = st.session_state.get("dash_mode", "list")
    
    if mode == "create":
        with st.form("create_trip_form"):
            st.markdown("### 🌟 建立全新旅程")
            c_name = st.text_input("旅程名稱", placeholder="例如：2026 東京賞櫻之旅")
            # 隱藏欄位，改為後台自動生成
            import random, string
            c_secret = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
            
            cc1, cc2 = st.columns(2)
            if cc1.form_submit_button("確定建立", use_container_width=True):
                # 預設為私人 (False)，密碼為 None
                success, msg = dm.create_trip(st.session_state.user, c_secret, c_name, False, None)
                if success: st.session_state.dash_mode = "list"; st.rerun()
                else: st.error(msg)
            if cc2.form_submit_button("取消", use_container_width=True):
                st.session_state.dash_mode = "list"; st.rerun()
    
    elif mode == "join":
        with st.form("join_form"):
            st.markdown("### 👥 加入旅程")
            j_secret = st.text_input("輸入旅程邀請碼")
            if st.form_submit_button("🔍 搜尋", use_container_width=True):
                info = dm.get_trip_info(j_secret)
                if info: st.session_state.pending_join = j_secret
                else: st.error("找不到此旅程")
        if "pending_join" in st.session_state:
            s = st.session_state.pending_join
            info = dm.get_trip_info(s)
            st.info(f"📍 找到：{info['trip_name']} (由 {info['owner_username']} {info['owner_id']} 建立)")
            with st.form("join_confirm"):
                j_pwd = st.text_input("密碼", type="password") if info['password'] else ""
                if st.form_submit_button("確認加入", use_container_width=True):
                    st.error("⚠️ 功能維護中，暫不開放加入")
                    # success, msg = dm.join_trip(st.session_state.user, s, j_pwd)
                    # if success: del st.session_state.pending_join; st.session_state.dash_mode = "list"; st.rerun()
                    # else: st.error(msg)

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

    # ─── 🔐 系統管理員後台 (僅 mark 可見) ───────────────────────
    if st.session_state.user == "mark":
        with st.expander("🔐 系統管理員後台", expanded=False):
            st.markdown("### 👥 使用者管理")
            all_users = dm._load_json(dm.USERS_FILE, {})
            st.metric("目前總註冊人數", len(all_users))
            
            # 建立使用者清單表格
            user_list = []
            for uname, info in all_users.items():
                user_list.append({"使用者名稱": uname, "序號": info.get("user_id")})
            
            if user_list:
                df = pd.DataFrame(user_list)
                st.dataframe(df, use_container_width=True)
                
                # 管理操作：刪除特定使用者
                st.markdown("#### ⚡ 強制管理操作")
                target_u = st.selectbox("選擇要管理的使用者", list(all_users.keys()), key="admin_target")
                if target_u == "mark":
                    st.caption("無法刪除管理員自己")
                else:
                    if st.button(f"🧨 強制刪除帳號: {target_u}", use_container_width=True):
                        success, msg = dm.delete_user(target_u)
                        if success: st.success(f"已刪除 {target_u}"); st.rerun()
                        else: st.error(msg)
            else:
                st.caption("目前尚無其他使用者")

    st.markdown("---")
    with st.expander("👤 帳號設定"):
        st.markdown("#### 🔒 修改密碼")
        new_p = st.text_input("輸入新密碼", type="password")
        if st.button("💾 儲存新密碼", use_container_width=True):
            if len(new_p) >= 4:
                success, msg = dm.update_user_password(st.session_state.user, new_p)
                if success: st.success(msg)
                else: st.error(msg)
            else: st.warning("密碼長度需至少 4 位")
        
        st.markdown("---")
        st.markdown("#### 🧨 危險區域")
        st.caption("警告：刪除帳號是不可逆的動作，所有旅程權限將會消失。")
        confirm = st.checkbox("我確定要永久刪除我的帳號")
        if st.button("❌ 刪除帳號", use_container_width=True, type="secondary", disabled=not confirm):
            success, msg = dm.delete_user(st.session_state.user)
            if success:
                st.session_state.user = None
                st.session_state.trip_code = None
                st.success("帳號已刪除，即將登出...")
                st.rerun()
            else:
                st.error(msg)
    if st.button("🚪 登出帳號", use_container_width=True, type="secondary"):
        st.session_state.user = None; st.session_state.trip_code = None; st.rerun()
    st.stop()

# ─── 旅程內部層 ────────────────────────────────────────────────
trip_code = st.session_state.trip_code
data = dm.load_data(trip_code)
trip_meta = dm.get_trip_info(trip_code)
rv = st.session_state.rate_ver

cols = st.columns(4)
for idx, (icon, label, key) in enumerate([("🏠","總覽","🏠 總覽看板"), ("📅","行程","📅 行程規劃"), ("💰","記帳","💰 記帳本"), ("⚙️","設定","⚙️ 旅程設定")]):
    if cols[idx].button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key; st.rerun()

page = st.session_state.get("page", "🏠 總覽看板")

# 頁面標題列 (增加返回儀表板按鈕)
t1, t2 = st.columns([7, 3])
with t1:
    st.markdown(f"### {trip_meta['trip_name'] if trip_meta else data['trip_name']}")
    st.caption(f"🎟️ 邀請碼: {trip_code} | 👤 持有人: {trip_meta['owner_username'] if trip_meta else 'Unknown'}")
with t2:
    if st.button("⬅️ 返回儀表板", use_container_width=True):
        st.session_state.trip_code = None; st.rerun()
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
        color = "#f6ad55" if spent_pct < 0.8 else "#f56565"
        st.markdown(f'<div style="background:#2d3748;height:24px;border-radius:12px;overflow:hidden;"><div style="background:{color};width:{spent_pct*100}%;height:100%;"></div></div>', unsafe_allow_html=True)
        st.markdown(f"已花 NT${spent:,.0f} / 預算 NT${budget:,.0f}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📊 分類支出")
        by_cat = dm.get_expenses_by_category(data)
        if by_cat:
            # 使用自定義顏色並優化視覺效果
            colors = [CATEGORY_COLORS.get(cat, "#a0aec0") for cat in by_cat.keys()]
            fig = go.Figure(go.Pie(
                labels=list(by_cat.keys()), 
                values=list(by_cat.values()), 
                hole=.6,
                marker=dict(colors=colors, line=dict(color='#1a2035', width=2)),
                textinfo='percent',
                texttemplate='%{percent:.0%}', # 改為整數百分比，更簡潔
                textfont=dict(size=14, color="white", family="Inter", weight="bold"),
                hovertemplate="<b>%{label}</b><br>支出金額: NT$%{value:,.0f}<extra></extra>"
            ))
            fig.update_layout(
                height=250, 
                margin=dict(t=10,b=10,l=0,r=0), 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(family="Inter", color="#e2e8f0")
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else: st.caption("無資料")
    with c2:
        st.markdown("#### 📈 每日預算")
        by_date = dm.get_expenses_by_date(data)
        if by_date:
            # 使用更高級的藍色調並優化圖表樣式
            fig = px.bar(
                x=list(by_date.keys()), 
                y=list(by_date.values()), 
                labels={'x':'', 'y':''}
            )
            fig.update_traces(
                marker_color='#7f00ff', # 換成更有質感的紫色
                marker_line_width=0,
                opacity=0.9,
                hovertemplate="日期: %{x}<br>支出: NT$%{y:,.0f}<extra></extra>"
            )
            fig.update_layout(
                height=250, 
                margin=dict(t=10,b=20,l=0,r=0), 
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(type='category', gridcolor='#2d3748', tickfont=dict(size=10)),
                yaxis=dict(gridcolor='#2d3748', showticklabels=False), # 隱藏側邊標籤更簡潔
                font=dict(family="Inter", color="#a0aec0")
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else: st.caption("無資料")

    if data["itinerary"]:
        st.markdown("#### 📍 即將行程")
        for item in sorted(data["itinerary"], key=lambda x: x["date"]+x["time"])[:3]:
            # 修正：緊湊 HTML 避免黑框框，且無備註時顯示空白
            n_dash = f"<div style='color:#94a3b8; font-size:0.85rem; margin-top:4px;'>📝 {item['notes']}</div>" if item.get('notes') else ""
            h_dash = f"<div class='timeline-item'><div style='color:#63b3ed; font-size:0.9rem; font-weight:700;'>📅 {item['date']} {item['time']}</div><div style='font-size:1.1rem; font-weight:700; margin:4px 0;'>{item['activity']}</div><div style='color:#94a3b8; font-size:0.85rem;'>📍 {item['location']}</div>{n_dash}</div>"
            st.markdown(h_dash, unsafe_allow_html=True)

elif page == "📅 行程規劃":
    # 編輯模式檢查
    edit_id = st.session_state.get("edit_it_id")
    if edit_id:
        item = next((i for i in data["itinerary"] if i["id"] == edit_id), None)
        if item:
            with st.form("edit_it_form"):
                st.markdown("#### 📝 編輯行程")
                ed = st.date_input("日期", datetime.strptime(item["date"], "%Y-%m-%d"))
                el = st.text_input("地點", item["location"])
                et = st.time_input("時間", datetime.strptime(item["time"], "%H:%M").time())
                ea = st.text_input("活動", item["activity"])
                en = st.text_area("備註", item.get("notes", ""))
                cc1, cc2 = st.columns(2)
                if cc1.form_submit_button("💾 儲存修改", use_container_width=True):
                    item.update({"date": str(ed), "time": et.strftime("%H:%M"), "location": el, "activity": ea, "notes": en})
                    dm.save_data(data, trip_code)
                    del st.session_state.edit_it_id; st.rerun()
                if cc2.form_submit_button("取消", use_container_width=True):
                    del st.session_state.edit_it_id; st.rerun()
    else:
        with st.form("add_it", clear_on_submit=True):
            st.markdown("#### ➕ 新增行程")
            c1, c2 = st.columns(2)
            d = c1.date_input("日期", date.today())
            l = c1.text_input("地點")
            t = c2.time_input("時間", value=datetime.now().time())
            a = c2.text_input("活動")
            n = st.text_area("備註 (選填)")
            if st.form_submit_button("📌 加入", use_container_width=True):
                if l and a: dm.add_itinerary_item(str(d), t.strftime("%H:%M"), l, a, n, trip_code); st.rerun()

    st.markdown("---")
    for item in sorted(data["itinerary"], key=lambda x: x["date"]+x["time"]):
        with st.container():
            # 使用緊湊的 HTML，避免縮進導致 Streamlit 誤判為程式碼區塊
            notes_html = f"<div style='color:#718096; font-size:0.85rem; margin-top:4px;'>📝 {item['notes']}</div>" if item.get('notes') else ""
            html_card = f"<div class='timeline-item'><div style='color:#63b3ed; font-weight:700;'>⏰ {item['time']} | {item['date']}</div><div style='font-size:1.2rem; font-weight:700; margin:4px 0;'>{item['activity']}</div><div style='color:#94a3b8;'>📍 {item['location']}</div>{notes_html}</div>"
            st.markdown(html_card, unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            if c1.button("📝 編輯", key=f"editit_{item['id']}", use_container_width=True):
                st.session_state.edit_it_id = item["id"]; st.rerun()
            if c2.button("💸 轉記帳", key=f"toexp_{item['id']}", use_container_width=True):
                st.session_state.pending_exp = {"desc": f"{item['activity']} @{item['location']}", "date": item["date"]}
                st.session_state.page = "💰 記帳本"; st.rerun()
            if c3.button("🗑️ 刪除", key=f"del_{item['id']}", use_container_width=True):
                dm.delete_itinerary_item(item['id'], trip_code); st.rerun()

elif page == "💰 記帳本":
    # 編輯模式檢查
    edit_exp_id = st.session_state.get("edit_exp_id")
    if edit_exp_id:
        exp = next((e for e in data["expenses"] if e["id"] == edit_exp_id), None)
        if exp:
            with st.form("edit_exp_form"):
                st.markdown("#### 📝 編輯支出")
                ed = st.date_input("日期", datetime.strptime(exp["date"], "%Y-%m-%d"))
                ecat = st.selectbox("分類", CATEGORIES, index=CATEGORIES.index(exp["category"]))
                ecur = st.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"], index=["JPY","TWD","USD","EUR","KRW"].index(exp["currency"]))
                eamt = st.number_input("金額", value=float(exp["amount_original"]))
                edesc = st.text_input("說明", exp["description"])
                cc1, cc2 = st.columns(2)
                if cc1.form_submit_button("💾 儲存修改", use_container_width=True):
                    rates = data["exchange_rates"]
                    twd = eamt * rates.get(ecur, 1.0) if ecur != "TWD" else eamt
                    exp.update({"date": str(ed), "category": ecat, "currency": ecur, "amount_original": eamt, "amount_twd": twd, "description": edesc})
                    dm.save_data(data, trip_code)
                    del st.session_state.edit_exp_id; st.rerun()
                if cc2.form_submit_button("取消", use_container_width=True):
                    del st.session_state.edit_exp_id; st.rerun()
    else:
        pending = st.session_state.get("pending_exp", {})
        with st.form("add_exp", clear_on_submit=True):
            st.markdown("#### ➕ 新增支出")
            c1, c2 = st.columns(2)
            d = c1.date_input("日期", datetime.strptime(pending["date"], "%Y-%m-%d") if pending.get("date") else date.today())
            cat = c1.selectbox("分類", CATEGORIES)
            cur = c2.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"])
            amt = c2.number_input("金額", min_value=0.0)
            desc = st.text_input("說明", value=pending.get("desc", ""))
            cc1, cc2 = st.columns(2)
            if cc1.form_submit_button("💰 記錄", use_container_width=True):
                if amt > 0:
                    dm.add_expense(str(d), cat, desc, amt, cur, trip_code)
                    if "pending_exp" in st.session_state: del st.session_state.pending_exp
                    st.rerun()
            if cc2.form_submit_button("❌ 取消", use_container_width=True):
                if "pending_exp" in st.session_state: del st.session_state.pending_exp
                st.rerun()

    st.markdown("---")
    for e in sorted(data["expenses"], key=lambda x: x["date"], reverse=True):
        with st.container():
            st.markdown(f"""<div class='expense-card'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='font-weight:700;'>{e['category']}</span>
                    <span style='color:#f6ad55; font-weight:800;'>NT${e['amount_twd']:,.0f}</span>
                </div>
                <div style='font-size:0.9rem;'>{e['description']}</div>
                <div style='color:#94a3b8; font-size:0.8rem;'>{e['date']} | {e['amount_original']:,.0f} {e['currency']}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("📝 編輯", key=f"editexp_{e['id']}", use_container_width=True):
                st.session_state.edit_exp_id = e["id"]; st.rerun()
            if c2.button("🗑️ 刪除", key=f"delexp_{e['id']}", use_container_width=True):
                dm.delete_expense(e['id'], trip_code); st.rerun()

elif page == "⚙️ 旅程設定":
    msg_area = st.empty()
    with st.form("set_meta"):
        st.markdown("#### ⚙️ 旅程設定")
        n = st.text_input("名稱", data["trip_name"])
        b = st.number_input("預算", value=float(data["total_budget_twd"]))
        # 隱藏隱私與密碼設定
        if st.form_submit_button("💾 儲存修改", use_container_width=True):
            data["trip_name"] = n; data["total_budget_twd"] = b
            dm.save_data(data, trip_code)
            m_db = dm._load_json(dm.TRIPS_META_FILE, {})
            if trip_code in m_db:
                m_db[trip_code].update({"trip_name": n})
                dm._save_json(dm.TRIPS_META_FILE, m_db)
            st.success("✅ 已儲存！"); st.rerun()

    with st.form("set_rates"):
        st.markdown("#### 💱 匯率設定")
        r = data["exchange_rates"]
        c1, c2 = st.columns(2)
        j = c1.number_input("🇯🇵 JPY", value=float(r.get("JPY", 0.215)), format="%.4f", key=f"jpy_{rv}")
        u = c1.number_input("🇺🇸 USD", value=float(r.get("USD", 32.0)), format="%.2f", key=f"usd_{rv}")
        e = c2.number_input("🇪🇺 EUR", value=float(r.get("EUR", 35.0)), format="%.2f", key=f"eur_{rv}")
        k = c2.number_input("🇰🇷 KRW", value=float(r.get("KRW", 0.024)), format="%.4f", key=f"krw_{rv}")
        
        if st.form_submit_button("💾 儲存匯率", use_container_width=True):
            new_rates = {"JPY":j, "USD":u, "EUR":e, "KRW":k}
            data["exchange_rates"] = new_rates
            
            # 關鍵修正：同步更新所有記帳的台幣金額
            for exp in data["expenses"]:
                cur = exp["currency"]
                if cur != "TWD":
                    exp["amount_twd"] = exp["amount_original"] * new_rates.get(cur, 1.0)
                else:
                    exp["amount_twd"] = exp["amount_original"]
            
            dm.save_data(data, trip_code)
            st.session_state.rate_ver += 1
            st.success("✅ 匯率已更新，且所有記帳金額已同步重算！")
            st.rerun()

    st.markdown("<p style='color:#a0aec0; font-size:0.85rem;'>💡 提醒：手動修改後請先儲存再進行網路更新。</p>", unsafe_allow_html=True)
    if st.button("🌐 更新網路即時匯率", use_container_width=True):
        sources = ["https://api.frankfurter.app/latest?from=TWD", "https://api.exchangerate-api.com/v4/latest/TWD", "https://open.er-api.com/v6/latest/TWD"]
        success_flag = False
        with st.spinner("連線中..."):
            for url in sources:
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        fx = resp.json().get("rates", {})
                        updated_rates = {}
                        for cur in ["JPY","USD","EUR","KRW"]:
                            if cur in fx: updated_rates[cur] = round(1 / fx[cur], 4)
                        
                        data["exchange_rates"].update(updated_rates)
                        
                        # 同步更新所有記帳的台幣金額
                        for exp in data["expenses"]:
                            c = exp["currency"]
                            if c != "TWD":
                                exp["amount_twd"] = exp["amount_original"] * data["exchange_rates"].get(c, 1.0)
                            else:
                                exp["amount_twd"] = exp["amount_original"]
                        
                        dm.save_data(data, trip_code)
                        success_flag = True; break
                except: continue
        if success_flag:
            st.session_state.rate_ver += 1; msg_area.success("✅ 成功！記帳金額已同步更新。"); st.rerun()
        else: msg_area.error("❌ 失敗")
