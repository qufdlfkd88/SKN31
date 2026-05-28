import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="호텔 관리 시스템",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="metric-container"] {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 16px;
}
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
.stButton > button { border-radius: 8px; font-family: 'Noto Sans KR', sans-serif; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 & 모델 ────────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("hotel_bookings.csv")

@st.cache_resource
def train_model(_df):
    features = [
        'lead_time', 'stays_in_weekend_nights', 'stays_in_week_nights',
        'adults', 'children', 'babies', 'previous_cancellations',
        'previous_bookings_not_canceled', 'booking_changes',
        'days_in_waiting_list', 'adr', 'required_car_parking_spaces',
        'total_of_special_requests', 'is_repeated_guest',
    ]
    cat_features = ['hotel', 'meal', 'market_segment', 'distribution_channel',
                    'reserved_room_type', 'deposit_type', 'customer_type']
    df_model = _df.copy()
    encoders = {}
    for col in cat_features:
        le = LabelEncoder()
        df_model[col] = le.fit_transform(df_model[col].astype(str))
        encoders[col] = le
    X = df_model[features + cat_features].fillna(0)
    y = df_model['is_canceled']
    model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X, y)
    return model, encoders, features, cat_features

@st.cache_data
def get_cancel_probabilities(_model, df, features, cat_features, _encoders):
    df_enc = df.copy()
    for col in cat_features:
        le = _encoders[col]
        df_enc[col] = df_enc[col].astype(str).apply(
            lambda x: le.transform([x])[0] if x in le.classes_ else 0
        )
    X = df_enc[features + cat_features].fillna(0)
    return _model.predict_proba(X)[:, 1]

# ── 세션 초기화 ──────────────────────────────────────────────────────
def init_session():
    if 'bookings' not in st.session_state:
        df = load_data()
        recent = df[df['reservation_status'] != 'Canceled'].tail(200).copy().reset_index(drop=True)
        recent['booking_id'] = ['BK' + str(10000 + i) for i in range(len(recent))]
        st.session_state.bookings = recent
    if 'model_trained' not in st.session_state:
        df = load_data()
        model, encoders, feats, cat_feats = train_model(df)
        st.session_state.model = model
        st.session_state.encoders = encoders
        st.session_state.features = feats
        st.session_state.cat_features = cat_feats
        st.session_state.model_trained = True
    if 'hotel_capacity' not in st.session_state:
        st.session_state.hotel_capacity = {'Resort Hotel': 120, 'City Hotel': 150}

init_session()

def get_probs(df=None):
    if df is None:
        df = st.session_state.bookings
    return get_cancel_probabilities(
        st.session_state.model, df,
        st.session_state.features, st.session_state.cat_features,
        st.session_state.encoders
    )

def risk_label(p):
    if p >= 0.6:   return "🔴 고위험"
    elif p >= 0.35: return "🟡 주의"
    else:           return "🟢 안전"

# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏨 호텔 관리 시스템")
    st.markdown("---")
    page = st.radio("메뉴", ["📋 예약 현황 대시보드", "➕ 예약 추가", "📊 오버부킹 분석"],
                    label_visibility="collapsed")
    st.markdown("---")
    probs_sb = get_probs()
    st.markdown(f"**총 예약 건수:** {len(st.session_state.bookings):,}건")
    st.markdown(f"**⚠️ 고위험 예약:** {(probs_sb >= 0.6).sum()}건")

# ════════════════════════════════════════════════════════════════════
# 페이지 1 — 예약 현황 대시보드
# ════════════════════════════════════════════════════════════════════
if page == "📋 예약 현황 대시보드":
    st.title("📋 예약 현황 대시보드")

    df = st.session_state.bookings.copy()
    probs = get_probs(df)
    df['취소확률'] = (probs * 100).round(1)
    df['위험도'] = [risk_label(p) for p in probs]

    total = len(df)
    high_risk = (probs >= 0.6).sum()
    med_risk  = ((probs >= 0.35) & (probs < 0.6)).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 예약", f"{total:,}건")
    c2.metric("🔴 고위험 예약", f"{high_risk}건",
              delta=f"{high_risk/total*100:.1f}%", delta_color="inverse")
    c3.metric("🟡 주의 예약",  f"{med_risk}건",
              delta=f"{med_risk/total*100:.1f}%",  delta_color="inverse")
    c4.metric("평균 객실 단가", f"₩{df['adr'].mean():,.0f}")

    st.markdown("---")

    color_map = {'🔴 고위험': '#ef4444', '🟡 주의': '#f59e0b', '🟢 안전': '#22c55e'}
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("위험도 분포")
        rc = df['위험도'].value_counts().reset_index()
        rc.columns = ['위험도', '건수']
        fig_pie = px.pie(rc, values='건수', names='위험도',
                         color='위험도', color_discrete_map=color_map, hole=0.5)
        fig_pie.update_traces(textinfo='percent+label', showlegend=False)
        fig_pie.update_layout(margin=dict(t=20,b=20,l=0,r=0), height=260)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("호텔별 예약 현황")
        hr = df.groupby(['hotel','위험도']).size().reset_index(name='건수')
        fig_bar = px.bar(hr, x='hotel', y='건수', color='위험도',
                         color_discrete_map=color_map, barmode='stack',
                         labels={'hotel':'호텔','건수':'예약 건수'})
        fig_bar.update_layout(margin=dict(t=20,b=20,l=0,r=0), height=260,
                               showlegend=True, legend_title_text='')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("예약 목록")

    f1, f2, f3 = st.columns(3)
    hotel_filter = f1.multiselect("호텔", df['hotel'].unique(), default=list(df['hotel'].unique()))
    risk_filter  = f2.multiselect("위험도", ['🔴 고위험','🟡 주의','🟢 안전'],
                                  default=['🔴 고위험','🟡 주의','🟢 안전'])
    search       = f3.text_input("예약 ID 검색", placeholder="BK10000")

    filtered = df[df['hotel'].isin(hotel_filter) & df['위험도'].isin(risk_filter)].copy()
    if search:
        filtered = filtered[filtered['booking_id'].str.contains(search, case=False)]
    filtered['_ord'] = filtered['위험도'].map({'🔴 고위험':0,'🟡 주의':1,'🟢 안전':2})
    filtered = filtered.sort_values('_ord')

    display_cols = ['booking_id','hotel','arrival_date_year','arrival_date_month',
                    'arrival_date_day_of_month','adults','children',
                    'reserved_room_type','meal','adr','deposit_type','취소확률','위험도']
    rename_map = {'booking_id':'예약ID','hotel':'호텔','arrival_date_year':'연도',
                  'arrival_date_month':'월','arrival_date_day_of_month':'일',
                  'adults':'성인','children':'아동','reserved_room_type':'객실타입',
                  'meal':'식사','adr':'단가','deposit_type':'보증금',
                  '취소확률':'취소확률(%)','위험도':'위험도'}

    show_df = filtered[display_cols].rename(columns=rename_map)

    def highlight_risk(row):
        r = row['위험도']
        if r == '🔴 고위험': return ['background-color:#fff1f1']*len(row)
        elif r == '🟡 주의':  return ['background-color:#fffbeb']*len(row)
        return ['']*len(row)

    styled = show_df.style.apply(highlight_risk, axis=1)\
                    .format({'취소확률(%)':'{:.1f}%','단가':'₩{:,.0f}'})
    st.dataframe(styled, use_container_width=True, height=480)
    st.caption(f"총 {len(filtered):,}건 표시 중 (전체 {len(df):,}건)")

    danger_df = filtered[filtered['위험도'] == '🔴 고위험'].head(5)
    if len(danger_df) > 0:
        st.markdown("---")
        st.subheader("⚠️ 즉시 주의 필요한 고위험 예약")
        for _, row in danger_df.iterrows():
            ca, cb, cc, cd = st.columns([2,2,2,1])
            ca.markdown(f"**예약 ID:** `{row['booking_id']}`  \n**호텔:** {row['hotel']}")
            cb.markdown(f"**도착일:** {row['arrival_date_year']}년 {row['arrival_date_month']} {row['arrival_date_day_of_month']}일  \n**객실:** {row['reserved_room_type']}타입")
            cc.markdown(f"**단가:** ₩{row['adr']:,.0f}  \n**보증금:** {row['deposit_type']}")
            cd.markdown(f"<span style='background:#fee2e2;color:#991b1b;border:1px solid #f87171;border-radius:8px;padding:6px 12px;font-weight:700;font-size:15px'>취소 {row['취소확률']:.1f}%</span>", unsafe_allow_html=True)
            st.divider()

# ════════════════════════════════════════════════════════════════════
# 페이지 2 — 예약 추가
# ════════════════════════════════════════════════════════════════════
elif page == "➕ 예약 추가":
    st.title("➕ 예약 추가")
    st.markdown("새 예약 정보를 입력하면 AI가 취소 확률을 실시간으로 예측합니다.")

    MONTHS_KO = {
        'January':'1월','February':'2월','March':'3월','April':'4월',
        'May':'5월','June':'6월','July':'7월','August':'8월',
        'September':'9월','October':'10월','November':'11월','December':'12월'
    }

    with st.form("booking_form"):
        st.subheader("🏨 기본 정보")
        r1c1, r1c2 = st.columns(2)
        hotel         = r1c1.selectbox("호텔", ['City Hotel','Resort Hotel'])
        customer_type = r1c2.selectbox("고객 유형", ['Transient','Contract','Transient-Party','Group'])

        st.subheader("📅 날짜 정보")
        r2c1, r2c2, r2c3 = st.columns(3)
        year  = r2c1.selectbox("연도", [2024,2025,2026])
        month = r2c2.selectbox("도착 월", list(MONTHS_KO.keys()), format_func=lambda x: MONTHS_KO[x])
        day   = r2c3.number_input("도착 일", min_value=1, max_value=31, value=15)

        r3c1, r3c2 = st.columns(2)
        lead_time   = r3c1.number_input("예약 리드타임 (일)", min_value=0, max_value=730, value=30,
                                         help="오늘로부터 도착일까지의 일수")
        days_waiting = r3c2.number_input("대기자 명단 대기일", min_value=0, max_value=500, value=0)

        st.subheader("🛏️ 숙박 정보")
        r4c1, r4c2, r4c3 = st.columns(3)
        weekend_nights = r4c1.number_input("주말 숙박 수", min_value=0, max_value=20, value=1)
        week_nights    = r4c2.number_input("평일 숙박 수", min_value=0, max_value=50, value=2)
        room_type      = r4c3.selectbox("객실 유형", ['A','B','C','D','E','F','G','H'])

        r5c1, r5c2, r5c3 = st.columns(3)
        adults   = r5c1.number_input("성인", min_value=1, max_value=10, value=2)
        children = r5c2.number_input("아동", min_value=0, max_value=10, value=0)
        babies   = r5c3.number_input("영아", min_value=0, max_value=5, value=0)

        st.subheader("💰 요금 & 서비스")
        r6c1, r6c2, r6c3 = st.columns(3)
        adr          = r6c1.number_input("1박 요금 (ADR, ₩)", min_value=0, max_value=5000, value=100)
        meal         = r6c2.selectbox("식사 유형", ['BB','HB','FB','SC','Undefined'],
                                      help="BB=조식, HB=하프보드, FB=풀보드, SC=없음")
        deposit_type = r6c3.selectbox("보증금 유형", ['No Deposit','Non Refund','Refundable'])

        r7c1, r7c2 = st.columns(2)
        market_segment       = r7c1.selectbox("마케팅 채널",
            ['Online TA','Offline TA/TO','Direct','Corporate','Groups','Complementary','Aviation'])
        distribution_channel = r7c2.selectbox("유통 채널",
            ['TA/TO','Direct','Corporate','GDS','Undefined'])

        r8c1, r8c2, r8c3 = st.columns(3)
        special_requests = r8c1.number_input("특별 요청 수", min_value=0, max_value=10, value=0)
        parking          = r8c2.number_input("주차 공간", min_value=0, max_value=5, value=0)
        booking_changes  = r8c3.number_input("예약 변경 횟수", min_value=0, max_value=20, value=0)

        st.subheader("📁 고객 이력")
        r9c1, r9c2, r9c3 = st.columns(3)
        prev_cancellations = r9c1.number_input("이전 취소 횟수", min_value=0, max_value=30, value=0)
        prev_not_canceled  = r9c2.number_input("이전 완료 예약 수", min_value=0, max_value=50, value=0)
        is_repeated        = r9c3.selectbox("재방문 고객", [0,1], format_func=lambda x: "예" if x else "아니오")

        submitted = st.form_submit_button("✅ 예약 추가 및 위험도 분석", type="primary", use_container_width=True)

    if submitted:
        new_row = {
            'hotel': hotel, 'is_canceled': 0, 'lead_time': lead_time,
            'arrival_date_year': year, 'arrival_date_month': month,
            'arrival_date_week_number': 1, 'arrival_date_day_of_month': day,
            'stays_in_weekend_nights': weekend_nights, 'stays_in_week_nights': week_nights,
            'adults': adults, 'children': children, 'babies': babies,
            'meal': meal, 'country': 'KOR',
            'market_segment': market_segment, 'distribution_channel': distribution_channel,
            'is_repeated_guest': is_repeated,
            'previous_cancellations': prev_cancellations,
            'previous_bookings_not_canceled': prev_not_canceled,
            'reserved_room_type': room_type, 'assigned_room_type': room_type,
            'booking_changes': booking_changes, 'deposit_type': deposit_type,
            'agent': 0, 'company': 0, 'days_in_waiting_list': days_waiting,
            'customer_type': customer_type, 'adr': adr,
            'required_car_parking_spaces': parking,
            'total_of_special_requests': special_requests,
            'reservation_status': 'Check-In', 'reservation_status_date': '2024-01-01',
        }

        cancel_prob = get_probs(pd.DataFrame([new_row]))[0]

        if cancel_prob >= 0.6:
            st.error(f"### ⛔ 고위험 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("**취소 위험이 매우 높습니다.** 아래 조치를 고려하세요:\n- 💳 **Non Refund 보증금** 요청\n- 📞 사전 컨펌 연락\n- 📋 대기 예약 우선 확보")
        elif cancel_prob >= 0.35:
            st.warning(f"### ⚠️ 주의 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("취소 가능성이 있습니다. 보증금 조건 확인을 권장합니다.")
        else:
            st.success(f"### ✅ 안전한 예약 — 취소 확률 {cancel_prob*100:.1f}%")
            st.markdown("취소 위험이 낮습니다.")

        factors = []
        if lead_time > 90:            factors.append(f"📅 리드타임 {lead_time}일 (길수록 취소율 ↑)")
        if prev_cancellations > 0:    factors.append(f"🚫 이전 취소 이력 {prev_cancellations}건")
        if deposit_type == 'No Deposit': factors.append("💸 무보증금 예약")
        if market_segment in ['Online TA','Groups']: factors.append(f"🌐 채널 ({market_segment}) — 취소율 높은 채널")
        if days_waiting > 0:          factors.append(f"⏳ 대기 후 예약 ({days_waiting}일)")
        if factors:
            with st.expander("🔍 취소 위험 요인 상세"):
                for f in factors:
                    st.markdown(f"- {f}")

        new_row['booking_id'] = 'BK' + str(10000 + len(st.session_state.bookings))
        st.session_state.bookings = pd.concat(
            [st.session_state.bookings, pd.DataFrame([new_row])], ignore_index=True
        )
        st.balloons()
        st.success(f"✅ 예약 `{new_row['booking_id']}` 이(가) 추가되었습니다!")

# ════════════════════════════════════════════════════════════════════
# 페이지 3 — 오버부킹 분석
# ════════════════════════════════════════════════════════════════════
elif page == "📊 오버부킹 분석":
    st.title("📊 오버부킹 분석")
    st.markdown("취소 확률을 반영한 **실질 점유율**과 안전한 오버부킹 가능 수를 계산합니다.")

    df = st.session_state.bookings.copy()
    probs = get_probs(df)
    df['cancel_prob']  = probs
    df['expected_show'] = 1 - probs

    st.markdown("---")
    st.subheader("⚙️ 호텔 객실 설정")
    cap_col1, cap_col2 = st.columns(2)
    resort_cap = cap_col1.number_input("🏖️ Resort Hotel 최대 객실 수", min_value=10, max_value=500,
                                        value=st.session_state.hotel_capacity['Resort Hotel'])
    city_cap   = cap_col2.number_input("🏙️ City Hotel 최대 객실 수",   min_value=10, max_value=500,
                                        value=st.session_state.hotel_capacity['City Hotel'])
    st.session_state.hotel_capacity['Resort Hotel'] = resort_cap
    st.session_state.hotel_capacity['City Hotel']   = city_cap

    safety_margin = st.slider("🛡️ 안전 마진 (%)", min_value=0, max_value=30, value=10,
                               help="높을수록 보수적으로 계산합니다.")
    st.markdown("---")

    for hotel_name, capacity in st.session_state.hotel_capacity.items():
        hotel_df = df[df['hotel'] == hotel_name]
        if len(hotel_df) == 0:
            continue

        hotel_probs = hotel_df['cancel_prob']
        total_bookings    = len(hotel_df)
        expected_occupancy = hotel_df['expected_show'].sum()
        expected_cancels   = hotel_probs.sum()
        high_risk_n        = (hotel_probs >= 0.6).sum()
        safe_overbooking   = max(0, int(expected_cancels * (1 - safety_margin / 100)))
        overbooking_limit  = capacity + safe_overbooking
        occupancy_rate     = min(expected_occupancy / capacity * 100, 100)

        st.subheader(f"{'🏖️' if 'Resort' in hotel_name else '🏙️'} {hotel_name}")

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("최대 객실 수",   f"{capacity}개")
        k2.metric("현재 예약 수",   f"{total_bookings}개")
        k3.metric("예상 실입실",    f"{expected_occupancy:.0f}개")
        k4.metric("예상 점유율",    f"{occupancy_rate:.1f}%",
                  delta=f"{occupancy_rate-100:.1f}%" if occupancy_rate > 100 else None,
                  delta_color="inverse")
        k5.metric("오버부킹 가능 수", f"+{safe_overbooking}개", delta="안전 범위")

        gauge_col, detail_col = st.columns([1.2, 1])

        with gauge_col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=occupancy_rate,
                number={'suffix':'%','font':{'size':36}},
                delta={'reference':100,'suffix':'%'},
                title={'text':"예상 점유율",'font':{'size':16}},
                gauge={
                    'axis': {'range':[0,120],'ticksuffix':'%'},
                    'bar':  {'color':'#3b82f6'},
                    'steps':[
                        {'range':[0,60],    'color':'#dcfce7'},
                        {'range':[60,85],   'color':'#fef9c3'},
                        {'range':[85,100],  'color':'#fef3c7'},
                        {'range':[100,120], 'color':'#fee2e2'},
                    ],
                    'threshold':{'line':{'color':'#dc2626','width':3},'thickness':0.75,'value':100}
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=30,b=10,l=20,r=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with detail_col:
            st.markdown("#### 상세 분석")
            rows = [
                ("총 예약",       f"{total_bookings}건"),
                ("예상 취소",     f"{expected_cancels:.0f}건"),
                ("예상 실입실",   f"{expected_occupancy:.0f}명"),
                ("남은 객실",     f"{max(0, capacity-expected_occupancy):.0f}개"),
                ("고위험 예약",   f"{high_risk_n}건"),
                ("안전 마진",     f"{safety_margin}%"),
                ("오버부킹 가능", f"+{safe_overbooking}개"),
                ("오버부킹 상한", f"{overbooking_limit}건"),
            ]
            for label, value in rows:
                cl, cr = st.columns(2)
                cl.markdown(f"<span style='color:#64748b;font-size:13px'>{label}</span>", unsafe_allow_html=True)
                cr.markdown(f"<span style='font-weight:600;font-size:13px'>{value}</span>", unsafe_allow_html=True)

        if total_bookings > overbooking_limit:
            st.error(f"🚨 **오버부킹 초과!** 현재 예약 {total_bookings}건이 상한({overbooking_limit}건)을 초과했습니다.")
        elif total_bookings > capacity:
            st.warning(f"⚠️ **오버부킹 운영 중** — 취소 예상치 반영 시 안전 범위 내 ({total_bookings}/{overbooking_limit}건)")
        elif capacity - total_bookings + safe_overbooking > 0:
            st.success(f"✅ **여유 있음** — 추가 예약 {capacity - total_bookings + safe_overbooking}건 가능 (오버부킹 포함)")
        else:
            st.info("ℹ️ **만실** — 오버부킹 범위 내에서만 추가 가능")

        st.markdown("##### 취소 확률 분포")
        fig_hist = px.histogram(hotel_df, x='cancel_prob', nbins=20,
                                labels={'cancel_prob':'취소 확률','count':'예약 수'},
                                color_discrete_sequence=['#3b82f6'])
        fig_hist.add_vline(x=0.6,  line_dash="dash", line_color="red",
                           annotation_text="고위험 기준 (60%)", annotation_position="top right")
        fig_hist.add_vline(x=0.35, line_dash="dash", line_color="orange",
                           annotation_text="주의 기준 (35%)")
        fig_hist.update_layout(height=200, margin=dict(t=10,b=10,l=0,r=0),
                                bargap=0.05, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("---")

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
        """)
