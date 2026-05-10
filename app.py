import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(__file__))
import importlib
import data_manager as dm
importlib.reload(dm)

# ─── 頁面設定 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="✈️ 智慧旅遊規劃師",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── Session State 初始化 ─────────────────────────────────────
if "recent_trips" not in st.session_state:
    st.session_state.recent_trips = []
if "trip_code" not in st.session_state:
    st.session_state.trip_code = None
if "page" not in st.session_state:
    st.session_state.page = "🏠 總覽看板"
if "edit_item_id" not in st.session_state:
    st.session_state.edit_item_id = None
if "expense_from_item" not in st.session_state:
    st.session_state.expense_from_item = None
if "edit_expense_id" not in st.session_state:
    st.session_state.edit_expense_id = None

# ─── 自訂 CSS 樣式（手機優先設計）─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── 基礎重設 ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    -webkit-text-size-adjust: 100%;
    -webkit-tap-highlight-color: transparent;
}
.main { background-color: #0e1117; }

/* ── 主要內容區塊最大寬度 & 手機 padding ── */
.block-container {
    max-width: 860px !important;
    padding: 1rem 1rem 6rem 1rem !important; /* 底部留空給 tab bar */
}

/* ── 頂部橫幅 ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1f3a 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid rgba(99, 179, 237, 0.2);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(99,179,237,0.08) 0%, transparent 70%);
}
.hero-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-top: 6px;
}

/* ── 指標卡片 ── */
.metric-card {
    background: linear-gradient(145deg, #1e2538, #1a2035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 14px;
    text-align: center;
    margin-bottom: 12px;
    transition: transform 0.2s, border-color 0.2s;
}
.metric-card:active { transform: scale(0.97); }
.metric-icon { font-size: 1.5rem; }
.metric-label {
    font-size: 0.72rem;
    color: #94a3b8;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
}
.metric-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-top: 3px;
    word-break: break-all;
}
.metric-value.danger  { color: #fc8181; }
.metric-value.warning { color: #f6ad55; }
.metric-value.success { color: #68d391; }

/* ── 行程時間軸 ── */
.timeline-item {
    background: #1e2538;
    border-left: 3px solid #63b3ed;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
    position: relative;
}
.timeline-item:before {
    content: '';
    position: absolute;
    left: -8px; top: 50%;
    transform: translateY(-50%);
    width: 13px; height: 13px;
    background: #63b3ed;
    border-radius: 50%;
    border: 2px solid #0e1117;
}
.timeline-time     { font-size: 0.75rem; color: #63b3ed; font-weight: 600; }
.timeline-activity { font-size: 0.95rem; font-weight: 600; color: #e2e8f0; margin-top: 2px; }
.timeline-location { font-size: 0.82rem; color: #94a3b8; margin-top: 2px; }

/* ── 進度條 ── */
.budget-bar-bg {
    background: #2d3748;
    border-radius: 99px;
    height: 10px;
    margin: 8px 0;
    overflow: hidden;
}
.budget-bar-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.5s ease;
}

/* ── 側邊欄（桌機用） ── */
[data-testid="stSidebar"] {
    background: #13192b !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    text-align: left !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    margin-bottom: 6px !important;
    width: 100% !important;
    min-height: 44px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,179,237,0.12) !important;
    color: #63b3ed !important;
    border-color: rgba(99,179,237,0.3) !important;
    opacity: 1 !important;
}

/* ── 表單與輸入 ── */
.stTextInput input, .stNumberInput input {
    background-color: #1e2538 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    min-height: 44px !important;  /* Apple HIG 最小觸控大小 */
    font-size: 1rem !important;
}
div[data-testid="stForm"] {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 16px;
}

/* ── 所有按鈕（觸控友善） ── */
.stButton > button {
    background: linear-gradient(135deg, #3182ce, #2b6cb0) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 44px !important;
    font-size: 0.95rem !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
    opacity: 0.9 !important;
}

/* ══════════════════════════════════════════
   底部導覽列（手機專用 Tab Bar）
   ════════════════════════════════════════ */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: rgba(19, 25, 43, 0.97);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255,255,255,0.08);
    display: flex;
    justify-content: space-around;
    align-items: stretch;
    padding-bottom: env(safe-area-inset-bottom, 0px); /* iPhone Home Bar */
    padding-top: 4px;
}
.nav-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px 4px;
    cursor: pointer;
    text-decoration: none;
    border: none;
    background: transparent;
    color: #64748b;
    font-size: 0.65rem;
    font-weight: 500;
    gap: 2px;
    min-height: 56px;
    -webkit-tap-highlight-color: transparent;
    transition: color 0.15s;
}
.nav-btn:active { opacity: 0.7; }
.nav-btn.active-tab { color: #63b3ed; }
.nav-btn .nav-icon { font-size: 1.5rem; line-height: 1; }
.nav-btn .nav-label { font-size: 0.65rem; }

/* ── 響應式：手機（≤ 768px = iPhone 全系列） ── */
@media (max-width: 768px) {
    .hero-title { font-size: 1.3rem; }
    .hero-banner { padding: 16px 18px; }
    .metric-value { font-size: 1.05rem; }
    .metric-card  { padding: 12px 10px; }
    .block-container { padding: 0.75rem 0.75rem 5.5rem 0.75rem !important; }

    /* 隱藏側邊欄漢堡按鈕（手機用底部導覽取代） */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"]        { display: none !important; }

    /* 讓圖表在手機垂直疊放 */
    .mobile-stack > div { width: 100% !important; }
}

/* ── 響應式：iPhone SE / 小螢幕（≤ 390px） ── */

/* Hide Streamlit floating share/deploy/rerun buttons */
.stDeployButton,
[data-testid="stDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
footer { display: none !important; }
@media (max-width: 390px) {
    .hero-title { font-size: 1.15rem; }
    .metric-value { font-size: 0.95rem; }
    .nav-btn .nav-icon { font-size: 1.3rem; }
}


/* ═══ 頂部導覽列（手機顯示，桌機隱藏）══════════════════════════ */
.top-nav-bar {
    display: flex;
    gap: 4px;
    margin-bottom: 16px;
    background: rgba(22, 28, 48, 0.9);
    border-radius: 14px;
    padding: 5px;
    border: 1px solid rgba(255,255,255,0.07);
}
.top-nav-bar .stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #64748b !important;
    font-size: 0.75rem !important;
    min-height: 44px !important;
    padding: 6px 4px !important;
    border-radius: 10px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: pre-line !important;
    line-height: 1.4 !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
.top-nav-bar .stButton > button:hover {
    color: #e2e8f0 !important;
    background: rgba(99,179,237,0.1) !important;
}
.top-nav-active .stButton > button {
    color: #63b3ed !important;
    background: rgba(99,179,237,0.12) !important;
}

/* 桌機上隱藏頂部導覽，手機上隱藏側邊欄 */
@media (min-width: 768px) {
    .top-nav-bar { display: none !important; }
}
@media (max-width: 767px) {
    section[data-testid="stSidebar"] { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── 登入介面（開啟旅程）───────────────────────────────────────
if st.session_state.trip_code is None:
    st.markdown("""
    <div style='text-align:center; padding: 40px 20px;'>
        <h1 style='font-size:3.5rem'>✈️</h1>
        <h2 style='color:#e2e8f0; margin-bottom:10px;'>智慧旅遊管家</h2>
        <p style='color:#94a3b8; margin-bottom:30px;'>輸入一個「旅程暗號」來開啟專屬紀錄。<br>相同暗號的人可以共同編輯資料喔！</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        code = st.text_input("🔑 旅程暗號 (例如: 夏日東京、Mark的日本行)", placeholder="請輸入自訂暗號...")
        submit = st.form_submit_button("🚀 開始/加入旅程", use_container_width=True)
        if submit:
            if code:
                # 簡單清理代碼，只保留英數字與中文
                import re
                clean_code = re.sub(r'[^\w\u4e00-\u9fff]', '_', code)
                st.session_state.trip_code = clean_code
                if clean_code not in st.session_state.recent_trips:
                    st.session_state.recent_trips.append(clean_code)
                st.rerun()
            else:
                st.warning("請輸入暗號！")
    
    if st.session_state.recent_trips:
        st.markdown("<p style='color:#64748b; font-size:0.9rem; margin-top:20px;'>最近開啟過的旅程：</p>", unsafe_allow_html=True)
        for rt in st.session_state.recent_trips:
            if st.button(f"📍 {rt}", key=f"rt_{rt}", use_container_width=True):
                st.session_state.trip_code = rt
                st.rerun()
    
    st.markdown("""
    <div style='color:#64748b; font-size:0.85rem; text-align:center; margin-top:40px; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px;'>
        💡 <b>小提示：</b><br>
        1. 輸入你獨有的暗號，就是你的私人空間。<br>
        2. 把暗號傳給朋友，就能實現多人共同規劃！
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 取得目前的代碼
trip_code = st.session_state.trip_code

# ─── 側邊欄（桌機）+ 底部導覽列（手機）────────────────────────
_nav_items = [
    ("🏠", "總覽",   "🏠 總覽看板"),
    ("📅", "行程",   "📅 行程規劃"),
    ("💰", "記帳",   "💰 記帳本"),
    ("⚙️", "設定",  "⚙️ 旅程設定"),
]

# 桌機側邊欄
with st.sidebar:
    st.markdown("## ✈️ 旅遊規劃師")
    st.markdown("---")
    for icon, short, key in _nav_items:
        if st.button(f"{icon} {short if short != '設定' else '旅程設定'}",
                     key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.session_state.edit_item_id = None
            st.session_state.expense_from_item = None
            st.rerun()
    st.markdown("---")
    _sb_data = dm.load_data(trip_code)
    _sb_spent = dm.get_total_spent_twd(_sb_data)
    _sb_budget = _sb_data["total_budget_twd"]
    _sb_pct = _sb_spent / _sb_budget * 100 if _sb_budget > 0 else 0
    _sb_color = "#68d391" if _sb_pct < 60 else ("#f6ad55" if _sb_pct < 85 else "#fc8181")
    st.markdown("**💳 預算使用狀況**")
    st.markdown(f"""
    <div class="budget-bar-bg">
        <div class="budget-bar-fill" style="width:{min(_sb_pct,100):.1f}%; background:{_sb_color};"></div>
    </div>
    <small style="color:#94a3b8;">已花費 NT${_sb_spent:,.0f} / NT${_sb_budget:,.0f} ({_sb_pct:.1f}%)</small>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<small style='color:#64748b;'>旅程：{_sb_data['trip_name']}</small>",
                unsafe_allow_html=True)


# ── 頂部導覽列（手機用，桌機靠側邊欄）───────────────────────────
st.markdown('<div class="top-nav-bar">', unsafe_allow_html=True)
_tnav_cols = st.columns(4)
for _tcol, (_ticon, _tshort, _tkey) in zip(
    _tnav_cols,
    [("🏠", "總覽", "🏠 總覽看板"),
     ("📅", "行程", "📅 行程規劃"),
     ("💰", "記帳", "💰 記帳本"),
     ("⚙️", "設定", "⚙️ 旅程設定")]
):
    with _tcol:
        _active_cls = "top-nav-active" if st.session_state.page == _tkey else ""
        st.markdown(f'<div class="{_active_cls}">', unsafe_allow_html=True)
        if st.button(f"{_ticon}\n{_tshort}", key=f"tnav_{_tkey}",
                     use_container_width=True):
            st.session_state.page = _tkey
            st.session_state.edit_item_id = None
            st.session_state.expense_from_item = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


page = st.session_state.page

# ─── 重新載入最新資料 ─────────────────────────────────────────
data = dm.load_data(trip_code)
total_spent = dm.get_total_spent_twd(data)
budget = data["total_budget_twd"]
remaining = budget - total_spent
pct = total_spent / budget * 100 if budget > 0 else 0

CATEGORY_COLORS = {
    "🏨 住宿": "#63b3ed",
    "✈️ 機票": "#9f7aea",
    "🚌 交通": "#68d391",
    "🍜 餐飲": "#f6ad55",
    "🛍️ 購物": "#fc8181",
    "🎡 娛樂": "#76e4f7",
    "💊 醫療": "#fbb6ce",
    "📦 其他": "#a0aec0",
}
CATEGORIES = list(CATEGORY_COLORS.keys())

# ══════════════════════════════════════════════════════════════
# 頁面 1：總覽看板
# ══════════════════════════════════════════════════════════════
if page == "🏠 總覽看板":
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">✈️ {data['trip_name']}</div>
        <div class="hero-subtitle">你的智慧型旅遊規劃與預算管家</div>
    </div>
    """, unsafe_allow_html=True)

    # 指標卡片
    r_class = "danger" if remaining < 0 else ("warning" if pct > 80 else "success")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-label">總預算</div>
            <div class="metric-value">NT${budget:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🧾</div>
            <div class="metric-label">已花費</div>
            <div class="metric-value warning">NT${total_spent:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🏦</div>
            <div class="metric-label">剩餘預算</div>
            <div class="metric-value {r_class}">NT${remaining:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-label">使用比例</div>
            <div class="metric-value {r_class}">{pct:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    if pct >= 100:
        st.error("🚨 **超出預算！** 你的花費已超過設定的總預算，請注意控制支出！")
    elif pct >= 85:
        st.warning("⚠️ **預算警告！** 你已花費了超過 85% 的預算，請開始節省！")
    elif pct >= 60:
        st.info("📢 **預算提醒：** 已使用超過一半預算，繼續保持！")

    if not data["expenses"] and not data["itinerary"]:
        st.markdown("---")
        st.markdown("""<div style='text-align:center; padding: 40px 20px; color: #64748b;'>
            <div style='font-size:3rem'>🗺️</div>
            <h3 style='color:#94a3b8;'>旅程還沒開始！</h3>
            <p style='font-size:0.95rem;line-height:1.7;'>
                請先點下方 ⚙️ <b style='color:#94a3b8;'>設定</b> 設定旅程名稱與預算，<br>
                再用 📅 <b style='color:#94a3b8;'>行程</b> 和 💰 <b style='color:#94a3b8;'>記帳</b> 開始記錄吧！
            </p>
        </div>""", unsafe_allow_html=True)
    else:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("#### 📊 花費分類佔比")
            by_cat = dm.get_expenses_by_category(data)
            if by_cat:
                cat_names = list(by_cat.keys())
                cat_vals  = list(by_cat.values())
                cat_colors = [CATEGORY_COLORS.get(n, "#a0aec0") for n in cat_names]
                # 格式化 hover 文字，加上 NT$ 與百分比
                total_exp = sum(cat_vals)
                custom_text = [f"NT${v:,.0f}<br>{v/total_exp*100:.1f}%" for v in cat_vals]
                fig_pie = go.Figure(go.Pie(
                    labels=cat_names,
                    values=cat_vals,
                    marker=dict(
                        colors=cat_colors,
                        line=dict(color="#0e1117", width=2)
                    ),
                    hole=0.52,
                    textinfo="label+percent",
                    textfont=dict(size=13, color="#e2e8f0"),
                    hovertemplate="<b>%{label}</b><br>金額：NT$%{value:,.0f}<br>佔比：%{percent}<extra></extra>",
                    pull=[0.03] * len(cat_names),
                ))
                fig_pie.update_layout(
                    height=280,  # 縮小高度
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    showlegend=True,
                    legend=dict(
                        font=dict(color="#94a3b8", size=10),
                        bgcolor="rgba(0,0,0,0)",
                        orientation="h",  # 改成橫向
                        x=0.5, y=-0.1, xanchor="center"
                    ),
                    annotations=[dict(
                        text=f"<b>NT${total_exp:,.0f}</b>",
                        x=0.5, y=0.5,
                        font=dict(size=12, color="#e2e8f0"),
                        showarrow=False
                    )],
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.markdown("<p style='color:#64748b; text-align:center; padding:20px;'>還沒有記帳資料</p>", unsafe_allow_html=True)

        with col_chart2:
            st.markdown("#### 📅 每日花費")
            by_date = dm.get_expenses_by_date(data)
            if by_date:
                date_labels = [str(k) for k in by_date.keys()]
                date_vals   = list(by_date.values())
                fig_bar = go.Figure(go.Bar(
                    x=date_labels,
                    y=date_vals,
                    marker=dict(
                        color=date_vals,
                        colorscale=[[0, "#3182ce"], [1, "#90cdf4"]],
                        cornerradius=6,
                    ),
                    hovertemplate="<b>%{x}</b><br>NT$%{y:,.0f}<extra></extra>",
                ))
                fig_bar.update_layout(
                    height=280,  # 縮小高度
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    xaxis=dict(
                        type="category",
                        gridcolor="rgba(255,255,255,0.04)",
                        tickfont=dict(color="#94a3b8", size=10),
                    ),
                    yaxis=dict(
                        gridcolor="rgba(255,255,255,0.06)",
                        tickfont=dict(color="#94a3b8", size=10),
                    ),
                    bargap=0.4,
                    margin=dict(t=20, b=20, l=10, r=10),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.markdown("<p style='color:#64748b; text-align:center; padding:40px;'>還沒有記帳資料</p>", unsafe_allow_html=True)

        # ── 詳細數據展開區 ──────────────────────────────────────
        if data["expenses"]:
            with st.expander("🔍 查看詳細消費數據", expanded=False):
                st.markdown("##### 📋 各分類消費明細")
                by_cat_detail = dm.get_expenses_by_category(data)
                total_all = sum(by_cat_detail.values())
                # 分類摘要卡片（橫向排列）
                cat_cols = st.columns(min(len(by_cat_detail), 4))
                for idx, (cat, amt) in enumerate(sorted(by_cat_detail.items(), key=lambda x: -x[1])):
                    col_idx = idx % len(cat_cols)
                    clr = CATEGORY_COLORS.get(cat, "#a0aec0")
                    pct_c = amt / total_all * 100
                    cat_cols[col_idx].markdown(f"""
                    <div style="background:linear-gradient(145deg,#1e2538,#1a2035);
                        border:1px solid {clr}44; border-left:4px solid {clr};
                        border-radius:10px; padding:12px 16px; margin-bottom:10px;">
                        <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">{cat}</div>
                        <div style="font-size:1.3rem;font-weight:800;color:{clr};margin-top:4px;">NT${amt:,.0f}</div>
                        <div style="font-size:0.8rem;color:#94a3b8;margin-top:2px;">{pct_c:.1f}% 的總花費</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("##### 🧾 所有支出明細表")
                # 整理成 DataFrame 顯示
                rows = []
                for e in sorted(data["expenses"], key=lambda x: x["date"], reverse=True):
                    orig = f"{e['amount_original']:,.0f} {e['currency']}" if e["currency"] != "TWD" else "-"
                    rows.append({
                        "日期": e["date"],
                        "分類": e["category"],
                        "備註": e["description"] or "-",
                        "原始金額": orig,
                        "台幣 (TWD)": f"NT${e['amount_twd']:,.0f}"
                    })
                df_exp = pd.DataFrame(rows)
                st.dataframe(df_exp, use_container_width=True, hide_index=True)

        # 最近行程（最多3筆）
        if data["itinerary"]:
            st.markdown("#### 📅 接下來的行程")
            sorted_items = sorted(data["itinerary"], key=lambda x: x["date"] + x["time"])[:3]
            for item in sorted_items:
                st.markdown(f"""<div class="timeline-item">
                    <div class="timeline-time">📅 {item['date']} &nbsp;⏰ {item['time']}</div>
                    <div class="timeline-activity">{item['activity']}</div>
                    <div class="timeline-location">📍 {item['location']}</div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 頁面 2：行程規劃
# ══════════════════════════════════════════════════════════════
elif page == "📅 行程規劃":
    st.markdown("## 📅 行程規劃")
    st.markdown("記錄每日行程，還可以直接在行程上記錄花費！")

    with st.form("add_itinerary_form", clear_on_submit=True):
        st.markdown("#### ➕ 新增一筆行程")
        c1, c2 = st.columns(2)
        with c1:
            item_date = st.date_input("日期", value=date.today())
            item_location = st.text_input("地點（例如：東京晴空塔）", placeholder="輸入地點名稱...")
        with c2:
            item_time = st.time_input("時間", value=datetime.strptime("09:00", "%H:%M").time(), step=timedelta(minutes=30))
            item_activity = st.text_input("活動（例如：觀景台參觀）", placeholder="輸入活動內容...")
        item_notes = st.text_area("備註（可選填）", placeholder="特別注意事項、預約號碼等...", height=80)
        submitted = st.form_submit_button("📌 加入行程", use_container_width=True)

        if submitted:
            if item_location and item_activity:
                dm.add_itinerary_item(
                    str(item_date), item_time.strftime("%H:%M"),
                    item_location, item_activity, item_notes,
                    user_key=trip_code
                )
                st.success("✅ 行程已成功加入！")
                st.rerun()
            else:
                st.error("請輸入地點和活動內容！")

    st.markdown("---")

    # 顯示行程
    itinerary = data["itinerary"]
    if not itinerary:
        st.info("還沒有行程，趕快新增你的第一筆行程吧！")
    else:
        st.markdown("#### 🗓️ 你的行程表")
        grouped = {}
        for item in sorted(itinerary, key=lambda x: x["date"] + x["time"]):
            grouped.setdefault(item["date"], []).append(item)

        for day_date, items in grouped.items():
            st.markdown(f"**📅 {day_date}**")
            for item in items:
                is_editing = st.session_state.edit_item_id == item['id']
                is_adding_expense = st.session_state.expense_from_item == item['id']

                # ── 行程卡片顯示 ──
                with st.container(border=True):
                    col_info, col_btns = st.columns([8, 2])
                    with col_info:
                        st.markdown(f"**⏰ {item['time']}**")
                        st.markdown(f"**{item['activity']}**")
                        st.caption(f"📍 {item['location']}")
                        if item.get('notes'):
                            st.caption(f"📝 {item['notes']}")
                        # ── 顯示這筆行程已經記錄的花費 ──
                        related = [
                            e for e in data["expenses"]
                            if e["date"] == item["date"] and (
                                item["activity"].lower() in e["description"].lower() or
                                e["description"].lower() in item["activity"].lower() or
                                e["description"] == item["activity"]
                            )
                        ]
                        if related:
                            total_rel = sum(e["amount_twd"] for e in related)
                            labels_html = "".join([f"<span style='background:rgba(99,179,237,0.15);border-radius:6px;padding:2px 8px;margin-right:6px;font-size:0.85rem;'>{e['category']} <b>NT${e['amount_twd']:,.0f}</b></span>" for e in related])
                            st.markdown(f"<div style='margin-top:6px;'>💵 <b>已記花費：</b> {labels_html}<br><small style='color:#f6ad55;'><b>小計 NT${total_rel:,.0f}</b></small></div>", unsafe_allow_html=True)
                    with col_btns:
                        if st.button("✏️ 編輯", key=f"edit_{item['id']}"):
                            st.session_state.edit_item_id = item['id'] if not is_editing else None
                            st.session_state.expense_from_item = None
                            st.rerun()
                        if st.button("💰 記費用", key=f"addexp_{item['id']}"):
                            st.session_state.expense_from_item = item['id'] if not is_adding_expense else None
                            st.session_state.edit_item_id = None
                            st.rerun()
                        if st.button("🗑️", key=f"del_it_{item['id']}", help="刪除此行程"):
                            dm.delete_itinerary_item(item['id'], user_key=trip_code)
                            st.session_state.edit_item_id = None
                            st.session_state.expense_from_item = None
                            st.rerun()

                    # ── 編輯模式 ──
                    if is_editing:
                        st.markdown("**✏️ 編輯行程**")
                        with st.form(f"edit_form_{item['id']}", clear_on_submit=False):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                new_date = st.date_input("日期", value=datetime.strptime(item['date'], "%Y-%m-%d").date(), key=f"edate_{item['id']}")
                                new_loc  = st.text_input("地點", value=item['location'], key=f"eloc_{item['id']}")
                            with ec2:
                                new_time = st.time_input("時間", value=datetime.strptime(item['time'], "%H:%M").time(), key=f"etime_{item['id']}", step=timedelta(minutes=30))
                                new_act  = st.text_input("活動", value=item['activity'], key=f"eact_{item['id']}")
                            new_notes = st.text_area("備註", value=item.get('notes',''), key=f"enotes_{item['id']}", height=60)
                            save_edit = st.form_submit_button("💾 儲存修改", use_container_width=True)
                            if save_edit:
                                dm.delete_itinerary_item(item['id'], user_key=trip_code)
                                dm.add_itinerary_item(str(new_date), new_time.strftime("%H:%M"), new_loc, new_act, new_notes, user_key=trip_code)
                                st.session_state.edit_item_id = None
                                st.rerun()

                    # ── 快速記費用（不用 form，避免 Enter 讀不到值的 bug）──
                    if is_adding_expense:
                        st.markdown("**💰 快速記錄這趟行程的花費**")
                        xc1, xc2, xc3 = st.columns(3)
                        with xc1:
                            xcat = st.selectbox("分類", CATEGORIES, key=f"xcat_{item['id']}")
                        with xc2:
                            xcur = st.selectbox("幣別", ["JPY","TWD","USD","EUR","KRW"], key=f"xcur_{item['id']}")
                        with xc3:
                            xamt = st.number_input("金額", min_value=0.0, step=100.0, format="%.0f", key=f"xamt_{item['id']}")
                        xdesc = st.text_input("備註說明", value=item['activity'] if f"xdesc_{item['id']}" not in st.session_state else st.session_state[f"xdesc_{item['id']}"], key=f"xdesc_{item['id']}")
                        if st.button("💾 記錄花費", key=f"submit_exp_{item['id']}", use_container_width=True):
                            if xamt > 0:
                                rate = data["exchange_rates"].get(xcur, 1.0)
                                conv = xamt * rate if xcur != "TWD" else xamt
                                dm.add_expense(item['date'], xcat, xdesc, xamt, xcur, user_key=trip_code)
                                st.success(f"✅ 已記錄 {xamt:,.0f} {xcur} ≈ NT${conv:,.0f}！")
                                st.rerun()
                            else:
                                st.warning("金額不能為 0！")

            st.markdown("")


# ══════════════════════════════════════════════════════════════
# 頁面 3：記帳本
# ══════════════════════════════════════════════════════════════
elif page == "💰 記帳本":
    st.markdown("## 💰 記帳本")
    st.markdown("支援多國幣別，自動換算成台幣！")

    with st.form("add_expense_form", clear_on_submit=True):
        st.markdown("#### ➕ 新增一筆支出")
        c1, c2 = st.columns(2)
        with c1:
            exp_date = st.date_input("消費日期", value=date.today())
            exp_category = st.selectbox("消費分類", CATEGORIES)
        with c2:
            exp_currency = st.selectbox("幣別", ["JPY", "TWD", "USD", "EUR", "KRW"])
            exp_amount = st.number_input("金額", min_value=0.0, step=100.0, format="%.0f")

        exp_desc = st.text_input("備註說明（例如：吃了拉麵！）", placeholder="描述這筆消費...")
        submitted = st.form_submit_button("💾 記錄支出", use_container_width=True)

        if submitted:
            if exp_amount > 0:
                rate = data["exchange_rates"].get(exp_currency, 1.0)
                converted = exp_amount * rate if exp_currency != "TWD" else exp_amount
                dm.add_expense(str(exp_date), exp_category, exp_desc, exp_amount, exp_currency, user_key=trip_code)
                st.success(f"✅ 已記錄！{exp_amount:,.0f} {exp_currency} ≈ NT${converted:,.0f} TWD")
                st.rerun()
            else:
                st.error("請輸入金額！")

    st.markdown("---")

    # 支出列表
    expenses = data["expenses"]
    if not expenses:
        st.markdown("<div style='text-align:center; padding:48px; color:#64748b;'><div style='font-size:3rem'>🧾</div><p>還沒有任何支出記錄，開始你的旅遊記帳吧！</p></div>", unsafe_allow_html=True)
    else:
        st.markdown("#### 🧾 支出明細")
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            filter_cat = st.selectbox("篩選分類", ["全部"] + CATEGORIES, key="filter_cat")
        with col_filter2:
            sort_order = st.selectbox("排序方式", ["最新優先", "最舊優先", "金額高到低", "金額低到高"])

        filtered = expenses if filter_cat == "全部" else [e for e in expenses if e["category"] == filter_cat]

        if sort_order == "最舊優先":
            filtered = sorted(filtered, key=lambda x: x["date"])
        elif sort_order == "金額高到低":
            filtered = sorted(filtered, key=lambda x: x["amount_twd"], reverse=True)
        elif sort_order == "金額低到高":
            filtered = sorted(filtered, key=lambda x: x["amount_twd"])
        else:
            filtered = sorted(filtered, key=lambda x: x["date"], reverse=True)

        for expense in filtered:
            is_editing_exp = st.session_state.edit_expense_id == expense['id']
            with st.container(border=True):
                orig_str = f"{expense['amount_original']:,.0f} {expense['currency']}" if expense['currency'] != 'TWD' else ""
                col_a, col_b = st.columns([10, 2])
                with col_a:
                    st.markdown(f"**{expense['category']}** <span style='color:#94a3b8; font-size:0.9rem;'>{expense['description'] or '無備註'}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {expense['date']}{f' · 原始金額：{orig_str}' if orig_str else ''}")
                    st.markdown(f"<span style='font-size:1.15rem; font-weight:700; color:#f6ad55;'>NT${expense['amount_twd']:,.0f}</span>", unsafe_allow_html=True)
                with col_b:
                    if st.button("✏️ 編輯", key=f"edit_exp_{expense['id']}"):
                        st.session_state.edit_expense_id = expense['id'] if not is_editing_exp else None
                        st.rerun()
                    if st.button("🗑️ 刪除", key=f"del_exp_{expense['id']}"):
                        dm.delete_expense(expense['id'], user_key=trip_code)
                        st.session_state.edit_expense_id = None
                        st.rerun()

                if is_editing_exp:
                    st.markdown("**✏️ 修改這筆支出**")
                    with st.form(f"edit_exp_form_{expense['id']}"):
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            e_cat = st.selectbox("分類", CATEGORIES,
                                index=CATEGORIES.index(expense['category']) if expense['category'] in CATEGORIES else 0)
                        with ec2:
                            currencies = ["JPY","TWD","USD","EUR","KRW"]
                            cur_idx = currencies.index(expense['currency']) if expense['currency'] in currencies else 1
                            e_cur = st.selectbox("幣別", currencies, index=cur_idx)
                        with ec3:
                            e_amt = st.number_input("金額（原始幣別）",
                                value=float(expense['amount_original']), min_value=0.0,
                                step=100.0, format="%.0f")
                        e_desc = st.text_input("備註說明", value=expense['description'])
                        e_date = st.date_input("日期", value=datetime.strptime(expense['date'], "%Y-%m-%d").date())
                        if st.form_submit_button("💾 儲存修改", use_container_width=True):
                            dm.update_expense(expense['id'], str(e_date), e_cat, e_desc, e_amt, e_cur, user_key=trip_code)
                            st.session_state.edit_expense_id = None
                            st.success("✅ 已更新！")
                            st.rerun()

        st.markdown(f"<div style='text-align:right; padding:12px; font-weight:700; color:#e2e8f0; font-size:1.1rem;'>篩選結果合計：NT${sum(e['amount_twd'] for e in filtered):,.0f}</div>", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════
# 頁面 4：旅程設定
# ══════════════════════════════════════════════════════════════
elif page == "⚙️ 旅程設定":
    st.markdown("## ⚙️ 旅程設定")
    st.markdown("在這裡調整你的旅程名稱、預算與匯率設定。")

    with st.form("settings_form"):
        st.markdown("#### 🌟 基本設定")
        new_name = st.text_input("旅程名稱", value=data["trip_name"])
        new_budget = st.number_input("總預算（台幣 TWD）", value=float(data["total_budget_twd"]), min_value=0.0, step=1000.0)

        st.markdown("#### 💱 匯率設定（1 外幣 = 多少台幣）")
        rates = data["exchange_rates"]
        c1, c2 = st.columns(2)
        with c1:
            jpy_rate = st.number_input("🇯🇵 JPY（日幣）", value=float(rates.get("JPY", 0.215)), format="%.4f", step=0.001)
            usd_rate = st.number_input("🇺🇸 USD（美金）", value=float(rates.get("USD", 32.0)), format="%.2f", step=0.1)
        with c2:
            eur_rate = st.number_input("🇪🇺 EUR（歐元）", value=float(rates.get("EUR", 35.0)), format="%.2f", step=0.1)
            krw_rate = st.number_input("🇰🇷 KRW（韓圓）", value=float(rates.get("KRW", 0.024)), format="%.4f", step=0.001)

        save_btn = st.form_submit_button("💾 儲存設定", use_container_width=True)
        if save_btn:
            new_rates = {"JPY": jpy_rate, "USD": usd_rate, "EUR": eur_rate, "KRW": krw_rate}
            dm.update_settings(new_name, new_budget, new_rates, user_key=trip_code)
            st.success("✅ 設定已儲存！")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔄 切換或新增旅程")
    st.markdown(f"<small style='color:#94a3b8;'>目前正在：<b>{trip_code}</b></small>", unsafe_allow_html=True)
    with st.expander("🚪 開啟另一份旅程資料"):
        new_c = st.text_input("輸入新的旅程暗號", placeholder="輸入暗號...")
        if st.button("切換旅程", use_container_width=True):
            if new_c:
                import re
                clean_new = re.sub(r'[^\w\u4e00-\u9fff]', '_', new_c)
                st.session_state.trip_code = clean_new
                if clean_new not in st.session_state.recent_trips:
                    st.session_state.recent_trips.append(clean_new)
                st.rerun()
        
        if len(st.session_state.recent_trips) > 1:
            st.markdown("<small style='color:#64748b;'>切換回最近的旅程：</small>", unsafe_allow_html=True)
            for rt in st.session_state.recent_trips:
                if rt != trip_code:
                    if st.button(f"🔙 {rt}", key=f"switch_{rt}", use_container_width=True):
                        st.session_state.trip_code = rt
                        st.rerun()
        
        if st.button("🚪 登出目前旅程", type="secondary", use_container_width=True):
            st.session_state.trip_code = None
            st.rerun()

    st.markdown("---")

    # ── 即時匯率 ──
    st.markdown("#### 🔄 載入即時匯率")
    st.caption("資料來源：open.er-api.com（免費，無需帳號）")
    col_fetch1, col_fetch2 = st.columns([2,1])
    with col_fetch1:
        if st.button("🌐 一鍵載入今日即時匯率", use_container_width=True):
            with st.spinner("正在連線取得最新匯率..."):
                try:
                    resp = requests.get("https://open.er-api.com/v6/latest/TWD", timeout=5)
                    resp.raise_for_status()
                    fx = resp.json().get("rates", {})
                    # 1 TWD = fx[X] 個外幣 → 1 外幣 = 1/fx[X] TWD
                    live_data = dm.load_data(trip_code)
                    if "JPY" in fx and fx["JPY"] > 0:
                        live_data["exchange_rates"]["JPY"] = round(1 / fx["JPY"], 5)
                    if "USD" in fx and fx["USD"] > 0:
                        live_data["exchange_rates"]["USD"] = round(1 / fx["USD"], 4)
                    if "EUR" in fx and fx["EUR"] > 0:
                        live_data["exchange_rates"]["EUR"] = round(1 / fx["EUR"], 4)
                    if "KRW" in fx and fx["KRW"] > 0:
                        live_data["exchange_rates"]["KRW"] = round(1 / fx["KRW"], 6)
                    dm.save_data(live_data, user_key=trip_code)
                    r = live_data["exchange_rates"]
                    st.success(
                        f"✅ 即時匯率已更新！\n\n"
                        f"JPY: {r['JPY']:.4f} | USD: {r['USD']:.2f} | "
                        f"EUR: {r['EUR']:.2f} | KRW: {r['KRW']:.5f}"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 無法取得即時匯率，請確認網路連線。錯誤：{e}")

    st.markdown("---")
    st.markdown("#### ⚠️ 危險區域")
    with st.expander("🗑️ 清除所有資料（不可恢復！）"):
        st.warning("這個操作將會永久刪除所有行程和記帳資料，無法恢復！")
        if st.button("🗑️ 確認清除所有資料", type="secondary", use_container_width=True):
            from data_manager import DEFAULT_DATA
            dm.save_data(DEFAULT_DATA, user_key=trip_code)
            st.success("所有資料已清除！")
            st.rerun()
