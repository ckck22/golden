# pages/2_📜_전체_내역_보기.py

import streamlit as st
from supabase import create_client
import pandas as pd
from collections import defaultdict

# --- Supabase 연결 (Home 페이지와 동일) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = ["강나윤", "김채린"]

st.set_page_config(page_title="전체 내역 보기", layout="wide")
st.title("📜 전체 지출 내역")

# --- 데이터 불러오기 및 처리 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        # 1. 데이터를 사용자별로 미리 그룹화
        user_data = defaultdict(list)
        for record in res.data:
            user_data[record['user_name']].append(record)

        # 2. 화면을 두 개의 컬럼으로 분리
        col1, col2 = st.columns(2)
        columns = {USERS[0]: col1, USERS[1]: col2}

        # 3. 각 사용자별로 컬럼에 데이터 표시
        for user, data_list in user_data.items():
            if user in columns:
                with columns[user]:
                    st.header(f"👤 {user}")
                    
                    # 4. 날짜별로 다시 그룹화해서 표시
                    df = pd.DataFrame(data_list)
                    df['date_only'] = pd.to_datetime(df['created_at']).dt.date
                    
                    for date, group in df.groupby('date_only'):
                        st.subheader(f"🗓️ {date.strftime('%Y년 %m월 %d일')}")
                        
                        # 같은 날짜의 지출 내역 표시
                        for _, row in group.iterrows():
                            # 수정 버튼과 내역을 한 줄에 나란히 표시
                            sub_col1, sub_col2 = st.columns([0.8, 0.2])
                            with sub_col1:
                                st.markdown(f"- **{row['amount']:,.0f}원**: {row['description']}")
                            with sub_col2:
                                # 각 버튼이 고유하도록 key 설정
                                if st.button("수정", key=f"edit_{row['id']}"):
                                    st.session_state.edit_id = row['id']
                        st.divider()

        # --- 수정 다이얼로그 (팝업) 로직 ---
        if 'edit_id' in st.session_state:
            record_to_edit = next((item for item in res.data if item['id'] == st.session_state.edit_id), None)
            
            if record_to_edit:
                @st.dialog("내역 수정하기")
                def edit_dialog():
                    st.write(f"**{pd.to_datetime(record_to_edit['created_at']).dt.date.iloc[0].strftime('%Y-%m-%d')}** 의 내역을 수정합니다.")
                    
                    with st.form("dialog_edit_form"):
                        new_amount = st.number_input("금액", value=float(record_to_edit['amount']))
                        new_description = st.text_input("내용", value=record_to_edit['description'])
                        
                        submitted = st.form_submit_button("수정 완료")
                        if submitted:
                            supabase.table("expenses").update({
                                "amount": new_amount,
                                "description": new_description
                            }).eq("id", st.session_state.edit_id).execute()
                            
                            del st.session_state.edit_id # 수정 완료 후 상태 초기화
                            st.rerun()

                edit_dialog()

    else:
        st.warning("아직 기록된 지출 내역이 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")