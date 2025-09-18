# expense_tracker_web.py

import streamlit as st
import datetime
import psycopg2
from contextlib import contextmanager

USERS = {
    "나": 800.00,
    "친구": 750.00
}

@contextmanager
def db_cursor():
    conn = None
    try:
        # secrets를 사용한 연결 코드를 이 안으로 가져옵니다.
        conn = psycopg2.connect(**st.secrets["postgres"])
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception as e:
        st.error(f"🚨 데이터베이스 오류: {e}")
        yield None
    finally:
        if conn:
            conn.close()


def setup_database():
    with db_cursor() as cur:
        if cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    user_name VARCHAR(50) NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                );
            """)
    print("데이터베이스 테이블 준비 완료.")

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="친구와 돈 관리", layout="centered")
st.title("💸 친구와 함께 돈 관리")

def display_status():
    totals = {user: 0.0 for user in USERS.keys()}
    with db_cursor() as cur:
        if cur:
            cur.execute("""
                SELECT user_name, SUM(amount) FROM expenses
                WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())
                GROUP BY user_name;
            """)
            for row in cur.fetchall():
                user, total = row
                if user in totals: totals[user] = float(total)

    col1, col2 = st.columns(2)
    user_columns = {"나": col1, "친구": col2}

    for user, total in totals.items():
        with user_columns[user]:
            target = USERS.get(user, 0)
            percentage = int((total / target) * 100) if target > 0 else 0
            remaining = target - total
            st.metric(label=f"👤 {user}의 총 지출", value=f"${total:,.2f}", delta=f"${remaining:,.2f} 남음", delta_color="inverse")
            st.progress(percentage)
            st.caption(f"목표 금액($ {target:,.2f})의 {percentage}% 사용")

setup_database()
display_status()

st.write("---")

with st.form("expense_form", clear_on_submit=True):
    st.subheader("✍️ 지출 내역 추가")
    selected_user = st.selectbox("누가 지출했나요?", USERS.keys())
    amount = st.number_input("금액", min_value=0.01, format="%.2f")
    description = st.text_input("어디에 사용했나요?")
    submitted = st.form_submit_button("추가하기")
    
    if submitted:
        with db_cursor() as cur:
            if cur:
                cur.execute(
                    "INSERT INTO expenses (user_name, amount, description, created_at) VALUES (%s, %s, %s, %s)",
                    (selected_user, amount, description, datetime.datetime.now(datetime.timezone.utc))
                )
        st.success(f"{selected_user}님의 지출 ${amount}이(가) 추가되었습니다!")
