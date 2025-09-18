# expense_tracker_web.py

import streamlit as st
import datetime
from supabase import create_client
from zoneinfo import ZoneInfo

# Supabase 연결 
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

USERS = {
    "강나윤": 1000.00,
    "김채린": 800.00
}

TARGET_TZ = ZoneInfo("America/Chicago")

# --- 현재 상태 표시 ---
def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    
    # 이번 달 지출 합계 불러오기
    res = supabase.table("expenses").select("user_name, amount, created_at").execute()
    if res.data:
        for row in res.data:
        now = datetime.datetime.now(TARGET_TZ)
        if created_at.month == now.month and created_at.year == now.year:

                totals[row["user_name"]] = totals.get(row["user_name"], 0) + float(row["amount"])

    col1, col2 = st.columns(2)
    user_columns = {"강나윤": col1, "김채린": col2}

    for user, total in totals.items():
        with user_columns[user]:
            target = USERS.get(user, 0)
            percentage = int((total / target) * 100) if target > 0 else 0
            remaining = target - total
            st.metric(
                label=f"👤 {user}의 총 금쪽력",
                value=f"${total:,.2f}",
                delta=f"${remaining:,.2f} 남음",
                delta_color="inverse"
            )
            st.progress(min(percentage, 100))
            st.caption(f"목표 금액($ {target:,.2f})의 {percentage}% 사용")

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="금쪽이가계부", layout="centered")
st.title("💸 금쪽이 가계부")

display_status()

st.write("---")

with st.form("expense_form", clear_on_submit=True):
    st.subheader("✍️ 지출 내역 추가")
    
    # 1. 날짜를 선택할 수 있는 입력창을 추가합니다. 기본값은 오늘입니다.
    selected_date = st.date_input("날짜", value=datetime.date.today())
    
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    
    categories = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
    description = st.selectbox("카테고리를 선택하세요", categories)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        # 2. 저장할 때, 현재 시간이 아닌 위에서 선택한 날짜를 사용합니다.
        submission_timestamp = datetime.datetime(
            selected_date.year, 
            selected_date.month, 
            selected_date.day,
            tzinfo=datetime.timezone.utc 
        )

        # 데이터베이스에 정보 저장
        supabase.table("expenses").insert({
            "user_name": selected_user,
            "amount": amount,
            "description": description,
            "memo" : memo,
            "created_at": submission_timestamp.isoformat() # 수정된 값 사용
        }).execute()
        
        st.rerun()