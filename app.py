import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="T호텔 당일정산시스템", layout="wide")

# 2. 로고 디자인
st.markdown("""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='color: #E74C3C; font-size: 100px; margin-bottom: 0px; font-family: "Arial Black", sans-serif;'>T</h1>
        <h2 style='color: #2C3E50; margin-top: -10px; letter-spacing: 10px; font-weight: bold;'>HOTEL</h2>
        <h3 style='color: #000000; margin-top: 5px; font-weight: bold; font-size: 28px;'>(당일정산시스템)</h3>
    </div>
    """, unsafe_allow_html=True)

st.divider()

if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- 1. 헤더 및 숙박중 수동 입력 ---
col_header, col_status = st.columns([3, 1])
with col_header:
    st.subheader("🛎️ 실시간 객실 현황")
with col_status:
    staying_qty = st.number_input("현재 숙박중 (객실 수)", min_value=0, step=1, value=0, key="staying_manual_input")

st.markdown("---")

# --- 2. 데이터 입력 섹션 ---
st.subheader("📝 데이터 입력")
input_col1, input_col2 = st.columns(2)

with input_col1:
    with st.form("acc_form", clear_on_submit=True):
        st.markdown("### 🛏️ 숙박 입력")
        c1, c2, c3 = st.columns(3)
        with c1:
            acc_channel = st.selectbox("채널", ["트립닷컴", "아고다", "여기어때", "현장현금", "현장카드", "계좌이체"])
        with c2:
            acc_room = st.text_input("객실호수", key="acc_room")
        with c3:
            acc_price = st.number_input("가격", min_value=0, step=1000, key="acc_price")
        acc_submit = st.form_submit_button("숙박 등록", use_container_width=True)
        if acc_submit:
            st.session_state.logs.append({"type": "숙박", "channel": acc_channel, "room": acc_room, "price": int(acc_price), "note": "숙박"})
            st.rerun()

with input_col2:
    with st.form("rent_form", clear_on_submit=True):
        st.markdown("### ⏳ 대실/기타 입력")
        r1, r2, r3 = st.columns(3)
        with r1:
            rent_channel = st.selectbox("채널", ["현금", "카드", "계좌이체"])
        with r2:
            rent_room = st.text_input("객실호수", key="rent_room")
        with r3:
            rent_note = st.selectbox("비고", ["대실", "일품", "세탁", "주차"])
            rent_price = st.number_input("가격", min_value=0, step=1000, key="rent_price")
        rent_submit = st.form_submit_button("대실/기타 등록", use_container_width=True)
        if rent_submit:
            st.session_state.logs.append({"type": "대실/기타", "channel": rent_channel, "room": rent_room, "price": int(rent_price), "note": rent_note})
            st.rerun()

# --- 데이터 처리 및 출력 섹션 ---
if st.session_state.logs or staying_qty > 0:
    df_real = pd.DataFrame(st.session_state.logs) if st.session_state.logs else pd.DataFrame(columns=["type", "channel", "room", "price", "note"])

    if staying_qty > 0:
        staying_data = [{"type": "숙박", "channel": "숙박중", "room": "-", "price": 0, "note": "숙박중"} for _ in range(staying_qty)]
        df_staying = pd.DataFrame(staying_data)
        df = pd.concat([df_real, df_staying], ignore_index=True)
    else:
        df = df_real.copy()

    # 가격 타입을 정수로 강제 고정
    df['price'] = df['price'].astype(int)

    def classify_pay_group(channel):
        return "카드" if channel in ["현장카드", "카드"] else "현금"
    df['pay_group'] = df['channel'].apply(classify_pay_group)

    # 통계 계산 (결과값도 무조건 정수로 변환)
    acc_cash_sum = int(df[(df['type'] == '숙박') & (df['pay_group'] == '현금')]['price'].sum())
    acc_card_sum = int(df[(df['type'] == '숙박') & (df['pay_group'] == '카드')]['price'].sum())
    rent_cash_sum = int(df[(df['type'] == '대실/기타') & (df['pay_group'] == '현금')]['price'].sum())
    rent_card_sum = int(df[(df['type'] == '대실/기타') & (df['pay_group'] == '카드')]['price'].sum())
    receivable = int(df[df['channel'].isin(["트립닷컴", "아고다", "여기어때", "계좌이체"])]['price'].sum())
    deposit = int(df[df['channel'].isin(["현장현금", "현금"])]['price'].sum())

    st.markdown("---")
    st.subheader("📊 정산 리포트")

    # [표 1]
    total_acc = acc_cash_sum + acc_card_sum
    total_rent = rent_cash_sum + rent_card_sum
    table1_data = {
        "구분": ["합계", "숙박", "대실/기타"],
        "개수 (Count)": [f"{len(df)} 건", f"{len(df[df['type']=='숙박'])} 건", f"{len(df[df['type']=='대실/기타'])} 건"],
        "합계 (Total)": [total_acc + total_rent, total_acc, total_rent],
        "현금 (현금+이체+OTA)": [acc_cash_sum + rent_cash_sum, acc_cash_sum, rent_cash_sum],
        "카드 (Card)": [acc_card_sum + rent_card_sum, acc_card_sum, rent_card_sum]
    }
    st.dataframe(pd.DataFrame(table1_data).style.format({"합계 (Total)": "{:,} 원", "현금 (현금+이체+OTA)": "{:,} 원", "카드 (Card)": "{:,} 원"}), use_container_width=True, hide_index=True)

    # [표 2]
    t2_cats = ["트립닷컴", "아고다", "여기어때", "계좌이체"]
    table2_data = [{"분류": c, "개수": f"{len(df[df['channel']==c])} 건", "합계": int(df[df['channel']==c]['price'].sum())} for c in t2_cats]
    st.dataframe(pd.DataFrame(table2_data).style.format({"합계": "{:,} 원"}), use_container_width=True, hide_index=True)

    # [표 3]
    c3_1, c3_2 = st.columns(2)
    c3_1.info(f"**미수금 합계** (OTA+이체)\n\n### {receivable:,} 원")
    c3_2.success(f"**입금 합계** (현장현금)\n\n### {deposit:,} 원")

    # [표 4] - 소수점 완전 박멸 핵심 로직
    st.markdown("---")
    st.markdown("#### [표 4] 가격별 상세 분류")
    
    def make_price_table_with_sum(data_type, pay_group):
        filtered_df = df[(df['type'] == data_type) & (df['pay_group'] == pay_group)].copy()
        if filtered_df.empty: return None
        
        # 그룹화 전 가격을 정수로 확실히 변환
        filtered_df['price'] = filtered_df['price'].astype(int)
        
        stats = filtered_df.groupby('price').size().reset_index(name='개수')
        stats['가격합'] = stats['price'] * stats['개수']
        
        # 합계 계산
        total_qty = int(stats['개수'].sum())
        total_sum = int(stats['가격합'].sum())
        
        # 표 하단 합계 행
        summary_row = pd.DataFrame({"가격": ["▶ 합계"], "개수": [total_qty], "가격합": [total_sum]})
        result_df = pd.concat([stats, summary_row], ignore_index=True)
        return result_df

    col4_1, col4_2 = st.columns(2)
    with col4_1:
        for pg in ["현금", "카드"]:
            st.markdown(f"**숙박 - {pg}**")
            res = make_price_table_with_sum("숙박", pg)
            if res is not None:
                # 스타일 포맷에서 f 제거하고 천단위 콤마만 남김
                st.dataframe(res.style.format({
                    "가격": lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x, 
                    "개수": "{:,}",
                    "가격합": lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x
                }), hide_index=True, use_container_width=True)
            else: st.text("데이터 없음")

    with col4_2:
        for pg in ["현금", "카드"]:
            st.markdown(f"**대실 - {pg}**")
            res = make_price_table_with_sum("대실/기타", pg)
            if res is not None:
                st.dataframe(res.style.format({
                    "가격": lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x, 
                    "개수": "{:,}",
                    "가격합": lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x
                }), hide_index=True, use_container_width=True)
            else: st.text("데이터 없음")

    with st.expander("📋 데이터 초기화"):
        if st.button("데이터 전체 초기화"):
            st.session_state.logs = []
            st.rerun()
else:
    st.info("데이터를 입력하면 하단에 통계 표가 생성됩니다.")

st.divider()
st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | T HOTEL 관리자")
