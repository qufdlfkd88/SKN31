import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


def get_probs():
    df_b = st.session_state.bookings
    from app import get_cancel_probabilities
    probs = get_cancel_probabilities(
        st.session_state.model, df_b,
        st.session_state.features, st.session_state.cat_features,
        st.session_state.encoders
    )
    return probs


def show():
    st.title("📊 오버부킹 분석")
    st.markdown("취소 확률을 반영한 **실질 점유율**과 안전한 오버부킹 가능 수를 계산합니다.")

    df = st.session_state.bookings.copy()
    probs = get_probs()
    df['cancel_prob'] = probs
    df['expected_show'] = 1 - probs  # 실제 입실 확률

    # ── 객실 설정 ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ 호텔 객실 설정")

    cap_col1, cap_col2 = st.columns(2)
    with cap_col1:
        resort_cap = st.number_input(
            "🏖️ Resort Hotel 최대 객실 수",
            min_value=10, max_value=500,
            value=st.session_state.hotel_capacity['Resort Hotel']
        )
    with cap_col2:
        city_cap = st.number_input(
            "🏙️ City Hotel 최대 객실 수",
            min_value=10, max_value=500,
            value=st.session_state.hotel_capacity['City Hotel']
        )

    st.session_state.hotel_capacity['Resort Hotel'] = resort_cap
    st.session_state.hotel_capacity['City Hotel'] = city_cap

    safety_margin = st.slider(
        "🛡️ 안전 마진 (%)",
        min_value=0, max_value=30, value=10,
        help="오버부킹 계산 시 적용할 여유율. 높을수록 보수적으로 계산합니다."
    )

    st.markdown("---")

    # ── 호텔별 분석 ───────────────────────────────────────────────
    for hotel_name, capacity in st.session_state.hotel_capacity.items():
        hotel_df = df[df['hotel'] == hotel_name]

        if len(hotel_df) == 0:
            continue

        hotel_probs = hotel_df['cancel_prob']
        hotel_show = hotel_df['expected_show']

        total_bookings = len(hotel_df)
        confirmed_rooms = total_bookings  # 현재 예약 건수 = 점유 중인 방

        # 예상 실입실 수 = Σ(1 - p_cancel)
        expected_occupancy = hotel_show.sum()

        # 고위험 예약 (취소될 가능성 높은 예약들)
        high_risk_n = (hotel_probs >= 0.6).sum()
        high_risk_expected_cancel = hotel_df.loc[hotel_probs >= 0.6, 'cancel_prob'].sum()

        # 오버부킹 가능 수 계산
        # 현재 예상 취소 = Σ p_cancel
        expected_cancels = hotel_probs.sum()
        safe_overbooking = int(expected_cancels * (1 - safety_margin / 100))
        safe_overbooking = max(0, safe_overbooking)

        current_net = total_bookings - expected_cancels
        available_rooms = capacity - current_net
        overbooking_limit = capacity + safe_overbooking

        # 점유율
        occupancy_rate = min(expected_occupancy / capacity * 100, 100)

        st.subheader(f"{'🏖️' if 'Resort' in hotel_name else '🏙️'} {hotel_name}")

        # KPI 행
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("최대 객실 수", f"{capacity}개")
        k2.metric("현재 예약 수", f"{total_bookings}개")
        k3.metric("예상 실입실", f"{expected_occupancy:.0f}개")
        k4.metric(
            "예상 점유율",
            f"{occupancy_rate:.1f}%",
            delta=f"{occupancy_rate-100:.1f}%" if occupancy_rate > 100 else None,
            delta_color="inverse"
        )
        k5.metric(
            "오버부킹 가능 수",
            f"+{safe_overbooking}개",
            delta="안전 범위",
            delta_color="normal"
        )

        # 게이지 차트
        gauge_col, detail_col = st.columns([1.2, 1])

        with gauge_col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=occupancy_rate,
                number={'suffix': '%', 'font': {'size': 36}},
                delta={'reference': 100, 'suffix': '%'},
                title={'text': "예상 점유율", 'font': {'size': 16}},
                gauge={
                    'axis': {'range': [0, 120], 'ticksuffix': '%'},
                    'bar': {'color': '#3b82f6'},
                    'steps': [
                        {'range': [0, 60], 'color': '#dcfce7'},
                        {'range': [60, 85], 'color': '#fef9c3'},
                        {'range': [85, 100], 'color': '#fef3c7'},
                        {'range': [100, 120], 'color': '#fee2e2'},
                    ],
                    'threshold': {
                        'line': {'color': '#dc2626', 'width': 3},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=30, b=10, l=20, r=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with detail_col:
            st.markdown("#### 상세 분석")

            rows = [
                ("총 예약", f"{total_bookings}건"),
                ("예상 취소", f"{expected_cancels:.0f}건"),
                ("예상 실입실", f"{expected_occupancy:.0f}명"),
                ("남은 객실", f"{max(0, capacity - expected_occupancy):.0f}개"),
                ("고위험 예약", f"{high_risk_n}건"),
                ("안전 마진", f"{safety_margin}%"),
                ("오버부킹 가능", f"+{safe_overbooking}개"),
                ("오버부킹 상한", f"{overbooking_limit}건"),
            ]

            for label, value in rows:
                col_l, col_r = st.columns(2)
                col_l.markdown(f"<span style='color:#64748b;font-size:13px'>{label}</span>", unsafe_allow_html=True)
                col_r.markdown(f"<span style='font-weight:600;font-size:13px'>{value}</span>", unsafe_allow_html=True)

        # 오버부킹 상태 경고
        if total_bookings > overbooking_limit:
            st.error(f"🚨 **오버부킹 초과!** 현재 예약 {total_bookings}건이 상한({overbooking_limit}건)을 초과했습니다. 즉시 조치 필요!")
        elif total_bookings > capacity:
            st.warning(f"⚠️ **오버부킹 운영 중** — 취소 예상치 반영 시 안전 범위 내 ({total_bookings}/{overbooking_limit}건)")
        elif available_rooms > 0:
            st.success(f"✅ **여유 있음** — 추가 예약 {max(0, capacity - total_bookings + safe_overbooking)}건 가능 (오버부킹 포함)")
        else:
            st.info("ℹ️ **만실** — 오버부킹 범위 내에서만 추가 가능")

        # 취소 확률 분포 히스토그램
        st.markdown("##### 취소 확률 분포")
        fig_hist = px.histogram(
            hotel_df, x='cancel_prob', nbins=20,
            labels={'cancel_prob': '취소 확률', 'count': '예약 수'},
            color_discrete_sequence=['#3b82f6'],
        )
        fig_hist.add_vline(x=0.6, line_dash="dash", line_color="red",
                           annotation_text="고위험 기준 (60%)", annotation_position="top right")
        fig_hist.add_vline(x=0.35, line_dash="dash", line_color="orange",
                           annotation_text="주의 기준 (35%)")
        fig_hist.update_layout(height=200, margin=dict(t=10, b=10, l=0, r=0),
                                bargap=0.05, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("---")

    # ── 오버부킹 전략 가이드 ──────────────────────────────────────
    with st.expander("📖 오버부킹 전략 가이드"):
        st.markdown("""
| 점유율 | 상태 | 권장 조치 |
|--------|------|-----------|
| < 60% | 🟢 여유 | 공격적 프로모션, 특가 제공 |
| 60~85% | 🟡 양호 | 정상 운영 |
| 85~100% | 🟠 주의 | 오버부킹 소량 허용, 모니터링 강화 |
| 100~110% | 🔴 오버부킹 | 고위험 예약 집중 관리, 대안 호텔 준비 |
| > 110% | 🚨 위험 | 즉시 신규 예약 중단, 고위험 예약 취소 유도 |

**오버부킹 계산식:**  
`안전 오버부킹 수 = Σ(취소확률) × (1 - 안전마진%)`

취소 확률이 높은 예약이 많을수록 더 많은 오버부킹이 가능합니다.
        """)
