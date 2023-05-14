import backtrader as bt
import backtrader.analyzers as bt_analyzers
import yfinance as yf
import pandas as pd

from strategies import BollingerStrategy, SmaCross, BuyAndHold


def single_run(ticker, starting_cash, stake_type, strategy):
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

    return (
        cerebro.broker.getvalue(),
        result_obj.analyzers.summary.get_analysis()["rnorm100"],
    )


class MultiRunner:
    def __init__(self):
        self.results = []
        self.strategies = (BollingerStrategy, SmaCross)
        self.stake_types = ("all_in", "fixed")

    def full_strategy_run(self, ticker, starting_cash):
        for strategy in self.strategies:
            for stake_type in self.stake_types:
                _, roi = single_run(ticker, starting_cash, stake_type, strategy)
                self.results.append([ticker, strategy.get_name(1), stake_type, roi])

    def multi_full_strategy_run(self, tickers, starting_cash):
        for ticker in tickers:
            self.full_strategy_run(ticker, starting_cash)

    def get_results(self):
        results = pd.DataFrame(self.results)
        results.columns = ("ticker", "strategy", "stake_type", "roi")
        results = results.sort_values("roi", ascending=False)
        return results


if __name__ == "__main__":
    runner = MultiRunner()
    runner.multi_full_strategy_run(
        tickers=("FSLR", "CTY.L", "SCHD", "EPD", "MODG"), starting_cash=5000
    )
    print(runner.get_results())
