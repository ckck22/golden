# expense_tracker_web.py

import streamlit as st
import datetime
from supabase import create_client

# Supabase 연결 
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

USERS = {
    "강나윤": 1000.00,
    "김채린": 800.00
}


# --- 현재 상태 표시 ---
def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    
    # 이번 달 지출 합계 불러오기
    res = supabase.table("expenses").select("user_name, amount, created_at").execute()
    if res.data:
        for row in res.data:
            created_at = datetime.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            if created_at.month == datetime.datetime.now().month:  # 이번 달만 집계
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
    st.subheader("✍️ 금쪽이 내역 추가")
    selected_user = st.selectbox("금쪽이를 선택하세요", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    
    categories = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
    description = st.selectbox("어디에 사용했나요?", categories)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("금쪽력 추가하기")
    
    if submitted:
        # 데이터베이스에 정보 저장
        supabase.table("expenses").insert({
            "user_name": selected_user,
            "amount": amount,
            "description": description,
            "memo" : memo,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }).execute()
        
        st.rerun()