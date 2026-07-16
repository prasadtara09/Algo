"""Read-only Streamlit dashboard for the latest bot reports.

Run with: streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


REPORTS_DIR = Path("reports")


@st.cache_data(ttl=10)
def read_csv(name):
    path = REPORTS_DIR / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data(ttl=10)
def read_metrics():
    path = REPORTS_DIR / "metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def currency(value):
    return f"₹{value:,.2f}" if value is not None else "—"


def main():
    st.set_page_config(page_title="Trade Bot Dashboard", page_icon="📈", layout="wide")
    st.title("Trade Bot Dashboard")
    st.caption("Backtest and paper-trading reports only — no live order controls.")

    metrics = read_metrics()
    trades = read_csv("trades.csv")
    equity = read_csv("equity_curve.csv")
    monthly = read_csv("monthly_returns.csv")
    signals = read_csv("latest_signals.csv")

    overview, scanner, trade_log, analytics = st.tabs(["Overview", "Scanner", "Trades", "Analytics"])

    with overview:
        if not metrics:
            st.info("Run `python run_backtest.py` to populate the dashboard.")
        else:
            columns = st.columns(5)
            columns[0].metric("Final equity", currency(metrics.get("FinalEquity")))
            columns[1].metric("Net P&L", currency(metrics.get("NetPnL")))
            columns[2].metric("Profit factor", metrics.get("ProfitFactor", "—"))
            columns[3].metric("Win rate", f"{metrics.get('WinRate', 0):.2f}%")
            columns[4].metric("Max drawdown", f"{metrics.get('MaxDrawdownPct', 0):.2f}%")
            if not equity.empty:
                st.plotly_chart(px.line(equity, x="Time", y="Equity", title="Equity curve"), use_container_width=True)

    with scanner:
        st.caption("Signals use the latest completed candle and all configured filters.")
        if signals.empty:
            st.info("No current signals meet every filter. Refresh the universe, then run `python run_scanner.py`.")
        else:
            st.dataframe(signals, use_container_width=True, hide_index=True)

    with trade_log:
        if trades.empty:
            st.info("No completed trades are available yet.")
        else:
            st.dataframe(trades, use_container_width=True, hide_index=True)

    with analytics:
        if metrics:
            st.json(metrics)
        if not monthly.empty:
            st.plotly_chart(px.bar(monthly, x="Month", y="PnL", title="Monthly P&L"), use_container_width=True)


if __name__ == "__main__":
    main()
