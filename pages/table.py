import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- Supabase 연결 (Home 페이지와 동일) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="전체 내역 보기", layout="wide")
st.title("📜 전체 지출 내역")

# --- 데이터 불러오기 ---
try:
    res = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
    if res.data:
        # Pandas DataFrame으로 데이터 변환 (테이블 형태로 보기 좋게)
        df = pd.DataFrame(res.data)
        
        # 날짜 형식 정리
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # 보여줄 컬럼만 선택 및 이름 변경
        df_display = df[['created_at', 'user_name', 'amount', 'description', 'id']]
        df_display.columns = ['날짜', '사용자', '금액', '내용', 'id']

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.write("---")
        st.subheader("✍️ 내역 수정하기")
        
        # 수정할 항목 선택
        id_to_edit = st.selectbox(
            "수정할 내역의 날짜와 내용을 선택하세요.",
            options=df_display.apply(lambda x: f"{x['날짜']} - {x['내용']} (ID: {x['id']})", axis=1),
            index=None,
            placeholder="수정할 항목을 선택..."
        )

        if id_to_edit:
            # 선택된 문자열에서 ID 추출
            selected_id = int(id_to_edit.split("(ID: ")[1][:-1])
            
            # 원본 데이터에서 해당 ID의 레코드 찾기
            record_to_edit = df[df['id'] == selected_id].iloc[0]

            with st.form("edit_form"):
                st.write(f"**ID {selected_id}** 내역을 수정합니다.")
                
                new_amount = st.number_input("금액", value=float(record_to_edit['amount']))
                new_description = st.text_input("내용", value=record_to_edit['description'])
                
                submitted = st.form_submit_button("수정 완료")
                
                if submitted:
                    # Supabase에 업데이트 요청
                    supabase.table("expenses").update({
                        "amount": new_amount,
                        "description": new_description
                    }).eq("id", selected_id).execute()
                    
                    st.toast("성공적으로 수정되었습니다! 🎉")
                    st.rerun()

    else:
        st.warning("아직 기록된 지출 내역이 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")