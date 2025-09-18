import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 한글 폰트 설정 ---
# Streamlit Cloud 배포 시 한글 깨짐 방지를 위해 폰트 파일이 필요할 수 있습니다.
# 일단 로컬에서 테스트하기 위해 컴퓨터에 있는 폰트를 사용합니다.
# Windows: Malgun Gothic, macOS: AppleGothic
try:
    font_path = "c:/Windows/Fonts/malgun.ttf" # Windows 기준
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지
except FileNotFoundError:
    st.warning("한글 폰트 파일을 찾을 수 없어 차트의 한글이 깨질 수 있습니다.")

# --- Supabase 연결 ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="지출 통계", layout="wide")
st.title("📊 월별 지출 통계")

# --- 데이터 불러오기 및 처리 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['month'] = df['created_at'].dt.strftime('%Y년 %m월')

        # --- 월 선택 필터 ---
        unique_months = df['month'].unique()
        selected_month = st.selectbox("분석할 월을 선택하세요:", unique_months)

        # 선택된 월의 데이터만 필터링
        df_selected = df[df['month'] == selected_month]

        if not df_selected.empty:
            # --- 요약 정보 표시 ---
            total_spent = df_selected['amount'].sum()
            avg_spent = df_selected['amount'].mean()
            expense_count = len(df_selected)

            col1, col2, col3 = st.columns(3)
            col1.metric("총 지출액", f"{total_spent:,.0f} 원")
            col2.metric("평균 지출액", f"{avg_spent:,.0f} 원")
            col3.metric("총 지출 건수", f"{expense_count} 건")
            st.divider()

            # --- 카테고리별 통계 ---
            st.subheader(f"'{selected_month}' 카테고리별 지출 분석")
            
            # 카테고리별 합계 계산
            category_summary = df_selected.groupby('description')['amount'].sum().sort_values(ascending=False)
            
            # 바 차트와 데이터 테이블을 나란히 표시
            chart_col, data_col = st.columns([0.6, 0.4])

            with chart_col:
                st.write("#### 지출 비율 (원형 차트)")
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
                ax.axis('equal')  # 원형을 유지
                st.pyplot(fig)
            
            with data_col:
                st.write("#### 상세 데이터")
                st.dataframe(category_summary.reset_index().rename(columns={'description': '카테고리', 'amount': '금액'}))

        else:
            st.info("선택하신 월에는 지출 내역이 없습니다.")
    else:
        st.warning("아직 기록된 지출 내역이 없습니다.")

except Exception as e:
    st.error(f"데이터를 분석하는 중 오류가 발생했습니다: {e}")