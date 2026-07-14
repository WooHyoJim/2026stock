import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────
st.set_page_config(
    page_title="한국 AI·반도체·로봇 주식 분석",
    page_icon="🇰🇷",
    layout="wide"
)

st.title("🇰🇷 한국 AI·반도체·로봇 대표주 분석 대시보드")
st.caption("Yahoo Finance 데이터 기반 · Plotly 시각화")

# ── 종목 카테고리 (티커: 종목명) ──────────────────
STOCK_CATEGORIES = {
    "🤖 AI / 소프트웨어": {
        "네이버 (035420.KS)": "035420.KS",
        "카카오 (035720.KS)": "035720.KS",
        "삼성SDS (018260.KS)": "018260.KS",
        "더존비즈온 (012510.KS)": "012510.KS",
        "솔트룩스 (304100.KQ)": "304100.KQ",
        "코난테크놀로지 (402030.KQ)": "402030.KQ",
    },
    "🔌 반도체": {
        "삼성전자 (005930.KS)": "005930.KS",
        "SK하이닉스 (000660.KS)": "000660.KS",
        "DB하이텍 (000990.KS)": "000990.KS",
        "리노공업 (058470.KQ)": "058470.KQ",
        "한미반도체 (042700.KS)": "042700.KS",
        "이오테크닉스 (039030.KQ)": "039030.KQ",
        "원익IPS (240810.KQ)": "240810.KQ",
    },
    "🦾 로봇 / 자동화": {
        "두산로보틱스 (454910.KS)": "454910.KS",
        "레인보우로보틱스 (277810.KQ)": "277810.KQ",
        "로보스타 (090360.KQ)": "090360.KQ",
        "에스비비테크 (389500.KQ)": "389500.KQ",
        "휴림로봇 (090710.KQ)": "090710.KQ",
        "현대위아 (011210.KS)": "011210.KS",
    },
}

# ── 사이드바: 사용자 입력 ──────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    category = st.selectbox("📂 카테고리 선택", options=list(STOCK_CATEGORIES.keys()))

    stock_dict = STOCK_CATEGORIES[category]
    stock_name = st.selectbox("🏢 종목 선택", options=list(stock_dict.keys()))
    ticker_input = stock_dict[stock_name]

    with st.expander("✏️ 직접 티커 입력하기"):
        custom_ticker = st.text_input("종목 코드 (예: 000270.KS 기아)", value="")
        if custom_ticker:
            ticker_input = custom_ticker.strip()

    st.markdown("---")

    period_option = st.selectbox(
        "기간 선택",
        options=["1개월", "3개월", "6개월", "1년", "2년", "5년", "직접 선택"],
        index=3
    )

    period_map = {
        "1개월": 30, "3개월": 90, "6개월": 180,
        "1년": 365, "2년": 730, "5년": 1825
    }

    if period_option == "직접 선택":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=365))
        with col2:
            end_date = st.date_input("종료일", datetime.now())
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_map[period_option])

    st.markdown("---")
    st.subheader("📊 보조 지표")
    show_ma = st.checkbox("이동평균선 (MA)", value=True)
    ma_periods = st.multiselect(
        "이동평균 기간",
        options=[5, 20, 60, 120, 200],
        default=[20, 60]
    ) if show_ma else []

    show_volume = st.checkbox("거래량", value=True)
    show_rsi = st.checkbox("RSI (상대강도지수)", value=True)

    st.markdown("---")
    chart_type = st.radio("차트 유형", ["캔들스틱", "라인"], index=0)


# ── 데이터 로드 함수 ────────────────────────────
@st.cache_data(ttl=3600)
def load_stock_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_ticker_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info
    except Exception:
        return {}


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ── 메인 로직 ──────────────────────────────────
if ticker_input:
    with st.spinner(f"{ticker_input} 데이터를 불러오는 중..."):
        df = load_stock_data(ticker_input, start_date, end_date)
        info = load_ticker_info(ticker_input)

    if df is None or df.empty:
        st.error("데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요. (코스피: .KS / 코스닥: .KQ)")
    else:
        company_name = info.get("longName", stock_name if not custom_ticker else ticker_input)
        currency = info.get("currency", "KRW")
        st.subheader(f"{company_name} ({ticker_input.upper()})")

        last_close = df["Close"].iloc[-1]
        prev_close = df["Close"].iloc[-2] if len(df) > 1 else last_close
        change = last_close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("현재가", f"{last_close:,.0f} {currency}", f"{change:+.0f} ({change_pct:+.2f}%)")
        col2.metric("최고가", f"{df['High'].max():,.0f}")
        col3.metric("최저가", f"{df['Low'].min():,.0f}")
        col4.metric("평균 거래량", f"{df['Volume'].mean():,.0f}")
        col5.metric("변동성(표준편차)", f"{df['Close'].std():,.0f}")

        st.markdown("---")

        # ── 이동평균 계산 ──
        for p in ma_periods:
            df[f"MA{p}"] = df["Close"].rolling(window=p).mean()

        # ── RSI 계산 ──
        if show_rsi:
            df["RSI"] = calc_rsi(df["Close"])

        # ── 서브플롯 구성 ──
        row_heights = [0.6]
        rows = 1
        specs_titles = ["가격"]
        if show_volume:
            row_heights.append(0.2)
            rows += 1
            specs_titles.append("거래량")
        if show_rsi:
            row_heights.append(0.2)
            rows += 1
            specs_titles.append("RSI")

        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=specs_titles
        )

        # ── 가격 차트 ──
        if chart_type == "캔들스틱":
            fig.add_trace(
                go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"],
                    name="가격",
                    increasing_line_color="#EF5350",   # 국내 관례: 상승 빨강
                    decreasing_line_color="#2962FF"    # 하락 파랑
                ),
                row=1, col=1
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["Close"], mode="lines",
                    name="종가", line=dict(color="#4C8BF5", width=2)
                ),
                row=1, col=1
            )

        # ── 이동평균선 ──
        ma_colors = ["#FFA726", "#AB47BC", "#66BB6A", "#EC407A", "#29B6F6"]
        for i, p in enumerate(ma_periods):
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df[f"MA{p}"], mode="lines",
                    name=f"MA{p}",
                    line=dict(color=ma_colors[i % len(ma_colors)], width=1.3)
                ),
                row=1, col=1
            )

        current_row = 2

        # ── 거래량 (국내 관례: 상승 빨강 / 하락 파랑) ──
        if show_volume:
            colors = ["#2962FF" if row["Close"] < row["Open"] else "#EF5350" for _, row in df.iterrows()]
            fig.add_trace(
                go.Bar(x=df.index, y=df["Volume"], name="거래량", marker_color=colors),
                row=current_row, col=1
            )
            current_row += 1

        # ── RSI ──
        if show_rsi:
            fig.add_trace(
                go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI", line=dict(color="#7E57C2")),
                row=current_row, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)

        fig.update_layout(
            height=800,
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=40, b=10)
        )

        st.plotly_chart(fig, use_container_width=True)

        # ── 같은 카테고리 내 종목 비교 ──
        with st.expander(f"📊 {category} 카테고리 종목 비교 (수익률 %)"):
            compare_tickers = list(stock_dict.values())
            compare_names = list(stock_dict.keys())

            with st.spinner("비교 데이터를 불러오는 중..."):
                compare_df = pd.DataFrame()
                for name, tkr in zip(compare_names, compare_tickers):
                    try:
                        d = load_stock_data(tkr, start_date, end_date)
                        if d is not None and not d.empty:
                            normalized = (d["Close"] / d["Close"].iloc[0] - 1) * 100
                            compare_df[name] = normalized
                    except Exception:
                        continue

            if not compare_df.empty:
                fig_compare = go.Figure()
                for col in compare_df.columns:
                    fig_compare.add_trace(
                        go.Scatter(x=compare_df.index, y=compare_df[col], mode="lines", name=col)
                    )
                fig_compare.update_layout(
                    template="plotly_white",
                    height=450,
                    yaxis_title="수익률 (%)",
                    hovermode="x unified",
                    margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig_compare, use_container_width=True)

        # ── 데이터 테이블 ──
        with st.expander("📋 원본 데이터 보기"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

            csv = df.to_csv().encode("utf-8-sig")
            st.download_button(
                "CSV로 다운로드", data=csv,
                file_name=f"{ticker_input}_stock_data.csv", mime="text/csv"
            )

        # ── 종목 상세 정보 ──
        with st.expander("ℹ️ 기업 정보"):
            info_cols = st.columns(2)
            with info_cols[0]:
                st.write(f"**섹터:** {info.get('sector', 'N/A')}")
                st.write(f"**산업:** {info.get('industry', 'N/A')}")
                market_cap = info.get('marketCap')
                st.write(f"**시가총액:** {market_cap:,}" if market_cap else "**시가총액:** N/A")
            with info_cols[1]:
                st.write(f"**PER:** {info.get('trailingPE', 'N/A')}")
                st.write(f"**배당수익률:** {info.get('dividendYield', 'N/A')}")
                st.write(f"**웹사이트:** {info.get('website', 'N/A')}")
else:
    st.info("👈 왼쪽 사이드바에서 종목을 선택해주세요.")

st.markdown("---")
st.caption("⚠️ 본 정보는 투자 참고용이며, 투자 판단의 책임은 본인에게 있습니다.")
