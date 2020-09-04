#https://pypi.org/project/websocket_client/
import websocket
import json
import csv
import os
from datetime import datetime

def load_symbols(filename):
    with open(filename, "r") as fh:
        reader = csv.DictReader(fh, delimiter=",")
        symbols = [item['Symbol'] for item in reader]
    return symbols

class StockStream:

    def __init__(self, stocks, save_folder="./data/raw_data"):
        self.stocks = stocks
        self.save_folder = save_folder
        websocket.enableTrace(True)
        assert os.environ.get('finnhub_token'), "Please set finnhub token for websocket"
        self.ws = websocket.WebSocketApp("wss://ws.finnhub.io?token="+os.environ.get("finnhub_token"),
                    on_message = lambda ws, message: self.on_message(ws, message),
                    on_error = lambda ws, message: self.on_error(ws, message),
                    on_close = lambda ws: self.on_close(ws),
                    on_open = lambda ws:  self.on_open(ws))

        self.save_files = {stock: open(os.path.join(self.save_folder, f"{stock}_raw.csv"), "a")
                                    for stock in self.stocks}
        self.data_store = {stock: {} for stock in self.stocks}


    def _sub_str(self, stock):
        tmp = {"type":"subscribe","symbol":stock}
        return json.dumps(tmp)

    def on_open(self, ws):
        for stock in self.stocks:
            self.ws.send(self._sub_str(stock))

    def on_message(self, ws, message):
        data = json.loads(message)
        if (data.get('type') == "ping"):
            print("sending pong")
            self.ws.send('{"type":"pong"}')
        else:
            try:
                data = data['data'][0]
                stock, price, volume, time = data['s'], data['p'], data['v'], data['t']
                time = datetime.fromtimestamp(int(time) // 1000)
                self.save_files[stock].write(f"{stock},{price},{volume},{time}\n")
            except:
                print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        for fh in self.save_files.values():
            fh.close()
        print("### closed ###")

    def run(self):
        self.ws.run_forever()

if __name__ == "__main__":
    symbols = ["NFLX", "FB", "TSLA", "MU", "AAPL", "WMT", "AMZN", "MSFT", "GOOG", "AMD", "NVDA", "ATVI", "INTC", "Z"]
    sd = StockStream(symbols)
    sd.run()
