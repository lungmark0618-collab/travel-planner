import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import data_manager as dm

def render_spending_charts(data, category_colors, categories):
    """渲染分類支出圓餅圖與每日預算堆疊圖"""
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📊 分類支出")
        by_cat = dm.get_expenses_by_category(data)
        if by_cat:
            total_spent = sum(by_cat.values())
            colors = [category_colors.get(cat, "#a0aec0") for cat in by_cat.keys()]
            fig = go.Figure(go.Pie(
                labels=list(by_cat.keys()), 
                values=list(by_cat.values()), 
                hole=.75,
                marker=dict(colors=colors, line=dict(color='#1a2035', width=3)),
                textinfo='none',
                hoverinfo='label+value'
            ))
            fig.add_annotation(
                text=f"總支出 ≈<br>NT${total_spent:,.0f}",
                showarrow=False,
                font=dict(size=16, color="white", family="Inter", weight="bold"),
                x=0.5, y=0.5
            )
            fig.update_layout(
                height=250, 
                margin=dict(t=10,b=10,l=0,r=0), 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # 自定義圖例表格
            legend_table = """
            <style>
                .legend-table { width: 100%; border-collapse: collapse; background: #1a2035; padding: 15px; border-radius: 12px; border: 1px solid #2d3748; }
                .legend-table td { padding: 8px 10px; vertical-align: middle; }
                .cat-name { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }
                .cat-pct { font-size: 1.1rem; font-weight: 800; color: #a0aec0; text-align: right; font-family: monospace; }
                .color-box { width: 14px; height: 14px; border-radius: 3px; display: inline-block; margin-right: 10px; }
            </style>
            <table class='legend-table'>
            """
            items = list(by_cat.items())
            for i in range(0, len(items), 2):
                legend_table += "<tr>"
                cat1, val1 = items[i]
                pct1 = (val1 / total_spent) * 100
                color1 = category_colors.get(cat1, "#a0aec0")
                legend_table += f"<td><div class='color-box' style='background:{color1};'></div><span class='cat-name'>{cat1}</span></td>"
                legend_table += f"<td class='cat-pct'>{pct1:.1f}%</td>"
                
                if i + 1 < len(items):
                    cat2, val2 = items[i+1]
                    pct2 = (val2 / total_spent) * 100
                    color2 = category_colors.get(cat2, "#a0aec0")
                    legend_table += f"<td style='padding-left:20px;'><div class='color-box' style='background:{color2};'></div><span class='cat-name'>{cat2}</span></td>"
                    legend_table += f"<td class='cat-pct'>{pct2:.1f}%</td>"
                else:
                    legend_table += "<td></td><td></td>"
                legend_table += "</tr>"
            legend_table += "</table>"
            st.markdown(legend_table, unsafe_allow_html=True)
        else:
            st.caption("無資料")
            
    with c2:
        st.markdown("#### 📈 每日預算")
        if data["expenses"]:
            df = pd.DataFrame(data["expenses"])
            fig = px.bar(
                df,
                x='date',
                y='amount_twd',
                color='category',
                color_discrete_map=category_colors,
                category_orders={"category": categories},
                labels={'date':'', 'amount_twd':'', 'category': '分類'}
            )
            fig.update_traces(
                marker_line_width=1,
                marker_line_color='#1a2035',
                hovertemplate="<b>%{fullData.name}</b><br>日期: %{x}<br>支出: NT$%{y:,.0f}<extra></extra>"
            )
            fig.update_layout(
                height=250, 
                margin=dict(t=10,b=20,l=0,r=0), 
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(type='category', gridcolor='#2d3748', tickfont=dict(size=12)),
                yaxis=dict(
                    gridcolor='#2d3748', 
                    showticklabels=True, 
                    tickfont=dict(size=12, weight='bold'),
                    tickprefix="NT$"
                ),
                font=dict(family="Inter", color="#a0aec0"),
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.caption("無資料")
