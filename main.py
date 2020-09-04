from collections import OrderedDict
from agent import AgentMACD, AgentMeanReversion, AgentWaveTrend, AgentRandom
from market import StockMarketDict
from portfolio import Portfolio
from plotter import plot_value_tracker, plot_buy_sell_points, plot_decision_vars
from agent import Decision

from utils import convert_date, split_datetime_str

class DrawDown:
    """
    Calulates and stored the maximum drawdown time and value.
    Defined as the time between the newest peak value and until it
    crosses into a new peak value.
    The high will then be the difference between the peak and the lowest for
    the given time frame
    """

    def __init__(self, time=True):
        self.time = time # Used in converting dates. if time is there or not
        self.last_peak = 0
        self.peak_date = ""
        self.max_time = 0
        self.max_height = 0

    def calc(self, value, day):
        if (value > self.last_peak):
            self.last_peak = value
            self.peak_date = day

        elif (value < self.last_peak):

            last_day = convert_date(self.peak_date, time=self.time)
            new_day  = convert_date(day, time=self.time)
            if (last_day == ""):
                self.max_time = max(self.max_time, 0)
            else:
                self.max_time = max(self.max_time, (new_day - last_day).days)

            if (self.max_height < self.last_peak - value):
                self.max_height = self.last_peak - value

class Executor:
    """
    Handles logic between agent and incoming data
    """

    def __init__(self, agent, market, portfolio, stocks, time=False, close_time="18:30:00"):
        self.agent = agent
        self.market = market
        self.portfolio = portfolio
        self.stocks = stocks
        self.time = time
        self.market.set_stocks(self.stocks)
        self.buy_next =  {}
        self.sell_next = {}
        self.dates = self.market.dates
        self.current_data = None
        self.close_time = close_time

        # Metrics to evaluate strategies
        self.value_tracker = OrderedDict()
        self.decision_tracker = OrderedDict()
        self.drawdown = DrawDown(time=time)

        # Keep track of day so we can reset things every day
        self.current_date = ""
        # Done for the day. If we want close positions at end of time period
        self.done_for_day = False

    def reset_dict(self, default_value):
        """
        Useful function to create a dictionary with stocks as keys
        and a given initial value
        """
        return {stock: default_value for stock in self.stocks}

    def buy_order(self, stock, day, quantity):
        price = self.market.buy(stock, day)
#        print(f"buying {stock} for {price} on {day}")
        if (price != None):
            self.portfolio.add(stock, price, day, quantity)
        return price

    def sell_order(self, stock, day, quantity):
        price = self.market.sell(stock, day)
#        print(f"selling {stock} for {price} on {day}")
        if (price != None):
            self.portfolio.sold(stock, price, day, quantity)
        return price

    def process_orders(self, day):
        """
        Iterate through the buy_next and sell_next orders
        and try to buy and sell

        After processing reset the dictionaries to prevent
        double buys/sells
        """
        results = {}
        for stock in self.buy_next.keys():
                results[stock + day] = self.buy_order(stock, day, 1)
                self.buy_next[stock] = False

        for stock in self.sell_next.keys():
                results[stock + day] = self.sell_order(stock, day, 1)
                self.sell_next[stock] = False

        self.buy_next  = {}
        self.sell_next = {}

        return results

    def run(self):

        # This not necessaryly the date its just next time when data comes.
        for day in self.market.dates:
            current_date, current_time = split_datetime_str(day)
            decisions = {}
            # Sell and quit for the day
            if (current_time == self.close_time):
                done_for_day = True
                self.agent.clear()
                self.buy_next = {}
                for stock in self.portfolio.current_stocks:
                    #print(f"selling {stock} for the day")
                    decisions[stock] = Decision("SELL")

            # Reset things on new day
            if (self.current_date != current_date):
                #print("new day")
                #print(current_date)
                self.current_date = current_date
                self.done_for_day = False

            # When the agent make a decision they put in order
            # for the next time step. Here they are send to the market to
            # be bought or sold and the given price.
            self.process_orders(day)

            if not self.done_for_day:
                # Metric tracking
                value = self.portfolio.total_value
                gain = self.portfolio.total_gain
                self.drawdown.calc(value, day)
                self.value_tracker[day] = gain

                # Im actually gathering all the data for every stock
                # Not using the iterator method that is in StockMarketDict
                data = self.market.data[day]

                decisions = self.agent.decide(data)
                self.decision_tracker[day] = decisions

                # Only buy once a day
                if (decisions != {}):
                    self.done_for_day = True

            # Handle Decisions
            for stock in decisions.keys():
                stock_decision = decisions[stock]

                # Set to buy or sell on next day
                if (stock_decision.result == "BUY"):
                    # Only buy a max quantity of 1 stock at a time.
                    if (stock not in self.portfolio.current_stocks):
                        self.buy_next[stock] = True
                elif (stock_decision.result == "SELL"):
                    self.sell_next[stock] = True


def random_runs(num_runs=1000):
    """
    Base line random buy and hold a stock for a day to get idea if other cases
    are significant;y better
    """
    test_file = "./data/intraday_datetimes_1min.pkl"
    stock = "AMZN"
    stocks = [stock]
    market = StockMarketDict(random_price=False, data_file=test_file)
    agent = AgentRandom(stocks=stocks)
    portfolio = Portfolio(cash=10000)
    # value_tracker is an ordered dictionary. Get last value as total gain %
    gains = []
    for _ in range(num_runs):
        portfolio = Portfolio(cash=10000)
        executor = Executor(market = market, agent=agent, portfolio=portfolio, stocks=stocks, time=days)
        executor.run()
        gain = list(executor.value_tracker.values())[-1]
        gains.append(gain)
    return gains

if __name__ == "__main__":
     days = True
     if days:
         test_file = "./data/intraday_datetimes_1min.pkl"
     else:
         test_file = "./data/daily_all.pkl"
     stock = "AMZN"
     stocks = [stock] #, "FB", "ATVI", "MO", "AIG", "GOOG", "CNP", "BSX"]
     market = StockMarketDict(random_price=False, data_file=test_file)
     #agent = AgentMACD(stocks=stocks, mac1_num=26, mac2_num=12, macd_num=9)
     #agent = AgentMeanReversion(stocks=stocks)
     #agent = AgentWaveTrend(stocks=stocks, window_size=120)
     agent = AgentRandom(stocks=stocks)
     portfolio = Portfolio(cash=10000)
     executor = Executor(market = market, agent=agent, portfolio=portfolio, stocks=stocks, time=days)
     executor.run()
     plot_value_tracker(executor)
#     plot_buy_sell_points(executor, "AMZN")
#     plot_decision_vars(executor, stock)
