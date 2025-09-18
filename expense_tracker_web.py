# expense_tracker_web.py

import streamlit as st
import datetime
from supabase import create_client
from zoneinfo import ZoneInfo

# --- 기본 설정 (이 부분이 진단 코드보다 먼저 실행되어야 합니다) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

USERS = {
    "강나윤": 500.00,
    "김채린": 400.00
}

TARGET_TZ = ZoneInfo("America/Chicago")


# --- 함수 정의 ---
def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    
    chicago_now = datetime.datetime.now(TARGET_TZ)
    
    res = supabase.table("expenses").select("user_name, amount, created_at").execute()
    if res.data:
        for row in res.data:
            created_at_utc = datetime.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            created_at_local = created_at_utc.astimezone(TARGET_TZ)
            
            if created_at_local.month == chicago_now.month and created_at_local.year == chicago_now.year:
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


# --- 진단 코드 시작 (정확한 위치) ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
now_chicago = datetime.datetime.now(TARGET_TZ)
# --- 진단 코드 끝 ---


display_status()

st.write("---")

with st.form("expense_form", clear_on_submit=True):
    st.subheader("✍️ 지출 내역 추가")
    
    selected_date = st.date_input("날짜", value=datetime.datetime.now(TARGET_TZ))
    
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    
    categories = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
    description = st.selectbox("카테고리를 선택하세요", categories)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        submission_timestamp = datetime.datetime(
            selected_date.year, 
            selected_date.month, 
            selected_date.day,
            tzinfo=datetime.timezone.utc 
        )

        supabase.table("expenses").insert({
            "user_name": selected_user,
            "amount": amount,
            "description": description,
            "memo" : memo,
            "created_at": submission_timestamp.isoformat()
        }).execute()
        
        st.rerun()