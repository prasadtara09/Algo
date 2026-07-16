import pandas as pd

def backtest(df, symbol, capital=100000):

    trades = []

    position = False

    entry = 0

    qty = 0

    stop = 0

    target = 0

    for i in range(50, len(df)):

        row = df.iloc[i]

        if not position:

            from strategy import buy_signal

            if buy_signal(df, i):

                entry = row["Close"]

                atr = row["ATR"]

                stop = entry - 1.5 * atr

                target = entry + 3 * atr

                risk = entry - stop

                if risk <= 0:
                    continue

                qty = max(
                    1,
                    int((capital * 0.01) / risk)
                )

                position = True

        else:

            exit_trade = False

            exit_price = row["Close"]

            # Stop Loss

            if row["Low"] <= stop:

                exit_trade = True

                exit_price = stop

            # Target

            elif row["High"] >= target:

                exit_trade = True

                exit_price = target

            # EMA Exit

            elif row["Close"] < row["EMA20"]:

                exit_trade = True

                exit_price = row["Close"]

            if exit_trade:

                pnl = (exit_price - entry) * qty

                trades.append({

                    "symbol": symbol,

                    "entry_price": round(entry,2),

                    "exit_price": round(exit_price,2),

                    "pnl": round(pnl,2)

                })

                position = False

    return pd.DataFrame(trades)