import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def get_probs():
    df_b = st.session_state.bookings
    from app import get_cancel_probabilities
    probs = get_cancel_probabilities(
        st.session_state.model, df_b,
        st.session_state.features, st.session_state.cat_features,
        st.session_state.encoders
    )
    return probs


def risk_label(p):
    if p >= 0.6:
        return "🔴 고위험"
    elif p >= 0.35:
        return "🟡 주의"
    else:
        return "🟢 안전"


def show():
    st.title("📋 예약 현황 대시보드")

    df = st.session_state.bookings.copy()
    probs = get_probs()
    df['취소확률'] = (probs * 100).round(1)
    df['위험도'] = [risk_label(p) for p in probs]

    # ── KPI 카드 ───────────────────────────────────────────────────
    total = len(df)
    high_risk = (probs >= 0.6).sum()
    med_risk = ((probs >= 0.35) & (probs < 0.6)).sum()
    avg_adr = df['adr'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 예약", f"{total:,}건")
    c2.metric("🔴 고위험 예약", f"{high_risk}건", delta=f"{high_risk/total*100:.1f}%", delta_color="inverse")
    c3.metric("🟡 주의 예약", f"{med_risk}건", delta=f"{med_risk/total*100:.1f}%", delta_color="inverse")
    c4.metric("평균 객실 단가", f"₩{avg_adr:,.0f}")

    st.markdown("---")

    # ── 차트 행 ────────────────────────────────────────────────────
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("위험도 분포")
        risk_counts = df['위험도'].value_counts().reset_index()
        risk_counts.columns = ['위험도', '건수']
        color_map = {
            '🔴 고위험': '#ef4444',
            '🟡 주의': '#f59e0b',
            '🟢 안전': '#22c55e',
        }
        fig_pie = px.pie(
            risk_counts, values='건수', names='위험도',
            color='위험도', color_discrete_map=color_map,
            hole=0.5
        )
        fig_pie.update_traces(textinfo='percent+label', showlegend=False)
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=260)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("호텔별 예약 현황")
        hotel_risk = df.groupby(['hotel', '위험도']).size().reset_index(name='건수')
        fig_bar = px.bar(
            hotel_risk, x='hotel', y='건수', color='위험도',
            color_discrete_map=color_map, barmode='stack',
            labels={'hotel': '호텔', '건수': '예약 건수'},
        )
        fig_bar.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=260,
                               showlegend=True, legend_title_text='')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ── 필터 ──────────────────────────────────────────────────────
    st.subheader("예약 목록")
    f1, f2, f3 = st.columns(3)
    with f1:
        hotel_filter = st.multiselect("호텔", df['hotel'].unique(), default=list(df['hotel'].unique()))
    with f2:
        risk_filter = st.multiselect(
            "위험도", ['🔴 고위험', '🟡 주의', '🟢 안전'],
            default=['🔴 고위험', '🟡 주의', '🟢 안전']
        )
    with f3:
        search = st.text_input("예약 ID 검색", placeholder="BK10000")

    filtered = df[df['hotel'].isin(hotel_filter) & df['위험도'].isin(risk_filter)]
    if search:
        filtered = filtered[filtered['booking_id'].str.contains(search, case=False)]

    # 위험 순으로 정렬
    risk_order = {'🔴 고위험': 0, '🟡 주의': 1, '🟢 안전': 2}
    filtered = filtered.copy()
    filtered['_risk_order'] = filtered['위험도'].map(risk_order)
    filtered = filtered.sort_values('_risk_order')

    display_cols = [
        'booking_id', 'hotel', 'arrival_date_year', 'arrival_date_month',
        'arrival_date_day_of_month', 'adults', 'children',
        'reserved_room_type', 'meal', 'adr', 'deposit_type',
        '취소확률', '위험도'
    ]
    rename_map = {
        'booking_id': '예약ID',
        'hotel': '호텔',
        'arrival_date_year': '연도',
        'arrival_date_month': '월',
        'arrival_date_day_of_month': '일',
        'adults': '성인',
        'children': '아동',
        'reserved_room_type': '객실타입',
        'meal': '식사',
        'adr': '단가',
        'deposit_type': '보증금',
        '취소확률': '취소확률(%)',
        '위험도': '위험도',
    }

    show_df = filtered[display_cols].rename(columns=rename_map)

    # 색상 하이라이트 함수
    def highlight_risk(row):
        risk = row['위험도']
        if risk == '🔴 고위험':
            return ['background-color: #fff1f1'] * len(row)
        elif risk == '🟡 주의':
            return ['background-color: #fffbeb'] * len(row)
        else:
            return [''] * len(row)

    styled = show_df.style.apply(highlight_risk, axis=1).format({'취소확률(%)': '{:.1f}%', '단가': '₩{:,.0f}'})

    st.dataframe(styled, use_container_width=True, height=480)

    st.caption(f"총 {len(filtered):,}건 표시 중 (전체 {len(df):,}건)")

    # ── 고위험 예약 상세 경고 ─────────────────────────────────────
    danger_df = filtered[filtered['위험도'] == '🔴 고위험'].head(5)
    if len(danger_df) > 0:
        st.markdown("---")
        st.subheader("⚠️ 즉시 주의 필요한 고위험 예약")
        for _, row in danger_df.iterrows():
            with st.container():
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
                col_a.markdown(f"**예약 ID:** `{row['booking_id']}`  \n**호텔:** {row['hotel']}")
                col_b.markdown(f"**도착일:** {row['arrival_date_year']}년 {row['arrival_date_month']} {row['arrival_date_day_of_month']}일  \n**객실:** {row['reserved_room_type']}타입")
                col_c.markdown(f"**단가:** ₩{row['adr']:,.0f}  \n**보증금:** {row['deposit_type']}")
                col_d.markdown(f"<span style='background:#fee2e2;color:#991b1b;border:1px solid #f87171;border-radius:8px;padding:6px 12px;font-weight:700;font-size:15px'>취소 {row['취소확률']:.1f}%</span>", unsafe_allow_html=True)
                st.divider()
