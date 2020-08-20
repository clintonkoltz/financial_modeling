from collections import OrderedDict
from agent import AgentMACD
from market import StockMarketDict
from portfolio import Portfolio
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

class Executor:
    """
    Handles logic between agent and incoming data
    """

    def __init__(self, agent, market, portfolio, stocks):
        self.agent = agent
        self.market = market
        self.portfolio = portfolio
        self.stocks = stocks
        self.market.set_stocks(self.stocks)
        self.buy_next = {stock: False for stock in self.stocks}
        self.sell_next = {stock: False for stock in self.stocks}
        self.value_tracker = OrderedDict()

    def plot_value_tracker(self):
        """
        Shows value of portfolio over time
        """
        dates = list(map(lambda x: mdates.datestr2num(x), list(self.value_tracker.keys())))
        values = list(self.value_tracker.values())

        plt.plot_date(dates, values, fmt="m")
        plt.show()

    def _plot_date_transform(self, dates):
        """
        Change the string of date format YYYY-MM-DD
        into matplotlib format
        """
        return list(map(mdates.datestr2num, dates))

    def plot_buy_sell_points(self, stock):
        """
        Plots the value of stock over time with the buy/sell points
        """
        assert stock in self.stocks, f"Need to choose a valid stock"
        assert len(self.portfolio.historical) > 0, "Must first run the backtest"

        # Get all specified stocks in the portfolio historical holdings
        port_holdings = list(filter(lambda h: h.stock==stock, self.portfolio.historical))
        buys = [(h.buy_date, h.buy_price) for h in port_holdings]
        buy_dates, buy_price = zip(*buys)
        buy_dates = self._plot_date_transform(buy_dates)

        sells = [(h.sell_date, h.sell_price) for h in port_holdings]
        sell_dates, sell_price = zip(*sells)
        sell_dates = self._plot_date_transform(sell_dates)

        # Stock price over time
        all_dates = self.market.dates
        valid_dates = [d for d in all_dates if self.market.data[d].get(stock)!=None]
        stock_values = [self.market.data[d][stock]['open'] for d in valid_dates if self.market.data[d][stock].get('open')!=None]
        valid_dates = self._plot_date_transform(valid_dates)

        plt.plot_date(valid_dates, stock_values, fmt="m", color='blue')
        plt.plot_date(sell_dates, sell_price, fmt="m", color='red', linestyle="", marker='o')
        plt.plot_date(buy_dates, buy_price, fmt="m", color='green', linestyle="", marker='o')
        plt.show()

    def buy_order(self, stock, day, quantity):
        price = self.market.buy(stock, day)
        if (price != None):
            self.portfolio.add(stock, price, day, quantity)


    def sell_order(self, stock, day, quantity):
        price = self.market.sell(stock, day)
        if (price != None):
            self.portfolio.sold(stock, price, day, quantity)


    def run(self):

        for day in self.market.dates:
            #if day < "20170101":
            #    continue
            self.value_tracker[day] = self.portfolio.total_value
            data = self.market.data[day]
            results = agent.decide(data)

            for stock in self.stocks:
                stock_decision, *_ = results[stock]

                # This part does the actual buying/selling of stocks
                if (self.buy_next[stock]):
                        self.buy_order(stock, day, 1)
                        self.buy_next[stock] = False
                if (self.sell_next[stock]):
                        self.sell_order(stock, day, 1)
                        self.sell_next[stock] = False

                if (stock_decision == None):
                    continue
                if (stock_decision == "BUY"):
                    if (len(list(filter(lambda h: h.stock==stock, self.portfolio.active))) == 0):
                        self.buy_next[stock] = True
                elif (stock_decision == "SELL"):
                    self.sell_next[stock] = True
                else:
                    continue

if __name__ == "__main__":
     stocks = ["T"]
     market = StockMarketDict(random_price=False)
     agent = AgentMACD(stocks=stocks, mac1_num=26, mac2_num=12)
     portfolio = Portfolio(cash=1000)
     executor = Executor(market = market, agent=agent, portfolio=portfolio, stocks=stocks)
     executor.run()
     executor.plot_buy_sell_points("T")
#     executor.plot_value_tracker()
