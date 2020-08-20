import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from market import StockMarketDict
from collections import OrderedDict
from portfolio import Portfolio

class AgentMeanReversion:
    """
    Calculate the moving average of a stock.
    Looks like people take the closing price
    to be used in averages

    if current price is above we can sell
    if below we should maybe buy
    """
    def __init__(self, stocks, avg_range=10, trend_modifier=3):
        self.stocks = stocks
        self.avg_range = avg_range
        self.history = {stock:np.array([]) for stock in self.stocks}
        self.long_trend = {stock:np.array([]) for stock in self.stocks}
        self.trend_modifier = trend_modifier

    def decide(self, data):
        """
        Given new data and current state
        make a decision to buy or sell.
        """
        decisions = {}
        for stock in self.stocks:
            stock_price = data.get(stock)
            if (stock_price == None):
                return None

            stock_price = stock_price['close']
            # Wait for enough data
            if (len(self.long_trend[stock]) < self.trend_modifier*self.avg_range):
                tmp = np.append(self.long_trend[stock], stock_price)
                self.long_trend[stock] = tmp
                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp
                decisions[stock] = None
            else:
                moving_avg = np.mean(self.history[stock])
                trend_len = len(self.long_trend[stock])
                long_trend_start = np.mean(self.long_trend[stock][:trend_len//2])
                long_trend_end   = np.mean(self.long_trend[stock][trend_len//2:])
                trend = long_trend_end - long_trend_start
                trend_percent = (trend / long_trend_end)
                std = np.std(self.history[stock])
                if ((stock_price > moving_avg + 1*std)):# and (trend_percent < 0)):
                    decisions[stock] = "SELL"
                elif ((stock_price < moving_avg - 1*std) and (trend_percent > 0)):
                    decisions[stock] = "BUY"
                else:
                    decisions[stock] = None
                self.history[stock] = self.history[stock][1:]
                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp

                self.long_trend[stock] = self.long_trend[stock][1:]
                tmp = np.append(self.long_trend[stock], stock_price)
                self.long_trend[stock] = tmp

        return decisions

class AgentMACD:
    """
    Trade on MACD crosses
    """
    def __init__(self, stocks, mac1_num=12, mac2_num=26, beta=0.9):
        self.stocks = stocks
        self.beta = beta
        self.MAC1 = {stock: np.array([]) for stock in self.stocks}
        self.MAC2 = {stock: np.array([]) for stock in self.stocks}
        self.mac1_num = max(mac1_num, mac2_num)
        self.mac2_num = min(mac1_num, mac2_num)
        self.beta_array = np.zeros(self.mac1_num)
        self._init_beta()

    def _init_beta(self):
        self.beta_array[0] = self.beta
        for i in range(1, self.mac1_num):
            self.beta_array[i] = (1-self.beta) * self.beta_array[i-1]

    def decide(self, data):
        """
        Given new data and current state
        make a decision to buy or sell.
        """
        decisions = {}
        for stock in self.stocks:
            stock_price = data.get(stock)
            if (stock_price == None):
                decisions[stock] = None
                continue

            stock_price = stock_price['close']
            # Wait for enough data
            if (len(self.MAC1[stock]) < self.mac1_num):

                tmp = np.append(self.MAC1[stock], stock_price)
                self.MAC1[stock] = tmp

                decisions[stock] = None

                if (len(self.MAC2[stock]) < self.mac2_num):

                    tmp = np.append(self.MAC2[stock], stock_price)
                    self.MAC2[stock] = tmp

                    decisions[stock] = None

                decisions[stock] = None

            else:
                # Add in somthing about macd history and trade when 
                # its at a min or max
                mac1 = sum(self.MAC1[stock] * self.beta_array[:self.mac1_num])
                mac2 = sum(self.MAC2[stock] * self.beta_array[:self.mac2_num])
                macd = mac2 - mac1

                if (macd > 0):
                    decisions[stock] = "SELL"
                elif (macd < 0):
                    decisions[stock] = "BUY"
                else:
                    decisions[stock] = None

                self.MAC1[stock] = self.MAC1[stock][1:]
                tmp = np.append(self.MAC1[stock], stock_price)
                self.MAC1[stock] = tmp

                self.MAC2[stock] = self.MAC2[stock][1:]
                tmp = np.append(self.MAC2[stock], stock_price)
                self.MAC2[stock] = tmp

        return decisions

class RandomAgent:
    """
        Will randomly select a stock
        Everyday there will be a 50 50 chance to sell.
        The sale will be a uniform random over the high low for the day.
        Will start with a set amount of money. Stop if we run out.
    """
    def __init__(self, market, cash, max_loss_ratio=10, max_stocks=1, avg_holding=10):
        self.max_stocks = max_stocks
        self.cash = cash
        self.init_cash = cash
        self.avg_holding = avg_holding
        self.min_value = cash / max_loss_ratio
        self.equity = 0
        self.market = market
        self.log = []
        self.orders = []
        self.holdings = []
        self.current_date = date(1999,11,1)
        self.end_date = date(2020,8,4)
        self.done = False
        self._init_buys()

    def _init_buys(self):
        for _ in range(self.max_stocks):
            stock = self.choose_stock()
            self.buy(stock)

    def reset(self):
        self.cash = self.init_cash
        self.equity = 0
        self.log = []
        self.orders = []
        self.holdings = []
        self.current_date = date(1999,11,1)
        self.end_date = date(2020,8,4)
        self.done = False
        self._init_buys()

    @property
    def net_worth(self):
        return self.cash + self.equity

    def choose_stock(self):
        choices = self.market.available_stocks(self.current_date)
        stock = random.choice(choices)
        return stock

    def buy(self, stock):
        """
        Always buy at open price if cash available and
        below max stock holdings
        """
        price = self.market.current_price(stock, self.current_date)

        # Dont buy if we dont have enough money.
        # OR if cannot find a price 
        # Also set another buy order so we dont end with nothing
        if ((not price) or (price > self.cash)):
        #    new_stock = self.choose_stock()
        #    self.buy_order(new_stock)
            return

        self.cash -= price
        self.equity += price
        self.holdings.append(Holding(stock, price, self.current_date, 1))
        self.sell_order(stock)
        return True

    def buy_order(self, stock):
        till_buy = timedelta(hours=24 * self._possion())
        buy_date = self.current_date + till_buy
        self.orders.append(("BUY", stock, buy_date))

    def sell(self, stock, rebuy=True):
        sell_price = self.market.sell(stock, self.current_date)

        # Either no price cuz holiday or just bad data
        if (not sell_price):
            return None

        self.cash += sell_price
        holding = [h for h in self.holdings if h.ticker==stock][0]
        holding.sell(sell_price, self.current_date)
        self.equity -= holding.buy_price
        self.log.append(holding.log + f",TOTAL_RETURN {(self.equity - self.cash) / self.init_cash}")
        self.remove_completed_holdings()
        if rebuy:
            buy_stock = self.choose_stock()
            self.buy_order(buy_stock)
        return True

    def sell_order(self, stock):
        # Find the sell date before hand
        till_sell = timedelta(hours=24 * self._possion())
        sell_date = self.current_date + till_sell
        self.orders.append(("SELL", stock, sell_date))

    def remove_completed_holdings(self):
        new_holdings = [h for h in self.holdings if h.sold==False]
        self.holdings = new_holdings

    def _possion(self):
        return int(np.random.poisson(self.avg_holding, 1)[0]) + 1

    def sort_orders(self):
        self.orders = sorted(self.orders, key=lambda x: x[2], reverse=True)

    def end_game(self):
        """
        At end date sell all current holdings
        """
        self.done = True
        for order_type, stock, _ in self.orders:
            if (order_type == "BUY"):
                pass
            elif (order_type == "SELL"):
                self.sell(stock, rebuy=False)

    def simulate(self):
        while (not self.done):
            self.step()
        gain = self.cash / self.init_cash
        return gain

    def step(self, steps=1):
        if self.done:
            return
        if (self.current_date >= self.end_date):
            print("We done at end date")
            self.end_game()
            return

        assert self.net_worth > self.min_value, "Cannot progress lost too much money"
        for _ in range(steps):
            self._step()

    def _step(self):
        """
        Fast forward to the next day the we will do a sell
        """
        self.sort_orders()
        order_type, stock, order_date = self.orders.pop()
        order_result = True

        if (order_type == "BUY"):
            assert self.cash > 0, "Dont have any money left to buy"
            order_result = self.buy(stock)
        elif (order_type == "SELL"):
            sell_result = self.sell(stock)

        # If sell result is none. meaning some
        # there wasnt a sell price for that day add it back to orders
        # at a later day
        if (not order_result):
            self.orders.append((order_type, stock, order_date+timedelta(hours=24)))

        if order_date > self.current_date:
            self.current_date = self.advance_day(self.current_date)

    def advance_day(self, day):
        day = day + timedelta(hours=24)

        # Skip weekends Monday 0, ... Sat 5, Sun 6
        if (day.weekday() > 4):
            return self.advance_day(day)

        # Skip holidays if market closed. No data
        elif (self.market_closed(day)):
            return self.advance_day(day)

        return day

    def market_closed(self, day):
        results = self.market.available_stocks(day)
        if (results == None):
            return True
        return False

if __name__ == "__main__":
    pass
