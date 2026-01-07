import streamlit as st
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="숙박 관리 시스템", layout="wide")

# --- 세션 상태 초기화 (데이터 저장소) ---
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- 1. 헤더 및 숙박중 수동 입력 ---
col_header, col_status = st.columns([3, 1])

with col_header:
    st.title("🏨 객실 관리 시스템")

with col_status:
    # 이 숫자를 나중에 '현금 0원' 데이터로 변환해서 합칩니다.
    staying_qty = st.number_input("현재 숙박중 (객실 수)", min_value=0, step=1, value=0, key="staying_manual_input")

st.markdown("---")

# --- 2. 입력 메뉴 (프론트엔드) ---
st.subheader("📝 데이터 입력")

input_col1, input_col2 = st.columns(2)

# [숙박] 입력 폼
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
        
        acc_submit = st.form_submit_button("숙박 등록")
        
        if acc_submit:
            st.session_state.logs.append({
                "type": "숙박",
                "channel": acc_channel,
                "room": acc_room,
                "price": acc_price,
                "note": "숙박"
            })
            st.rerun()

# [대실과 기타] 입력 폼
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

        rent_submit = st.form_submit_button("대실/기타 등록")
        
        if rent_submit:
            st.session_state.logs.append({
                "type": "대실/기타",
                "channel": rent_channel,
                "room": rent_room,
                "price": rent_price,
                "note": rent_note
            })
            st.rerun()

# --- 데이터 처리 로직 (백엔드) ---
# 로그가 있거나, 숙박중 개수가 1 이상이면 계산 시작
if st.session_state.logs or staying_qty > 0:
    
    # 1. 실제 입력된 로그 가져오기
    if st.session_state.logs:
        df_real = pd.DataFrame(st.session_state.logs)
    else:
        # 로그가 하나도 없을 경우 빈 프레임 생성
        df_real = pd.DataFrame(columns=["type", "channel", "room", "price", "note"])

    # 2. '숙박중' 개수만큼 가상의 데이터 생성 (현금, 0원)
    if staying_qty > 0:
        staying_data = []
        for _ in range(staying_qty):
            staying_data.append({
                "type": "숙박",
                "channel": "숙박중", # 채널명은 '숙박중'
                "room": "-",
                "price": 0,          # 가격 0원
                "note": "숙박중"
            })
        df_staying = pd.DataFrame(staying_data)
        
        # 실제 데이터와 숙박중 데이터를 합침 -> 모든 통계는 이 df로 계산
        df = pd.concat([df_real, df_staying], ignore_index=True)
    else:
        df = df_real.copy()

    # ---------------------------------------------------------
    # 통계 변수 초기화
    # ---------------------------------------------------------
    acc_cash_sum = 0; acc_card_sum = 0
    rent_cash_sum = 0; rent_card_sum = 0
    receivable = 0; deposit = 0
    
    # 개수 집계
    count_acc = len(df[df['type'] == '숙박'])
    count_rent = len(df[df['type'] == '대실/기타'])
    count_total = count_acc + count_rent
    
    # 채널별 집계용
    channel_stats = {
        "트립닷컴": {"count": 0, "sum": 0},
        "아고다": {"count": 0, "sum": 0},
        "여기어때": {"count": 0, "sum": 0},
        "계좌이체": {"count": 0, "sum": 0}
    }

    # 결제 수단 분류 헬퍼 함수
    def classify_pay_group(channel):
        if channel in ["현장카드", "카드"]:
            return "카드"
        else:
            # 숙박중, 현금, OTA, 계좌이체 -> 모두 현금성 그룹으로 분류
            return "현금" 

    # DataFrame에 결제 그룹 컬럼 추가
    df['pay_group'] = df['channel'].apply(classify_pay_group)

    for _, row in df.iterrows():
        p = row['price']
        c = row['channel']
        t = row['type']
        pg = row['pay_group']
        
        # (1) 대분류 (현금 vs 카드)
        if t == "숙박":
            if pg == "카드": acc_card_sum += p
            else: acc_cash_sum += p # 숙박중(0원)도 여기 포함됨 (금액 변동 없음)
        else: # 대실/기타
            if pg == "카드": rent_card_sum += p
            else: rent_cash_sum += p

        # (2) 미수금 vs 입금 로직
        if c in ["트립닷컴", "아고다", "여기어때", "계좌이체"]:
            receivable += p
        elif c in ["현장현금", "현금"]:
            deposit += p
        # '숙박중'은 가격이 0원이므로 미수금/입금 어디에도 금액 영향 없음 (논리적 맞음)
            
        # (3) 표2 집계
        if c in ["트립닷컴", "아고다", "여기어때"]:
            channel_stats[c]["count"] += 1
            channel_stats[c]["sum"] += p
        elif c == "계좌이체":
            channel_stats["계좌이체"]["count"] += 1
            channel_stats["계좌이체"]["sum"] += p

    # 총계 계산
    total_cash_sum = acc_cash_sum + rent_cash_sum
    total_card_sum = acc_card_sum + rent_card_sum
    total_acc_sum = acc_cash_sum + acc_card_sum
    total_rent_sum = rent_cash_sum + rent_card_sum
    grand_total = total_acc_sum + total_rent_sum

    st.markdown("---")
    st.subheader("📊 정산 리포트")

    # ---------------------------------------------------------
    # [표 1] 매출 종합 집계
    # ---------------------------------------------------------
    st.markdown("#### [표 1] 매출 종합 집계")
    table1_data = {
        "구분": ["합계", "숙박", "대실/기타"],
        "개수 (Count)": [f"{count_total} 건", f"{count_acc} 건", f"{count_rent} 건"],
        "합계 (Total)": [grand_total, total_acc_sum, total_rent_sum],
        "현금 (현금+이체+OTA)": [total_cash_sum, acc_cash_sum, rent_cash_sum],
        "카드 (Card)": [total_card_sum, acc_card_sum, rent_card_sum]
    }
    df_table1 = pd.DataFrame(table1_data)
    st.dataframe(df_table1.style.format({
        "합계 (Total)": "{:,} 원",
        "현금 (현금+이체+OTA)": "{:,} 원",
        "카드 (Card)": "{:,} 원"
    }), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # [표 2] 채널 및 이체 상세
    # ---------------------------------------------------------
    st.markdown("#### [표 2] 채널 및 이체 상세")
    table2_data = []
    for key in ["트립닷컴", "아고다", "여기어때", "계좌이체"]:
        table2_data.append({
            "분류": key,
            "개수": f"{channel_stats[key]['count']} 건",
            "합계": channel_stats[key]['sum']
        })
    df_table2 = pd.DataFrame(table2_data)
    st.dataframe(df_table2.style.format({"합계": "{:,} 원"}), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # [표 3] 자금 흐름 현황
    # ---------------------------------------------------------
    st.markdown("#### [표 3] 자금 흐름 현황")
    col_t3_1, col_t3_2 = st.columns(2)
    with col_t3_1:
        st.info(f"**미수금 합계** (OTA + 이체)\n\n### {receivable:,} 원")
    with col_t3_2:
        st.success(f"**입금 합계** (현장 현금)\n\n### {deposit:,} 원")

    # ---------------------------------------------------------
    # [표 4] 가격별 상세 분류
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("#### [표 4] 가격별 상세 분류")
    
    def make_price_table(data_type, pay_group):
        # 데이터 필터링
        filtered_df = df[(df['type'] == data_type) & (df['pay_group'] == pay_group)]
        if filtered_df.empty:
            return pd.DataFrame(columns=["가격", "개수", "가격합"])
        
        # 가격별 그룹핑
        stats = filtered_df.groupby('price').size().reset_index(name='개수')
        stats['가격합'] = stats['price'] * stats['개수']
        stats.columns = ["가격", "개수", "가격합"]
        return stats

    col4_1, col4_2 = st.columns(2)

    with col4_1:
        st.caption("🟦 숙박 상세 내역")
        st.markdown("**1. 숙박 - 현금** (OTA/이체/숙박중 포함)")
        df_acc_cash = make_price_table("숙박", "현금")
        
        # '숙박중'은 가격이 0원이므로 여기서 [0, N, 0] 형태로 표시됩니다.
        if not df_acc_cash.empty:
            st.dataframe(df_acc_cash.style.format({"가격": "{:,}", "가격합": "{:,}"}), hide_index=True)
        else:
            st.text("데이터 없음")

        st.markdown("**2. 숙박 - 카드**")
        df_acc_card = make_price_table("숙박", "카드")
        if not df_acc_card.empty:
            st.dataframe(df_acc_card.style.format({"가격": "{:,}", "가격합": "{:,}"}), hide_index=True)
        else:
            st.text("데이터 없음")

    with col4_2:
        st.caption("🟧 대실/기타 상세 내역")
        st.markdown("**1. 대실 - 현금** (이체 포함)")
        df_rent_cash = make_price_table("대실/기타", "현금")
        if not df_rent_cash.empty:
            st.dataframe(df_rent_cash.style.format({"가격": "{:,}", "가격합": "{:,}"}), hide_index=True)
        else:
            st.text("데이터 없음")

        st.markdown("**2. 대실 - 카드**")
        df_rent_card = make_price_table("대실/기타", "카드")
        if not df_rent_card.empty:
            st.dataframe(df_rent_card.style.format({"가격": "{:,}", "가격합": "{:,}"}), hide_index=True)
        else:
            st.text("데이터 없음")

    with st.expander("📋 전체 데이터 확인 (숙박중 포함)"):
        st.dataframe(df)
        if st.button("데이터 초기화"):
            st.session_state.logs = []
            st.rerun()

else:
    st.info("데이터를 입력하면 하단에 통계 표가 생성됩니다.")