import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

from agent import AgentMACD, AgentMeanReversion
from market import StockMarketDict
from portfolio import Portfolio

def plot_value_tracker(executor):
    """
    Shows value of portfolio over time
    """
    assert len(executor.portfolio.historical) > 0, "Must first run the backtest"

    dates = list(map(lambda x: mdates.datestr2num(x), list(executor.value_tracker.keys())))
    values = list(executor.value_tracker.values())
    plt.plot_date(dates, values, fmt="m")
    plt.show()

def plot_date_transform(dates):
    """
    Change the string of date format YYYY-MM-DD
    into matplotlib format
    """
    return list(map(mdates.datestr2num, dates))

def plot_buy_sell_points(executor, stock):
    """
    Plots the value of stock over time with the buy/sell points
    """
    assert stock in executor.stocks, f"Need to choose a valid stock"
    assert len(executor.portfolio.historical) > 0, "Must first run the backtest"

    # Get all specified stocks in the portfolio historical holdings
    port_holdings = list(filter(lambda h: h.stock==stock, executor.portfolio.historical))
    buys = [(h.buy_date, h.buy_price) for h in port_holdings]
    buy_dates, buy_price = zip(*buys)
    buy_dates = plot_date_transform(buy_dates)

    sells = [(h.sell_date, h.sell_price) for h in port_holdings]
    sell_dates, sell_price = zip(*sells)
    sell_dates = plot_date_transform(sell_dates)

    # Stock price over time
    all_dates = executor.market.dates
    valid_dates = [d for d in all_dates if executor.market.data[d].get(stock)!=None]
    stock_values = [executor.market.data[d][stock]['open'] for d in valid_dates if executor.market.data[d][stock].get('open')!=None]
    valid_dates = plot_date_transform(valid_dates)

    plt.plot_date(valid_dates, stock_values, fmt="m", color='blue')
    plt.plot_date(sell_dates, sell_price, fmt="m", color='red', linestyle="", marker='o')
    plt.plot_date(buy_dates, buy_price, fmt="m", color='green', linestyle="", marker='o')
    plt.show()

def plot_decision_vars(executor, stock):
    """
    Decision are tracked in executor variable decision_tracker
    which is type dict {day: {stock:Decision()}}
    """
    assert stock in executor.stocks, f"Need to choose a valid stock"
    assert len(executor.portfolio.historical) > 0, "Must first run the backtest"

    all_dates = list(executor.decision_tracker.keys())
    # All dates that a decision was made for given stock
    print(executor.decision_tracker[all_dates[100]][stock])
    valid_dates = [d for d in all_dates if not executor.decision_tracker[d][stock].empty()]
    # Get all variables used in decision on valid days
    variables = list(map(lambda d: executor.decision_tracker[d][stock].variables, valid_dates))
    mac1 = list(map(lambda x: x.get('mac1'), variables))
    mac2 = list(map(lambda x: x.get('mac2'), variables))
    valid_dates = plot_date_transform(valid_dates)

    plt.plot_date(valid_dates, mac1, fmt="m", color='blue')
    plt.plot_date(valid_dates, mac2, fmt="m", color='green')
    plt.show()

if __name__ == "__main__":
     stocks = ["T"]
     market = StockMarketDict(random_price=False)
     agent = AgentMACD(stocks=stocks, mac1_num=26, mac2_num=12)
     agent = AgentMeanReversion(stocks=stocks)
     portfolio = Portfolio(cash=1000)
     executor = Executor(market=market, agent=agent, portfolio=portfolio, stocks=stocks)
     executor.run()
     plot_buy_sell_points(executor, "T")
