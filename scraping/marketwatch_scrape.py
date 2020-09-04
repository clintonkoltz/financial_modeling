
from datetime import datetime, date
import json
import csv
import os
import requests


class MarketWatchScraper():
    """
    Sends a request to some api that marketwatch.com gets its data from and came return
    1 minute stock values for upto the past 10 days
    """

    def __init__(self, time_frame='D10', time_step="PT1M", market=None):
        self.stock = None

        self.market_choices = ['XNYS','XNAS', 'DOW JONES GLOBAL', None] # None trys all markets
        self.frame_choices  = ['D10'] # There are other choices but havent used them yet
        self.step_choices   = ['PT1M'] #There are other choices but havent used them yet

        assert market in self.market_choices,    f"Need to choose a market from {self.market_choices}"
        assert time_frame in self.frame_choices, f"Need to choose a time_frame from {self.frame_choices}"
        assert time_step in self.step_choices ,  f"Need to choose a time_step from {self.step_choices}"

        self.time_frame = time_frame
        self.time_step = time_step
        self.market = market
        self.headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
                                    "Content-Type": "application/json, text/javascript, */*; q=0.01",
                                    "Dylan2010.EntitlementToken": "cecc4267a0194af89ca343805a3e57af"}
    def build_request(self, stock):
        """
        Handles logic for trying all the market for a valid request
        if self.market is None
        """
        output = None
        if (self.market == None): # If none try all markets
            for market in self.market_choices:
                # Stop infinite loop
                if (market == None):
                    continue
                resp = self.handle_request(stock, self.time_frame, self.time_step, market)
                # If good code return it. Else try other markets 
                if (resp != None):
                    return resp

        else:
            output = self.handle_request(stock, self.time_frame, self.time_step, self.market)
        return output

    def handle_request(self, *args, **kwargs):
        """ Only returning good response.
        Maybe should return reguardless for troubleshootings
        """
        req_url = self.request_url(*args, **kwargs)
        r = requests.get(req_url, headers=self.headers)
        if (r.status_code == 200):
            return r
        else:
            return None

    def request_url(self, stock, time_frame, time_step, market):
            req_url = f'https://api-secure.wsj.net/api/michelangelo/timeseries/history?json={{"Step":"{time_step}","TimeFrame":"{time_frame}",'\
                      f'"EntitlementToken":"cecc4267a0194af89ca343805a3e57af","IncludeMockTick":true,"FilterNullSlots":false,' \
                      f'"FilterClosedPoints":true,"IncludeClosedSlots":false,"IncludeOfficialClose":true,"InjectOpen":false,' \
                      f'"ShowPreMarket":false,"ShowAfterHours":false,"UseExtendedTimeFrame":false,"WantPriorClose":true,' \
                      f'"IncludeCurrentQuotes":false,"ResetTodaysAfterHoursPercentChange":false,'\
                      f'"Series":[{{"Key":"STOCK/US/{market}/{stock}","Dialect":"Charting","Kind":"Ticker","SeriesId":"s1",'\
                      f'"DataTypes":["Open","Last","High","Low","Volume"],"Indicators":[{{"Parameters":[{{"Name":"ShowOpen"}},{{"Name":"ShowHigh"}},'\
                      f'{{"Name":"ShowLow"}},{{"Name":"ShowPriorClose","Value":true}},{{"Name":"Show52WeekHigh"}},'\
                      f'{{"Name":"Show52WeekLow"}}],"Kind":"OpenHighLowLines","SeriesId":"i2"}}]}}]}}&ckey=cecc4267a0'
            return req_url

    def get_data(self, stock):
        r = self.build_request(stock)
        # Return None if cannot extract data
        try:
            time_values = json.loads(r.content)['TimeInfo']['Ticks']
            time_values = list(map(self.tick_to_date, time_values))
        except:
            return None, None

        # Values is composed of Open Last High Low Volume
        values = json.loads(r.content)['Series'][0]['DataPoints']
        return time_values, values

    def tick_to_date(self, tick):
        """
        Time data comes in UNIX time format.
        Convert to YYYY-MM-DD hh:mm:ss
        """
        tick = int(tick) / 1000
        return datetime.utcfromtimestamp(tick).strftime("%Y-%m-%d %H:%M:%S")

    def save_intraday(self, stock, save_dir="../data/intradays", log_file="intraday_fails.log"):
        day = date.today().strftime("%m_%d_%y")
        save_file = os.path.join(save_dir, f"{stock}_intra_1min_{day}.csv")

        if os.path.exists(save_file):
            print(f"Skipping {ticker}, save file {save_file} already exists")
            return

        time_values, values = self.get_data(stock)

        if not time_values:
            with open(log_file, "a") as fh:
                fh.write(f"Issue with getting data {stock}\n")
            print(f"Issue with getting data {stock}")
            return

        print(f"Writing file {save_file}")
        with open(save_file, "w") as fh:
            fh.write("Time,Open,Close,High,Low,Volume\n")
            for t_value, val in zip(time_values, values):
                assert len(val) == 5, f"Data is not the correct size. Found length {len(val)} should be 4. Data is {val}"
                fh.write(f"{t_value},{val[0]},{val[1]},{val[2]},{val[3]},{val[4]}\n")


def load_symbols(filename):
    with open(filename, "r") as fh:
        reader = csv.DictReader(fh, delimiter=",")
        symbols = [item['Symbol'] for item in reader]
    return symbols

def scrape_all():
    symbol_file = "sp500_symbols.txt"
    symbols = load_symbols(symbol_file)
    api = MarketWatchScraper()
    for sym in symbols:
        api.save_intraday(sym)
    print("Done")

if __name__ == "__main__":
    scrape_all()
