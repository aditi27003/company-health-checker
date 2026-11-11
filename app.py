"""
app.py  -  the web page.

Run it with:   streamlit run app.py
Streamlit turns this Python file into a website in your browser.
Each st.something() line puts one thing on the page.
"""

import streamlit as st
from health import make_ticker, fetch_statements, calculate_ratios, health_report

st.set_page_config(page_title="Company Health Checker", page_icon="🩺", layout="centered")

st.title("🩺 Company Health Checker")
st.write("Type an Indian company's NSE symbol to check its financial health "
         "using the ratios from MBA finance.")

# ---- Input box ----
col1, col2 = st.columns([3, 1])
with col1:
    symbol = st.text_input("NSE symbol", value="INFY",
                           help="Examples: INFY, TCS, RELIANCE, ITC, ASIANPAINT, MARUTI")
with col2:
    st.write("")
    st.write("")
    go = st.button("Check", type="primary", use_container_width=True)

COLOURS = {"Healthy": "🟢", "Watch": "🟡", "Risky": "🔴", "N/A": "⚪"}

if go:
    ticker = make_ticker(symbol)
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            name, income, balance = fetch_statements(ticker)
            df = calculate_ratios(income, balance)
    except Exception as e:
        st.error(str(e))
        st.stop()

    rows, score, verdict = health_report(df)

    # ---- Headline score ----
    st.header(name)
    st.metric("Overall health score", f"{score} / 100", help="Healthy = 2 points, Watch = 1, Risky = 0")
    st.subheader(f"{COLOURS[verdict]} Verdict: {verdict}")
    st.caption(f"Based on the latest year available ({df.index[-1]}).")

    # ---- One card per ratio ----
    st.divider()
    for r in rows:
        value = "—" if r["Value"] != r["Value"] else f"{r['Value']:.2f}"   # NaN check
        st.markdown(f"**{COLOURS[r['Rating']]} {r['Ratio']}: {value}**  \n{r['Why']}")

    # ---- Trends over the years ----
    st.divider()
    st.subheader("Sales and profit over the years (₹ crore)")
    crore = df[["Revenue", "Net Profit"]] / 1e7          # 1 crore = 10,000,000
    crore.index = crore.index.astype(str)
    st.bar_chart(crore)

    st.subheader("All ratios by year")
    table = df[["Profit Margin %", "ROE %", "Debt to Equity",
                "Current Ratio", "Revenue Growth %"]].round(2)
    table.index = table.index.astype(str)
    st.dataframe(table, use_container_width=True)

    st.caption("For learning only, not investment advice. Data: Yahoo Finance.")
