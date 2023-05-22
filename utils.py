import pandas as pd


def load_tickers(name):
    ticker_db = pd.read_csv(name + '.csv')
    return list(ticker_db.Symbol)


