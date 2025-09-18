import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

st.set_page_config(page_title="지출 통계", layout="wide")
st.title("📊 월별 지출 통계")

# --- [수정] 한글 폰트 설정 (디버깅 코드 추가) ---
st.subheader("⚠️ 폰트 경로 디버깅")

# 1. 현재 파일의 디렉토리 경로
try:
    current_dir = os.path.dirname(__file__)
    st.write(f"1. 스크립트가 실행 중인 폴더: `{current_dir}`")

    # 2. 폰트 파일의 전체 경로
    font_path = os.path.join(current_dir, 'NanumGothic.ttf')
    st.write(f"2. 코드가 찾으려는 폰트 파일의 전체 경로: `{font_path}`")

    # 3. 파일 존재 여부 확인
    font_exists = os.path.exists(font_path)
    st.write(f"3. 위 경로에 파일이 실제로 존재하나요?: **{font_exists}**")

    if font_exists:
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
        plt.rcParams['axes.unicode_minus'] = False
        st.success("폰트 파일을 성공적으로 로드했습니다. 이제 차트가 정상적으로 보여야 합니다.")
    else:
        st.error(
            "폰트 파일을 찾을 수 없습니다! 위 '2번 경로'에 'NanumGothic.ttf' 파일이 있는지, 파일 이름에 오타가 없는지 확인해주세요."
        )
except Exception as e:
    st.error(f"스크립트 경로를 찾는 중 에러 발생: {e}")
    st.info("Streamlit을 로컬에서 실행할 때 `__file__` 관련 에러가 발생할 수 있습니다. 폰트 경로를 직접 지정해보세요. 예: `font_path = 'pages/NanumGothic.ttf'`")

st.divider()

# --- Supabase 연결 ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = ["강나윤", "김채린"]

# --- 데이터 불러오기 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
        df['month'] = df['created_at'].dt.strftime('%Y년 %m월')

        col1, col2 = st.columns(2)
        
        unique_months = sorted(df['month'].unique(), reverse=True)
        selected_month = col1.selectbox("분석할 월을 선택하세요:", unique_months)
        selected_user = col2.selectbox("누구의 통계를 볼까요?:", USERS)

        df_month_filtered = df[df['month'] == selected_month]
        df_selected = df_month_filtered[df_month_filtered['user_name'] == selected_user]
        st.subheader(f"'{selected_month}' {selected_user}님 지출 분석")

        if not df_selected.empty:
            total_spent = df_selected['amount'].sum()
            avg_spent = df_selected['amount'].mean()
            expense_count = len(df_selected)

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("총 지출액", f"${total_spent:,.0f} ")
            metric_col2.metric("평균 지출액", f"${avg_spent:,.0f} ")
            metric_col3.metric("총 지출 건수", f"{expense_count} 건")
            st.divider()

            category_summary = df_selected.groupby('description')['amount'].sum().sort_values(ascending=False)
            
            chart_col, data_col = st.columns([0.6, 0.4])
            with chart_col:
                st.write("#### 지출 비율 (원형 차트)")
                if not category_summary.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
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