import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="호텔 관리 시스템",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f172a;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 2px 0;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.08) !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-family: 'Noto Sans KR', sans-serif;
    font-weight: 500;
}

/* Warning badge */
.warn-badge {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fbbf24;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}
.danger-badge {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #f87171;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}
.safe-badge {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #4ade80;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ── 데이터 & 모델 캐시 ──────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("hotel_bookings.csv")
    return df

@st.cache_resource
def train_model(df):
    features = [
        'lead_time', 'stays_in_weekend_nights', 'stays_in_week_nights',
        'adults', 'children', 'babies', 'previous_cancellations',
        'previous_bookings_not_canceled', 'booking_changes',
        'days_in_waiting_list', 'adr', 'required_car_parking_spaces',
        'total_of_special_requests', 'is_repeated_guest',
    ]
    cat_features = ['hotel', 'meal', 'market_segment', 'distribution_channel',
                    'reserved_room_type', 'deposit_type', 'customer_type']

    df_model = df.copy()
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
    probs = _model.predict_proba(X)[:, 1]
    return probs

# ── 세션 상태 초기화 ────────────────────────────────────────────────
def init_session():
    if 'bookings' not in st.session_state:
        df = load_data()
        # 최근 200개만 초기 데이터로 사용
        recent = df[df['reservation_status'] != 'Canceled'].tail(200).copy()
        recent = recent.reset_index(drop=True)
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
        st.session_state.hotel_capacity = {
            'Resort Hotel': 120,
            'City Hotel': 150,
        }

init_session()

# ── 사이드바 네비게이션 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏨 호텔 관리 시스템")
    st.markdown("---")
    page = st.radio(
        "메뉴",
        ["📋 예약 현황 대시보드", "➕ 예약 추가", "📊 오버부킹 분석"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown(f"**총 예약 건수:** {len(st.session_state.bookings):,}건")

    # 취소 위험 예약 수 계산
    df_b = st.session_state.bookings
    probs = get_cancel_probabilities(
        st.session_state.model, df_b,
        st.session_state.features, st.session_state.cat_features,
        st.session_state.encoders
    )
    high_risk = (probs >= 0.6).sum()
    st.markdown(f"**⚠️ 고위험 예약:** {high_risk}건")

# ── 페이지 라우팅 ───────────────────────────────────────────────────
if page == "📋 예약 현황 대시보드":
    from pages_impl import dashboard
    dashboard.show()
elif page == "➕ 예약 추가":
    from pages_impl import add_booking
    add_booking.show()
elif page == "📊 오버부킹 분석":
    from pages_impl import overbooking
    overbooking.show()
