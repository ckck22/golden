import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

st.set_page_config(page_title="지출 통계", layout="wide")
st.title("📊 월별 지출 통계")

# --- 한글 폰트 설정 (이전과 동일) ---
# ... (폰트 설정 코드는 그대로 둡니다) ...
try:
    font_path = "c:/Windows/Fonts/malgun.ttf"
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    pass # 폰트가 없어도 앱이 멈추지 않도록 함

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
        
        # [수정] 사용자 선택 필터에 '전체' 옵션 추가
        view_option = ["전체"] + USERS
        selected_user = col2.selectbox("누구의 통계를 볼까요?:", view_option)

        # [수정] 필터링 로직 변경
        df_month_filtered = df[df['month'] == selected_month]
        if selected_user == "전체":
            df_selected = df_month_filtered
            st.subheader(f"'{selected_month}' 전체 지출 분석")
        else:
            df_selected = df_month_filtered[df_month_filtered['user_name'] == selected_user]
            st.subheader(f"'{selected_month}' {selected_user}님 지출 분석")

        if not df_selected.empty:
            # ❗❗ --- 여기가 수정된 부분입니다 --- ❗❗
            total_spent = df_selected['amount'].sum()
            expense_count = len(df_selected)
            
            # 1. 지출이 있었던 '날'의 수를 셉니다.
            days_with_expenses = df_selected['created_at'].dt.date.nunique()
            
            # 2. 하루 평균 지출액을 계산합니다. (0으로 나누는 오류 방지)
            daily_avg_spent = total_spent / days_with_expenses if days_with_expenses > 0 else 0

            # 3. st.metric 위젯을 수정합니다.
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("총 지출액", f"${total_spent:,.0f} ")
            metric_col2.metric("하루 평균 지출액", f"${daily_avg_spent:,.0f} ") # <- 라벨과 값 변경
            metric_col3.metric("총 지출 건수", f"{expense_count} 건")
            st.divider()
            # ❗❗ --- 수정 끝 --- ❗❗

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