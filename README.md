# 🩺 Company Health Checker

A small web app that checks the financial health of any NSE-listed Indian company.
Type a symbol (like `INFY` or `ITC`). The app downloads the company's yearly financial
statements from Yahoo Finance, works out five key MBA finance ratios, and gives each one
a **Healthy / Watch / Risky** rating with a plain-English reason, plus an overall score out of 100.

## What it checks

| Ratio | Formula | What it tells you |
|---|---|---|
| Net Profit Margin | Net Profit ÷ Revenue | How much of each ₹100 of sales becomes profit |
| Return on Equity (ROE) | Net Profit ÷ Shareholders' Equity | How well the company uses its owners' money |
| Debt-to-Equity | Total Debt ÷ Equity | How much the company relies on borrowed money |
| Current Ratio | Current Assets ÷ Current Liabilities | Whether it can pay bills due within a year |
| Revenue Growth | (This year − Last year) ÷ Last year | Whether sales are growing |

Scoring: Healthy = 2 points, Watch = 1, Risky = 0, converted to a score out of 100.

## Tech used
- **Python** and **pandas**: tables and calculations
- **yfinance**: free financial data from Yahoo Finance
- **Streamlit**: turns a Python script into a web page

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at http://localhost:8501.

## Files
- `health.py`: fetches data, calculates the ratios, rates them
- `app.py`: the web page

## Limitations
- Banks and insurance companies don't report current assets and liabilities the usual way, so some ratios show N/A for them.
- The thresholds are simple rules of thumb for learning. This app is not investment advice.
