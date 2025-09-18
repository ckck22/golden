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

# --- 지출 추가 폼을 위한 준비 코드 ---

# session_state에 'amount' 키가 없으면 0.0으로 초기화
if "amount" not in st.session_state:
    st.session_state.amount = 0.0

# 버튼 클릭 시 금액을 변경하는 콜백 함수 정의
def add_amount(value):
    st.session_state.amount += value

def subtract_amount(value):
    st.session_state.amount = max(0.0, st.session_state.amount - value) # 0 미만 방지

# --- 지출 추가 폼 ---
with st.form("expense_form"):
    st.subheader("✍️ 지출 내역 추가")
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    
    # 금액 입력 부분을 +, - 버튼과 함께 배치
    st.write("금액")
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
    # st.number_input에 key를 지정하여 session_state와 연결
    col1.number_input(
        "금액 입력", 
        key="amount", 
        min_value=0.0, 
        format="%.2f", 
        label_visibility="collapsed"
    )
    
    # 각 버튼에 위에서 만든 함수를 on_click으로 연결
    col2.button("➖ 1", on_click=subtract_amount, args=[1.0], use_container_width=True)
    col3.button("➕ 1", on_click=add_amount, args=[1.0], use_container_width=True)
    col4.button("➕ 10", on_click=add_amount, args=[10.0], use_container_width=True)
    col5.button("➕ 100", on_click=add_amount, args=[100.0], use_container_width=True)
    
    description = st.text_input("어디에 사용했나요?")
    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        # 폼 제출 시 session_state에 저장된 금액을 사용
        amount_to_submit = st.session_state.amount
        
        if amount_to_submit > 0 and description:
            supabase.table("expenses").insert({
                "user_name": selected_user,
                "amount": amount_to_submit,
                "description": description,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }).execute()

            st.toast(f"{selected_user}님의 지출 ${amount_to_submit}이(가) 추가되었습니다! 🎉")
            
            # 제출 후 다음 입력을 위해 금액을 0으로 초기화
            st.session_state.amount = 0.0
            st.rerun()
        else:
            st.warning("금액과 내용을 모두 입력해주세요.")