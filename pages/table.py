import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
from zoneinfo import ZoneInfo

# --- Supabase 연결 ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 기본 설정 ---
USERS = ["강나윤", "김채린"]
CATEGORIES = ["식비", "교통", "주거/통신", "쇼핑", "문화/여가", "기타"]
TARGET_TZ = ZoneInfo("America/Chicago") # 시카고 시간대 설정


st.set_page_config(page_title="전체 내역 보기", layout="wide")
st.title("📜 이번 달 전체 지출 내역")

# --- 데이터 불러오기 및 처리 ---
try:
    # 모든 데이터를 created_at 기준으로 내림차순 정렬하여 불러오기
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()

    if res.data:
        df = pd.DataFrame(res.data)
        # UTC 시간을 시카고 시간으로 변환
        df['created_at_dt'] = pd.to_datetime(df['created_at']).dt.tz_convert(TARGET_TZ)

        # 현재 월 계산 (시카고 시간 기준)
        now_in_chicago = datetime.datetime.now(TARGET_TZ)
        current_month = now_in_chicago.month
        current_year = now_in_chicago.year
        
        # 이번 달 데이터만 필터링
        df_monthly = df[(df['created_at_dt'].dt.month == current_month) & (df['created_at_dt'].dt.year == current_year)]

        if not df_monthly.empty:
            # 사용자별로 데이터 분리
            user_data = {user: df_monthly[df_monthly['user_name'] == user] for user in USERS}

            col1, col2 = st.columns(2)
            columns = {USERS[0]: col1, USERS[1]: col2}

            for user, user_df in user_data.items():
                if not user_df.empty:
                    with columns[user]:
                        st.header(f"👤 {user}")
                        
                        # 날짜만 추출한 컬럼 추가
                        user_df['date_only'] = user_df['created_at_dt'].dt.date
                        
                        # 날짜별로 그룹화하여 표시
                        for date, group in user_df.groupby('date_only'):
                            st.subheader(f"🗓️ {date.strftime('%Y년 %m월 %d일')}")
                            
                            # 그룹 내 각 항목 표시
                            for _, row in group.iterrows():
                                sub_col1, sub_col2, sub_col3 = st.columns([0.7, 0.15, 0.15])
                                with sub_col1:
                                    st.markdown(f"- **[{row['description']}]** ${row['amount']:,.0f}")
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
            st.info("이번 달에 기록된 지출 내역이 없습니다.")

        # --- 수정 다이얼로그 (팝업) 로직 ---
        if 'edit_id' in st.session_state:
            # 수정할 레코드를 전체 데이터프레임(df)에서 찾음
            record_to_edit = df[df['id'] == st.session_state.edit_id].iloc[0]
            
            @st.dialog("내역 수정하기")
            def edit_dialog():
                # 날짜 표시 (시카고 시간 기준)
                record_date = record_to_edit['created_at_dt'].strftime('%Y-%m-%d')
                st.write(f"**{record_date}** 의 내역을 수정합니다.")

                with st.form("dialog_edit_form"):
                    try:
                        current_category_index = CATEGORIES.index(record_to_edit['description'])
                    except ValueError:
                        current_category_index = 0 # 카테고리가 목록에 없으면 기본값으로
                    new_description = st.selectbox("카테고리", options=CATEGORIES, index=current_category_index)
                    new_amount = st.number_input("금액", value=float(record_to_edit['amount']), format="%.2f")
                    new_memo = st.text_input("메모", value=record_to_edit.get('memo', ''))
                    
                    if st.form_submit_button("수정 완료"):
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