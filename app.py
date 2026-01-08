import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 타이틀 변경
st.set_page_config(page_title="T호텔 당일정산시스템", layout="wide")

# 2. T호텔 로고 및 상단 디자인 (T 강조)
st.markdown("""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='color: #1E3A8A; font-size: 80px; margin-bottom: 0px; font-family: "Arial Black", sans-serif;'>T</h1>
        <h2 style='color: #333333; margin-top: 0px; letter-spacing: 5px;'>HOTEL</h2>
        <h3 style='background-color: #f0f2f6; padding: 10px; border-radius: 10px;'>당일정산시스템</h3>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- 데이터 입력 섹션 ---
st.subheader("📝 당일 내역 입력")
col1, col2, col3 = st.columns(3)

with col1:
    category = st.selectbox("분류 선택", ["숙박-현금", "숙박-카드", "대실-현금", "대실-카드", "기타"])
with col2:
    amount = st.number_input("금액 입력", min_value=0, step=1000)
with col3:
    note = st.text_input("비고 (객실번호 등)")

if st.button("내역 추가하기"):
    # 세션 상태에 데이터 저장 (DB 연결 전 임시 저장)
    if 'settle_data' not in st.session_state:
        st.session_state.settle_data = []
    
    st.session_state.settle_data.append({
        "분류": category,
        "금액": amount,
        "비고": note,
        "시간": datetime.now().strftime("%H:%M:%S")
    })
    st.success("내역이 추가되었습니다!")

st.divider()

# --- 데이터 처리 및 출력 섹션 ---
if 'settle_data' in st.session_state and len(st.session_state.settle_data) > 0:
    df = pd.DataFrame(st.session_state.settle_data)

    # 표4. 가격별 상세 분류 (사장님 요청 핵심 사항)
    st.subheader("📊 표4. 가격별 상세 분류")
    
    target_categories = ["숙박-현금", "숙박-카드", "대실-현금", "대실-카드"]
    
    # 4개 영역을 2개씩 나누어 배치 (폰에서 보기 좋게)
    for cat in target_categories:
        st.write(f"#### 📍 {cat}")
        filtered_df = df[df['분류'] == cat].copy()
        
        if not filtered_df.empty:
            # 개수와 합계 계산
            total_count = len(filtered_df)
            total_sum = filtered_df['금액'].sum()
            
            # 합계 행 생성
            summary_df = pd.DataFrame({
                "분류": ["【 합계 】"],
                "금액": [total_sum],
                "비고": [f"총 {total_count}건"],
                "시간": ["-"]
            })
            
            # 데이터와 합계 결합
            display_df = pd.concat([filtered_df, summary_df], ignore_index=True)
            
            # 표 출력
            st.table(display_df)
        else:
            st.info(f"{cat} 내역이 없습니다.")
            
    # 전체 요약 (종합)
    st.divider()
    st.subheader("💰 당일 종합 합계")
    total_revenue = df['금액'].sum()
    st.metric("오늘의 총 매출", f"{total_revenue:,} 원")

else:
    st.info("입력된 내역이 없습니다. 위에서 데이터를 입력해 주세요.")

# 하단 푸터
st.divider()
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | T HOTEL 관리자 모드")
