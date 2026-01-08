import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 타이틀 변경
st.set_page_config(page_title="T호텔 당일정산시스템", layout="wide")

# 2. T호텔 로고 및 상단 디자인 (T를 강렬한 빨간색으로 강조)
st.markdown("""
    <div style='text-align: center; padding: 20px; border: 2px solid #f0f2f6; border-radius: 15px; background-color: #ffffff;'>
        <h1 style='color: #E74C3C; font-size: 100px; margin-bottom: 0px; font-family: "Arial Black", sans-serif;'>T</h1>
        <h2 style='color: #2C3E50; margin-top: -10px; letter-spacing: 10px; font-weight: bold;'>HOTEL</h2>
        <div style='background-color: #2C3E50; color: white; padding: 10px; border-radius: 5px; display: inline-block; margin-top: 10px;'>
            <h3 style='margin: 0; letter-spacing: 2px;'>당일정산시스템</h3>
        </div>
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

if st.button("내역 추가하기", use_container_width=True):
    # 세션 상태에 데이터 저장
    if 'settle_data' not in st.session_state:
        st.session_state.settle_data = []
    
    st.session_state.settle_data.append({
        "분류": category,
        "금액": amount,
        "비고": note,
        "시간": datetime.now().strftime("%H:%M:%S")
    })
    st.success(f"[{category}] 내역이 추가되었습니다!")

st.divider()

# --- 데이터 처리 및 출력 섹션 ---
if 'settle_data' in st.session_state and len(st.session_state.settle_data) > 0:
    df = pd.DataFrame(st.session_state.settle_data)

    # 표4. 가격별 상세 분류 (사장님 요청 핵심 사항)
    st.subheader("📊 표4. 가격별 상세 분류")
    
    target_categories = ["숙박-현금", "숙박-카드", "대실-현금", "대실-카드"]
    
    for cat in target_categories:
        st.markdown(f"#### 📍 {cat}")
        filtered_df = df[df['분류'] == cat].copy()
        
        if not filtered_df.empty:
            # 개수와 합계 계산
            total_count = len(filtered_df)
            total_sum = filtered_df['금액'].sum()
            
            # 합계 행 생성 (가독성을 위해 특수 기호 추가)
            summary_df = pd.DataFrame({
                "분류": ["▶ 합계"],
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
    col_total1, col_total2 = st.columns(2)
    with col_total1:
        st.subheader("💰 당일 종합 합계")
        total_revenue = df['금액'].sum()
        st.metric("오늘의 총 매출", f"{total_revenue:,} 원")
    with col_total2:
        st.subheader("📈 건수 요약")
        st.write(f"총 입력 건수: {len(df)}건")

else:
    st.info("입력된 내역이 없습니다. 위에서 데이터를 입력해 주세요.")

# 하단 푸터
st.divider()
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | T HOTEL 관리자 모드")
