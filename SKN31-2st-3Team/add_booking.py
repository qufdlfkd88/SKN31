import streamlit as st
import pandas as pd
import numpy as np


MONTHS_KO = {
    'January': '1월', 'February': '2월', 'March': '3월', 'April': '4월',
    'May': '5월', 'June': '6월', 'July': '7월', 'August': '8월',
    'September': '9월', 'October': '10월', 'November': '11월', 'December': '12월'
}


def predict_cancel_prob(row_dict):
    from app import get_cancel_probabilities
    df_single = pd.DataFrame([row_dict])
    probs = get_cancel_probabilities(
        st.session_state.model, df_single,
        st.session_state.features, st.session_state.cat_features,
        st.session_state.encoders
    )
    return probs[0]


def show():
    st.title("➕ 예약 추가")
    st.markdown("새 예약 정보를 입력하면 AI가 취소 확률을 실시간으로 예측합니다.")

    with st.form("booking_form"):
        st.subheader("🏨 기본 정보")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            hotel = st.selectbox("호텔", ['City Hotel', 'Resort Hotel'])
        with r1c2:
            customer_type = st.selectbox("고객 유형", ['Transient', 'Contract', 'Transient-Party', 'Group'])

        st.subheader("📅 날짜 정보")
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            year = st.selectbox("연도", [2024, 2025, 2026])
        with r2c2:
            month = st.selectbox("도착 월", list(MONTHS_KO.keys()), format_func=lambda x: MONTHS_KO[x])
        with r2c3:
            day = st.number_input("도착 일", min_value=1, max_value=31, value=15)

        r3c1, r3c2 = st.columns(2)
        with r3c1:
            lead_time = st.number_input("예약 리드타임 (일)", min_value=0, max_value=730, value=30,
                                         help="오늘로부터 도착일까지의 일수")
        with r3c2:
            days_waiting = st.number_input("대기자 명단 대기일", min_value=0, max_value=500, value=0)

        st.subheader("🛏️ 숙박 정보")
        r4c1, r4c2, r4c3 = st.columns(3)
        with r4c1:
            weekend_nights = st.number_input("주말 숙박 수", min_value=0, max_value=20, value=1)
        with r4c2:
            week_nights = st.number_input("평일 숙박 수", min_value=0, max_value=50, value=2)
        with r4c3:
            room_type = st.selectbox("객실 유형", ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])

        r5c1, r5c2, r5c3 = st.columns(3)
        with r5c1:
            adults = st.number_input("성인", min_value=1, max_value=10, value=2)
        with r5c2:
            children = st.number_input("아동", min_value=0, max_value=10, value=0)
        with r5c3:
            babies = st.number_input("영아", min_value=0, max_value=5, value=0)

        st.subheader("💰 요금 & 서비스")
        r6c1, r6c2, r6c3 = st.columns(3)
        with r6c1:
            adr = st.number_input("1박 요금 (ADR, ₩)", min_value=0, max_value=5000, value=100)
        with r6c2:
            meal = st.selectbox("식사 유형", ['BB', 'HB', 'FB', 'SC', 'Undefined'],
                                 help="BB=조식, HB=하프보드, FB=풀보드, SC=없음")
        with r6c3:
            deposit_type = st.selectbox("보증금 유형", ['No Deposit', 'Non Refund', 'Refundable'])

        r7c1, r7c2 = st.columns(2)
        with r7c1:
            market_segment = st.selectbox("마케팅 채널",
                ['Online TA', 'Offline TA/TO', 'Direct', 'Corporate', 'Groups', 'Complementary', 'Aviation'])
        with r7c2:
            distribution_channel = st.selectbox("유통 채널",
                ['TA/TO', 'Direct', 'Corporate', 'GDS', 'Undefined'])

        r8c1, r8c2, r8c3 = st.columns(3)
        with r8c1:
            special_requests = st.number_input("특별 요청 수", min_value=0, max_value=10, value=0)
        with r8c2:
            parking = st.number_input("주차 공간", min_value=0, max_value=5, value=0)
        with r8c3:
            booking_changes = st.number_input("예약 변경 횟수", min_value=0, max_value=20, value=0)

        st.subheader("📁 고객 이력")
        r9c1, r9c2, r9c3 = st.columns(3)
        with r9c1:
            prev_cancellations = st.number_input("이전 취소 횟수", min_value=0, max_value=30, value=0)
        with r9c2:
            prev_not_canceled = st.number_input("이전 완료 예약 수", min_value=0, max_value=50, value=0)
        with r9c3:
            is_repeated = st.selectbox("재방문 고객", [0, 1], format_func=lambda x: "예" if x else "아니오")

        submitted = st.form_submit_button("✅ 예약 추가 및 위험도 분석", type="primary", use_container_width=True)

    if submitted:
        new_row = {
            'hotel': hotel,
            'is_canceled': 0,
            'lead_time': lead_time,
            'arrival_date_year': year,
            'arrival_date_month': month,
            'arrival_date_week_number': 1,
            'arrival_date_day_of_month': day,
            'stays_in_weekend_nights': weekend_nights,
            'stays_in_week_nights': week_nights,
            'adults': adults,
            'children': children,
            'babies': babies,
            'meal': meal,
            'country': 'KOR',
            'market_segment': market_segment,
            'distribution_channel': distribution_channel,
            'is_repeated_guest': is_repeated,
            'previous_cancellations': prev_cancellations,
            'previous_bookings_not_canceled': prev_not_canceled,
            'reserved_room_type': room_type,
            'assigned_room_type': room_type,
            'booking_changes': booking_changes,
            'deposit_type': deposit_type,
            'agent': 0,
            'company': 0,
            'days_in_waiting_list': days_waiting,
            'customer_type': customer_type,
            'adr': adr,
            'required_car_parking_spaces': parking,
            'total_of_special_requests': special_requests,
            'reservation_status': 'Check-In',
            'reservation_status_date': '2024-01-01',
        }

        # 취소 확률 예측
        cancel_prob = predict_cancel_prob(new_row)

        # 결과 박스
        if cancel_prob >= 0.6:
            st.error(f"### ⛔ 고위험 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("""
**취소 위험이 매우 높습니다.** 아래 조치를 고려하세요:
- 💳 **Non Refund 보증금** 요청
- 📞 사전 컨펌 연락
- 📋 대기 예약 우선 확보
            """)
        elif cancel_prob >= 0.35:
            st.warning(f"### ⚠️ 주의 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("취소 가능성이 있습니다. 보증금 조건 확인을 권장합니다.")
        else:
            st.success(f"### ✅ 안전한 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("취소 위험이 낮습니다.")

        # 주요 위험 요인 표시
        factors = []
        if lead_time > 90:
            factors.append(f"📅 리드타임 {lead_time}일 (길수록 취소율 ↑)")
        if prev_cancellations > 0:
            factors.append(f"🚫 이전 취소 이력 {prev_cancellations}건")
        if deposit_type == 'No Deposit':
            factors.append("💸 무보증금 예약")
        if market_segment in ['Online TA', 'Groups']:
            factors.append(f"🌐 채널 ({market_segment}) — 취소율 높은 채널")
        if days_waiting > 0:
            factors.append(f"⏳ 대기 후 예약 ({days_waiting}일)")

        if factors:
            with st.expander("🔍 취소 위험 요인 상세"):
                for f in factors:
                    st.markdown(f"- {f}")

        # 예약 저장
        new_id = 'BK' + str(10000 + len(st.session_state.bookings))
        new_row['booking_id'] = new_id

        new_df = pd.DataFrame([new_row])
        st.session_state.bookings = pd.concat(
            [st.session_state.bookings, new_df], ignore_index=True
        )

        st.balloons()
        st.success(f"✅ 예약 `{new_id}` 이(가) 추가되었습니다!")
