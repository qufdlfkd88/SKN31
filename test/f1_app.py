import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import pymysql
import sqlalchemy # 재원 추가
from datetime import datetime

# ── DB 설정 ─────────────────────────────────────────────

@st.cache_resource
def get_connection():
    return pymysql.connect(
        host="192.168.0.51",      # ← DB 주소
        user="teamf1",           # ← 계정
        password="비밀번호",    # ← 비번
        database="f1db",       # ← DB 이름
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# ── 페이지 설정 ─────────────────────────────────────────────
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
            
                
    /*
    by. 김동민 
    */
    
    .legendtext{
        fill: #FFFFFF !important;
        transition: all 0.2s ease 0s;
        --legendtext-g-radius: 0px;
        box-shadow: 0px 0px var(--legendtext-g-radius) #FFFFFF;
    }
    .statSelectBox{
        margin-top: -12px;
    }
</style>
""", unsafe_allow_html=True)


# ── 데이터 (Ergast API 또는 하드코딩) ────────────────────────

# by. 김동민 1--------------------------------------------
# 현재 연도
nowyears = datetime.now().year
# 판다스 표시 숫자 소수 둘째자리에서 절삭, 정수는 전부 절삭
def format_points(val):
    if val == int(val):
        return int(val)
    return round(val, 2)
# 

@st.cache_data(ttl=3600)
# 연도를 주면 드라이버 정보에 대한 데이터 프레임을 반환, api
def get_driver_standings(years = nowyears):
    """Jolpica API에서 드라이버 순위 가져오기 (안전한 파싱 적용)"""
    url = f"https://api.jolpi.ca/ergast/f1/{years}/driverStandings.json"
    
    try:
        res = requests.get(url, timeout=5)

        if res.status_code == 200:
            data = res.json()
            
            # 1. 최상단 리스트가 비어있는지 안전하게 확인
            standings_lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
            
            # 데이터가 아예 없는 연도라면 빈 데이터프레임 반환
            if not standings_lists:
                print(f"경고: {years}년의 순위 데이터가 존재하지 않습니다.")
                return pd.DataFrame() 
            
            standings = standings_lists[0].get("DriverStandings", [])
            rows = []
            
            for s in standings:
                # Driver 정보도 get으로 안전하게 가져오기
                driver = s.get("Driver", {})
                
                # 2. 팀(Constructor) 정보가 비어있을 수 있는 상황 대비
                constructors = s.get("Constructors", [])
                team_name = constructors[0].get("name", "개인/알수없음") if constructors else "개인/알수없음"
                
                rows.append({
                    "순위": int(s.get("position", 0)),
                    "드라이버": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "국적": driver.get("nationality", "Unknown"),
                    "팀": team_name,
                    "포인트": float(s.get("points", 0.0)), # 3. 절반 포인트(0.5) 룰을 위해 float 사용
                    "승수": int(s.get("wins", 0)),
                })
            
            df = pd.DataFrame(rows)
            df['포인트'] = df["포인트"].apply(format_points)
            return df
        else:
            print(f"API 호출 실패 (상태 코드: {res.status_code}). 샘플 데이터를 반환합니다.")
            
    except requests.exceptions.RequestException as e:
        print(f"네트워크 오류 발생: {e}. 샘플 데이터를 반환합니다.")
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
# driver_standings와 마찬가지로 수정
# 연도를 주면 팀 통계를 반환, api
@st.cache_data(ttl=3600)
def get_constructor_standings(years = nowyears):
    
    url = f"https://api.jolpi.ca/ergast/f1/{years}/constructorStandings.json"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
        data = res.json()
        standings_list = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", {})
        if not standings_list:
            return pd.DataFrame([{"순위" : 0, "팀" : "There were no teams in this year", "포인트" : 0, "승수" : 0}])
        standings = standings_list[0].get("ConstructorStandings", {})
        rows = []
        for s in standings:
            constructor = s.get("Constructor", {})
            rows.append({
                "순위": int(s.get("position", 0)),
                "팀": constructor.get("name", 'unknown'),
                "포인트": float(s.get("points", 0)),
                "승수": int(s.get("wins", 0)),
            })
        df = pd.DataFrame(rows)
        df['포인트'] = df["포인트"].apply(format_points)
        return df
    else:
        return pd.DataFrame([
            {"순위": 1, "팀": "Red Bull Racing", "포인트": 110, "승수": 3},
            {"순위": 2, "팀": "Ferrari", "포인트": 104, "승수": 1},
            {"순위": 3, "팀": "McLaren", "포인트": 94, "승수": 0},
            {"순위": 4, "팀": "Mercedes", "포인트": 37, "승수": 0},
            {"순위": 5, "팀": "Aston Martin", "포인트": 33, "승수": 0},
        ])
# 전체 연도의 드라이버/팀 정보, 개별 연도의 드라이버/팀 정보를 csv로 받음
@st.cache_data(ttl=3600)
def get_driver_standings_all():
    df = pd.read_csv("data/driver_standing.csv")
    return df
@st.cache_data(ttl=3600)
def get_constructor_standings_all():
    df = pd.read_csv("data/constructor_standing.csv")
    return df
def get_driver_standings_year(years):
    all_df = get_driver_standings_all()
    return all_df[all_df["연도"]==years]
def get_constructor_standings_year(years):
    all_df = get_constructor_standings_all()
    return all_df[all_df["연도"]==years]

# 여기까지 김동민 작업 1 -----------------------------------



@st.cache_data(ttl=3600)
def get_constructor_standings_from_mysql(year):
    """팀원의 MySQL DB에서 선택한 연도의 최종 순위를 가져오는 함수"""
    try:
        # ✅ 팀원이 준 정보를 아래 형식에 맞춰서 수정해!
        # mysql+pymysql://아이디:비밀번호@아이피주소:포트번호/디비이름
        user = "teamf1"        # 예: root
        password = "1111"
        host = "192.168.0.51"     # 팀원의 PC 또는 서버 IP
        port = "3306"
        database = "f1db"      # 데이터가 들어있는 DB 이름
        
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        engine = sqlalchemy.create_engine(db_url)
        
        # ✅ CSV 버전과 동일하게 3개 테이블을 조인해서 최종전 결과를 가져오는 쿼리야.
        query = f"""
            SELECT 
                cs.position AS '순위',
                c.name AS '팀',
                cs.points AS '포인트',
                cs.wins AS '승수'
            FROM constructor_standings cs
            JOIN constructors c ON cs.constructorId = c.constructorId
            JOIN races r ON cs.raceId = r.raceId
            WHERE r.year = {year}
              AND r.round = (SELECT MAX(round) FROM races WHERE year = {year})
            ORDER BY cs.position ASC
        """
        
        df = pd.read_sql(query, engine)
        
        # 포인트 포맷팅 (0.5점 등 소수점 처리)
        if not df.empty and 'format_points' in globals():
            df['포인트'] = df['포인트'].apply(format_points)
            
        return df
        
    except Exception as e:
        st.error(f"❌ 팀원 DB 연결 실패: {e}")
        return pd.DataFrame()


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
    "Red Bull": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#358C75",
    "Alpine F1 Team": "#FF87BC",
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
    
    # 1. 제목과 드롭다운 배치 (기존 코드 활용)
    col_title, col_select = st.columns([3, 1])
    with col_title:
        st.markdown("## 🏁 컨스트럭터 챔피언십")
    with col_select:
        year_list = list(range(2024, 1949, -1))
        selected_year = st.selectbox("시즌 선택", year_list, label_visibility="collapsed")
    
    # 2. ✅ 팀원의 MySQL DB에서 데이터 불러오기!
    df = get_constructor_standings_from_mysql(selected_year)

    if df.empty:
        st.warning(f"데이터베이스에 {selected_year}년 자료가 없거나 연결이 원활하지 않아.")
    else:
        # 3. 불러온 데이터로 표와 차트 그리기 (기존 Plotly 코드 그대로 사용)
        st.dataframe(
            df.style.background_gradient(subset=["포인트"], cmap="Reds"),
            use_container_width=True,
            hide_index=True,
        )
        
        # 파이 차트와 바 차트 그리기
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
    st.markdown("## 📅 F1 레이스 일정")

    # ─────────────────────────────────────────────────────────
    # 연도별 레이스 일정을 API에서 가져오는 함수
    # @st.cache_data → 같은 연도는 다시 불러오지 않고 저장
    # ─────────────────────────────────────────────────────────
    @st.cache_data(ttl=3600)
    def get_schedule(year):
        """Jolpica API에서 특정 연도의 레이스 일정을 가져옵니다."""
        try:
            url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return pd.DataFrame()

            data = response.json()
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

            if not races:
                return pd.DataFrame()

            rows = []
            for race in races:
                rows.append({
                    "라운드": int(race.get("round", 0)),
                    "그랑프리": race.get("raceName", ""),
                    "나라": race.get("Circuit", {}).get("Location", {}).get("country", ""),
                    "도시": race.get("Circuit", {}).get("Location", {}).get("locality", ""),
                    "서킷": race.get("Circuit", {}).get("circuitName", ""),
                    "날짜": race.get("date", ""),
                })

            return pd.DataFrame(rows)

        except Exception as e:
            print(f"레이스 일정 API 오류: {e}")
            return pd.DataFrame()

    # ─────────────────────────────────────────────────────────
    # 연도 선택 드롭다운 (2026 ~ 1950)
    # list(range(2026, 1949, -1)) → [2026, 2025, 2024, ..., 1950]
    # ─────────────────────────────────────────────────────────
    연도_목록 = list(range(2026, 1949, -1))  # 2026부터 1950까지 숫자 목록 만들기

    선택_연도 = st.selectbox(
        "📅 연도를 선택하세요",
        options=연도_목록,   # 드롭다운에 보여줄 목록
        index=0,             # 기본값: 첫 번째 항목 (2026)
    )

    # ─────────────────────────────────────────────────────────
    # 선택한 연도의 데이터 불러오기
    # ─────────────────────────────────────────────────────────
    with st.spinner(f"⏳ {선택_연도}년 일정을 불러오는 중..."):
        schedule_df = get_schedule(선택_연도)

    # 데이터가 없으면 안내 메시지 표시
    if schedule_df.empty:
        st.warning(f"⚠️ {선택_연도}년 데이터를 불러올 수 없어요. 잠시 후 다시 시도해주세요.")

    else:
        # ─────────────────────────────────────────────────────
        # 오늘 날짜 기준으로 상태 자동 계산
        # ─────────────────────────────────────────────────────
        from datetime import date

        오늘 = date.today()  # 오늘 날짜

        # 각 레이스가 완료됐는지, 다음인지, 예정인지 자동으로 판단
        상태_목록 = []
        다음레이스_찾음 = False  # 다음 레이스를 아직 못 찾은 상태

        for _, row in schedule_df.iterrows():
            레이스날짜 = date.fromisoformat(row["날짜"])  # 문자열 → 날짜로 변환

            if 레이스날짜 < 오늘:
                상태_목록.append("✅ 완료")           # 오늘보다 이전 = 완료
            elif not 다음레이스_찾음:
                상태_목록.append("🔴 다음 레이스")    # 처음 만나는 미래 날짜 = 다음 레이스
                다음레이스_찾음 = True
            else:
                상태_목록.append("🔘 예정")            # 그 이후 = 예정

        schedule_df["상태"] = 상태_목록  # 표에 상태 컬럼 추가

        # ─────────────────────────────────────────────────────
        # 통계 요약 숫자 (상단에 크게 표시)
        # ─────────────────────────────────────────────────────
        전체 = len(schedule_df)
        완료수 = schedule_df["상태"].str.contains("완료").sum()
        예정수 = schedule_df["상태"].str.contains("예정").sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏁 전체 레이스", f"{전체}개")
        with col2:
            st.metric("✅ 완료", f"{완료수}개")
        with col3:
            st.metric("🔘 남은 레이스", f"{예정수}개")

        st.divider()

        # ─────────────────────────────────────────────────────
        # 다음 레이스 강조 배너 (해당 연도에 다음 레이스가 있을 때만 표시)
        # ─────────────────────────────────────────────────────
        다음레이스_df = schedule_df[schedule_df["상태"] == "🔴 다음 레이스"]

        if not 다음레이스_df.empty:
            r = 다음레이스_df.iloc[0]  # 첫 번째 행 꺼내기
            st.markdown(f"""
            <div class='next-race-banner'>
                <p style='color:#FFD0D0; font-size:12px; letter-spacing:3px; margin:0;'>NEXT RACE</p>
                <h2 style='color:white; font-size:26px; margin:8px 0;'>🏎️ {r['그랑프리']}</h2>
                <p style='color:#FFD0D0; font-size:15px; margin:0;'>
                    📍 {r['도시']}, {r['나라']} &nbsp;|&nbsp; 🏟️ {r['서킷']} &nbsp;|&nbsp; 📅 {r['날짜']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.write("")  # 여백

        # ─────────────────────────────────────────────────────
        # 레이스 목록 표 출력
        # ─────────────────────────────────────────────────────
        st.subheader(f"📋 {선택_연도}년 전체 일정")

        # 행마다 색깔을 다르게 칠해주는 함수
        def 색깔_적용(row):
            if "완료" in row["상태"]:
                return ["background-color: #1a3a2a; color: #4CAF50"] * len(row)  # 초록
            elif "다음" in row["상태"]:
                return ["background-color: #3a1a1a; color: #E10600"] * len(row)  # 빨강
            else:
                return ["color: #888888"] * len(row)  # 회색

        # 표 출력 (색깔 적용)
        st.dataframe(
            schedule_df.style.apply(색깔_적용, axis=1),
            use_container_width=True,   # 화면 너비에 꽉 맞게
            hide_index=True,            # 왼쪽 숫자 인덱스 숨기기
            height=560,                 # 표 높이
        )

        st.caption("📌 날짜 기준은 레이스 당일 입니다")


# 📊 통계 분석 by. 김동민
elif page == "📊 통계 분석":
    st.markdown("## 📊 시즌별 통계 분석")

    stat_col1, stat_col2 = st.columns([3, 1])
    stat_years_list = list(range(nowyears, 1949, -1))
    stat_years_list.insert(0, "전체")
    tab1, tab2 = stat_col1.tabs(["드라이버 분석", "팀 분석"])
    stat_years = stat_col2.selectbox("", stat_years_list, index=1, label_visibility="collapsed")
    driver_df = None
    constructor_df = None
    # 연도별 보기와 전체 기간 보기. 
    # 전체기간 보기면 선수 이름 기준, 승점과 포인트를 합쳐서 보여준다
    if stat_years != "전체":
        driver_df = get_driver_standings_year(stat_years)
        constructor_df = get_constructor_standings_year(stat_years)
    else:
        driver_df = get_driver_standings_all()
        constructor_df = get_constructor_standings_all()
        # 이름 기준으로 포인트, 승수는 더하고, 국적과 팀은 마지막 정보 사용.
        stats_df = driver_df.groupby('드라이버')[['포인트', '승수']].sum().reset_index()
        info_df = driver_df.groupby('드라이버')[['순위', '국적', '팀']].last().reset_index()
        driver_df = pd.merge(stats_df, info_df, on='드라이버')

        con_stats_df = constructor_df.groupby('팀')[['포인트', '승수']].sum().reset_index()
        con_info_df = constructor_df.groupby('팀')[['순위']].last().reset_index()
        constructor_df = pd.merge(con_stats_df, con_info_df, on='팀').sort_values(by='포인트', ascending=False)
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

        st.markdown("### 🏆 TOP 10 드라이버")
        top5 = driver_df.sort_values(by='포인트', ascending=False).reset_index().head(10)
        print(top5)
    
        for rank , row in top5.iterrows():
            color = TEAM_COLORS.get(row["팀"], "#888")
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][rank]
            with st.container():
                st.markdown(f"""
                <html><head></head><body>
                <div class='driver-card' style='border-left-color:{color}; --shadow-color:{color};'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:20px; margin-right:8px;'>{medal}</span>
                            <strong style='font-size:16px;'>{row['드라이버']}</strong>
                            <span style='color:#888; font-size:13px; margin-left:8px;'>{row['팀']}</span>
                        </div>
                        <div style='text-align:right;position:absolute; right: 20%;'>
                            <div style='color:{color}; font-size:20px; font-weight:bold;'>{row['승수']}</div>
                            <div style='color:#888; font-size:11px;'>WINS</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='color:{color}; font-size:20px; font-weight:bold;'>{row['포인트']}</div>
                            <div style='color:#888; font-size:11px;'>PTS</div>
                        </div>
                    </div>
                </div>
                </body></html>
                """, unsafe_allow_html=True)

            

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

        st.markdown("### 🏆 TOP 10 팀")
        top5 = constructor_df.sort_values(by='포인트', ascending=False).reset_index().head(10)
        print(top5)
    
        for rank , row in top5.iterrows():
            color = TEAM_COLORS.get(row["팀"], "#888")
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][rank]
            with st.container():
                st.markdown(f"""
                <html><head></head><body>
                <div class='driver-card' style='border-left-color:{color}; --shadow-color:{color};'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:20px; margin-right:8px;'>{medal}</span>
                            <strong style='font-size:16px;'>{row['팀']}</strong>
                        </div>
                        <div style='text-align:right;position:absolute; right: 20%;'>
                            <div style='color:{color}; font-size:20px; font-weight:bold;'>{row['승수']}</div>
                            <div style='color:#888; font-size:11px;'>WINS</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='color:{color}; font-size:20px; font-weight:bold;'>{row['포인트']}</div>
                            <div style='color:#888; font-size:11px;'>PTS</div>
                        </div>
                    </div>
                </div>
                </body></html>
                """, unsafe_allow_html=True)