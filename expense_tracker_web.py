import streamlit as st
import datetime
from supabase import create_client
from zoneinfo import ZoneInfo

# --- Supabase 연결 ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = {
    "강나윤": 1000.00,
    "김채린": 800.00
}
CATEGORIES = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
TARGET_TZ = ZoneInfo("America/Chicago")

# --- 함수 정의 (display_status는 이전과 동일) ---
def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    now_local = datetime.datetime.now(TARGET_TZ)
    res = supabase.table("expenses").select("user_name, amount, created_at").execute()
    if res.data:
        for row in res.data:
            created_at_utc = datetime.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            created_at_local = created_at_utc.astimezone(TARGET_TZ)
            if created_at_local.year == now_local.year and created_at_local.month == now_local.month:
                totals[row["user_name"]] = totals.get(row["user_name"], 0) + float(row["amount"])

    col1, col2 = st.columns(2)
    user_columns = {"강나윤": col1, "김채린": col2}
    for user, total in totals.items():
        with user_columns[user]:
            target = USERS.get(user, 0)
            percentage = int((total / target) * 100) if target > 0 else 0
            remaining = target - total
            st.metric(label=f"👤 {user}의 총 지출", value=f"${total:,.2f}", delta=f"${remaining:,.2f} 남음", delta_color="inverse")
            st.progress(min(percentage, 100))
            st.caption(f"목표 금액($ {target:,.2f})의 {percentage}% 사용")

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="친구와 돈 관리", layout="centered")
st.title("💸 친구와 함께 돈 관리")

display_status()
st.write("---")
st.subheader("✍️ 지출 내역 추가")

# --- ❗❗ 구조 변경: 금액 조절 UI (폼 바깥에 위치) ❗❗ ---
if "amount" not in st.session_state:
    st.session_state.amount = 0.0

def add_amount(value):
    st.session_state.amount += value

def subtract_amount(value):
    st.session_state.amount = max(0.0, st.session_state.amount - value)

st.write("금액")
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
col1.number_input("금액 입력", key="amount", min_value=0.0, format="%.2f", label_visibility="collapsed")
col2.button("➖ 1", on_click=subtract_amount, args=[1.0], use_container_width=True)
col3.button("➕ 1", on_click=add_amount, args=[1.0], use_container_width=True)
col4.button("➕ 10", on_click=add_amount, args=[10.0], use_container_width=True)
col5.button("➕ 100", on_click=add_amount, args=[100.0], use_container_width=True)

# --- ❗❗ 지출 추가 폼 (나머지 정보 입력) ❗❗ ---
with st.form("expense_form"):
    selected_date = st.date_input("날짜", value=datetime.datetime.now(TARGET_TZ))
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    description = st.selectbox("카테고리를 선택하세요", CATEGORIES)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        amount_to_submit = st.session_state.amount
        if amount_to_submit > 0:
            submission_timestamp = datetime.datetime(
                selected_date.year, selected_date.month, selected_date.day,
                tzinfo=datetime.timezone.utc 
            )
            supabase.table("expenses").insert({
                "user_name": selected_user,
                "amount": amount_to_submit,
                "description": description,
                "memo": memo,
                "created_at": submission_timestamp.isoformat()
            }).execute()

            st.toast(f"'{description}' 내역이 추가되었습니다! 🎉")
            st.session_state.amount = 0.0
            st.rerun()
        else:
            st.warning("금액을 0보다 크게 입력해주세요.")