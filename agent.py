import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from market import StockMarketDict
from collections import OrderedDict, defaultdict
from portfolio import Portfolio
import random

from wavelet import lowpassfilter

class Decision:
    """
    Data class for agent decisions
        result is "BUY" "SELL" or None
        variable is a dictionary {variable_name: value}
        condition: str on how the variables are put together
    """

    def __init__(self, result=None, variables={}, condition=""):
        self.result = result
        self.variables = variables
        self.condition = condition

    def __repr__(self):
        return f"Decision({self.result}, {self.condition})"

    def empty(self):
        if (self.result == None):
            return True
        else:
            return False

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
        decisions = {stock: Decision() for stock in self.stocks}

        for stock in self.stocks:
            stock_price = data.get(stock)
            if (stock_price == None):
                continue

            stock_price = stock_price['close']
            # Wait for enough data
            if (len(self.long_trend[stock]) < self.trend_modifier*self.avg_range):
                tmp = np.append(self.long_trend[stock], stock_price)
                self.long_trend[stock] = tmp
                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp
            else:
                moving_avg = np.mean(self.history[stock])
                trend_len = len(self.long_trend[stock])
                long_trend_start = np.mean(self.long_trend[stock][:trend_len//2])
                long_trend_end   = np.mean(self.long_trend[stock][trend_len//2:])
                trend = long_trend_end - long_trend_start
                trend_percent = (trend / long_trend_end)
                std = np.std(self.history[stock])
                var_dict = {"moving_avg":moving_avg, "std":std, "trend_percent": trend_percent}

                if ((stock_price > moving_avg + 1*std) and (trend_percent < 0)):
                    decisions[stock] = Decision("SELL", var_dict, "moving_ave + std and trend_percent > 0")
                elif ((stock_price < moving_avg - 1*std)):# and (trend_percent > 0)):
                    decisions[stock] = Decision("BUY", var_dict, "moving_ave - std")

                self.history[stock] = self.history[stock][1:]
                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp

                self.long_trend[stock] = self.long_trend[stock][1:]
                tmp = np.append(self.long_trend[stock], stock_price)
                self.long_trend[stock] = tmp

        return decisions

class AgentWaveTrend:
    """
    Use wavelets to filter out high frequencies on price data.
    Use the filtered data to determine the 'trend'
    trend is average of last half - average last half
    then scaled by last half so they are comparable
    The stocks are sorted then filtered by a minimim volume size.
    only the top stock is returned with a BUY decision
    """
    def __init__(self, stocks, window_size=20, wavelet_type='db4', value_threshold=0.63):
        self.stocks = stocks
        self.window_size = window_size
        self.wavelet_type = wavelet_type
        self.value_threshold = value_threshold
        self.history = {} #stock:np.array([]) for stock in self.stocks}
        self.history_vol = {} #stock:np.array([]) for stock in self.stocks}
        self.trends = {}
        self.ave_vol = {}

    def clear(self):
        """
        Option to restart on new day
        """
        self.history = {} #stock:np.array([]) for stock in self.stocks}
        self.trends = {}


    def decide(self, data):
        """
        Given new data and current state
        make a decision to buy or sell.
        """
        decisions = {}

        for stock in data.keys():# self.stocks:

            if (not isinstance(self.history.get(stock), np.ndarray)):
                self.history[stock] = np.array([])
                self.history_vol[stock] = np.array([])
            stock_price = data.get(stock)
            if (stock_price == None):
                continue

            stock_vol = stock_price['volume']
            stock_price = stock_price['close']
            # Wait for enough data

            if (len(self.history[stock]) < self.window_size):
                tmp = np.append(self.history_vol[stock], stock_vol)
                self.history_vol[stock] = tmp

                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp

            else:
                filtered_price = lowpassfilter(self.history[stock], wavelet=self.wavelet_type, threshold=self.value_threshold)
                f_len = len(filtered_price)
                low_ave  = np.mean(filtered_price[:f_len//2])
                high_ave = np.mean(filtered_price[f_len//2:])
                trend = high_ave - low_ave
                trend = trend / high_ave
                var_dict = {"trend":trend}

                # Save trend for all stocks
                self.trends[stock] = trend
                self.ave_vol[stock] = np.mean(self.history_vol[stock])

#                if (trend > 0.1):
#                    decisions[stock] = Decision("BUY", var_dict, "trend > 0")
#                elif (trend < 0):
#                    decisions[stock] = Decision("SELL", var_dict, "trend < 0")

                self.history[stock] = self.history[stock][1:]
                tmp = np.append(self.history[stock], stock_price)
                self.history[stock] = tmp

        if (len(self.trends) > 0):
            top = sorted(self.trends, key=lambda x: self.trends[x], reverse=True)
            best = list(filter(lambda x: self.ave_vol[x] > 0, top))
            selection_index = 20
            print(best[selection_index])
            print(self.trends[best[selection_index]])
            print(self.ave_vol[best[selection_index]])
            decisions[best[selection_index]] = Decision("BUY")

        return decisions


class AgentRandom:
    """
    Pick a single stock every day to buy and hold
    """
    def __init__(self, stocks):
        self.stocks = stocks

    def clear(self):
        pass

    def decide(self, data):
        """
        Given new data and current state
        make a decision to buy or sell.
        """

        decisions = {}
        choice = random.choice(list(data.keys()))
        decisions[choice] = Decision("BUY")
        return decisions


class AgentMACD:
    """
    Trade on MACD crosses
    """
    def __init__(self, stocks, mac1_num=12, mac2_num=26, macd_num=9, beta=0.9):
        self.stocks = stocks
        self.beta = beta
        self.MAC = {stock: np.array([]) for stock in self.stocks}
        self.MACD = {stock: np.array([]) for stock in self.stocks}

        self.mac1_num = max(mac1_num, mac2_num)
        self.mac2_num = min(mac1_num, mac2_num)
        self.macd_num = macd_num
        self.beta_array = np.zeros(self.mac1_num)
        self._init_beta()

    def _init_beta(self):
        """ Weights for EMA
        """
        self.beta_array[0] = 1 #self.beta
        for i in range(1, self.mac1_num):
            self.beta_array[i] = 1 #(1-self.beta) * self.beta_array[i-1]

    def mac1(self, stock):
        x = np.average(self.MAC[stock][::-1][:self.mac1_num],  weights=self.beta_array[:self.mac1_num])
        return x

    def mac2(self, stock):
        x = np.average(self.MAC[stock][::-1][:self.mac2_num],  weights=self.beta_array[:self.mac2_num])
        return x

    def macd(self, stock):
        return np.average(self.MACD[stock][::-1][:self.mac1_num],  weights=self.beta_array[:self.macd_num])

    def decide(self, data):
        """ Given new data and current state
        make a decision to buy or sell.
        """
        decisions = {stock: Decision() for stock in self.stocks}
        for stock in self.stocks:
            stock_price = data.get(stock)
            decisions[stock] = Decision()
            if (stock_price == None):
                continue
            # Wait for enough data

            stock_price = stock_price['close']

            # Need a EMA of the MACD values
            if (len(self.MACD[stock]) < self.macd_num):

                # Fill bigger one if not filled
                if (len(self.MAC[stock]) < self.mac1_num):
                    tmp = np.append(self.MAC[stock], stock_price)
                    self.MAC[stock] = tmp

                # if bigger one filled can compute macd
                else:
                    # Update mac values to include newest
                    self.MAC[stock] = self.MAC[stock][1:]
                    tmp = np.append(self.MAC[stock], stock_price)
                    self.MAC[stock] = tmp

                    macd = self.mac2(stock) - self.mac1(stock)
                    tmp = np.append(self.MACD[stock], macd)
                    self.MACD[stock] = tmp

            # If MACD is filled can compute a decision
            else:

                # Need to track history of neg and pos to see when cross
                # For only trading 1 stock at a time this works without
                # having to store history
                self.MAC[stock] = self.MAC[stock][1:]
                tmp = np.append(self.MAC[stock], stock_price)
                self.MAC[stock] = tmp

                macd = self.mac2(stock) - self.mac1(stock)

                self.MACD[stock] = self.MACD[stock][1:]
                tmp = np.append(self.MACD[stock], macd)
                self.MACD[stock] = tmp

                signal = macd - self.macd(stock)

                var_dict = {"mac1":self.mac1(stock), "mac2": self.mac2(stock), "macd": self.macd(stock)}

                if (signal < 0):
                    decisions[stock] = Decision("SELL", var_dict, "macd < 0")
                elif (signal > 0):
                    decisions[stock] = Decision("BUY", var_dict, "macd > 0")

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
