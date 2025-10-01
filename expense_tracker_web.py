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
    "강나윤": 1000.00,
    "김채린": 800.00
}

TARGET_TZ = ZoneInfo("America/Chicago")


# --- 함수 정의 ---
def display_status():
    """데이터베이스에서 '이번 달'의 지출 내역만 효율적으로 가져와 합계를 계산하고 표시합니다."""
    totals = {user: 0.0 for user in USERS.keys()}
    
    # 1. 현재 시카고 시간 기준으로 이달의 시작일과 다음 달의 시작일을 계산합니다.
    now_local = datetime.datetime.now(TARGET_TZ)
    first_day_of_month = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    next_month = first_day_of_month.month + 1
    next_year = first_day_of_month.year
    if next_month > 12:
        next_month = 1
        next_year += 1
    first_day_of_next_month = first_day_of_month.replace(year=next_year, month=next_month)

    # 2. 이 시간들을 UTC로 변환합니다 (데이터베이스는 UTC 기준이므로).
    start_utc = first_day_of_month.astimezone(datetime.timezone.utc)
    end_utc = first_day_of_next_month.astimezone(datetime.timezone.utc)

    # 3. Supabase에 요청할 때 gte/lt 필터를 사용해 정확한 범위의 데이터만 요청합니다.
    res = supabase.table("expenses") \
        .select("user_name, amount") \
        .gte("created_at", start_utc.isoformat()) \
        .lt("created_at", end_utc.isoformat()) \
        .execute()

    if res.data:
        # 이미 이번 달 데이터만 필터링되었으므로, 바로 합산만 하면 됩니다.
        for row in res.data:
            totals[row["user_name"]] = totals.get(row["user_name"], 0) + float(row["amount"])

    # --- 진단용 코드 (펼쳐서 확인 가능) ---
    with st.expander("🔍 개발자 진단 도구"):
        st.write("현재 시간 (시카고):", now_local.strftime('%Y-%m-%d %H:%M:%S'))
        st.write("이번 달 시작 (시카고):", first_day_of_month.strftime('%Y-%m-%d %H:%M:%S'))
        st.write("DB에 요청한 UTC 시작 시간:", start_utc.strftime('%Y-%m-%d %H:%M:%S'))
        st.write("DB에 요청한 UTC 종료 시간:", end_utc.strftime('%Y-%m-%d %H:%M:%S'))
        st.write("DB에서 가져온 '이번 달' 데이터:", res.data)

    # --- 대시보드 표시 ---
    col1, col2 = st.columns(2)
    user_columns = {"강나윤": col1, "김채린": col2}

    for user, total in totals.items():
        with user_columns[user]:
            target = USERS.get(user, 0)
            percentage = int((total / target) * 100) if target > 0 else 0
            remaining = target - total
            st.metric(
                label=f"👤 {user}의 총 지출",
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
    st.subheader("✌️ 금쪽력 추가")
    
    selected_date = st.date_input("날짜", value=datetime.datetime.now(TARGET_TZ))
    
    selected_user = st.selectbox("어떤 금쪽이인가요?", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    
    categories = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
    description = st.selectbox("카테고리", categories)
    memo = st.text_input("메모 (선택사항)")

    submitted = st.form_submit_button("금쪽력 추가하기")
    
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