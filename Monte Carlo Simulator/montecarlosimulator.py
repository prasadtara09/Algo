import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


def permutation_test_positive_edge(trade_pnl, permutations=10000, seed=None):
    """Randomization test of H0: mean P&L = 0 against H1: mean P&L > 0.

    Under the null, each observed trade magnitude is equally likely to have
    either sign.  The +1 correction keeps the Monte Carlo p-value valid even
    when no randomized sample is as profitable as the observed sample.
    """
    values = np.asarray(trade_pnl, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Permutation testing requires at least one trade.")
    if permutations < 1:
        raise ValueError("Permutation count must be at least 1.")

    rng = np.random.default_rng(seed)
    observed_mean = float(np.mean(values))
    null_means = np.empty(permutations, dtype=float)

    # Work in chunks so large trade logs do not create a huge temporary array.
    chunk_size = max(1, min(permutations, 1_000_000 // values.size))
    magnitudes = np.abs(values)
    for start in range(0, permutations, chunk_size):
        stop = min(start + chunk_size, permutations)
        signs = rng.choice((-1.0, 1.0), size=(stop - start, values.size))
        null_means[start:stop] = np.mean(signs * magnitudes, axis=1)

    p_value = (np.count_nonzero(null_means >= observed_mean) + 1) / (permutations + 1)
    return observed_mean, null_means, float(p_value)

# --- UI Configuration ---
st.set_page_config(page_title="Quantitative Monte Carlo Simulator", layout="wide", initial_sidebar_state="expanded")
st.title("📈 Institutional Monte Carlo Risk Simulator")
st.markdown("Upload your backtest trade log to automatically extract your edge and stress-test sequence risk.")


def clean_numeric_series(series: pd.Series) -> pd.Series:
    """
    Convert a column to numeric even if it contains currency symbols,
    commas, percent signs, or stray whitespace. Anything that can't be
    parsed becomes NaN (and is dropped later), rather than silently
    being compared as a string.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(r"[₹$,%]", "", regex=True)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # (123.45) -> -123.45
    )
    return pd.to_numeric(cleaned, errors="coerce")


def guess_pnl_column(columns) -> int:
    """
    Try to default the selectbox to the column that actually looks like
    a signed P&L figure, instead of just picking the first column.
    Priority: exact/near matches on common P&L naming conventions.
    """
    normalized = [c.strip().lower() for c in columns]

    priority_patterns = [
        r"^pnl[_ ]?absolute$",
        r"pnl.*absolute",
        r"^pnl$",
        r"p&?l",
        r"profit.*loss",
        r"net.*profit",
        r"reali[sz]ed.*pnl",
    ]

    for pattern in priority_patterns:
        for i, name in enumerate(normalized):
            if re.search(pattern, name):
                return i

    # Fallback: first column that isn't obviously a price/size/fee/timestamp field
    exclude_keywords = ["price", "size", "fee", "timestamp", "id", "ticker", "symbol", "side", "status", "percent", "%"]
    for i, name in enumerate(normalized):
        if not any(k in name for k in exclude_keywords):
            return i

    return 0


# --- Sidebar Inputs & File Uploader ---
with st.sidebar:
    st.header("1. Ingest Trade Data")
    uploaded_file = st.file_uploader("Upload Trade Log", type=["csv", "json"])

    st.header("2. Simulation Parameters")
    capital = st.number_input("Starting Capital (₹)", value=10000, step=1000)
    simulations = st.number_input("Simulation Count", value=1000, step=500)
    run_permutation_test = st.checkbox(
        "Run permutation test",
        value=True,
        help="Tests whether average P&L is significantly greater than zero using random sign flips."
    )
    if run_permutation_test:
        permutations = st.number_input("Permutation Count", min_value=100, value=10000, step=1000)
        random_seed = st.number_input("Random Seed", min_value=0, value=42, step=1)

if uploaded_file is not None:
    # --- Data Parsing Engine ---
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_json(uploaded_file)

        # Strip stray whitespace from column names (common in exported CSVs)
        df.columns = [c.strip() for c in df.columns]

        # Auto-select the most likely P&L column, but let the user override it
        default_idx = guess_pnl_column(df.columns)
        pnl_col = st.sidebar.selectbox(
            "Select P&L Column",
            df.columns,
            index=default_idx,
            help="Auto-detected based on column name. Change this if it picked the wrong one."
        )

        # Extract and properly clean the raw trade outcomes
        raw_series = clean_numeric_series(df[pnl_col])
        n_unparsed = raw_series.isna().sum() - df[pnl_col].isna().sum()
        raw_trades = raw_series.dropna().values
        trades = len(raw_trades)

        if trades == 0:
            st.error("No valid numeric trade data found in this column. Try a different column.")
            st.stop()

        if n_unparsed > 0:
            st.sidebar.warning(f"{n_unparsed} value(s) in '{pnl_col}' couldn't be parsed as numbers and were excluded.")

        # Automatically calculate the strategy's DNA
        wins = raw_trades[raw_trades > 0]
        losses = raw_trades[raw_trades < 0]
        breakeven = raw_trades[raw_trades == 0]

        win_rate = len(wins) / trades
        loss_rate = len(losses) / trades
        avg_win = np.mean(wins) if len(wins) > 0 else 0
        avg_loss = abs(np.mean(losses)) if len(losses) > 0 else 0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        profit_factor = (win_rate * avg_win) / (loss_rate * avg_loss) if (loss_rate * avg_loss) != 0 else float('inf')
        win_loss_ratio = avg_win / avg_loss if avg_loss != 0 else 1.0
        kelly_pct = win_rate - (loss_rate / win_loss_ratio) if win_loss_ratio > 0 else 0

        # --- Verification panel so you can sanity-check the numbers yourself ---
        with st.expander("🔍 Verify column selection & win/loss counts", expanded=False):
            st.write(f"**Column used:** `{pnl_col}`")
            st.write(f"Wins: {len(wins)} | Losses: {len(losses)} | Breakeven: {len(breakeven)} | Total: {trades}")
            st.dataframe(df[[pnl_col]].head(10))

        # --- Top Level Metrics Board ---
        st.subheader(f"Extracted Strategy DNA ({trades} Trades)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.metric("Win Rate", f"{win_rate * 100:.1f}%")
        col2.metric("Avg Win", f"₹{avg_win:,.2f}")
        col3.metric("Avg Loss", f"₹{avg_loss:,.2f}")

        exp_color = "normal" if expectancy > 0 else "inverse"
        col4.metric("Expectancy (Edge)", f"₹{expectancy:,.2f}", delta="Positive" if expectancy > 0 else "Negative", delta_color=exp_color)
        col5.metric("Profit Factor", f"{profit_factor:.2f}")
        col6.metric("Kelly Criterion", f"{kelly_pct * 100:.2f}%")

        if run_permutation_test:
            with st.spinner("Testing the edge against randomized outcomes..."):
                observed_mean, null_means, p_value = permutation_test_positive_edge(
                    raw_trades, int(permutations), int(random_seed)
                )

            st.markdown("---")
            st.subheader("Permutation Test: Is the Edge Greater Than Zero?")
            test_col, chart_col = st.columns([1, 2])
            with test_col:
                st.metric("One-sided p-value", f"{p_value:.4f}")
                st.metric("Observed mean P&L", f"₹{observed_mean:,.2f}")
                if p_value < 0.05:
                    st.success("Statistically significant at the 5% level: the data supports a positive edge.")
                else:
                    st.warning("Not significant at the 5% level. The observed edge may be due to chance or the sample may be too small.")
                st.caption(
                    "H₀: mean trade P&L is zero. H₁: mean trade P&L is positive. "
                    "Trade magnitudes are retained while their signs are randomized."
                )
            with chart_col:
                fig_perm, ax_perm = plt.subplots(figsize=(8, 3.5))
                fig_perm.patch.set_facecolor('#0E1117')
                ax_perm.set_facecolor('#0E1117')
                ax_perm.hist(null_means, bins=40, color='#4c78a8', alpha=0.8)
                ax_perm.axvline(observed_mean, color='#00f900', linestyle='dashed', linewidth=2, label='Observed mean')
                ax_perm.set_xlabel("Mean P&L under H₀ (₹)", color='white')
                ax_perm.set_ylabel("Frequency", color='white')
                ax_perm.tick_params(colors='white')
                ax_perm.legend()
                for spine in ax_perm.spines.values():
                    spine.set_color('#333333')
                st.pyplot(fig_perm)
                plt.close(fig_perm)

        if expectancy <= 0:
            st.error("⚠️ **Warning:** The uploaded data shows a negative mathematical expectancy. A Monte Carlo simulation is not necessary because the baseline strategy lacks an edge.")
        else:
            # --- Monte Carlo Engine ---
            with st.spinner("Shuffling historical sequences..."):
                # Instead of theoretical probabilities, we sample directly from your actual trade history
                random_indices = np.random.randint(0, trades, size=(simulations, trades))
                simulated_trades = raw_trades[random_indices]

                # Calculate cumulative equity curves
                equity_curves = capital + np.cumsum(simulated_trades, axis=1)

                # Calculate Drawdowns
                running_max = np.maximum.accumulate(equity_curves, axis=1)
                running_max = np.maximum(running_max, capital)
                drawdowns = (running_max - equity_curves) / running_max
                max_drawdowns = np.max(drawdowns, axis=1)

                worst_case_dd = np.percentile(max_drawdowns, 95)

                st.markdown("---")
                st.subheader(f"Simulation Results (95th Percentile Risk: {worst_case_dd * 100:.2f}%)")

                # --- Visualizations ---
                fig_col, hist_col = st.columns([2, 1])

                with fig_col:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    fig.patch.set_facecolor('#0E1117')
                    ax.set_facecolor('#0E1117')

                    for i in range(min(100, simulations)):
                        ax.plot(equity_curves[i], color='#00f900' if equity_curves[i][-1] > capital else '#ff4b4b', alpha=0.1)

                    ax.axhline(capital, color='white', linestyle='--', alpha=0.5)
                    ax.set_ylabel("Account Equity (₹)", color='white')
                    ax.set_xlabel("Trade Number", color='white')
                    ax.tick_params(colors='white')
                    for spine in ax.spines.values():
                        spine.set_color('#333333')

                    st.pyplot(fig)
                    plt.close(fig)

                with hist_col:
                    fig_hist, ax_hist = plt.subplots(figsize=(5, 4))
                    fig_hist.patch.set_facecolor('#0E1117')
                    ax_hist.set_facecolor('#0E1117')

                    ax_hist.hist(max_drawdowns * 100, bins=30, color='#ff4b4b', alpha=0.7)
                    ax_hist.axvline(worst_case_dd * 100, color='white', linestyle='dashed', linewidth=2)
                    ax_hist.set_xlabel("Max Drawdown (%)", color='white')
                    ax_hist.set_ylabel("Frequency", color='white')
                    ax_hist.tick_params(colors='white')
                    for spine in ax_hist.spines.values():
                        spine.set_color('#333333')

                    st.pyplot(fig_hist)
                    plt.close(fig_hist)

    except Exception as e:
        st.error(f"Error processing file: {e}. Please ensure it is a valid CSV or JSON.")
else:
    st.info("👈 Please upload a CSV or JSON file containing your trade history to begin.")
