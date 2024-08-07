from datetime import datetime
from lumibot.brokers import Alpaca 
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies import Strategy
from lumibot.traders import Trader

#ML
from finbert_utils import estimate_sentiment

#news
from alpaca_trade_api import REST
from timedelta import Timedelta

#credentials
from credentials import API_KEY, API_SECRET, BASE_URL

ALPACA_CONFIG = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLStrategy(Strategy): 
    def initialize(self, symbol: str = "SPY", cash_at_risk: float=.10): 
        self.symbol = symbol
        self.sleeptime = "12H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
    
    def position_sizing(self):
        cash = self.get_cash()
        # if broker.is_market_open():
        #     last_price = self.get_last_price(self.symbol)
        #     print(f"Last Price: {last_price:.2f}")
        # else:
        #     print("market is closed")
        last_price = self.get_last_price(self.symbol)
        quantity = cash * self.cash_at_risk // last_price
        return cash, last_price, quantity
    
    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, 
                                 start=three_days_prior, 
                                 end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        probability, sentiment = self.get_sentiment()
        if cash > last_price: 
            if sentiment == "positive" and probability > .90: 
                if self.last_trade == "sell": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type="bracket", 
                    take_profit_price=last_price*1.20, 
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order) 
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > .90: 
                if self.last_trade == "buy": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell", 
                    type="bracket", 
                    take_profit_price=last_price*.8, 
                    stop_loss_price=last_price*1.05
                )
                self.submit_order(order) 
                self.last_trade = "sell"


if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = MLStrategy(name="mlstrategy", broker=broker, parameters={"symbol":"AAPL", "cash_at_risk": .5})

    start_date = datetime(2023, 7, 1)
    end_date = datetime(2023, 7, 31)

    strategy.backtest(
        YahooDataBacktesting, 
        start_date, 
        end_date, 
        parameters={"symbol":"AAPL", "cash_at_risk": .5}
    )