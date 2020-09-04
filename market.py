import mysql.connector
import pandas as pd
import random
import pickle
import os
from datetime import datetime, date, timedelta


class StockMarketDict:
    """
    Used for backtesting
    Act like a market and return current market values
    for given stocks
    """

    def __init__(self, stocks=[], random_price=False, data_file="./data/intraday_datetimes_1min.pkl"):
        self.data_file = data_file
        self.random_price = random_price
        with open(self.data_file, "rb") as fh:
            self.data = pickle.load(fh)
        self.dates = list(sorted(self.data.keys()))
        self.stocks = stocks

    def set_stocks(self, stocks):
        self.stocks = stocks

    def __len__(self):
        return len(self.dates)

    def __iter__(self):
        for current_day in self.dates:
            if (self.stocks == []):
                yield self.data[current_day]
            else:
                data = self.data[current_day]
                print(data.get(self.stocks[0]))
                yield {stock: data.get(stock) for stock in self.stocks}

    def sell(self, stock, current_date):
        """
        Selling will be uniform random roll over high low value
        """
        if current_date not in self.data.keys():
            return None

        stock_data = self.data[current_date].get(stock)
        if (stock_data == None):
            return None

        if (self.random_price):
            high = stock_data.get('high')
            low = stock_data.get('low')
            if ((high==None) or (low==None)):
                return None
            r = random.random()
            sell_price = low * r + high * (1-r)
            return sell_price
        else:
            return stock_data.get("open")

    def buy(self, stock, current_date):
        if current_date not in self.data.keys():
            return None

        stock_data = self.data[current_date].get(stock)
        if (stock_data == None):
            return None

        if (self.random_price):
            high = stock_data.get('high')
            low = stock_data.get('low')
            if ((high==None) or (low==None)): return None
            r = random.random()
            buy_price = low * r + high * (1-r)
            return buy_price
        else:
            return stock_data.get("open")

    def current_price(self, stock, current_date):
        if current_date not in self.data.keys():
            return None

        result = self.data[formatted_date][stock].get('open')
        if (not result):
                return None
        return result

class StockMarketSQL:

    def __init__(self, table="dailyTicker"):
        assert os.environ.get('DB_USER'), "Set mysql database user DB_USER"
        assert os.environ.get('DB_PASS'), "Set mysql database password DB_PASS"
        self.con = mysql.connector.connect(user=os.environ.get('DB_USER'), database="stocks", password=os.enviorn.get('DB_PASS'))
        self.cur = self.con.cursor()
        self.table = table
        self.current_date = date(1999,11,1)
        self.end_date = date(2020,8,4)

    @property
    def _format_date(self):
        day_str = self.current_date.strftime("%Y-%m-%d")
        return day_str + " 00:00:00"

    def available_stocks(self):
        self.cur.execute(f"SELECT company FROM stockCreation WHERE date <= \"{self._format_date}\"")
        results = self.cur.fetchall()
        results = self._unwrap_results(results)
        return results

    def _unwrap_results(self, results):
        results = list(map(lambda x: x[0], results))
        return results

    def advance(self, num=1):
        if (self.current_date >= self.end_date):
            return
        if num > 0:
            self.current_date = self.current_date + timedelta(hours=24)
            self.advance(num-1)

        if (self.current_date.weekday() > 4):
            # Skip weekends
            # Monday 0, ... Sat 5, Sun 6
            self.advance(1)

    def current_price(self, ticker):
        self.cur.execute(f"SELECT open FROM {self.table} WHERE company=\"{ticker}\" AND date=\"{self._format_date}\"")
        results = self.cur.fetchall()
        results = self._unwrap_results(results)
        # Check if there is some holiday buy checking if any stocks have a price
        if (len(results) == 0):
            # is_holiday will advance the current day is no other stocks have prices
            if (self.is_holiday()):
                return self.current_price(ticker)
            else:
                return None

        return results[0]

    def is_holiday(self):
        """
        Some days maybe a holiday.
        See if any stock has a price for that day. If not we call
        self.advance to move on.
        """
        self.cur.execute(f"SELECT open FROM {self.table} WHERE date=\"{self._format_date}\"")
        results = self.cur.fetchall()
        results = self._unwrap_results(results)
        if len(results) == 0:
            self.advance()
            return True
        return False

    def sell(self, ticker):
        """
        Selling will be uniform random roll over high low value
        """

        self.cur.execute(f"SELECT high,low FROM {self.table} WHERE company=\"{ticker}\" AND date=\"{self._format_date}\"")
        results = self.cur.fetchall()
        if (len(results) == 0):
            if (self.is_holiday()): # Is holiday will advance the current day if true
                return self.sell(ticker)
            else:
                return None
        assert len(results) == 1, f"Selling no results found for {ticker} on {self._format_date}"
        high, low = results[0]
        r = random.random()
        buy_price = low * r + high * (1-r)
        return buy_price

class StockMarketDataFrame:

    def __init__(self, data_file="daily_all.csv"):
        self.dataframe = pd.read_csv(data_file)
        self.data_file = data_file
        self.current_date = date(1999,11,1)
        self.end_date = date(2020,8,4)

    @property
    def _format_date(self):
        day_str = self.current_date.strftime("%Y-%m-%d")
        return day_str

    def available_stocks(self):
        results = self.dataframe.loc[lambda x:
                        x["timestamp"] == self._format_date]["company"]
        return results.values

    def advance(self, num=1):
        if (self.current_date >= self.end_date):
            return
        if num > 0:
            self.current_date = self.current_date + timedelta(hours=24)
            self.advance(num-1)

        if (self.current_date.weekday() > 4):
            # Skip weekends
            # Monday 0, ... Sat 5, Sun 6
            self.advance(1)

    def current_price(self, ticker):
        results =  self.dataframe.loc[ lambda x:
                                    (x["timestamp"] == self._format_date) &
                                    (x["company"] == ticker)]["open"]

        # Check if there is some holiday buy checking if any stocks have a price
        if (results.empty):
            # is_holiday will advance the current day is no other stocks have prices
            if (self.is_holiday()):
                return self.current_price(ticker)
            else:
                return None

        return results.values[0]

    def is_holiday(self):
        """
        Some days maybe a holiday.
        See if any stock has a price for that day. If not we call
        self.advance to move on.
        """
        results =  self.dataframe.loc[ lambda x:
                                    (x["timestamp"] == self._format_date)]["open"]

        if (results.empty):
            print(f"Found holiday {self.current_date}")
            self.advance()
            return True
        return False

    def sell(self, ticker):
        """
        Selling will be uniform random roll over high low value
        """
        results =  self.dataframe.loc[ lambda x:
                                    (x["timestamp"] == self._format_date) &
                                    (x["company"] == ticker)]
        if (results.empty):
            if (self.is_holiday()): # Is holiday will advance the current day if true
                return self.sell(ticker)
            else:
                return None
        assert len(results) == 1, f"Selling no results found for {ticker} on {self._format_date}"
        high, low = results["high"], results["low"]
        r = random.random()
        buy_price = low * r + high * (1-r)
        return buy_price.values[0]

