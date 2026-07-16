import pandas as pd


def export(trades):

    rows = []

    for t in trades:

        rows.append({

            "Symbol": t.symbol,

            "Side": t.side,

            "Entry Time": t.entry_time,

            "Exit Time": t.exit_time,

            "Entry": t.entry_price,

            "Exit": t.exit_price,

            "Qty": t.quantity,

            "PnL": t.pnl,

            "Exit Reason": t.exit_reason,

            "RR": t.rr,

            "ATR": t.atr,

        })

    df = pd.DataFrame(rows)

    df.to_csv(

        "reports/trades.csv",

        index=False,

    )

    return df