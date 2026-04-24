import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="F1 Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# # CSS를 활용하여 숨기기 : 
# hide_streamlit_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             footer {visibility: hidden;}
#             header {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# ── CSS 스타일 (F1 브랜드 컬러) ──────────────────────────────
st.markdown("""
<style>
    /* F1 브랜드 컬러 */
    :root {
        --f1-red: #E10600;
        --f1-dark: #15151E;
        --f1-white: #FFFFFF;
    }

    /* 배경색 */
    .stApp {
        background-color: #15151E;
        color: white;
    }
    /* 리스트 라벨 색상 변경 */
    .stSelectbox label p{
        color: #FFFFFF !important;
    }
    
    /* 상단 바 deploy 버튼 제거 */
    .stAppDeployButton {
        visibility: hidden;
    }
    [data-testid="stSidebarHeader"] button{
        filter: brightness(200%);
        visibility: visible !important;
    }        
    
    /* 어두운 텍스트들 밝게 수정 */
    [data-testid="stMarkdownContainer"] > p{
        color: #cacaca;
        transition: all 0.2s ease 0s;
    }  
    [data-testid="stMarkdownContainer"] > p:hover{
        color: #FFFFFF;
    }
    [data-testid="stCaptionContainer"] {
        color: #dddddd;
    }
    /* 상단바 크기, 색상 조절 */
    .stAppHeader {
        background-color: #7D2020;
        height: 1.75rem;
        min-height: 1.75rem;
        transition: all 0.2s ease 0s; 
    }
    .stAppHeader:hover {
        background-color: #5A1717;
    }
            
    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #1E1E2E;
    }
    /* 헤더 */
    .f1-header {
        background: linear-gradient(135deg, #E10600, #FF4444);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
    }

    /* 카드 스타일 */
    .f1-card {
        background: #1E1E2E;
        border: 1px solid #2E2E3E;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s;
    }

    .f1-card:hover {
        transform: translateY(-2px);
        border-color: #E10600;
    }
    /* 드라이버 카드 */
    .driver-card {
        background: linear-gradient(145deg, #1E1E2E, #2E2E3E);
        border-left: 4px solid #E10600;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        transition: all 0.2s ease 0s;
        --shadow-ox: 0px;
        --shadow-oy: 0px;
        --shadow-blur: 0px;
        --shadow-color: #000000;
        box-shadow: var(--shadow-ox) var(--shadow-oy) var(--shadow-blur) var(--shadow-color);
    }
    .driver-card:hover{
        border-left-width: 12px;
        filter: brightness(110%);
        --shadow-blur: 10px;
    }

    /* 배지 */
    .position-badge {
        background: #E10600;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }

    /* 섹션 제목 */
    h1, h2, h3 {
        color: white !important;
    }

    .section-title {
        color: #E10600;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    /* 메트릭 카드 */
    [data-testid="metric-container"] {
        background: #1E1E2E;
        border: 1px solid #2E2E3E;
        border-radius: 10px;
        padding: 10px;
    }
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1E1E2E;
        border-radius: 8px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888;
        padding: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E10600 !important;
        color: white !important;
        border-radius: 6px;
    }

    /* 다음 레이스 배너 */
    .next-race-banner {
        background: linear-gradient(135deg, #E10600 0%, #8B0000 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 20px;
    }
    .next-race-banner:hover {
        filter: brightness(130%);
    }
    /* 다음 레이스 배너 - 내부 유튜브 비디오 임베드 */
    .video-wrapper {
        position: relative;
        height: 0px;
        opacity: 0;
        transition: all 0.5s ease 0s;    
        justify-content: center;
        width: 100%;
        height: 0px;
        border: none;
    }
    /* 레이스 배너에 마우스 올릴 경우 */
    .next-race-banner:hover .video-wrapper {
        margin-top: 20px;
        height:480px;
        opacity: 1;
    }
    /* 데이터프레임에 마우스 올리면 나타나는 UI 지우기. 사용시 주석 지울 것 */
    [data-testid="stElementToolbar"] {
        visibility: hidden !important;        
    }
    
    /* 테이블 */
    .stDataFrame {
        background: #1E1E2E !important;
    }
</style>
""", unsafe_allow_html=True)


# ── 데이터 (Ergast API 또는 하드코딩) ────────────────────────

@st.cache_data(ttl=3600)
def get_driver_standings():
    """Ergast API에서 2026 드라이버 순위 가져오기"""
    try:
        url = "https://ergast.com/api/f1/currenta/driverStandings.json"
        res = requests.get(url, timeout=5)
        data = res.json()
        standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
        rows = []
        for s in standings:
            rows.append({
                "순위": int(s["position"]),
                "드라이버": s["Driver"]["givenName"] + " " + s["Driver"]["familyName"],
                "국적": s["Driver"]["nationality"],
                "팀": s["Constructors"][0]["name"],
                "포인트": int(s["points"]),
                "승수": int(s["wins"]),
            })
        return pd.DataFrame(rows)
    except Exception:
        # API 실패 시 샘플 데이터
        return pd.DataFrame([
            {"순위": 1, "드라이버": "Max Verstappen", "국적": "Dutch", "팀": "Red Bull Racing", "포인트": 77, "승수": 3},
            {"순위": 2, "드라이버": "Lando Norris", "국적": "British", "팀": "McLaren", "포인트": 62, "승수": 0},
            {"순위": 3, "드라이버": "Carlos Sainz", "국적": "Spanish", "팀": "Ferrari", "포인트": 59, "승수": 1},
            {"순위": 4, "드라이버": "Charles Leclerc", "국적": "Monégasque", "팀": "Ferrari", "포인트": 45, "승수": 0},
            {"순위": 5, "드라이버": "George Russell", "국적": "British", "팀": "Mercedes", "포인트": 37, "승수": 0},
            {"순위": 6, "드라이버": "Oscar Piastri", "국적": "Australian", "팀": "McLaren", "포인트": 32, "승수": 0},
            {"순위": 7, "드라이버": "Fernando Alonso", "국적": "Spanish", "팀": "Aston Martin", "포인트": 24, "승수": 0},
            {"순위": 8, "드라이버": "Lewis Hamilton", "국적": "British", "팀": "Ferrari", "포인트": 19, "승수": 0},
            {"순위": 9, "드라이버": "Lance Stroll", "국적": "Canadian", "팀": "Aston Martin", "포인트": 9, "승수": 0},
            {"순위": 10, "드라이버": "Nico Hulkenberg", "국적": "German", "팀": "Haas F1 Team", "포인트": 6, "승수": 0},
        ])


@st.cache_data(ttl=3600)
def get_constructor_standings():
    try:
        url = "https://ergast.com/api/f1/current/constructorStandings.json"
        res = requests.get(url, timeout=5)
        data = res.json()
        standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"]
        rows = []
        for s in standings:
            rows.append({
                "순위": int(s["position"]),
                "팀": s["Constructor"]["name"],
                "포인트": int(s["points"]),
                "승수": int(s["wins"]),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame([
            {"순위": 1, "팀": "Red Bull Racing", "포인트": 110, "승수": 3},
            {"순위": 2, "팀": "Ferrari", "포인트": 104, "승수": 1},
            {"순위": 3, "팀": "McLaren", "포인트": 94, "승수": 0},
            {"순위": 4, "팀": "Mercedes", "포인트": 37, "승수": 0},
            {"순위": 5, "팀": "Aston Martin", "포인트": 33, "승수": 0},
        ])


# 2026 시즌 레이스 일정 (샘플)
RACE_SCHEDULE = [
    {"라운드": 1, "그랑프리": "🇦🇺 호주", "서킷": "Albert Park", "날짜": "2026-03-13", "상태": "완료"},
    {"라운드": 2, "그랑프리": "🇨🇳 중국", "서킷": "Shanghai", "날짜": "2026-03-20", "상태": "완료"},
    {"라운드": 3, "그랑프리": "🇯🇵 일본", "서킷": "Suzuka", "날짜": "2026-03-27", "상태": "완료"},
    {"라운드": 4, "그랑프리": "🇺🇸 마이애미", "서킷": "Miami International", "날짜": "2026-05-01", "상태": "다음 레이스 🔴"},
    {"라운드": 5, "그랑프리": "🇨🇦 캐나다", "서킷": "Circuit Gilles Villeneuve", "날짜": "2026-05-22", "상태": "예정"},
    {"라운드": 6, "그랑프리": "🇲🇨 모나코", "서킷": "Circuit de Monaco", "날짜": "2026-06-05", "상태": "예정"},
    {"라운드": 7, "그랑프리": "🇪🇸 스페인", "서킷": "Circuit de Barcelona", "날짜": "2026-06-19", "상태": "예정"},
    {"라운드": 8, "그랑프리": "🇦🇹 오스트리아", "서킷": "Red Bull Ring", "날짜": "2026-06-26", "상태": "예정"},
    {"라운드": 9, "그랑프리": "🇬🇧 영국", "서킷": "Silverstone", "날짜": "2026-07-03", "상태": "예정"},
    {"라운드": 10, "그랑프리": "🇭🇺 헝가리", "서킷": "Hungaroring", "날짜": "2026-07-24", "상태": "예정"},
]

# 팀 컬러
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#358C75",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "Haas F1 Team": "#B6BABD",
    "Kick Sauber": "#52E252",
    "RB": "#6692FF",
}


# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px;'>
        <span " style='font-size:48px'>🏎️</span>
        <h2 style='color:#E10600; margin:0;'>F1 Dashboard</h2>
        <p style='color:#888; font-size:12px;'>2026 시즌</p>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.selectbox(
        "📍페이지 선택",
        ["🏠 홈", "🏆 드라이버 순위", "🏁 컨스트럭터 순위", "📅 레이스 일정", "📊 통계 분석"]
    )

    st.markdown("---")
    st.markdown("### 🔴 다음 레이스")
    st.markdown("""
    <div style='background:#E10600; border-radius:8px; padding:12px; text-align:center;'>
        <div style='font-size:24px;'>🇺🇸</div>
        <div style='font-weight:bold; font-size:16px;'>Miami GP</div>
        <div style='font-size:12px; color:#FFD0D0;'>2026년 5월 1일</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Data: Ergast Motor Racing API")


# ── 메인 컨텐츠 ─────────────────────────────────────────────

# 🏠 홈
if page == "🏠 홈":
    # 헤더
    st.markdown("""
    <div class='f1-header'>
        <span style='font-size:48px;'>🏎️</span>
        <div>
            <h1 style='margin:0; color:white; font-size:32px;'>FORMULA 1</h1>
            <p style='margin:0; color:#FFD0D0; font-size:14px;'>2026 월드 챔피언십</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 다음 레이스 배너
    st.markdown("""
    <div class='next-race-banner'>
        <p style='color:#FFD0D0; font-size:12px; letter-spacing:3px; margin:0;'>NEXT RACE</p>
        <h2 style='color:white; font-size:28px; margin:8px 0;'>🇺🇸 MIAMI GRAND PRIX</h2>
        <p style='color:#FFD0D0; font-size:16px; margin:0;'>Miami International Autodrome · 2026년 5월 1-3일</p>
        <iframe class="video-wrapper" src="https://www.youtube.com/embed/C3pAE40Fgc0?si=vX-VxgVNa5rRNYfH" allow="autoplay;"></iframe>
    </div>
    """, unsafe_allow_html=True)

    # 주요 지표
    driver_df = get_driver_standings()
    constructor_df = get_constructor_standings()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 드라이버 선두", driver_df.iloc[0]["드라이버"].split()[-1], f"{driver_df.iloc[0]['포인트']}pts")
    with col2:
        st.metric("🏁 컨스트럭터 선두", constructor_df.iloc[0]["팀"], f"{constructor_df.iloc[0]['포인트']}pts")
    with col3:
        gap = driver_df.iloc[0]["포인트"] - driver_df.iloc[1]["포인트"]
        st.metric("📊 1-2위 격차", f"{gap} pts", "")
    with col4:
        st.metric("🔢 완료된 레이스", "3 / 24", "라운드")

    st.markdown("---")

    # 상위 5명 드라이버
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("### 🏆 드라이버 TOP 5")
        top5 = driver_df.head(5)
        for _, row in top5.iterrows():
            color = TEAM_COLORS.get(row["팀"], "#888")
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][row["순위"] - 1]
            st.markdown(f"""
            <div class='driver-card' style='border-left-color:{color}; --shadow-color:{color};'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='font-size:20px; margin-right:8px;'>{medal}</span>
                        <strong style='font-size:16px;'>{row['드라이버']}</strong>
                        <span style='color:#888; font-size:13px; margin-left:8px;'>{row['팀']}</span>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:{color}; font-size:20px; font-weight:bold;'>{row['포인트']}</div>
                        <div style='color:#888; font-size:11px;'>PTS</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown("### 📊 포인트 차트")
        fig = px.bar(
            top5,
            x="드라이버",
            y="포인트",
            color="팀",
            color_discrete_map=TEAM_COLORS,
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickangle=-30),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)


# 🏆 드라이버 순위
elif page == "🏆 드라이버 순위":
    st.markdown("## 🏆 2026 드라이버 챔피언십")
    df = get_driver_standings()

    # 검색창을 선택하면 필터창을 지우고, 반대면 반대로 만들기. on_change 속성에 콜백함수로 넣음
    def dr_change_driver():
        st.session_state.dr_search_team = ""
    def dr_change_team():
        st.session_state.dr_search_driver = ""

    # 검색 & 필터
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 드라이버 검색", key="dr_search_driver", on_change=dr_change_driver, placeholder="이름을 입력하세요...", )
    with col2:
        team_filter = st.selectbox("팀 필터", ["전체"] + sorted(df["팀"].unique().tolist()), key="dr_search_team", on_change=dr_change_team)
    if search:
        df = df[df["드라이버"].str.contains(search, case=False)]
    if team_filter != "전체":
        df = df[df["팀"] == team_filter]
    # 테이블
    st.dataframe(
        df.style.background_gradient(subset=["포인트"], cmap="Reds"),
        use_container_width=True,
        hide_index=True,
    )

    # 포인트 시각화
    st.markdown("### 📊 포인트 분포")
    fig = px.bar(
        df,
        x="드라이버",
        y="포인트",
        color="팀",
        color_discrete_map=TEAM_COLORS,
        template="plotly_dark",
        text="포인트",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig, use_container_width=True)


# 🏁 컨스트럭터 순위
elif page == "🏁 컨스트럭터 순위":
    st.markdown("## 🏁 2026 컨스트럭터 챔피언십")
    df = get_constructor_standings()

    st.dataframe(
        df.style.background_gradient(subset=["포인트"], cmap="Reds"),
        use_container_width=True,
        hide_index=True,
    )

    # 파이 차트
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🍕 포인트 점유율")
        fig = px.pie(
            df.head(8),
            names="팀",
            values="포인트",
            color="팀",
            color_discrete_map=TEAM_COLORS,
            template="plotly_dark",
            hole=0.4,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📊 팀별 포인트")
        fig = px.bar(
            df,
            x="포인트",
            y="팀",
            color="팀",
            color_discrete_map=TEAM_COLORS,
            orientation="h",
            template="plotly_dark",
            text="포인트",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)


# 📅 레이스 일정
elif page == "📅 레이스 일정":
    st.markdown("## 📅 2026 레이스 일정")

    schedule_df = pd.DataFrame(RACE_SCHEDULE)

    for _, row in schedule_df.iterrows():
        is_next = row["상태"] == "다음 레이스 🔴"
        is_done = row["상태"] == "완료"

        border = "#E10600" if is_next else ("#555" if is_done else "#2E2E3E")
        bg = "rgba(225,6,0,0.1)" if is_next else "rgba(30,30,46,0.8)"

        col1, col2, col3, col4 = st.columns([1, 3, 3, 2])
        with col1:
            st.markdown(f"<div style='color:#888; text-align:center; padding-top:8px;'>R{row['라운드']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-weight:bold; font-size:16px; padding-top:8px;'>{row['그랑프리']}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='color:#888; padding-top:8px;'>🏟️ {row['서킷']}</div>", unsafe_allow_html=True)
        with col4:
            color = "#E10600" if is_next else ("#4CAF50" if is_done else "#888")
            st.markdown(f"<div style='color:{color}; padding-top:8px; text-align:right;'>{row['상태']}</div>", unsafe_allow_html=True)

        if is_next:
            st.info(f"📅 {row['날짜']} — 다음 레이스입니다!")
        st.markdown("---")


# 📊 통계 분석
elif page == "📊 통계 분석":
    st.markdown("## 📊 2026 시즌 통계 분석")

    driver_df = get_driver_standings()
    constructor_df = get_constructor_standings()

    tab1, tab2 = st.tabs(["드라이버 분석", "팀 분석"])

    with tab1:
        st.markdown("### 포인트 vs 승수 산점도")
        fig = px.scatter(
            driver_df,
            x="포인트",
            y="승수",
            color="팀",
            size="포인트",
            hover_name="드라이버",
            color_discrete_map=TEAM_COLORS,
            template="plotly_dark"
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(30,30,46,0.5)")
        fig.update_traces(textposition="top center", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### 팀 포인트 비교")
        fig = go.Figure(data=[
            go.Bar(
                name="포인트",
                x=constructor_df["팀"],
                y=constructor_df["포인트"],
                marker_color=[TEAM_COLORS.get(t, "#888") for t in constructor_df["팀"]],
            )
        ])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,30,46,0.5)",
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)