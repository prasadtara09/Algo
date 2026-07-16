def calculate_score(row):

    score = 0

    details = []

    if row["EMA20"] > row["EMA50"]:

        score += 20

        details.append("EMA")

    if row["Close"] > row["EMA20"]:

        score += 15

        details.append("PRICE")

    if row["Close"] > row["VWAP"]:

        score += 20

        details.append("VWAP")

    if row["RSI"] > 55:

        score += 15

        details.append("RSI")

    if row["ADX"] > 25:

        score += 15

        details.append("ADX")

    if row["Volume"] > row["VOL_MA"]:

        score += 15

        details.append("VOL")

    return score, details