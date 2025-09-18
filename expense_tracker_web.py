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

# 1. 기준 시간대를 명확히 정의 (수정 없음)
TARGET_TZ = ZoneInfo("America/Chicago")


# --- 현재 상태 표시 ---
def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    
    # 2. 시카고 기준 현재 시간을 변수로 저장
    chicago_now = datetime.datetime.now(TARGET_TZ)
    
    # 이번 달 지출 합계 불러오기
    res = supabase.table("expenses").select("user_name, amount, created_at").execute()
    if res.data:
        for row in res.data:
            # DB에서 가져온 UTC 시간을 datetime 객체로 변환
            created_at_utc = datetime.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            
            # 3. UTC 시간을 시카고 시간으로 변환
            created_at_local = created_at_utc.astimezone(TARGET_TZ)
            
            # 4. 시카고 시간 기준으로 이번 달 데이터인지 비교
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

display_status()

st.write("---")

with st.form("expense_form", clear_on_submit=True):
    st.subheader("✍️ 지출 내역 추가")
    
    # 5. 날짜 입력창의 기본값을 시카고 현재 날짜로 설정
    selected_date = st.date_input("날짜", value=datetime.datetime.now(TARGET_TZ))
    
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    
    categories = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
    description = st.selectbox("카테고리를 선택하세요", categories)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        # 사용자가 선택한 날짜(date)를 시간 정보가 포함된 datetime 객체로 변환
        # 데이터는 항상 UTC 기준으로 저장하는 것이 좋습니다.
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
            "created_at": submission_timestamp.isoformat()
        }).execute()
        
        st.rerun()