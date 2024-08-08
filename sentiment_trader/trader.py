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

class SentimentStrategy(Strategy): 
    def initialize(self, symbol: str = "SPY", max_cash_at_risk: float=.10, confidence_threshold: float=.999, emergency_threshold: float = .999, news_days_prior: int = 3): 
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.max_cash_at_risk = max_cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        self.confidence_threshold = confidence_threshold
        self.emergency_threshold = emergency_threshold
        self.days = news_days_prior
    
    def position_sizing(self):
        cash = self.get_cash()
        # if broker.is_market_open():
        #     last_price = self.get_last_price(self.symbol)
        #     print(f"Last Price: {last_price:.2f}")
        # else:
        #     print("market is closed")
        last_price = self.get_last_price(self.symbol)
        quantity = cash * self.max_cash_at_risk // last_price
        return cash, last_price, quantity

    def get_sentiment(self):

        def get_dates():
            today = self.get_datetime()
            days_prior = today - Timedelta(days=self.days)
            return today.strftime('%Y-%m-%d'), days_prior.strftime('%Y-%m-%d')
        
        today, days_prior = get_dates()
        news = self.api.get_news(symbol=self.symbol, 
                                 start=days_prior, 
                                 end=today)
        news = [ev.__dict__["_raw"]["summary"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment, news

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        probability, sentiment, _ = self.get_sentiment()
        if cash > last_price: 
            if sentiment == "positive" and probability > self.confidence_threshold: 
                #print("last_price:" + str(last_price) + " cash:" + str(cash) + " quantity:" + str(quantity))

                if self.last_trade == "sell" and probability > self.emergency_threshold: 

                    self.sell_all()

                elif self.last_trade == "sell":

                    position = self.get_position(self.symbol)
                    if not position: 
                        return
                    half = max(1, int(abs(position.quantity * probability)))

                    order = self.create_order(
                        self.symbol, 
                        half, 
                        "buy", 
                        type="market"
                    )

                    self.submit_order(order) 
                    
                else:
                    order = self.create_order(
                        self.symbol, 
                        max(1, quantity*float(1-(probability - self.confidence_threshold)/(1 - self.confidence_threshold))),
                        "buy", 
                        type="bracket", 
                        take_profit_price=last_price*1.20, 
                        stop_loss_price=last_price*.95
                    )

                    self.submit_order(order) 
                self.last_trade = "buy"

            elif sentiment == "negative" and probability > self.confidence_threshold: 

                if self.last_trade == "buy" and probability > self.emergency_threshold: 

                    self.sell_all()

                elif self.last_trade == "buy":

                    position = self.get_position(self.symbol)
                    if not position: 
                        return
                    half = max(1, int(abs(position.quantity * probability)))

                    order = self.create_order(
                        self.symbol, 
                        half, 
                        "sell", 
                        type="market"
                    )

                    self.submit_order(order) 
                    
                else:
                    order = self.create_order(
                        self.symbol, 
                        max(1, quantity*float(1-(probability - self.confidence_threshold)/(1 - self.confidence_threshold))), 
                        "sell", 
                        type="bracket", 
                        take_profit_price=last_price*.8, 
                        stop_loss_price=last_price*1.05
                    )

                    self.submit_order(order) 
                self.last_trade = "sell"

if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    params = {"symbol":"SPY", "max_cash_at_risk": .9, "confidence_threshold": .4, "emergency_threshold":.99,"news_days_prior": 5}
    strategy = SentimentStrategy(name="sentimentmlstrategy", broker=broker, parameters=params)

    start_date = datetime(2020, 8, 1)
    end_date = datetime(2024, 8, 1)

    strategy.backtest(
        YahooDataBacktesting, 
        start_date, 
        end_date, 
        parameters=params
    )