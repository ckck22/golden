import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt

# --- 기본 설정 ---
# Supabase 연결
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

USERS = ["강나윤", "김채린"]

# 카테고리 한/영 변환을 위한 사전
CATEGORY_MAP = {
    "식비": "Food",
    "교통": "Transportation",
    "주거/통신": "Housing/Utilities",
    "쇼핑": "Shopping",
    "문화/여가": "Entertainment/Leisure",
    "기타": "Other"
}

st.set_page_config(page_title="Expense Statistics", layout="wide")
st.title("📊 Monthly Expense Statistics")

# --- 데이터 불러오기 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
        df['month'] = df['created_at'].dt.strftime('%Y-%m')

        # --- 필터링 옵션 ---
        col1, col2 = st.columns(2)
        unique_months = sorted(df['month'].unique(), reverse=True)
        selected_month = col1.selectbox("Select Month:", unique_months)
        
        view_option = ["All"] + USERS
        selected_user = col2.selectbox("Select User:", view_option)

        # --- 데이터 처리 ---
        df_month_filtered = df[df['month'] == selected_month]
        if selected_user == "All":
            df_selected = df_month_filtered
            st.subheader(f"Analysis for {selected_month} (All Users)")
        else:
            df_selected = df_month_filtered[df_month_filtered['user_name'] == selected_user]
            st.subheader(f"Analysis for {selected_month} ({selected_user})")

        if not df_selected.empty:
            # --- 요약 정보 표시 ---
            total_spent = df_selected['amount'].sum()
            days_with_expenses = df_selected['created_at'].dt.date.nunique()
            daily_avg_spent = total_spent / days_with_expenses if days_with_expenses > 0 else 0
            expense_count = len(df_selected)

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Total Spent", f"${total_spent:,.2f}")
            metric_col2.metric("Daily Average", f"${daily_avg_spent:,.2f}")
            metric_col3.metric("Total Transactions", f"{expense_count}")
            st.divider()

            # --- 카테고리별 통계 ---
            category_summary = df_selected.groupby('description')['amount'].sum().sort_values(ascending=False)
            
            # 차트 라벨을 영어로 변환
            category_summary.index = category_summary.index.map(CATEGORY_MAP).fillna(category_summary.index)
            
            chart_col, data_col = st.columns([0.6, 0.4])
            with chart_col:
                st.write("#### Spending by Category (Pie Chart)")
                if not category_summary.empty:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    st.info("No category data to display.")
            
            with data_col:
                st.write("#### Detailed Data")
                st.dataframe(category_summary.reset_index().rename(columns={'description': 'Category', 'amount': 'Amount ($)'}))

        else:
            st.info("No expense data found for the selected criteria.")
    else:
        st.warning("No expense records found.")

except Exception as e:
    st.error(f"An error occurred while analyzing data: {e}")