# pages/3_📊_통계.py

import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 한글 폰트 설정 (이전과 동일) ---
try:
    font_path = "c:/Windows/Fonts/malgun.ttf" # Windows 기준
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False
except FileNotFoundError:
    st.warning("한글 폰트 파일을 찾을 수 없어 차트의 한글이 깨질 수 있습니다.")

# --- Supabase 연결 (이전과 동일) ---
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
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['month'] = df['created_at'].dt.strftime('%Y년 %m월')

        # --- 필터링 옵션 ---
        col1, col2 = st.columns(2)
        
        # 월 선택 필터
        unique_months = df['month'].unique()
        selected_month = col1.selectbox("분석할 월을 선택하세요:", unique_months)
        
        # ❗❗ 사용자 선택 필터 추가 ❗❗
        view_option = ["전체"] + USERS
        selected_user = col2.selectbox("누구의 통계를 볼까요?:", view_option)

        # --- 데이터 처리 ---
        # 1. 선택된 월로 데이터 필터링
        df_month_filtered = df[df['month'] == selected_month]
        
        # 2. 선택된 사용자로 추가 필터링
        if selected_user == "전체":
            df_selected = df_month_filtered
            st.subheader(f"'{selected_month}' 전체 지출 분석")
        else:
            df_selected = df_month_filtered[df_month_filtered['user_name'] == selected_user]
            st.subheader(f"'{selected_month}' {selected_user}님 지출 분석")


        if not df_selected.empty:
            # --- 요약 정보 표시 (선택된 데이터 기준) ---
            total_spent = df_selected['amount'].sum()
            avg_spent = df_selected['amount'].mean()
            expense_count = len(df_selected)

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("총 지출액", f"${total_spent:,.0f} ")
            metric_col2.metric("평균 지출액", f"${avg_spent:,.0f} ")
            metric_col3.metric("총 지출 건수", f"{expense_count} 건")
            st.divider()

            # --- 카테고리별 통계 (선택된 데이터 기준) ---
            category_summary = df_selected.groupby('description')['amount'].sum().sort_values(ascending=False)
            
            chart_col, data_col = st.columns([0.6, 0.4])
            with chart_col:
                st.write("#### 지출 비율 (원형 차트)")
                if not category_summary.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
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