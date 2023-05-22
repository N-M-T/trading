import backtrader as bt
import backtrader.analyzers as bt_analyzers
import yfinance as yf
import pandas as pd
import financedatabase as fd
import timeit

from utils import load_tickers
from strategies import BollingerStrategy, SmaCross, BuyAndHold


def single_run(ticker, starting_cash, stake_type, strategy, plot=None):
    try:
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy)

        # generate ticker object and parse history
        ticker_object = yf.Ticker(ticker)
        history = ticker_object.history(period="1y")

        # download historical data
        data = bt.feeds.PandasData(dataname=yf.download(ticker, period="1y"))

        # calculate maximum stake based on available cash
        high = int(history["High"].iloc[-1])
        stake = int(starting_cash / high)

        # prepare cerebro
        cerebro.adddata(data)
        cerebro.broker.setcash(starting_cash)
        cerebro.broker.setcommission(commission=0.01)
        cerebro.addanalyzer(bt_analyzers.Returns, _name="summary")

        # determine stake type
        if stake_type == "all_in":
            cerebro.addsizer(bt.sizers.AllInSizerInt)
        else:
            cerebro.addsizer(bt.sizers.FixedSize, stake=stake)

        # run test
        result_obj = cerebro.run()[0]

        if plot:
            cerebro.plot()

        return (
            cerebro.broker.getvalue(),
            result_obj.analyzers.summary.get_analysis()["rnorm100"],
        )
    except Exception:
        return 0, 0


class MultiRunner:
    def __init__(self):
        self.results = []
        self.strategies = (BollingerStrategy, SmaCross)
        self.stake_types = ("all_in", "fixed")

    def full_strategy_run(self, ticker, fund_name, starting_cash):
        for strategy in self.strategies:
            for stake_type in self.stake_types:
                try:
                    _, roi = single_run(
                        ticker, starting_cash, stake_type, strategy
                    )
                except IndexError:
                    roi = 0

                self.results.append(
                    [ticker, fund_name, strategy.get_name(1), stake_type, roi]
                )

    def multi_full_strategy_run(self, funds, starting_cash):
        for index, row in funds.iterrows():
            ticker = index
            fund_name = row["name"]
            self.full_strategy_run(ticker, fund_name, starting_cash)

    def get_results(self):
        results = pd.DataFrame(self.results)
        results.columns = ("ticker", "name", "strategy", "stake_type", "roi")
        results = results.sort_values("roi", ascending=False)
        return results

    def results_flush(self):
        self.results = []


if __name__ == "__main__":
    # print(single_run('0P00000C3C.L', 5000, 'all_in', SmaCross, plot=False))

    funds = fd.Funds()
    funds_df = funds.select()

    '''funds_df = funds.select(
        category_group="Equities", category="United Kingdom", exclude_exchanges=False
    )'''

    runner = MultiRunner()
    runner.multi_full_strategy_run(funds=funds_df, starting_cash=5000)
    results = runner.get_results()
    results.to_pickle("results_Full.pkl")
    results.to_csv("results_Full.csv")

