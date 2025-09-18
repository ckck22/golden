import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os # 파일 경로를 위해 os 모듈 추가

# --- [수정] 한글 폰트 설정 (앱에 포함된 폰트 사용) ---
# 앱이 어디서 실행되든 동일한 폰트를 사용하게 하여 깨짐 현상을 방지합니다.
# 'NanumGothic.ttf' 파일이 이 파이썬 파일과 같은 위치에 있다고 가정합니다.
font_path = os.path.join(os.path.dirname(__file__), 'NanumGothic.ttf')

# 폰트 파일이 있는지 확인
if os.path.exists(font_path):
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.warning(
        "폰트 파일을 찾을 수 없습니다. 'NanumGothic.ttf' 파일을 현재 폴더에 추가해주세요."
        "차트의 한글이 깨질 수 있습니다."
    )

# --- Supabase 연결 ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = ["강나윤", "김채린"]

st.set_page_config(page_title="지출 통계", layout="wide")
st.title("📊 월별 지출 통계")

# --- 데이터 불러오기 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # 시간대 정보 무시하고 날짜 변환
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
        df['month'] = df['created_at'].dt.strftime('%Y년 %m월')

        # --- 필터링 옵션 ---
        col1, col2 = st.columns(2)
        
        unique_months = sorted(df['month'].unique(), reverse=True)
        selected_month = col1.selectbox("분석할 월을 선택하세요:", unique_months)
        
        # ❗❗ [수정] "전체" 옵션 제거하고 USERS 리스트만 사용 ❗❗
        selected_user = col2.selectbox("누구의 통계를 볼까요?:", USERS)

        # --- 데이터 처리 ---
        # 1. 월 필터링
        df_month_filtered = df[df['month'] == selected_month]
        
        # 2. ❗❗ [수정] 사용자 필터링 로직 간소화 ❗❗
        df_selected = df_month_filtered[df_month_filtered['user_name'] == selected_user]
        st.subheader(f"'{selected_month}' {selected_user}님 지출 분석")

        if not df_selected.empty:
            # --- 요약 정보 표시 ---
            total_spent = df_selected['amount'].sum()
            avg_spent = df_selected['amount'].mean()
            expense_count = len(df_selected)

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("총 지출액", f"${total_spent:,.0f} ")
            metric_col2.metric("평균 지출액", f"${avg_spent:,.0f} ")
            metric_col3.metric("총 지출 건수", f"{expense_count} 건")
            st.divider()

            # --- 카테고리별 통계 ---
            category_summary = df_selected.groupby('description')['amount'].sum().sort_values(ascending=False)
            
            chart_col, data_col = st.columns([0.6, 0.4])
            with chart_col:
                st.write("#### 지출 비율 (원형 차트)")
                if not category_summary.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    # 차트 라벨에 한글이 표시되도록 설정
                    labels = category_summary.index
                    ax.pie(category_summary, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    st.info("표시할 카테고리 데이터가 없습니다.")
            
            with data_col:
                st.write("#### 상세 데이터")
                st.dataframe(category_summary.reset_index().rename(columns={'description': '카테고리', 'amount': '금액'}))

        else:
            st.info("선택하신 조건에 해당하는 지출 내역이 없습니다.")
    else:
        st.warning("아직 기록된 지출 내역이 없습니다.")

except Exception as e:
    st.error(f"데이터를 분석하는 중 오류가 발생했습니다: {e}")