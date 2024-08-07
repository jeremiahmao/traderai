from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies import Strategy
from lumibot.traders import Trader
from datetime import datetime

API_KEY = "PKDYWBSRKSK4IAX7CPBD"
API_SECRET = "6VEzwiEcSUOF7IUfNRfdstSomtknQvaexMWTqmd3"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLStrat(Strategy):
    def initialize(self, symbol: str = "SPY"):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None

    def on_trading_iteration(self):
        if not self.last_trade:
            order = self.create_order(
                self.symbol,
                10,
                "buy",
                type = "market"
            )
            self.submit_order(order)
            self.last_trade = "buy"



broker = Alpaca(ALPACA_CREDS)
strategy = MLStrat(name="mlstrat", broker = broker, parameters={"symbol":"SPY"})

start_date = datetime(2023, 7, 1)
end_date = datetime(2023, 8, 4)

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY"}
    )

