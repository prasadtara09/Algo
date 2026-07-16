from data.universe import UNIVERSE_FILE, refresh_nifty200_symbols


def main():
    symbols = refresh_nifty200_symbols()
    print(f"Saved {len(symbols)} NIFTY 200 symbols to {UNIVERSE_FILE}")


if __name__ == "__main__":
    main()
