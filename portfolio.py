class Portfolio:

    """
    Class will keep track of results of trades and keep log
    of what has been traded when.

    """
    def __init__(self, cash):
        self.active = []
        self.historical = []
        self.equity = 0
        self.cash = cash
        self.initial_cash = cash

    def add(self, stock, price, day, quantity):
        # TODO use quantity for cash
        if (price < self.cash):
            print(f"Bought {stock} price {price}")
            self.active.append(Holding(stock, price, day, quantity))
            self.cash -= price

    @property
    def total_value(self):
        cash_reserves = sum([h.profit for h in self.historical])
        equity = sum([a.buy_price for a in self.active])
        return 100*((cash_reserves + equity + self.cash) - self.initial_cash) / self.initial_cash

    def move_completed(self):
        active   = [h for h in self.active if h.sold==False]
        finished = [h for h in self.active if h.sold==True]
        self.active = active
        self.historical.extend(finished)

    def sold(self, stock, price, day, quantity):
        for holding in self.active:
            if (holding.stock== stock):
                print(f"Sold {stock} price {price}")
                # If selling less make new holding
                # and sell that then update old to new amount
                if (holding.quantity > quantity):
                    holding.quantity -= quantity
                    sell_holding = copy.deepcopy(holding)
                    sell_holding.quantity = quantity
                    sell_holding.sell(price, day)
                # Case equal. Just sell
                elif (holding.quantity == quantity):
                    holding.sell(price, day)
                    self.move_completed()
                # Case too many. Only sell what we have.
                elif (holding.quantity < quantity):
                    holding.sell(price, day)
                    self.move_completed()
                self.cash += price
                break

class Holding:

    def __init__(self, stock, buy_price, buy_date, quantity):
        self.stock = stock
        self.quantity = quantity
        self.buy_price = buy_price
        self.buy_date = buy_date
        self.sold = False
        self.profit = None
        self.sell_price = None
        self.sell_date = None
        self.profit = None
        self.gain = None

    def __repr__(self):
        return f"BUY {self.stock} at {self.buy_price} on {self.buy_date},"\
               f"SELL for {self.sell_price} on {self.sell_date},"\
               f"PROFIT {self.profit}, GAIN {self.gain}"

    def __str__(self):
        return self.__repr__()

    def sell(self, sell_price, sell_date):
        self.sold = True
        self.sell_price = sell_price
        self.sell_date = sell_date
        self.profit = self.sell_price - self.buy_price
        self.gain = (self.sell_price/self.buy_price) * 100

    @property
    def log(self):
        assert self.sold, "Cannot log until order is sold"
        return str(self)
