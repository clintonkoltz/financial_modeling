import requests
import csv
import os

class AlphaFinanceAPI:
    """
    Use to get stock prices on a day scale
    """

    def __init__(self):
        self.base_url = "https://www.alphavantage.co/query"
        self.headers = {}
        self.key  = "I992MXIVP5APH6P5"

    def price_history(self, ticker, outputsize='full', interval=None):
        params = {'function': "TIME_SERIES_DAILY",
                  'symbol':   ticker,
                  'interval': interval,
                  'outputsize': outputsize,
                  'datatype': 'csv',
                  'apikey': self.key,
                  }
        response = requests.get(self.base_url, params=params, headers=self.headers)
        if (response.status_code == 200):
            return response
        else:
            print(f"Error looking up symbol {ticker}")
            return None

    def save_historical(self, ticker):
        save_file = f"{ticker}_daily.csv"
        if os.path.exists(save_file):
            print(f"Skipping {ticker}, already exists")
            return

        resp = self.price_history(ticker)

        if not resp:
            return

        print(f"Writing to file {save_file}")
        with open(save_file, "wb") as fh:
            fh.write(resp.content)

        # Have it return true to know that is did something
        # so we dont have to sleep.
        return True


class FinanceAPI:

    """
    Used to get price history on the day scale
    Also some extra info about companies
    """


    def __init__(self):
        self.base_url = "https://financialmodelingprep.com/api/v3/"
        self.headers = {"Content-type": "application/json"}
        self.data = {"apikey": "f9894a015ae82e8680bd155fac5178f3"}

    def profile(self, ticker):
        url_extra = "company/profile/"
        return self.base_request(url_extra, ticker)

    def income_statement(self, ticker, annual=True):
        url_extra = "financials/income-statement/"
        self._is_annual(annual)
        return self.base_request(url_extra, ticker)

    def balance_sheet(self, ticker, annual=True):
        url_extra = "financials/balance-sheet-statement/"
        self._is_annual(annual)
        return self.base_request(url_extra, ticker)

    def price_history(self, ticker):
        url_extra = "historical-price-full/"
        return self.base_request(url_extra, ticker)

    def _is_annual(self, annual=True):
        if (annual):
            self.data["period"] = "annual"
        else:
            self.data["period"] = "quarter"

    def base_request(self, url_extra, ticker):
        ticker = ticker.upper()
        url = self.base_url + url_extra + ticker
        response = requests.get(url, params=self.data, headers=self.headers)
        if (response.status_code == 200):
            return response.json()
        else:
            print(f"Error looking up symbol {ticker}")
            return None

def history_to_file(api, ticker):
    """
    Get daily stock info for a stock and save to a file if
    such data exists
    """
    resp = f.price_history(ticker)
    data = resp.get('historical')
    if not data:
        print(f"Not historical for {ticker}")
        return

    if (len(data) < 0):
        print(f"There is no data for ticker {ticker}")
        return

    save_file = f"{ticker}_daily.csv"
    if os.path.exists(save_file):
        print(f"Skipping {ticker}, already exists")
        return

    with open(save_file, "w") as fh:
        keys = sorted(data[0].keys())
        # Label key is date with spaces and commas ruins the csv
        # Also there is a data value in a better format
        ignore_keys = ["label"]
        fh.write(",".join([str(key) for key in keys if key not in ignore_keys])+"\n")
        for item in data:
            fh.write(",".join([str(item[key]) for key in keys if key not in ignore_keys]) + "\n")


def load_symbols(filename):
    with open(filename, "r") as fh:
        reader = csv.DictReader(fh, delimiter=",")
        symbols = [item['Symbol'] for item in reader]
    return symbols

if __name__ == "__main__":
    symbol_file = "sp500_symbols.txt"
    symbols = load_symbols(symbol_file)
    print(symbols)

