
from collections import OrderedDict
from agent import AgentMACD
from market import StockMarketDict
from portfolio import Portfolio

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
        self.buy_next = {}
        self.sell_next = {}
        self.value_tracker = OrderedDict()

    def plot_value_tracker(self):
        dates = list(map(lambda x: mdates.datestr2num(x), list(self.value_tracker.keys())))
        values = list(self.value_tracker.values())

        plt.plot_date(dates, values, fmt="m")
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
        # Await new data from markets
        # Do we want it for all tickers? How should it be specified?

        # Get data from the market on all the stocks
        # Send the data to the agent for a decision
        for day in self.market.dates:
            #if day < "20170101":
            #    continue
            self.value_tracker[day] = self.portfolio.total_value
            data = self.market.data[day]


            for stock in self.stocks:

                if (self.buy_next.get(stock)):
                        self.buy_order(stock, day, 1)
                        self.buy_next[stock] = False
                if (self.sell_next.get(stock)):
                        self.sell_order(stock, day, 1)
                        self.sell_next[stock] = False
                result = agent.decide(data)

                if (result == None):
                    continue

                if (result[stock] == "BUY"):
                    if (len(list(filter(lambda h: h.stock==stock, self.portfolio.active))) == 0):
                        self.buy_next[stock] = True
                elif (result[stock] == "SELL"):
                    self.sell_next[stock] = True
                else:
                    continue

if __name__ == "__main__":
     stocks = ["T"]
     market = StockMarketDict(random_price=True)
     agent = AgentMACD(stocks=stocks, mac1_num=26, mac2_num=12)
     portfolio = Portfolio(cash=1000)
     executor = Executor(market = market, agent=agent, portfolio=portfolio, stocks=stocks)
     executor.run()
