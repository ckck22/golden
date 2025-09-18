# pages/2_📜_전체_내역_보기.py

import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- Supabase 연결 (Home 페이지와 동일) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = ["강나윤", "김채린"]
CATEGORIES = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]


st.set_page_config(page_title="최근 내역 보기", layout="wide")
st.title("📜 최근 지출 내역 (오늘 & 어제)")

# --- 데이터 불러오기 및 처리 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['created_at_dt'] = pd.to_datetime(df['created_at'])

        # 오늘과 어제 날짜 계산
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        # 오늘과 어제 데이터만 필터링
        df_recent = df[df['created_at_dt'].dt.date.isin([today, yesterday])]

        if not df_recent.empty:
            # 사용자별로 데이터 분리
            user_data = {user: df_recent[df_recent['user_name'] == user] for user in USERS}

            col1, col2 = st.columns(2)
            columns = {USERS[0]: col1, USERS[1]: col2}

            for user, user_df in user_data.items():
                if not user_df.empty:
                    with columns[user]:
                        st.header(f"👤 {user}")
                        
                        user_df['date_only'] = user_df['created_at_dt'].dt.date
                        
                        for date, group in user_df.groupby('date_only'):
                            day_str = "오늘" if date == today else "어제"
                            st.subheader(f"🗓️ {date.strftime('%Y년 %m월 %d일')} ({day_str})")
                            
                            for _, row in group.iterrows():
                                sub_col1, sub_col2, sub_col3 = st.columns([0.7, 0.15, 0.15])
                                with sub_col1:
                                    # ❗❗ 1. 메모 표시 수정 ❗❗
                                    # 카테고리와 금액을 먼저 표시
                                    st.markdown(f"- **[{row['description']}]** ${row['amount']:,.0f}")
                                    # 메모가 있는 경우에만 들여쓰기해서 표시
                                    if pd.notna(row['memo']) and row['memo']:
                                        st.caption(f"📝 {row['memo']}")

                                with sub_col2:
                                    if st.button("수정", key=f"edit_{row['id']}", use_container_width=True):
                                        st.session_state.edit_id = row['id']
                                with sub_col3:
                                    if st.button("삭제", key=f"delete_{row['id']}", use_container_width=True):
                                        st.session_state.delete_id = row['id']
                            st.divider()
        else:
            st.info("오늘과 어제 기록된 지출 내역이 없습니다.")

        # --- 수정 다이얼로그 (팝업) 로직 ---
        if 'edit_id' in st.session_state:
            record_to_edit = df[df['id'] == st.session_state.edit_id].iloc[0]
            
            @st.dialog("내역 수정하기")
            def edit_dialog():
                st.write(f"**{pd.to_datetime(record_to_edit['created_at']).strftime('%Y-%m-%d')}** 의 내역을 수정합니다.")
                with st.form("dialog_edit_form"):
                    
                    # ❗❗ 2. 메모 수정 기능 추가 ❗❗
                    # 카테고리 선택 (기존 카테고리가 기본값으로 선택됨)
                    try:
                        current_category_index = CATEGORIES.index(record_to_edit['description'])
                    except ValueError:
                        current_category_index = 0
                    new_description = st.selectbox("카테고리", options=CATEGORIES, index=current_category_index)
                    
                    new_amount = st.number_input("금액", value=float(record_to_edit['amount']))
                    
                    # 메모 입력칸 추가 (기존 메모가 기본값으로 보임)
                    new_memo = st.text_input("메모", value=record_to_edit.get('memo', ''))
                    
                    if st.form_submit_button("수정 완료"):
                        # 업데이트 로직에 memo 추가
                        supabase.table("expenses").update({
                            "amount": new_amount, 
                            "description": new_description,
                            "memo": new_memo
                        }).eq("id", st.session_state.edit_id).execute()
                        
                        del st.session_state.edit_id
                        st.toast("성공적으로 수정되었습니다! 🎉")
                        st.rerun()
            edit_dialog()

        # --- 삭제 확인 다이얼로그 (팝업) 로직 ---
        if 'delete_id' in st.session_state:
            # (삭제 로직은 변경 없음)
            record_to_delete = df[df['id'] == st.session_state.delete_id].iloc[0]
            
            @st.dialog("삭제 확인")
            def delete_dialog():
                st.warning(f"정말로 아래 내역을 삭제하시겠습니까?")
                st.info(f"**[{record_to_delete['description']}]** ${record_to_delete['amount']:,.0f} - {record_to_delete.get('memo', '')}")
                
                col1, col2 = st.columns(2)
                if col1.button("예, 삭제합니다"):
                    supabase.table("expenses").delete().eq("id", st.session_state.delete_id).execute()
                    del st.session_state.delete_id
                    st.toast("삭제되었습니다.")
                    st.rerun()
                if col2.button("아니요"):
                    del st.session_state.delete_id
                    st.rerun()
            delete_dialog()

    else:
        st.warning("아직 기록된 지출 내역이 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")