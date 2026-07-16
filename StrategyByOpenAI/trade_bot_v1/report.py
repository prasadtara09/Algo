import pandas as pd

def generate_report(df):

    if df.empty:

        print("No Trades")

        return

    wins = df[df.pnl > 0]

    loss = df[df.pnl <= 0]

    print(df)

    print()

    print("Trades :", len(df))

    print("Wins :", len(wins))

    print("Loss :", len(loss))

    print("Win Rate :", round(len(wins)/len(df)*100,2), "%")

    print("Net Profit :", round(df.pnl.sum(),2))

    print("Average Trade :", round(df.pnl.mean(),2))

    df.to_csv("trade_report.csv", index=False)