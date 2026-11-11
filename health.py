"""
health.py  -  the "brain" of the app.

This file does three jobs:
  1. Fetch a company's financial statements from Yahoo Finance (free).
  2. Calculate the key ratios we learn in MBA finance.
  3. Give each ratio a simple rating: Healthy / Watch / Risky.

The web page itself lives in app.py. Keeping the maths here means
you can test it without opening the website.
"""

import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# 1. FETCHING DATA
# ---------------------------------------------------------------------------

def make_ticker(name: str) -> str:
    """Indian stocks on Yahoo end with .NS (NSE). Add it if the user forgot.
    Example: 'infy' -> 'INFY.NS'"""
    name = name.strip().upper()
    if "." not in name:
        name += ".NS"
    return name


def fetch_statements(ticker: str):
    """Download the yearly Income Statement and Balance Sheet.

    Returns (company_name, income_statement, balance_sheet).
    Each statement is a table: rows = line items (e.g. 'Net Income'),
    columns = years.
    """
    t = yf.Ticker(ticker)
    income = t.financials          # yearly profit & loss
    balance = t.balance_sheet      # yearly balance sheet
    if income is None or income.empty:
        raise ValueError(
            f"No data found for '{ticker}'. Check the symbol "
            "(e.g. INFY, TCS, RELIANCE, ITC)."
        )
    try:
        company_name = t.info.get("longName", ticker)
    except Exception:
        company_name = ticker
    return company_name, income, balance


# ---------------------------------------------------------------------------
# 2. CALCULATING RATIOS
# ---------------------------------------------------------------------------

def pick_row(table: pd.DataFrame, possible_names: list[str]) -> pd.Series | None:
    """Yahoo sometimes names the same item differently for different
    companies. We try each name in order and return the first that exists."""
    for name in possible_names:
        if name in table.index:
            return table.loc[name]
    return None


def calculate_ratios(income: pd.DataFrame, balance: pd.DataFrame) -> pd.DataFrame:
    """Build one table with the key numbers and ratios for each year."""
    revenue = pick_row(income, ["Total Revenue", "Operating Revenue"])
    profit = pick_row(income, ["Net Income", "Net Income Common Stockholders"])
    equity = pick_row(balance, ["Stockholders Equity", "Common Stock Equity",
                                "Total Equity Gross Minority Interest"])
    debt = pick_row(balance, ["Total Debt"])
    cur_assets = pick_row(balance, ["Current Assets"])
    cur_liab = pick_row(balance, ["Current Liabilities"])

    df = pd.DataFrame({
        "Revenue": revenue,
        "Net Profit": profit,
        "Equity": equity,
        "Debt": debt,
        "Current Assets": cur_assets,
        "Current Liabilities": cur_liab,
    })

    # Columns from Yahoo are dates; turn them into simple years, oldest first.
    df.index = pd.to_datetime(df.index).year
    df = df.sort_index()
    df = df.dropna(subset=["Revenue", "Net Profit"])   # skip empty years

    # --- The ratios (all in %, except D/E and Current Ratio) ---
    # Net Profit Margin: out of every Rs 100 of sales, how much is profit?
    df["Profit Margin %"] = df["Net Profit"] / df["Revenue"] * 100
    # ROE: how much profit the company makes on shareholders' money.
    df["ROE %"] = df["Net Profit"] / df["Equity"] * 100
    # Debt-to-Equity: how much borrowed money per Rs 1 of owners' money.
    df["Debt to Equity"] = df["Debt"] / df["Equity"]
    # Current Ratio: can the company pay bills due within a year?
    df["Current Ratio"] = df["Current Assets"] / df["Current Liabilities"]
    # Revenue Growth: how much sales grew compared to last year.
    df["Revenue Growth %"] = df["Revenue"].pct_change() * 100

    return df


# ---------------------------------------------------------------------------
# 3. RATING EACH RATIO
# ---------------------------------------------------------------------------
# Each rule: (good_if_above, risky_if_below) for "higher is better" ratios.
# These are simple rules of thumb for learning, not investment advice.

def rate(ratio: str, value: float) -> tuple[str, str]:
    """Return (rating, plain-English reason) for one ratio value."""
    if pd.isna(value):
        return "N/A", "Data not available (common for banks and insurers)."

    if ratio == "Profit Margin %":
        if value >= 15:
            return "Healthy", f"Keeps Rs {value:.0f} as profit from every Rs 100 of sales. Strong."
        if value >= 5:
            return "Watch", f"Keeps Rs {value:.0f} from every Rs 100 of sales. Okay, not great."
        return "Risky", f"Keeps only Rs {value:.1f} from every Rs 100 of sales (or is making a loss)."

    if ratio == "ROE %":
        if value >= 15:
            return "Healthy", f"Earns {value:.0f}% a year on shareholders' money. Better than an FD."
        if value >= 8:
            return "Watch", f"Earns {value:.0f}% on shareholders' money. Similar to safe investments."
        return "Risky", f"Earns only {value:.1f}% on shareholders' money."

    if ratio == "Debt to Equity":            # lower is better
        if value <= 0.5:
            return "Healthy", f"Borrows Rs {value:.2f} for every Rs 1 of its own money. Low debt."
        if value <= 1.5:
            return "Watch", f"Borrows Rs {value:.2f} for every Rs 1 of its own money. Moderate debt."
        return "Risky", f"Borrows Rs {value:.2f} for every Rs 1 of its own money. Heavy debt."

    if ratio == "Current Ratio":
        if value >= 1.5:
            return "Healthy", f"Has Rs {value:.2f} of short-term assets for every Rs 1 of bills due soon."
        if value >= 1:
            return "Watch", f"Has Rs {value:.2f} for every Rs 1 of bills due soon. Just enough."
        return "Risky", f"Has only Rs {value:.2f} for every Rs 1 of bills due soon."

    if ratio == "Revenue Growth %":
        if value >= 10:
            return "Healthy", f"Sales grew {value:.0f}% last year."
        if value >= 0:
            return "Watch", f"Sales grew only {value:.1f}% last year."
        return "Risky", f"Sales fell {abs(value):.1f}% last year."

    return "N/A", ""


RATIOS = ["Profit Margin %", "ROE %", "Debt to Equity", "Current Ratio", "Revenue Growth %"]
POINTS = {"Healthy": 2, "Watch": 1, "Risky": 0}


def health_report(df: pd.DataFrame) -> tuple[list[dict], int, str]:
    """Rate the latest year's ratios and combine them into a score out of 100."""
    latest = df.iloc[-1]
    rows, points, counted = [], 0, 0
    for r in RATIOS:
        rating, reason = rate(r, latest[r])
        rows.append({"Ratio": r, "Value": latest[r], "Rating": rating, "Why": reason})
        if rating in POINTS:
            points += POINTS[rating]
            counted += 1

    score = round(points / (2 * counted) * 100) if counted else 0
    if score >= 70:
        verdict = "Healthy"
    elif score >= 40:
        verdict = "Watch"
    else:
        verdict = "Risky"
    return rows, score, verdict
